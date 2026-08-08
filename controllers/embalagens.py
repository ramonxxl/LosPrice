"""
LosPrice - Controller de embalagens
====================================

Embalagem e sempre custo POR UNIDADE: comprou 100 caixas por R$ 45,00,
cada caixa custa R$ 0,45. Nao tem conversao de unidade nem fator de
correcao - por isso este controller e bem mais simples que o de ingredientes.

O que importa aqui e o alerta de peso: embalagem passando de ~10% do
custo do produto costuma ser sinal de desperdicio ou de item superdimensionado.
"""

from controllers.base import (
    ErroValidacao, fornecedores_ativos, nome_repetido, numero, opcional, texto,
)
from database.conexao import conectar

TIPOS = [
    "Caixa", "Saco", "Sacola", "Copo", "Tampa", "Papel", "Marmita",
    "Bandeja", "Pote", "Guardanapo", "Talher", "Etiqueta", "Filme", "Outros",
]

# Acima disso a embalagem come um pedaco relevante do produto.
LIMITE_PESO_PCT = 10.0


# ---------------------------------------------------------------------------
# Leitura
# ---------------------------------------------------------------------------

_SELECT = """
    SELECT e.*, f.nome AS fornecedor_nome
      FROM embalagens e
      LEFT JOIN fornecedores f ON f.id = e.fornecedor_id
"""


def listar(busca=None, tipo=None, incluir_inativas=False):
    condicoes, parametros = [], []

    if not incluir_inativas:
        condicoes.append("e.ativo = 1")
    if busca:
        condicoes.append("(e.nome LIKE ? OR e.tipo LIKE ?)")
        alvo = f"%{busca}%"
        parametros += [alvo, alvo]
    if tipo and tipo != "Todos":
        condicoes.append("e.tipo = ?")
        parametros.append(tipo)

    sql = _SELECT
    if condicoes:
        sql += " WHERE " + " AND ".join(condicoes)
    sql += " ORDER BY e.nome COLLATE NOCASE"

    with conectar() as cur:
        cur.execute(sql, parametros)
        return [dict(linha) for linha in cur.fetchall()]


def obter(embalagem_id):
    with conectar() as cur:
        cur.execute(_SELECT + " WHERE e.id = ?", (embalagem_id,))
        linha = cur.fetchone()
    return dict(linha) if linha else None


def tipos_em_uso():
    with conectar() as cur:
        cur.execute(
            "SELECT DISTINCT tipo FROM embalagens "
            " WHERE tipo IS NOT NULL AND tipo <> '' ORDER BY tipo COLLATE NOCASE"
        )
        return [linha["tipo"] for linha in cur.fetchall()]


def fornecedores():
    return fornecedores_ativos()


def estatisticas():
    with conectar() as cur:
        cur.execute("SELECT COUNT(*) AS n, AVG(custo_unitario) AS media, "
                    "       MAX(custo_unitario) AS maior "
                    "  FROM embalagens WHERE ativo = 1")
        linha = cur.fetchone()
    return {
        "total": linha["n"] or 0,
        "media": linha["media"] or 0.0,
        "maior": linha["maior"] or 0.0,
    }


# ---------------------------------------------------------------------------
# Validacao
# ---------------------------------------------------------------------------


def validar(dados, embalagem_id=None):
    nome = texto(dados.get("nome"), "o nome da embalagem")

    qtd = numero(dados.get("qtd_comprada"), "Quantidade comprada", minimo=0)
    valor = numero(dados.get("valor_pago"), "Valor pago", minimo=-0.01)

    if qtd != int(qtd):
        raise ErroValidacao("A quantidade de embalagens deve ser um numero "
                            "inteiro de unidades.")

    if nome_repetido("embalagens", nome, embalagem_id):
        raise ErroValidacao(f"Ja existe uma embalagem chamada '{nome}'.")

    return {
        "nome": nome,
        "tipo": opcional(dados.get("tipo")),
        "qtd_comprada": qtd,
        "valor_pago": valor,
        "custo_unitario": valor / qtd,
        "fornecedor_id": dados.get("fornecedor_id"),
        "observacoes": opcional(dados.get("observacoes")),
    }


