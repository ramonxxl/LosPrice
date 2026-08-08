"""
LosPrice - Camada de banco de dados
====================================
Sistema Inteligente de Precificacao

Responsavel por:
    - Conexao com o SQLite
    - Criacao do schema
    - Dados padrao (canais de venda e configuracoes)
    - Backup automatico

Regra do projeto: nenhuma tela acessa o banco diretamente.
Todo acesso passa pelos controllers.
"""

import os
import shutil
import sqlite3
import sys
from contextlib import contextmanager
from datetime import datetime

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------

# Rodando como .exe do PyInstaller, o codigo vive numa pasta interna que e
# substituida a cada atualizacao. Banco, backups e relatorios precisam ficar
# FORA dela, ao lado do executavel, senao o usuario perde os dados ao
# atualizar ou mover o programa.
CONGELADO = getattr(sys, "frozen", False)

PASTA_DATABASE = os.path.dirname(os.path.abspath(__file__))

if CONGELADO:
    PASTA_RAIZ = os.path.dirname(sys.executable)
    PASTA_DADOS = os.path.join(PASTA_RAIZ, "dados")
else:
    PASTA_RAIZ = os.path.dirname(PASTA_DATABASE)
    PASTA_DADOS = PASTA_DATABASE

PASTA_BACKUP = os.path.join(PASTA_RAIZ, "backups")
CAMINHO_BANCO = os.path.join(PASTA_DADOS, "losprice.db")


def caminho_recurso(*partes):
    """
    Caminho de um arquivo empacotado (assets/). No .exe eles ficam em
    sys._MEIPASS; em desenvolvimento, na raiz do projeto.
    """
    base = getattr(sys, "_MEIPASS", None) or os.path.dirname(PASTA_DATABASE)
    return os.path.join(base, *partes)

# Unidades base usadas internamente. Tudo e convertido para uma delas.
UNIDADE_BASE_PESO = "G"
UNIDADE_BASE_VOLUME = "ML"
UNIDADE_BASE_UNIDADE = "UN"

# Fatores de conversao para a unidade base
CONVERSOES = {
    "KG": (UNIDADE_BASE_PESO, 1000.0),
    "G": (UNIDADE_BASE_PESO, 1.0),
    "L": (UNIDADE_BASE_VOLUME, 1000.0),
    "ML": (UNIDADE_BASE_VOLUME, 1.0),
    "UN": (UNIDADE_BASE_UNIDADE, 1.0),
    "DZ": (UNIDADE_BASE_UNIDADE, 12.0),
    "PCT": (UNIDADE_BASE_UNIDADE, 1.0),
}


# ---------------------------------------------------------------------------
# Conexao
# ---------------------------------------------------------------------------


def _preparar_conexao(conexao):
    """Aplica os PRAGMAs que o projeto depende."""
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    conexao.execute("PRAGMA journal_mode = WAL")


def abrir_conexao():
    """Retorna uma conexao ja configurada. Quem chama e responsavel por fechar."""
    os.makedirs(PASTA_DADOS, exist_ok=True)
    conexao = sqlite3.connect(CAMINHO_BANCO)
    _preparar_conexao(conexao)
    return conexao


@contextmanager
def conectar():
    """
    Uso:
        with conectar() as cur:
            cur.execute("SELECT * FROM ingredientes")
            linhas = cur.fetchall()

    Faz commit no sucesso e rollback em caso de erro.
    """
    conexao = abrir_conexao()
    cursor = conexao.cursor()
    try:
        yield cursor
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

