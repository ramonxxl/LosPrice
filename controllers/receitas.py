"""
LosPrice - Controller de receitas (fichas tecnicas)
====================================================

Onde ingredientes e embalagens viram um produto com custo real.

Ponto importante do desenho: o custo fica gravado em receitas.custo_total,
mas os precos dos ingredientes mudam o tempo todo. Entao existem duas
nocoes de custo:

    custo gravado  - o que foi calculado da ultima vez
    custo atual    - recalculado agora, com os precos de hoje

Quando os dois divergem, a ficha esta DESATUALIZADA. E isso que alimenta
o alerta 'a mussarela subiu 18%, 12 receitas precisam ser recalculadas'.
"""

from controllers.base import ErroValidacao, nome_repetido, numero, opcional, texto
from core.calculo import ROTULO_BASE, calcular_receita, mesma_grandeza
from database.conexao import conectar

CATEGORIAS = [
    "Pastel", "Pizza", "Hamburguer", "Porcao", "Salgado",
    "Marmita", "Bebida", "Doce", "Combo", "Outros",
]

UNIDADES_RENDIMENTO = ["UN", "PORCAO", "KG", "L", "FATIA"]

# Divergencia em reais a partir da qual a ficha e considerada desatualizada.
TOLERANCIA = 0.005

# Unidades que a ficha aceita conforme a unidade base do ingrediente.
UNIDADES_POR_BASE = {
    "G": ["G", "KG"],
    "ML": ["ML", "L"],
    "UN": ["UN", "DZ"],
}


# ---------------------------------------------------------------------------
# Leitura
# ---------------------------------------------------------------------------


def listar(busca=None, categoria=None, incluir_inativas=False):
    condicoes, parametros = [], []

    if not incluir_inativas:
        condicoes.append("r.ativo = 1")
    if busca:
        condicoes.append("(r.nome LIKE ? OR r.categoria LIKE ?)")
        alvo = f"%{busca}%"
        parametros += [alvo, alvo]
    if categoria and categoria != "Todas":
        condicoes.append("r.categoria = ?")
        parametros.append(categoria)

    sql = """
        SELECT r.*,
               (SELECT COUNT(*) FROM receita_ingredientes ri WHERE ri.receita_id = r.id)
                   AS qtd_ingredientes,
               (SELECT COUNT(*) FROM receita_embalagens re WHERE re.receita_id = r.id)
                   AS qtd_embalagens
          FROM receitas r
    """
    if condicoes:
        sql += " WHERE " + " AND ".join(condicoes)
    sql += " ORDER BY r.nome COLLATE NOCASE"

    with conectar() as cur:
        cur.execute(sql, parametros)
        receitas = [dict(linha) for linha in cur.fetchall()]

    # marca as fichas cujo custo mudou desde o ultimo calculo
    for receita in receitas:
        atual = _custo_atual(receita["id"])
        receita["custo_atual"] = atual
        receita["desatualizada"] = abs(atual - receita["custo_total"]) > TOLERANCIA

    return receitas


def obter(receita_id):
    with conectar() as cur:
        cur.execute("SELECT * FROM receitas WHERE id = ?", (receita_id,))
        linha = cur.fetchone()
        if not linha:
            return None
        receita = dict(linha)

    receita["itens"] = itens(receita_id)
    return receita


def itens(receita_id):
    """Ficha completa: ingredientes e embalagens em uma lista so."""
    resultado = []

    with conectar() as cur:
        cur.execute(
            """
            SELECT ri.id, ri.ingrediente_id AS item_id, ri.quantidade, ri.unidade,
                   ri.custo_calc, i.nome, i.categoria, i.custo_unitario,
                   i.unidade_base, i.ativo
              FROM receita_ingredientes ri
              JOIN ingredientes i ON i.id = ri.ingrediente_id
             WHERE ri.receita_id = ?
             ORDER BY ri.id
            """,
            (receita_id,),
        )
        for linha in cur.fetchall():
            item = dict(linha)
            item["tipo"] = "ingrediente"
            resultado.append(item)

        cur.execute(
            """
            SELECT re.id, re.embalagem_id AS item_id, re.quantidade,
                   re.custo_calc, e.nome, e.tipo AS categoria, e.custo_unitario,
                   e.ativo
              FROM receita_embalagens re
              JOIN embalagens e ON e.id = re.embalagem_id
             WHERE re.receita_id = ?
             ORDER BY re.id
            """,
            (receita_id,),
        )
        for linha in cur.fetchall():
            item = dict(linha)
            item["tipo"] = "embalagem"
            item["unidade"] = "UN"
            item["unidade_base"] = "UN"
            resultado.append(item)

    return resultado


