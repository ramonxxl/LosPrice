"""
LosPrice - Controller de ingredientes
======================================

Faz a ponte entre a tela e o banco. A tela nunca escreve SQL,
o banco nunca sabe que existe interface.

Responsabilidades:
    - Validar os dados vindos do formulario
    - Derivar o custo por unidade base usando core.calculo
    - Gravar o historico de precos a cada alteracao
    - Avisar quais receitas ficaram desatualizadas
"""

from controllers.base import (
    ErroValidacao, fornecedores_ativos, nome_repetido, numero, opcional, texto,
)
from database.conexao import conectar
from core.calculo import (
    CONVERSOES, ErroCalculo, ROTULO_BASE,
    custo_unitario, fator_correcao, variacao_percentual,
)

UNIDADES_COMPRA = ["KG", "G", "L", "ML", "UN", "DZ", "PCT", "CX"]

CATEGORIAS_SUGERIDAS = [
    "Carnes", "Frios e Laticinios", "Hortifruti", "Massas", "Molhos",
    "Temperos", "Bebidas", "Doces", "Oleos e Gorduras", "Secos", "Outros",
]


# ---------------------------------------------------------------------------
# Leitura
# ---------------------------------------------------------------------------

_SELECT = """
    SELECT i.*, f.nome AS fornecedor_nome
      FROM ingredientes i
      LEFT JOIN fornecedores f ON f.id = i.fornecedor_id
"""


def listar(busca=None, categoria=None, incluir_inativos=False):
    condicoes, parametros = [], []

    if not incluir_inativos:
        condicoes.append("i.ativo = 1")
    if busca:
        condicoes.append("(i.nome LIKE ? OR i.marca LIKE ? OR i.categoria LIKE ?)")
        alvo = f"%{busca}%"
        parametros += [alvo, alvo, alvo]
    if categoria and categoria != "Todas":
        condicoes.append("i.categoria = ?")
        parametros.append(categoria)

    sql = _SELECT
    if condicoes:
        sql += " WHERE " + " AND ".join(condicoes)
    sql += " ORDER BY i.nome COLLATE NOCASE"

    with conectar() as cur:
        cur.execute(sql, parametros)
        return [dict(linha) for linha in cur.fetchall()]


def obter(ingrediente_id):
    with conectar() as cur:
        cur.execute(_SELECT + " WHERE i.id = ?", (ingrediente_id,))
        linha = cur.fetchone()
    return dict(linha) if linha else None


def categorias():
    """Categorias em uso, para o filtro."""
    with conectar() as cur:
        cur.execute(
            """
            SELECT DISTINCT categoria FROM ingredientes
             WHERE categoria IS NOT NULL AND categoria <> ''
             ORDER BY categoria COLLATE NOCASE
            """
        )
        return [linha["categoria"] for linha in cur.fetchall()]


def fornecedores():
    """Retorna [(id, nome)] dos fornecedores ativos."""
    return fornecedores_ativos()


def historico(ingrediente_id, limite=30):
    with conectar() as cur:
        cur.execute(
            """
            SELECT h.*, f.nome AS fornecedor_nome
              FROM historico_precos h
              LEFT JOIN fornecedores f ON f.id = h.fornecedor_id
             WHERE h.ingrediente_id = ?
             ORDER BY h.id DESC
             LIMIT ?
            """,
            (ingrediente_id, limite),
        )
        return [dict(linha) for linha in cur.fetchall()]


def estatisticas():
    with conectar() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM ingredientes WHERE ativo = 1")
        total = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(DISTINCT categoria) AS n FROM ingredientes "
                    "WHERE ativo = 1 AND categoria IS NOT NULL AND categoria <> ''")
        grupos = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) AS n FROM ingredientes "
                    "WHERE ativo = 1 AND fator_correcao > 1")
        com_perda = cur.fetchone()["n"]
    return {"total": total, "categorias": grupos, "com_fator": com_perda}


# ---------------------------------------------------------------------------
# Validacao
# ---------------------------------------------------------------------------


