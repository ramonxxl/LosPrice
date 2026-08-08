"""
LosPrice - Controller de fornecedores
======================================

Cadastro simples, mas com um detalhe util: como o historico de precos
guarda de quem foi cada compra, da para responder "qual fornecedor
esta mais barato neste item" quando o mesmo insumo ja foi comprado
de mais de um lugar.
"""

from controllers.base import ErroValidacao, nome_repetido, opcional, texto
from database.conexao import conectar


# ---------------------------------------------------------------------------
# Leitura
# ---------------------------------------------------------------------------


def listar(busca=None, incluir_inativos=False):
    condicoes, parametros = [], []

    if not incluir_inativos:
        condicoes.append("f.ativo = 1")
    if busca:
        condicoes.append("(f.nome LIKE ? OR f.contato LIKE ? OR f.telefone LIKE ?)")
        alvo = f"%{busca}%"
        parametros += [alvo, alvo, alvo]

    sql = """
        SELECT f.*,
               (SELECT COUNT(*) FROM ingredientes i
                 WHERE i.fornecedor_id = f.id AND i.ativo = 1) AS qtd_ingredientes,
               (SELECT COUNT(*) FROM embalagens e
                 WHERE e.fornecedor_id = f.id AND e.ativo = 1) AS qtd_embalagens
          FROM fornecedores f
    """
    if condicoes:
        sql += " WHERE " + " AND ".join(condicoes)
    sql += " ORDER BY f.nome COLLATE NOCASE"

    with conectar() as cur:
        cur.execute(sql, parametros)
        fornecedores = [dict(linha) for linha in cur.fetchall()]

    for fornecedor in fornecedores:
        fornecedor["total_itens"] = (fornecedor["qtd_ingredientes"]
                                     + fornecedor["qtd_embalagens"])
    return fornecedores


def obter(fornecedor_id):
    with conectar() as cur:
        cur.execute("SELECT * FROM fornecedores WHERE id = ?", (fornecedor_id,))
        linha = cur.fetchone()
    return dict(linha) if linha else None


def itens(fornecedor_id):
    """Tudo que este fornecedor entrega, ingredientes e embalagens juntos."""
    resultado = []

    with conectar() as cur:
        cur.execute(
            """
            SELECT nome, categoria, qtd_comprada, unidade_compra, valor_pago,
                   custo_unitario, unidade_base, ativo
              FROM ingredientes
             WHERE fornecedor_id = ?
             ORDER BY nome COLLATE NOCASE
            """,
            (fornecedor_id,),
        )
        for linha in cur.fetchall():
            resultado.append(dict(linha) | {"tipo": "Ingrediente"})

        cur.execute(
            """
            SELECT nome, tipo AS categoria, qtd_comprada, valor_pago,
                   custo_unitario, ativo
              FROM embalagens
             WHERE fornecedor_id = ?
             ORDER BY nome COLLATE NOCASE
            """,
            (fornecedor_id,),
        )
        for linha in cur.fetchall():
            resultado.append(dict(linha) | {"tipo": "Embalagem",
                                            "unidade_compra": "UN",
                                            "unidade_base": "UN"})

    return resultado


def gasto_total(fornecedor_id):
    """Soma do que ja foi lancado como compra deste fornecedor."""
    with conectar() as cur:
        cur.execute(
            "SELECT COALESCE(SUM(valor_pago), 0) AS total FROM historico_precos "
            " WHERE fornecedor_id = ?",
            (fornecedor_id,),
        )
        historico = cur.fetchone()["total"]

        cur.execute(
            "SELECT COALESCE(SUM(valor_pago), 0) AS total FROM embalagens "
            " WHERE fornecedor_id = ?",
            (fornecedor_id,),
        )
        embalagens = cur.fetchone()["total"]

    return historico + embalagens


