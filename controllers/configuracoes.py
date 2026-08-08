"""
LosPrice - Controller de configuracoes
=======================================

Reune o que estava espalhado: dados da empresa, regime tributario,
taxas de cada canal, custos fixos mensais e backup.

O rateio de custo fixo e o ponto que mais muda o resultado do usuario.
Em vez de chutar "10% de custo fixo", ele lanca aluguel, energia, gas e
salarios, informa quantas unidades vende por mes, e o sistema devolve
o rateio real - em R$ por unidade e em % sobre o faturamento.
"""

from controllers.base import ErroValidacao, numero, opcional, texto
from database.conexao import (
    PASTA_BACKUP, conectar, fazer_backup, obter_config,
    restaurar_backup, salvar_config,
)

# Aliquota de partida por regime. O usuario pode sobrescrever.
REGIMES = {
    "MEI": 0.0,
    "Simples Nacional - Anexo I": 4.0,
    "Simples Nacional - Anexo III": 6.0,
    "Simples Nacional - Anexo V": 15.5,
    "Personalizado": 0.0,
}

CATEGORIAS_CUSTO = [
    "Aluguel", "Energia", "Agua", "Gas", "Internet", "Salarios",
    "Contador", "Software", "Marketing", "Manutencao", "Outros",
]


# ---------------------------------------------------------------------------
# Empresa
# ---------------------------------------------------------------------------


def empresa():
    return {
        "nome": obter_config("empresa_nome", "") or "",
        "cnpj": obter_config("empresa_cnpj", "") or "",
        "regime": obter_config("regime_tributario", "MEI") or "MEI",
        "imposto_pct": float(obter_config("imposto_pct", "0") or 0),
        "margem_padrao_pct": float(obter_config("margem_padrao_pct", "30") or 30),
        "cartao_pct_padrao": float(obter_config("cartao_pct_padrao", "3.5") or 3.5),
        "custo_fixo_pct": float(obter_config("custo_fixo_pct", "0") or 0),
        "arredondar": obter_config("arredondar_preco", "1") == "1",
        "backup_automatico": obter_config("backup_automatico", "1") == "1",
    }


def salvar_empresa(dados):
    nome = opcional(dados.get("nome"))

    imposto = numero(dados.get("imposto_pct"), "Imposto", minimo=-0.01,
                     maximo=99.99, obrigatorio=False, padrao=0.0)
    margem = numero(dados.get("margem_padrao_pct"), "Margem padrao", minimo=-0.01,
                    maximo=99.99, obrigatorio=False, padrao=30.0)
    cartao = numero(dados.get("cartao_pct_padrao"), "Taxa de cartao", minimo=-0.01,
                    maximo=99.99, obrigatorio=False, padrao=3.5)
    fixo = numero(dados.get("custo_fixo_pct"), "Custo fixo", minimo=-0.01,
                  maximo=99.99, obrigatorio=False, padrao=0.0)

    salvar_config("empresa_nome", nome or "")
    salvar_config("empresa_cnpj", opcional(dados.get("cnpj")) or "")
    salvar_config("regime_tributario", dados.get("regime") or "MEI")
    salvar_config("imposto_pct", imposto)
    salvar_config("margem_padrao_pct", margem)
    salvar_config("cartao_pct_padrao", cartao)
    salvar_config("custo_fixo_pct", fixo)
    salvar_config("arredondar_preco", "1" if dados.get("arredondar") else "0")
    salvar_config("backup_automatico", "1" if dados.get("backup_automatico") else "0")


def aliquota_do_regime(regime):
    return REGIMES.get(regime, 0.0)


# ---------------------------------------------------------------------------
# Canais de venda
# ---------------------------------------------------------------------------


def canais(incluir_inativos=True):
    sql = "SELECT * FROM canais"
    if not incluir_inativos:
        sql += " WHERE ativo = 1"
    sql += " ORDER BY ordem, id"

    with conectar() as cur:
        cur.execute(sql)
        return [dict(linha) for linha in cur.fetchall()]


def validar_canal(dados, canal_id=None):
    nome = texto(dados.get("nome"), "o nome do canal")

    comissao = numero(dados.get("comissao_pct"), "Comissao", minimo=-0.01,
                      maximo=99.99, obrigatorio=False, padrao=0.0)
    cartao = numero(dados.get("cartao_pct"), "Taxa de cartao", minimo=-0.01,
                    maximo=99.99, obrigatorio=False, padrao=0.0)
    fixa = numero(dados.get("taxa_fixa"), "Taxa fixa", minimo=-0.01,
                  obrigatorio=False, padrao=0.0)

    if comissao + cartao >= 100:
        raise ErroValidacao("Comissao e cartao somados nao podem chegar a 100%.")

    with conectar() as cur:
        sql = "SELECT id FROM canais WHERE nome = ? COLLATE NOCASE"
        parametros = [nome]
        if canal_id:
            sql += " AND id <> ?"
            parametros.append(canal_id)
        cur.execute(sql, parametros)
        if cur.fetchone():
            raise ErroValidacao(f"Ja existe um canal chamado '{nome}'.")

    return {
        "nome": nome,
        "comissao_pct": comissao,
        "cartao_pct": cartao,
        "taxa_fixa": fixa,
        "cor": dados.get("cor") or "#FF6B00",
    }


def criar_canal(dados):
    registro = validar_canal(dados)
    with conectar() as cur:
        cur.execute("SELECT COALESCE(MAX(ordem), 0) + 1 AS proxima FROM canais")
        registro["ordem"] = cur.fetchone()["proxima"]
        cur.execute(
            """
            INSERT INTO canais (nome, comissao_pct, cartao_pct, taxa_fixa, cor, ordem)
            VALUES (:nome, :comissao_pct, :cartao_pct, :taxa_fixa, :cor, :ordem)
            """,
            registro,
        )
        return cur.lastrowid