def disponiveis():
    """Ingredientes e embalagens ativos, para o seletor da ficha."""
    with conectar() as cur:
        cur.execute(
            "SELECT id, nome, categoria, custo_unitario, unidade_base "
            "  FROM ingredientes WHERE ativo = 1 ORDER BY nome COLLATE NOCASE"
        )
        ingredientes = [dict(l) | {"tipo": "ingrediente"} for l in cur.fetchall()]

        cur.execute(
            "SELECT id, nome, tipo AS categoria, custo_unitario "
            "  FROM embalagens WHERE ativo = 1 ORDER BY nome COLLATE NOCASE"
        )
        embalagens = [dict(l) | {"tipo": "embalagem", "unidade_base": "UN"}
                      for l in cur.fetchall()]

    return ingredientes, embalagens


def categorias():
    with conectar() as cur:
        cur.execute(
            "SELECT DISTINCT categoria FROM receitas "
            " WHERE categoria IS NOT NULL AND categoria <> '' "
            " ORDER BY categoria COLLATE NOCASE"
        )
        return [linha["categoria"] for linha in cur.fetchall()]


def estatisticas(desatualizadas=None):
    """
    desatualizadas: informe a contagem quando ja tiver a lista em maos.
    listar() ja calcula o custo atual de cada ficha; recalcular tudo aqui
    de novo dobrava o trabalho a cada recarga de tela.
    """
    with conectar() as cur:
        cur.execute("SELECT COUNT(*) AS n, AVG(custo_unitario) AS media "
                    "  FROM receitas WHERE ativo = 1")
        linha = cur.fetchone()

    if desatualizadas is None:
        desatualizadas = len(listar_desatualizadas())

    return {
        "total": linha["n"] or 0,
        "custo_medio": linha["media"] or 0.0,
        "desatualizadas": desatualizadas,
    }


def listar_desatualizadas():
    """Fichas cujo custo mudou porque algum insumo mudou de preco."""
    with conectar() as cur:
        cur.execute("SELECT id, nome, custo_total FROM receitas WHERE ativo = 1")
        receitas = [dict(l) for l in cur.fetchall()]

    pendentes = []
    for receita in receitas:
        atual = _custo_atual(receita["id"])
        if abs(atual - receita["custo_total"]) > TOLERANCIA:
            receita["custo_atual"] = atual
            receita["diferenca"] = atual - receita["custo_total"]
            pendentes.append(receita)
    return pendentes


# ---------------------------------------------------------------------------
# Calculo
# ---------------------------------------------------------------------------


def _montar_entrada(lista_itens):
    """Converte os itens da ficha no formato que core.calculo espera."""
    ingredientes, embalagens = [], []

    for item in lista_itens:
        if item["tipo"] == "ingrediente":
            ingredientes.append({
                "nome": item["nome"],
                "custo_por_base": item["custo_unitario"],
                "unidade_base": item["unidade_base"],
                "quantidade": item["quantidade"],
                "unidade": item["unidade"],
            })
        else:
            embalagens.append({
                "nome": item["nome"],
                "custo_unitario": item["custo_unitario"],
                "quantidade": item["quantidade"],
            })

    return ingredientes, embalagens


def calcular(lista_itens, rendimento=1.0):
    """Custo de uma ficha em memoria, sem tocar no banco. Usado ao vivo no formulario."""
    ingredientes, embalagens = _montar_entrada(lista_itens)
    return calcular_receita(ingredientes, embalagens, rendimento)