# ---------------------------------------------------------------------------
# Escrita
# ---------------------------------------------------------------------------


def criar(dados):
    registro = validar(dados)
    with conectar() as cur:
        cur.execute(
            """
            INSERT INTO embalagens
                (nome, tipo, qtd_comprada, valor_pago, custo_unitario,
                 fornecedor_id, observacoes)
            VALUES (:nome, :tipo, :qtd_comprada, :valor_pago, :custo_unitario,
                    :fornecedor_id, :observacoes)
            """,
            registro,
        )
        return cur.lastrowid


def atualizar(embalagem_id, dados):
    """Retorna o resumo da mudanca, igual ao controller de ingredientes."""
    anterior = obter(embalagem_id)
    if not anterior:
        raise ErroValidacao("Embalagem nao encontrada.")

    registro = validar(dados, embalagem_id)
    mudou_preco = abs(registro["custo_unitario"] - anterior["custo_unitario"]) > 1e-9

    with conectar() as cur:
        cur.execute(
            """
            UPDATE embalagens SET
                nome = :nome, tipo = :tipo, qtd_comprada = :qtd_comprada,
                valor_pago = :valor_pago, custo_unitario = :custo_unitario,
                fornecedor_id = :fornecedor_id, observacoes = :observacoes,
                atualizado_em = datetime('now', 'localtime')
             WHERE id = :id
            """,
            {**registro, "id": embalagem_id},
        )

    from core.calculo import variacao_percentual

    return {
        "custo_antigo": anterior["custo_unitario"],
        "custo_novo": registro["custo_unitario"],
        "variacao_pct": variacao_percentual(anterior["custo_unitario"],
                                            registro["custo_unitario"]),
        "mudou_preco": mudou_preco,
        "receitas_afetadas": receitas_afetadas(embalagem_id) if mudou_preco else [],
    }


def excluir(embalagem_id):
    """Em uso vira desativacao, para nao quebrar as fichas tecnicas."""
    usos = receitas_afetadas(embalagem_id)
    if usos:
        with conectar() as cur:
            cur.execute("UPDATE embalagens SET ativo = 0, "
                        "atualizado_em = datetime('now', 'localtime') WHERE id = ?",
                        (embalagem_id,))
        return {"apagado": False, "receitas": usos}

    with conectar() as cur:
        cur.execute("DELETE FROM embalagens WHERE id = ?", (embalagem_id,))
    return {"apagado": True, "receitas": []}


def reativar(embalagem_id):
    with conectar() as cur:
        cur.execute("UPDATE embalagens SET ativo = 1 WHERE id = ?", (embalagem_id,))


# ---------------------------------------------------------------------------
# Impacto
# ---------------------------------------------------------------------------


def receitas_afetadas(embalagem_id):
    with conectar() as cur:
        cur.execute(
            """
            SELECT DISTINCT r.id, r.nome
              FROM receita_embalagens re
              JOIN receitas r ON r.id = re.receita_id
             WHERE re.embalagem_id = ?
             ORDER BY r.nome COLLATE NOCASE
            """,
            (embalagem_id,),
        )
        return [dict(linha) for linha in cur.fetchall()]


def peso_no_produto(custo_embalagem, custo_produto):
    """
    Quanto a embalagem representa do custo total.
    Retorna (percentual, alerta) - alerta True quando passa do limite.
    """
    total = (custo_embalagem or 0) + (custo_produto or 0)
    if total <= 0:
        return 0.0, False
    pct = custo_embalagem / total * 100.0
    return pct, pct > LIMITE_PESO_PCT


def descrever_compra(embalagem):
    """'100 un por R$ 45,00' para a coluna da tabela."""
    from utils.tema import formatar_moeda

    qtd = f"{embalagem['qtd_comprada']:g}"
    return f"{qtd} un · {formatar_moeda(embalagem['valor_pago'])}"