def validar(dados, ingrediente_id=None):
    """
    Recebe os dados crus do formulario e devolve o registro pronto para gravar,
    ja com custo_unitario e unidade_base calculados.
    """
    nome = texto(dados.get("nome"), "o nome do ingrediente")

    unidade = (dados.get("unidade_compra") or "").strip().upper()
    if unidade not in CONVERSOES:
        raise ErroValidacao(f"Unidade invalida: '{unidade}'.")

    qtd = numero(dados.get("qtd_comprada"), "Quantidade comprada", minimo=0)
    valor = numero(dados.get("valor_pago"), "Valor pago", minimo=-0.01)
    fator = numero(dados.get("fator_correcao"), "Fator de correcao",
                   minimo=0, obrigatorio=False, padrao=1.0)

    if fator < 1:
        raise ErroValidacao("O fator de correcao nao pode ser menor que 1. "
                            "Use 1 quando nao ha perda.")
    if fator > 10:
        raise ErroValidacao("Fator de correcao acima de 10 parece engano. "
                            "Confira os pesos bruto e liquido.")

    if nome_repetido("ingredientes", nome, ingrediente_id):
        raise ErroValidacao(f"Ja existe um ingrediente chamado '{nome}'.")

    try:
        custo, base = custo_unitario(qtd, unidade, valor, fator)
    except ErroCalculo as erro:
        raise ErroValidacao(str(erro))

    return {
        "nome": nome,
        "categoria": opcional(dados.get("categoria")),
        "marca": opcional(dados.get("marca")),
        "unidade_compra": unidade,
        "unidade_base": base,
        "qtd_comprada": qtd,
        "valor_pago": valor,
        "fator_correcao": fator,
        "custo_unitario": custo,
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
            INSERT INTO ingredientes
                (nome, categoria, marca, unidade_compra, unidade_base,
                 qtd_comprada, valor_pago, fator_correcao, custo_unitario,
                 fornecedor_id, observacoes)
            VALUES (:nome, :categoria, :marca, :unidade_compra, :unidade_base,
                    :qtd_comprada, :valor_pago, :fator_correcao, :custo_unitario,
                    :fornecedor_id, :observacoes)
            """,
            registro,
        )
        novo_id = cur.lastrowid
        _gravar_historico(cur, novo_id, registro)
    return novo_id


def atualizar(ingrediente_id, dados):
    """
    Retorna (custo_antigo, custo_novo, variacao_pct, receitas_afetadas).
    A tela usa isso para avisar 'subiu 18%, 12 receitas afetadas'.
    """
    anterior = obter(ingrediente_id)
    if not anterior:
        raise ErroValidacao("Ingrediente nao encontrado.")

    registro = validar(dados, ingrediente_id)
    mudou_preco = abs(registro["custo_unitario"] - anterior["custo_unitario"]) > 1e-9

    with conectar() as cur:
        cur.execute(
            """
            UPDATE ingredientes SET
                nome = :nome, categoria = :categoria, marca = :marca,
                unidade_compra = :unidade_compra, unidade_base = :unidade_base,
                qtd_comprada = :qtd_comprada, valor_pago = :valor_pago,
                fator_correcao = :fator_correcao, custo_unitario = :custo_unitario,
                fornecedor_id = :fornecedor_id, observacoes = :observacoes,
                atualizado_em = datetime('now', 'localtime')
             WHERE id = :id
            """,
            {**registro, "id": ingrediente_id},
        )
        if mudou_preco:
            _gravar_historico(cur, ingrediente_id, registro)

    variacao = variacao_percentual(anterior["custo_unitario"], registro["custo_unitario"])
    afetadas = receitas_afetadas(ingrediente_id) if mudou_preco else []

    return {
        "custo_antigo": anterior["custo_unitario"],
        "custo_novo": registro["custo_unitario"],
        "variacao_pct": variacao,
        "mudou_preco": mudou_preco,
        "receitas_afetadas": afetadas,
    }


def _gravar_historico(cur, ingrediente_id, registro, origem="MANUAL"):
    cur.execute(
        """
        INSERT INTO historico_precos
            (ingrediente_id, qtd_comprada, unidade_compra, valor_pago,
             custo_unitario, fornecedor_id, origem)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (ingrediente_id, registro["qtd_comprada"], registro["unidade_compra"],
         registro["valor_pago"], registro["custo_unitario"],
         registro["fornecedor_id"], origem),
    )


def excluir(ingrediente_id):
    """
    Nao apaga se o ingrediente estiver em uso: desativa.
    Assim as receitas antigas nao perdem a referencia.
    """
    usos = receitas_afetadas(ingrediente_id)
    if usos:
        with conectar() as cur:
            cur.execute("UPDATE ingredientes SET ativo = 0, "
                        "atualizado_em = datetime('now', 'localtime') WHERE id = ?",
                        (ingrediente_id,))
        return {"apagado": False, "receitas": usos}

    with conectar() as cur:
        cur.execute("DELETE FROM ingredientes WHERE id = ?", (ingrediente_id,))
    return {"apagado": True, "receitas": []}


def reativar(ingrediente_id):
    with conectar() as cur:
        cur.execute("UPDATE ingredientes SET ativo = 1 WHERE id = ?", (ingrediente_id,))


# ---------------------------------------------------------------------------
# Impacto nas receitas
# ---------------------------------------------------------------------------


def receitas_afetadas(ingrediente_id):
    """Receitas que usam este ingrediente."""
    with conectar() as cur:
        cur.execute(
            """
            SELECT DISTINCT r.id, r.nome
              FROM receita_ingredientes ri
              JOIN receitas r ON r.id = ri.receita_id
             WHERE ri.ingrediente_id = ?
             ORDER BY r.nome COLLATE NOCASE
            """,
            (ingrediente_id,),
        )
        return [dict(linha) for linha in cur.fetchall()]


def calcular_fator(peso_bruto, peso_liquido):
    """Auxiliar do formulario: converte pesos em fator de correcao."""
    bruto = numero(peso_bruto, "Peso bruto", minimo=0)
    liquido = numero(peso_liquido, "Peso limpo", minimo=0)
    try:
        return fator_correcao(bruto, liquido)
    except ErroCalculo as erro:
        raise ErroValidacao(str(erro))


def rotulo_unidade(unidade_base):
    return ROTULO_BASE.get(unidade_base, unidade_base)


def descrever_compra(ingrediente):
    """'5 kg por R$ 185,00' para a coluna da tabela."""
    from utils.tema import formatar_moeda, formatar_quantidade
    qtd = formatar_quantidade(ingrediente["qtd_comprada"],
                              ingrediente["unidade_compra"].lower())
    return f"{qtd} · {formatar_moeda(ingrediente['valor_pago'])}"