def _custo_atual(receita_id):
    """Recalcula com os precos de hoje."""
    lista = itens(receita_id)
    if not lista:
        return 0.0
    try:
        return calcular(lista, 1.0).custo_total
    except Exception:
        return 0.0


def recalcular(receita_id):
    """Grava o custo atualizado na receita e em cada linha da ficha."""
    receita = obter(receita_id)
    if not receita:
        raise ErroValidacao("Receita nao encontrada.")

    resultado = calcular(receita["itens"], receita["rendimento"])

    with conectar() as cur:
        cur.execute(
            "UPDATE receitas SET custo_total = ?, custo_unitario = ?, "
            "       atualizado_em = datetime('now', 'localtime') WHERE id = ?",
            (resultado.custo_total, resultado.custo_unitario, receita_id),
        )
        for item, detalhe in zip(receita["itens"], resultado.detalhes):
            tabela = ("receita_ingredientes" if item["tipo"] == "ingrediente"
                      else "receita_embalagens")
            cur.execute(f"UPDATE {tabela} SET custo_calc = ? WHERE id = ?",
                        (detalhe["custo"], item["id"]))

    return resultado


def recalcular_todas():
    """Atualiza todas as fichas defasadas de uma vez."""
    pendentes = listar_desatualizadas()
    for receita in pendentes:
        recalcular(receita["id"])
    return len(pendentes)


# ---------------------------------------------------------------------------
# Validacao
# ---------------------------------------------------------------------------


def validar(dados, receita_id=None):
    nome = texto(dados.get("nome"), "o nome da receita")

    rendimento = numero(dados.get("rendimento"), "Rendimento", minimo=0,
                        obrigatorio=False, padrao=1.0)

    tempo = dados.get("tempo_preparo")
    tempo = numero(tempo, "Tempo de preparo", minimo=-1, obrigatorio=False, padrao=None)

    lista = dados.get("itens") or []
    if not lista:
        raise ErroValidacao("Adicione pelo menos um ingrediente a ficha tecnica.")

    for item in lista:
        if item["quantidade"] is None or item["quantidade"] <= 0:
            raise ErroValidacao(f"A quantidade de '{item['nome']}' deve ser "
                                "maior que zero.")
        if item["tipo"] == "ingrediente" and not mesma_grandeza(
                item["unidade"], item["unidade_base"]):
            base = ROTULO_BASE.get(item["unidade_base"], item["unidade_base"])
            raise ErroValidacao(
                f"'{item['nome']}' e medido em {base}, mas a ficha pede "
                f"{item['unidade'].lower()}. Escolha uma unidade compativel."
            )

    if nome_repetido("receitas", nome, receita_id):
        raise ErroValidacao(f"Ja existe uma receita chamada '{nome}'.")

    return {
        "nome": nome,
        "categoria": opcional(dados.get("categoria")),
        "rendimento": rendimento,
        "unidade_rend": (dados.get("unidade_rend") or "UN").upper(),
        "tempo_preparo": int(tempo) if tempo else None,
        "modo_preparo": opcional(dados.get("modo_preparo")),
        "itens": lista,
    }


# ---------------------------------------------------------------------------
# Escrita
# ---------------------------------------------------------------------------


def criar(dados):
    registro = validar(dados)
    lista = registro.pop("itens")
    resultado = calcular(lista, registro["rendimento"])

    with conectar() as cur:
        cur.execute(
            """
            INSERT INTO receitas
                (nome, categoria, rendimento, unidade_rend, tempo_preparo,
                 modo_preparo, custo_total, custo_unitario)
            VALUES (:nome, :categoria, :rendimento, :unidade_rend, :tempo_preparo,
                    :modo_preparo, :custo_total, :custo_unitario)
            """,
            {**registro, "custo_total": resultado.custo_total,
             "custo_unitario": resultado.custo_unitario},
        )
        receita_id = cur.lastrowid
        _gravar_itens(cur, receita_id, lista, resultado)

    return receita_id