SCHEMA = """

-- Fornecedores -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fornecedores (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nome          TEXT    NOT NULL,
    contato       TEXT,
    telefone      TEXT,
    email         TEXT,
    cnpj          TEXT,
    observacoes   TEXT,
    ativo         INTEGER NOT NULL DEFAULT 1,
    criado_em     TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);


-- Ingredientes -------------------------------------------------------------
-- O usuario cadastra a COMPRA (5 kg por R$ 185,00) e o sistema deriva o
-- custo por unidade base (grama, ml ou unidade).
--
--   custo_unitario = (valor_pago / qtd_convertida) * fator_correcao
--
-- fator_correcao trata a perda de limpeza/coccao:
--   comprou 1000 g, aproveita 700 g  ->  fator = 1000 / 700 = 1.4286
CREATE TABLE IF NOT EXISTS ingredientes (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    nome           TEXT    NOT NULL,
    categoria      TEXT,
    marca          TEXT,

    unidade_compra TEXT    NOT NULL,          -- KG, G, L, ML, UN, DZ, PCT
    unidade_base   TEXT    NOT NULL,          -- G, ML ou UN
    qtd_comprada   REAL    NOT NULL CHECK (qtd_comprada > 0),
    valor_pago     REAL    NOT NULL CHECK (valor_pago >= 0),

    fator_correcao REAL    NOT NULL DEFAULT 1.0 CHECK (fator_correcao > 0),
    custo_unitario REAL    NOT NULL DEFAULT 0, -- custo por G / ML / UN, ja corrigido

    fornecedor_id  INTEGER,
    observacoes    TEXT,
    ativo          INTEGER NOT NULL DEFAULT 1,
    criado_em      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    atualizado_em  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),

    FOREIGN KEY (fornecedor_id) REFERENCES fornecedores (id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_ingredientes_nome      ON ingredientes (nome);
CREATE INDEX IF NOT EXISTS idx_ingredientes_categoria ON ingredientes (categoria);


-- Historico de precos ------------------------------------------------------
-- Cada atualizacao de preco vira uma linha. Alimenta os alertas de
-- "ingrediente subiu X%" e o grafico de variacao.
CREATE TABLE IF NOT EXISTS historico_precos (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    ingrediente_id INTEGER NOT NULL,
    qtd_comprada   REAL    NOT NULL,
    unidade_compra TEXT    NOT NULL,
    valor_pago     REAL    NOT NULL,
    custo_unitario REAL    NOT NULL,
    fornecedor_id  INTEGER,
    origem         TEXT    NOT NULL DEFAULT 'MANUAL',  -- MANUAL | NFE | IMPORTACAO
    data_registro  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),

    FOREIGN KEY (ingrediente_id) REFERENCES ingredientes (id) ON DELETE CASCADE,
    FOREIGN KEY (fornecedor_id)  REFERENCES fornecedores (id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_historico_ingrediente ON historico_precos (ingrediente_id);


-- Embalagens ---------------------------------------------------------------
-- Custo sempre por unidade. Comprou 100 caixas por R$ 45,00 -> R$ 0,45 cada.
CREATE TABLE IF NOT EXISTS embalagens (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    nome           TEXT    NOT NULL,
    tipo           TEXT,                       -- CAIXA, SACO, COPO, PAPEL, TAMPA...
    qtd_comprada   REAL    NOT NULL CHECK (qtd_comprada > 0),
    valor_pago     REAL    NOT NULL CHECK (valor_pago >= 0),
    custo_unitario REAL    NOT NULL DEFAULT 0,
    fornecedor_id  INTEGER,
    observacoes    TEXT,
    ativo          INTEGER NOT NULL DEFAULT 1,
    criado_em      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    atualizado_em  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),

    FOREIGN KEY (fornecedor_id) REFERENCES fornecedores (id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_embalagens_nome ON embalagens (nome);


-- Receitas / Fichas tecnicas -----------------------------------------------
CREATE TABLE IF NOT EXISTS receitas (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    nome           TEXT    NOT NULL,
    categoria      TEXT,                       -- PASTEL, PIZZA, BURGER, PORCAO...
    rendimento     REAL    NOT NULL DEFAULT 1 CHECK (rendimento > 0),
    unidade_rend   TEXT    NOT NULL DEFAULT 'UN',
    tempo_preparo  INTEGER,                    -- minutos
    modo_preparo   TEXT,
    imagem         TEXT,                       -- caminho relativo em assets/
    vendas_mes     REAL    NOT NULL DEFAULT 0, -- volume estimado, para engenharia de cardapio
    custo_total    REAL    NOT NULL DEFAULT 0, -- custo do lote inteiro
    custo_unitario REAL    NOT NULL DEFAULT 0, -- custo_total / rendimento
    ativo          INTEGER NOT NULL DEFAULT 1,
    criado_em      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    atualizado_em  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_receitas_nome ON receitas (nome);


-- Itens da receita: ingredientes -------------------------------------------
CREATE TABLE IF NOT EXISTS receita_ingredientes (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    receita_id     INTEGER NOT NULL,
    ingrediente_id INTEGER NOT NULL,
    quantidade     REAL    NOT NULL CHECK (quantidade > 0),
    unidade        TEXT    NOT NULL,           -- unidade digitada pelo usuario
    custo_calc     REAL    NOT NULL DEFAULT 0, -- congelado no momento do calculo

    FOREIGN KEY (receita_id)     REFERENCES receitas (id)     ON DELETE CASCADE,
    FOREIGN KEY (ingrediente_id) REFERENCES ingredientes (id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_ri_receita     ON receita_ingredientes (receita_id);
CREATE INDEX IF NOT EXISTS idx_ri_ingrediente ON receita_ingredientes (ingrediente_id);


-- Itens da receita: embalagens ---------------------------------------------
CREATE TABLE IF NOT EXISTS receita_embalagens (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    receita_id   INTEGER NOT NULL,
    embalagem_id INTEGER NOT NULL,
    quantidade   REAL    NOT NULL DEFAULT 1 CHECK (quantidade > 0),
    custo_calc   REAL    NOT NULL DEFAULT 0,

    FOREIGN KEY (receita_id)   REFERENCES receitas (id)   ON DELETE CASCADE,
    FOREIGN KEY (embalagem_id) REFERENCES embalagens (id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_re_receita ON receita_embalagens (receita_id);


-- Canais de venda ----------------------------------------------------------
-- Todos os percentuais incidem sobre o PRECO DE VENDA, nunca sobre o custo.
CREATE TABLE IF NOT EXISTS canais (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    nome         TEXT    NOT NULL UNIQUE,
    comissao_pct REAL    NOT NULL DEFAULT 0,   -- taxa da plataforma
    cartao_pct   REAL    NOT NULL DEFAULT 0,   -- taxa da maquininha/gateway
    taxa_fixa    REAL    NOT NULL DEFAULT 0,   -- valor em R$ por pedido
    cor          TEXT    NOT NULL DEFAULT '#FF6B00',
    ordem        INTEGER NOT NULL DEFAULT 0,
    ativo        INTEGER NOT NULL DEFAULT 1
);


-- Precificacao -------------------------------------------------------------
-- Uma linha por receita x canal.
CREATE TABLE IF NOT EXISTS precificacao (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    receita_id      INTEGER NOT NULL,
    canal_id        INTEGER NOT NULL,

    margem_pct      REAL    NOT NULL DEFAULT 0,  -- lucro desejado sobre a venda
    imposto_pct     REAL    NOT NULL DEFAULT 0,
    custo_fixo_pct  REAL    NOT NULL DEFAULT 0,  -- rateio de energia/gas/aluguel
    custo_fixo_rs   REAL    NOT NULL DEFAULT 0,  -- rateio em valor absoluto

    preco_sugerido  REAL    NOT NULL DEFAULT 0,  -- resultado do calculo
    preco_praticado REAL,                        -- o que o usuario cobra de fato
    lucro_liquido   REAL    NOT NULL DEFAULT 0,
    margem_real_pct REAL    NOT NULL DEFAULT 0,

    atualizado_em   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),

    UNIQUE (receita_id, canal_id),
    FOREIGN KEY (receita_id) REFERENCES receitas (id) ON DELETE CASCADE,
    FOREIGN KEY (canal_id)   REFERENCES canais (id)   ON DELETE CASCADE
);


-- Custos fixos mensais -----------------------------------------------------
-- Base para o rateio real (aluguel, energia, gas, salarios, internet...).
CREATE TABLE IF NOT EXISTS custos_fixos (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    descricao    TEXT    NOT NULL,
    categoria    TEXT,
    valor_mensal REAL    NOT NULL DEFAULT 0,
    ativo        INTEGER NOT NULL DEFAULT 1,
    criado_em    TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);


-- Configuracoes ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS configuracoes (
    chave     TEXT PRIMARY KEY,
    valor     TEXT,
    descricao TEXT
);
"""