def comparativo():
    """
    Insumos ja comprados de mais de um fornecedor, com o melhor preco.
    Usa o historico, que guarda de quem foi cada compra.
    """
    with conectar() as cur:
        cur.execute(
            """
            SELECT i.id, i.nome, i.unidade_base,
                   COUNT(DISTINCT h.fornecedor_id) AS fornecedores
              FROM historico_precos h
              JOIN ingredientes i ON i.id = h.ingrediente_id
             WHERE h.fornecedor_id IS NOT NULL
             GROUP BY i.id
            HAVING fornecedores > 1
             ORDER BY i.nome COLLATE NOCASE
            """
        )
        candidatos = [dict(linha) for linha in cur.fetchall()]

        resultado = []
        for item in candidatos:
            cur.execute(
                """
                SELECT f.nome AS fornecedor, MIN(h.custo_unitario) AS custo
                  FROM historico_precos h
                  JOIN fornecedores f ON f.id = h.fornecedor_id
                 WHERE h.ingrediente_id = ?
                 GROUP BY h.fornecedor_id
                 ORDER BY custo
                """,
                (item["id"],),
            )
            ofertas = [dict(linha) for linha in cur.fetchall()]
            if len(ofertas) < 2:
                continue

            melhor, pior = ofertas[0], ofertas[-1]
            economia = pior["custo"] - melhor["custo"]
            resultado.append({
                "ingrediente": item["nome"],
                "unidade_base": item["unidade_base"],
                "melhor_fornecedor": melhor["fornecedor"],
                "melhor_custo": melhor["custo"],
                "pior_fornecedor": pior["fornecedor"],
                "pior_custo": pior["custo"],
                "economia": economia,
                "economia_pct": (economia / pior["custo"] * 100) if pior["custo"] else 0,
            })

    return resultado


def estatisticas():
    with conectar() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM fornecedores WHERE ativo = 1")
        total = cur.fetchone()["n"]
        cur.execute(
            "SELECT COUNT(*) AS n FROM ingredientes "
            " WHERE ativo = 1 AND fornecedor_id IS NULL"
        )
        sem_fornecedor = cur.fetchone()["n"]
    return {"total": total, "itens_sem_fornecedor": sem_fornecedor}


# ---------------------------------------------------------------------------
# Escrita
# ---------------------------------------------------------------------------


def validar(dados, fornecedor_id=None):
    nome = texto(dados.get("nome"), "o nome do fornecedor")

    if nome_repetido("fornecedores", nome, fornecedor_id):
        raise ErroValidacao(f"Ja existe um fornecedor chamado '{nome}'.")

    return {
        "nome": nome,
        "contato": opcional(dados.get("contato")),
        "telefone": opcional(dados.get("telefone")),
        "email": opcional(dados.get("email")),
        "cnpj": opcional(dados.get("cnpj")),
        "observacoes": opcional(dados.get("observacoes")),
    }


def criar(dados):
    registro = validar(dados)
    with conectar() as cur:
        cur.execute(
            """
            INSERT INTO fornecedores (nome, contato, telefone, email, cnpj, observacoes)
            VALUES (:nome, :contato, :telefone, :email, :cnpj, :observacoes)
            """,
            registro,
        )
        return cur.lastrowid


def atualizar(fornecedor_id, dados):
    if not obter(fornecedor_id):
        raise ErroValidacao("Fornecedor nao encontrado.")

    registro = validar(dados, fornecedor_id)
    with conectar() as cur:
        cur.execute(
            """
            UPDATE fornecedores SET
                nome = :nome, contato = :contato, telefone = :telefone,
                email = :email, cnpj = :cnpj, observacoes = :observacoes
             WHERE id = :id
            """,
            {**registro, "id": fornecedor_id},
        )


def excluir(fornecedor_id):
    """
    Com itens vinculados, desativa. Apagar deixaria os insumos orfaos
    e a gente perderia de quem eles vieram.
    """
    vinculados = itens(fornecedor_id)
    if vinculados:
        with conectar() as cur:
            cur.execute("UPDATE fornecedores SET ativo = 0 WHERE id = ?",
                        (fornecedor_id,))
        return {"apagado": False, "itens": len(vinculados)}

    with conectar() as cur:
        cur.execute("DELETE FROM fornecedores WHERE id = ?", (fornecedor_id,))
    return {"apagado": True, "itens": 0}


def reativar(fornecedor_id):
    with conectar() as cur:
        cur.execute("UPDATE fornecedores SET ativo = 1 WHERE id = ?", (fornecedor_id,))