def atualizar(receita_id, dados):
    if not obter(receita_id):
        raise ErroValidacao("Receita nao encontrada.")

    registro = validar(dados, receita_id)
    lista = registro.pop("itens")
    resultado = calcular(lista, registro["rendimento"])

    with conectar() as cur:
        cur.execute(
            """
            UPDATE receitas SET
                nome = :nome, categoria = :categoria, rendimento = :rendimento,
                unidade_rend = :unidade_rend, tempo_preparo = :tempo_preparo,
                modo_preparo = :modo_preparo, custo_total = :custo_total,
                custo_unitario = :custo_unitario,
                atualizado_em = datetime('now', 'localtime')
             WHERE id = :id
            """,
            {**registro, "id": receita_id,
             "custo_total": resultado.custo_total,
             "custo_unitario": resultado.custo_unitario},
        )
        # a ficha e regravada por inteiro: mais simples e sem risco de sobra
        cur.execute("DELETE FROM receita_ingredientes WHERE receita_id = ?", (receita_id,))
        cur.execute("DELETE FROM receita_embalagens WHERE receita_id = ?", (receita_id,))
        _gravar_itens(cur, receita_id, lista, resultado)

    return receita_id


def _gravar_itens(cur, receita_id, lista, resultado):
    # Casa item com custo por POSICAO, nao por nome: a mesma ficha pode
    # repetir o mesmo ingrediente em duas linhas (150 g agora, 50 g no final).
    fila = {"ingrediente": [], "embalagem": []}
    for detalhe in resultado.detalhes:
        fila[detalhe["tipo"]].append(detalhe["custo"])

    indice = {"ingrediente": 0, "embalagem": 0}

    for item in lista:
        tipo = item["tipo"]
        posicao = indice[tipo]
        custo = fila[tipo][posicao] if posicao < len(fila[tipo]) else 0.0
        indice[tipo] += 1

        if tipo == "ingrediente":
            cur.execute(
                """
                INSERT INTO receita_ingredientes
                    (receita_id, ingrediente_id, quantidade, unidade, custo_calc)
                VALUES (?, ?, ?, ?, ?)
                """,
                (receita_id, item["item_id"], item["quantidade"],
                 item["unidade"].upper(), custo),
            )
        else:
            cur.execute(
                """
                INSERT INTO receita_embalagens
                    (receita_id, embalagem_id, quantidade, custo_calc)
                VALUES (?, ?, ?, ?)
                """,
                (receita_id, item["item_id"], item["quantidade"], custo),
            )


def excluir(receita_id):
    """Receita precificada e desativada; sem precificacao, e apagada."""
    with conectar() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM precificacao WHERE receita_id = ?",
                    (receita_id,))
        precificada = cur.fetchone()["n"] > 0

    if precificada:
        with conectar() as cur:
            cur.execute("UPDATE receitas SET ativo = 0, "
                        "atualizado_em = datetime('now', 'localtime') WHERE id = ?",
                        (receita_id,))
        return {"apagado": False}

    with conectar() as cur:
        cur.execute("DELETE FROM receitas WHERE id = ?", (receita_id,))
    return {"apagado": True}


def duplicar(receita_id):
    """Copia a ficha inteira. Util para variacoes: 'Pastel de Carne com Queijo'."""
    receita = obter(receita_id)
    if not receita:
        raise ErroValidacao("Receita nao encontrada.")

    base = receita["nome"]
    nome = f"{base} (copia)"
    contador = 2
    while nome_repetido("receitas", nome):
        nome = f"{base} (copia {contador})"
        contador += 1

    return criar({
        "nome": nome,
        "categoria": receita["categoria"],
        "rendimento": receita["rendimento"],
        "unidade_rend": receita["unidade_rend"],
        "tempo_preparo": receita["tempo_preparo"],
        "modo_preparo": receita["modo_preparo"],
        "itens": receita["itens"],
    })


def unidades_para(unidade_base):
    """Unidades que a ficha aceita para um item medido nessa base."""
    return UNIDADES_POR_BASE.get(unidade_base, ["UN"])