def atualizar_canal(canal_id, dados):
    registro = validar_canal(dados, canal_id)
    with conectar() as cur:
        cur.execute(
            """
            UPDATE canais SET nome = :nome, comissao_pct = :comissao_pct,
                   cartao_pct = :cartao_pct, taxa_fixa = :taxa_fixa, cor = :cor
             WHERE id = :id
            """,
            {**registro, "id": canal_id},
        )


def alternar_canal(canal_id, ativo):
    with conectar() as cur:
        cur.execute("UPDATE canais SET ativo = ? WHERE id = ?",
                    (1 if ativo else 0, canal_id))


def excluir_canal(canal_id):
    """Canal com precificacao gravada e desativado, para nao perder historico."""
    with conectar() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM precificacao WHERE canal_id = ?",
                    (canal_id,))
        usado = cur.fetchone()["n"] > 0

    if usado:
        alternar_canal(canal_id, False)
        return {"apagado": False}

    with conectar() as cur:
        cur.execute("DELETE FROM canais WHERE id = ?", (canal_id,))
    return {"apagado": True}


# ---------------------------------------------------------------------------
# Custos fixos mensais
# ---------------------------------------------------------------------------


def custos_fixos(incluir_inativos=False):
    sql = "SELECT * FROM custos_fixos"
    if not incluir_inativos:
        sql += " WHERE ativo = 1"
    sql += " ORDER BY valor_mensal DESC"

    with conectar() as cur:
        cur.execute(sql)
        return [dict(linha) for linha in cur.fetchall()]


def total_custo_fixo():
    with conectar() as cur:
        cur.execute("SELECT COALESCE(SUM(valor_mensal), 0) AS total "
                    "  FROM custos_fixos WHERE ativo = 1")
        return cur.fetchone()["total"]


def criar_custo_fixo(dados):
    descricao = texto(dados.get("descricao"), "a descricao do custo")
    valor = numero(dados.get("valor_mensal"), "Valor mensal", minimo=-0.01)

    with conectar() as cur:
        cur.execute(
            "INSERT INTO custos_fixos (descricao, categoria, valor_mensal) "
            "VALUES (?, ?, ?)",
            (descricao, opcional(dados.get("categoria")), valor),
        )
        return cur.lastrowid


def atualizar_custo_fixo(custo_id, dados):
    descricao = texto(dados.get("descricao"), "a descricao do custo")
    valor = numero(dados.get("valor_mensal"), "Valor mensal", minimo=-0.01)

    with conectar() as cur:
        cur.execute(
            "UPDATE custos_fixos SET descricao = ?, categoria = ?, valor_mensal = ? "
            " WHERE id = ?",
            (descricao, opcional(dados.get("categoria")), valor, custo_id),
        )


def excluir_custo_fixo(custo_id):
    with conectar() as cur:
        cur.execute("DELETE FROM custos_fixos WHERE id = ?", (custo_id,))


def rateio(unidades_por_mes):
    """
    Converte o custo fixo do mes em R$ por unidade produzida.
    E a alternativa honesta ao 'chuta 10%'.
    """
    total = total_custo_fixo()
    unidades = numero(unidades_por_mes, "Unidades por mes", minimo=0,
                      obrigatorio=False, padrao=None)

    if not unidades:
        return {"total": total, "unidades": None, "por_unidade": None}

    return {
        "total": total,
        "unidades": unidades,
        "por_unidade": total / unidades,
    }


def rateio_percentual(faturamento_mensal):
    """Custo fixo como percentual do faturamento - formato que a tela de preco usa."""
    total = total_custo_fixo()
    faturamento = numero(faturamento_mensal, "Faturamento mensal", minimo=0,
                         obrigatorio=False, padrao=None)
    if not faturamento:
        return None
    return total / faturamento * 100.0


# ---------------------------------------------------------------------------
# Backup
# ---------------------------------------------------------------------------


def gerar_backup():
    caminho = fazer_backup(int(obter_config("backups_manter", "10") or 10))
    if not caminho:
        raise ErroValidacao("Nao ha banco de dados para copiar ainda.")
    return caminho


def listar_backups():
    import os

    if not os.path.exists(PASTA_BACKUP):
        return []

    arquivos = []
    for nome in os.listdir(PASTA_BACKUP):
        if not (nome.startswith("losprice_") and nome.endswith(".db")):
            continue
        caminho = os.path.join(PASTA_BACKUP, nome)
        info = os.stat(caminho)
        arquivos.append({
            "nome": nome,
            "caminho": caminho,
            "tamanho": info.st_size,
            "data": info.st_mtime,
        })

    return sorted(arquivos, key=lambda a: a["data"], reverse=True)


def restaurar(caminho):
    restaurar_backup(caminho)


def resumo_banco():
    """Contagem por tabela, mostrada na aba de backup."""
    tabelas = [
        ("Ingredientes", "ingredientes"),
        ("Embalagens", "embalagens"),
        ("Receitas", "receitas"),
        ("Fornecedores", "fornecedores"),
        ("Precificacoes", "precificacao"),
        ("Historico de precos", "historico_precos"),
    ]
    resultado = []
    with conectar() as cur:
        for rotulo, tabela in tabelas:
            cur.execute(f"SELECT COUNT(*) AS n FROM {tabela}")
            resultado.append((rotulo, cur.fetchone()["n"]))
    return resultado