# ---------------------------------------------------------------------------
# Migracoes
# ---------------------------------------------------------------------------

# Colunas adicionadas depois que o schema original ja estava em uso.
# Cada entrada: (tabela, coluna, definicao SQL).
# CREATE TABLE IF NOT EXISTS nao altera tabela existente, entao bancos
# antigos precisam do ALTER TABLE.
MIGRACOES_COLUNAS = [
    # volume mensal estimado, base da engenharia de cardapio
    ("receitas", "vendas_mes", "REAL NOT NULL DEFAULT 0"),
]


def _colunas(cur, tabela):
    cur.execute(f"PRAGMA table_info({tabela})")
    return {linha["name"] for linha in cur.fetchall()}


def aplicar_migracoes():
    """Roda no inicio. Idempotente: o que ja existe e ignorado."""
    aplicadas = []
    with conectar() as cur:
        for tabela, coluna, definicao in MIGRACOES_COLUNAS:
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (tabela,),
            )
            if not cur.fetchone():
                continue
            if coluna in _colunas(cur, tabela):
                continue
            cur.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {definicao}")
            aplicadas.append(f"{tabela}.{coluna}")
    return aplicadas


# ---------------------------------------------------------------------------
# Dados padrao
# ---------------------------------------------------------------------------

CANAIS_PADRAO = [
    # nome                         comissao  cartao  fixa   cor        ordem
    ("Balcao",                        0.0,    0.0,   0.0, "#2E9E5B", 1),
    ("WhatsApp / Delivery proprio",   0.0,    3.5,   0.0, "#25D366", 2),
    ("iFood - Entrega propria",      12.0,    0.0,   0.0, "#EA1D2C", 3),
    ("iFood - Entrega iFood",        27.0,    0.0,   0.0, "#EA1D2C", 4),
    ("99Food",                       20.0,    0.0,   0.0, "#FFD400", 5),
    ("Rappi",                        25.0,    0.0,   0.0, "#FF441F", 6),
]

