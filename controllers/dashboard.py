"""
LosPrice - Controller do dashboard
===================================

Reune numeros que ja existem espalhados nos outros controllers e devolve
prontos para a tela desenhar.

O criterio de tudo aqui: nao mostrar numero bonito, mostrar o que exige
acao. Um dashboard que so informa vira enfeite; o que aponta problema
faz o dono abrir o sistema todo dia.
"""

from controllers import receitas as rec_ctrl
from core.calculo import variacao_percentual
from database.conexao import conectar

# Variacao de preco a partir da qual vale avisar
LIMITE_VARIACAO = 5.0


# ---------------------------------------------------------------------------
# Numeros do topo
# ---------------------------------------------------------------------------


def resumo():
    with conectar() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM ingredientes WHERE ativo = 1")
        ingredientes = cur.fetchone()["n"]

        cur.execute("SELECT COUNT(*) AS n FROM embalagens WHERE ativo = 1")
        embalagens = cur.fetchone()["n"]

        cur.execute("SELECT COUNT(*) AS n, COALESCE(AVG(custo_unitario), 0) AS custo "
                    "  FROM receitas WHERE ativo = 1")
        linha = cur.fetchone()
        receitas, custo_medio = linha["n"], linha["custo"]

        cur.execute("SELECT COUNT(*) AS n FROM fornecedores WHERE ativo = 1")
        fornecedores = cur.fetchone()["n"]

        cur.execute(
            """
            SELECT COUNT(DISTINCT p.receita_id) AS precificadas,
                   COALESCE(AVG(p.margem_real_pct), 0) AS margem,
                   COALESCE(SUM(CASE WHEN p.margem_real_pct < 0 THEN 1 ELSE 0 END), 0)
                       AS prejuizo
              FROM precificacao p
              JOIN receitas r ON r.id = p.receita_id
             WHERE r.ativo = 1
            """
        )
        linha = cur.fetchone()

    return {
        "ingredientes": ingredientes,
        "embalagens": embalagens,
        "receitas": receitas,
        "fornecedores": fornecedores,
        "custo_medio": custo_medio,
        "precificadas": linha["precificadas"],
        "margem_media": linha["margem"],
        "no_prejuizo": linha["prejuizo"],
        "desatualizadas": len(rec_ctrl.listar_desatualizadas()),
    }


# ---------------------------------------------------------------------------
# Alertas
# ---------------------------------------------------------------------------


def alertas():
    """
    Lista de problemas acionaveis, do mais grave para o menos.
    Cada item traz a tela para onde o usuario deve ir.
    """
    resultado = []

    # 1. vendendo no prejuizo
    with conectar() as cur:
        cur.execute(
            """
            SELECT r.nome AS receita, c.nome AS canal,
                   p.preco_praticado, p.lucro_liquido, p.margem_real_pct
              FROM precificacao p
              JOIN receitas r ON r.id = p.receita_id
              JOIN canais   c ON c.id = p.canal_id
             WHERE p.margem_real_pct < 0 AND r.ativo = 1 AND c.ativo = 1
             ORDER BY p.margem_real_pct
            """
        )
        prejuizo = [dict(l) for l in cur.fetchall()]

    if prejuizo:
        detalhes = [f"{p['receita']} no {p['canal']}: "
                    f"{p['margem_real_pct']:.1f}%" for p in prejuizo[:4]]
        resultado.append({
            "gravidade": "prejuizo",
            "titulo": f"{len(prejuizo)} preco(s) vendendo no prejuizo",
            "detalhes": detalhes,
            "extra": len(prejuizo) - 4,
            "destino": "precificacao",
        })

    # 2. fichas defasadas
    defasadas = rec_ctrl.listar_desatualizadas()
    if defasadas:
        detalhes = [f"{d['nome']}: {d['diferenca']:+.2f} no custo"
                    for d in defasadas[:4]]
        resultado.append({
            "gravidade": "atencao",
            "titulo": f"{len(defasadas)} ficha(s) com custo defasado",
            "detalhes": detalhes,
            "extra": len(defasadas) - 4,
            "destino": "receitas",
        })

    # 3. insumos que subiram
    subidas = [v for v in variacoes(limite=20) if v["variacao_pct"] > LIMITE_VARIACAO]
    if subidas:
        detalhes = [f"{s['nome']}: +{s['variacao_pct']:.1f}%" for s in subidas[:4]]
        resultado.append({
            "gravidade": "atencao",
            "titulo": f"{len(subidas)} insumo(s) subiram de preco",
            "detalhes": detalhes,
            "extra": len(subidas) - 4,
            "destino": "ingredientes",
        })

    # 4. receitas sem preco definido
    with conectar() as cur:
        cur.execute(
            """
            SELECT r.nome FROM receitas r
             WHERE r.ativo = 1
               AND NOT EXISTS (SELECT 1 FROM precificacao p WHERE p.receita_id = r.id)
             ORDER BY r.nome COLLATE NOCASE
            """
        )
        sem_preco = [l["nome"] for l in cur.fetchall()]

    if sem_preco:
        resultado.append({
            "gravidade": "info",
            "titulo": f"{len(sem_preco)} receita(s) ainda sem preco definido",
            "detalhes": sem_preco[:4],
            "extra": len(sem_preco) - 4,
            "destino": "precificacao",
        })

    # 5. insumos sem fornecedor
    with conectar() as cur:
        cur.execute(
            "SELECT nome FROM ingredientes "
            " WHERE ativo = 1 AND fornecedor_id IS NULL ORDER BY nome COLLATE NOCASE"
        )
        sem_fornecedor = [l["nome"] for l in cur.fetchall()]

    if sem_fornecedor:
        resultado.append({
            "gravidade": "info",
            "titulo": f"{len(sem_fornecedor)} insumo(s) sem fornecedor",
            "detalhes": sem_fornecedor[:4],
            "extra": len(sem_fornecedor) - 4,
            "destino": "ingredientes",
        })

    return resultado