CONFIG_PADRAO = [
    ("empresa_nome",        "",      "Nome do estabelecimento"),
    ("empresa_cnpj",        "",      "CNPJ do estabelecimento"),
    ("regime_tributario",   "MEI",   "MEI, SIMPLES_I, SIMPLES_III, SIMPLES_V"),
    ("imposto_pct",         "0",     "Aliquota de imposto sobre a venda (%)"),
    ("margem_padrao_pct",   "30",    "Margem de lucro sugerida (%)"),
    ("cartao_pct_padrao",   "3.5",   "Taxa media de cartao (%)"),
    ("custo_fixo_pct",      "0",     "Rateio de custo fixo sobre a venda (%)"),
    ("arredondar_preco",    "1",     "Arredondar preco sugerido para .90"),
    ("tema",                "escuro", "escuro ou claro"),
    ("backup_automatico",   "1",     "Gerar backup ao abrir o sistema"),
    ("backups_manter",      "10",    "Quantidade de backups a preservar"),
]


def popular_padroes():
    """Insere canais e configuracoes padrao apenas se ainda nao existirem."""
    with conectar() as cur:
        for nome, comissao, cartao, fixa, cor, ordem in CANAIS_PADRAO:
            cur.execute(
                """
                INSERT OR IGNORE INTO canais
                    (nome, comissao_pct, cartao_pct, taxa_fixa, cor, ordem)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (nome, comissao, cartao, fixa, cor, ordem),
            )

        for chave, valor, descricao in CONFIG_PADRAO:
            cur.execute(
                "INSERT OR IGNORE INTO configuracoes (chave, valor, descricao) VALUES (?, ?, ?)",
                (chave, valor, descricao),
            )


# ---------------------------------------------------------------------------
# Configuracoes (atalhos)
# ---------------------------------------------------------------------------


def obter_config(chave, padrao=None):
    with conectar() as cur:
        cur.execute("SELECT valor FROM configuracoes WHERE chave = ?", (chave,))
        linha = cur.fetchone()
    return linha["valor"] if linha else padrao


def salvar_config(chave, valor):
    with conectar() as cur:
        cur.execute(
            """
            INSERT INTO configuracoes (chave, valor) VALUES (?, ?)
            ON CONFLICT (chave) DO UPDATE SET valor = excluded.valor
            """,
            (chave, str(valor)),
        )


# ---------------------------------------------------------------------------
# Backup
# ---------------------------------------------------------------------------


def fazer_backup(manter=10):
    """
    Copia o banco para /backups com data e hora no nome.
    Mantem apenas os N mais recentes. Retorna o caminho gerado ou None.
    """
    if not os.path.exists(CAMINHO_BANCO):
        return None

    os.makedirs(PASTA_BACKUP, exist_ok=True)
    carimbo = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    destino = os.path.join(PASTA_BACKUP, f"losprice_{carimbo}.db")

    # backup nativo do sqlite: consistente mesmo com o banco aberto
    origem = abrir_conexao()
    try:
        copia = sqlite3.connect(destino)
        try:
            origem.backup(copia)
        finally:
            copia.close()
    finally:
        origem.close()

    _limpar_backups_antigos(manter)
    return destino


def _limpar_backups_antigos(manter):
    if manter <= 0:
        return
    arquivos = sorted(
        (
            os.path.join(PASTA_BACKUP, nome)
            for nome in os.listdir(PASTA_BACKUP)
            if nome.startswith("losprice_") and nome.endswith(".db")
        ),
        reverse=True,
    )
    for antigo in arquivos[manter:]:
        try:
            os.remove(antigo)
        except OSError:
            pass


def restaurar_backup(caminho):
    """Substitui o banco atual por um backup. Guarda o atual antes de trocar."""
    if not os.path.exists(caminho):
        raise FileNotFoundError(f"Backup nao encontrado: {caminho}")
    fazer_backup()
    shutil.copy2(caminho, CAMINHO_BANCO)


# ---------------------------------------------------------------------------
# Inicializacao
# ---------------------------------------------------------------------------


def inicializar(com_backup=True):
    """
    Ponto de entrada chamado pelo main.py.
    Cria o banco se nao existir, garante o schema e os dados padrao.
    """
    banco_novo = not os.path.exists(CAMINHO_BANCO)

    if com_backup and not banco_novo:
        try:
            manter = int(obter_config("backups_manter", "10"))
            if obter_config("backup_automatico", "1") == "1":
                fazer_backup(manter)
        except Exception:
            pass  # backup nunca deve impedir o sistema de abrir

    conexao = abrir_conexao()
    try:
        conexao.executescript(SCHEMA)
        conexao.commit()
    finally:
        conexao.close()

    aplicar_migracoes()
    popular_padroes()
    return banco_novo


if __name__ == "__main__":
    novo = inicializar(com_backup=False)
    print("LosPrice - banco de dados")
    print(f"  Arquivo : {CAMINHO_BANCO}")
    print(f"  Situacao: {'criado agora' if novo else 'ja existia'}")

    with conectar() as cur:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tabelas = [linha["name"] for linha in cur.fetchall() if not linha["name"].startswith("sqlite_")]
        cur.execute("SELECT nome, comissao_pct, cartao_pct FROM canais ORDER BY ordem")
        canais = cur.fetchall()

    print(f"\n  {len(tabelas)} tabelas: {', '.join(tabelas)}")
    print("\n  Canais de venda:")
    for canal in canais:
        print(f"    - {canal['nome']:<32} comissao {canal['comissao_pct']:>5.1f}%  cartao {canal['cartao_pct']:>4.1f}%")