# ---------------------------------------------------------------------------
# Ranking de produtos
# ---------------------------------------------------------------------------


def ranking(limite=6):
    """Produtos precificados, do pior para o melhor resultado."""
    with conectar() as cur:
        cur.execute(
            """
            SELECT r.id, r.nome, r.categoria, r.custo_unitario,
                   AVG(p.margem_real_pct) AS margem,
                   AVG(p.lucro_liquido)   AS lucro,
                   COUNT(p.id)            AS canais
              FROM precificacao p
              JOIN receitas r ON r.id = p.receita_id
              JOIN canais   c ON c.id = p.canal_id
             WHERE r.ativo = 1 AND c.ativo = 1
             GROUP BY r.id
             ORDER BY margem
            """
        )
        produtos = [dict(l) for l in cur.fetchall()]

    return produtos[:limite]


def por_canal():
    """Resultado medio de cada canal - mostra onde o dinheiro fica."""
    with conectar() as cur:
        cur.execute(
            """
            SELECT c.nome, c.cor, c.comissao_pct,
                   COUNT(p.id)              AS produtos,
                   AVG(p.margem_real_pct)   AS margem,
                   AVG(p.lucro_liquido)     AS lucro,
                   AVG(p.preco_praticado)   AS preco
              FROM precificacao p
              JOIN canais   c ON c.id = p.canal_id
              JOIN receitas r ON r.id = p.receita_id
             WHERE c.ativo = 1 AND r.ativo = 1
             GROUP BY c.id
             ORDER BY c.ordem, c.id
            """
        )
        return [dict(l) for l in cur.fetchall()]


# ---------------------------------------------------------------------------
# Movimentacao de precos
# ---------------------------------------------------------------------------


def variacoes(limite=6):
    """Ultima variacao de preco de cada insumo que ja mudou pelo menos uma vez."""
    with conectar() as cur:
        cur.execute(
            """
            SELECT ingrediente_id, COUNT(*) AS n
              FROM historico_precos
             GROUP BY ingrediente_id
            HAVING n > 1
            """
        )
        candidatos = [l["ingrediente_id"] for l in cur.fetchall()]

        resultado = []
        for ingrediente_id in candidatos:
            cur.execute(
                """
                SELECT h.custo_unitario, h.data_registro, i.nome, i.unidade_base
                  FROM historico_precos h
                  JOIN ingredientes i ON i.id = h.ingrediente_id
                 WHERE h.ingrediente_id = ? AND i.ativo = 1
                 ORDER BY h.id DESC
                 LIMIT 2
                """,
                (ingrediente_id,),
            )
            linhas = cur.fetchall()
            if len(linhas) < 2:
                continue

            atual, anterior = linhas[0], linhas[1]
            variacao = variacao_percentual(anterior["custo_unitario"],
                                           atual["custo_unitario"])
            if variacao is None or abs(variacao) < 0.01:
                continue

            resultado.append({
                "nome": atual["nome"],
                "unidade_base": atual["unidade_base"],
                "custo_anterior": anterior["custo_unitario"],
                "custo_atual": atual["custo_unitario"],
                "variacao_pct": variacao,
                "data": atual["data_registro"],
            })

    resultado.sort(key=lambda v: abs(v["variacao_pct"]), reverse=True)
    return resultado[:limite]


def insumos_mais_pesados(limite=5):
    """
    Ingredientes que mais pesam no custo das fichas.
    E onde negociar com fornecedor rende mais.
    """
    with conectar() as cur:
        cur.execute(
            """
            SELECT i.nome, SUM(ri.custo_calc) AS total,
                   COUNT(DISTINCT ri.receita_id) AS receitas
              FROM receita_ingredientes ri
              JOIN ingredientes i ON i.id = ri.ingrediente_id
              JOIN receitas    r ON r.id = ri.receita_id
             WHERE r.ativo = 1
             GROUP BY i.id
             ORDER BY total DESC
             LIMIT ?
            """,
            (limite,),
        )
        itens = [dict(l) for l in cur.fetchall()]

    soma = sum(i["total"] for i in itens) or 1
    for item in itens:
        item["participacao_pct"] = item["total"] / soma * 100
    return itens
