"""
LosPrice - Importador do cardapio Los Pastelles
================================================

Carga inicial a partir do cardapio publicado. Cria:

    24 ingredientes  + 6 bebidas (revenda)
     3 embalagens
    62 fichas tecnicas de pastel + 6 de bebida

IMPORTANTE - as gramaturas sao REFERENCIA, nao medicao.
O cardapio diz "Pastel de Carne", nao diz quantos gramas de carne.
Os numeros abaixo sao pontos de partida plausiveis para uma pastelaria;
ajuste cada ficha na tela de Receitas com a sua medida real. Enquanto
isso nao for feito, o custo calculado nao vale como decisao de preco.

Os insumos entram com custo ZERO de proposito: assim nenhuma ficha
mostra um custo que parece verdadeiro sem ser.

    python scripts/importar_cardapio.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controllers import embalagens as emb_ctrl
from controllers import ingredientes as ing_ctrl
from controllers import receitas as rec_ctrl
from database import conexao

# ---------------------------------------------------------------------------
# Gramaturas de referencia
# ---------------------------------------------------------------------------

SOLO = 130        # recheio principal sozinho
COM_UM = 110      # principal acompanhado de 1 complemento
COM_DOIS = 100    # principal acompanhado de 2 complementos

QUEIJO = 40
CATUPIRY = 25
BACON = 20
MILHO = 25
AZEITONA = 12
BROCOLIS_COMP = 50
PRESUNTO = 30
TOMATE = 20
CEBOLA = 10
OREGANO = 1
DOCE = 45
FRUTA = 35

MASSA = 1         # unidade
OLEO = 12         # ml absorvidos na fritura

# ---------------------------------------------------------------------------
# Ingredientes
# ---------------------------------------------------------------------------

INGREDIENTES = [
    # nome,                categoria,             unidade
    ("Carne moida",        "Carnes",              "KG"),
    ("Frango desfiado",    "Carnes",              "KG"),
    ("Calabresa",          "Carnes",              "KG"),
    ("Costela desfiada",   "Carnes",              "KG"),
    ("Bacon",              "Carnes",              "KG"),
    ("Presunto",           "Frios e Laticinios",  "KG"),
    ("Queijo mussarela",   "Frios e Laticinios",  "KG"),
    ("Catupiry",           "Frios e Laticinios",  "KG"),
    ("Ovo",                "Outros",              "UN"),
    ("Palmito",            "Secos",               "KG"),
    ("Creme de palmito",   "Secos",               "KG"),
    ("Milho",              "Secos",               "KG"),
    ("Azeitona",           "Secos",               "KG"),
    ("Brocolis",           "Hortifruti",          "KG"),
    ("Tomate",             "Hortifruti",          "KG"),
    ("Cebola roxa",        "Hortifruti",          "KG"),
    ("Morango",            "Hortifruti",          "KG"),
    ("Banana",             "Hortifruti",          "KG"),
    ("Vinagrete",          "Hortifruti",          "KG"),
    ("Oregano",            "Temperos",            "KG"),
    ("Chocolate",          "Doces",               "KG"),
    ("Doce de leite",      "Doces",               "KG"),
    ("Massa de pastel",    "Massas",              "UN"),
    ("Oleo de soja",       "Oleos e Gorduras",    "L"),
]

BEBIDAS = [
    ("Agua 500 ml",              "Bebidas", "UN", 4.00),
    ("Refrigerante lata",        "Bebidas", "UN", 6.00),
    ("Suco Tropical 500 ml",     "Bebidas", "UN", 6.00),
    ("Coca-Cola 2 L",            "Bebidas", "UN", 16.00),
    ("Guarana Antarctica 2 L",   "Bebidas", "UN", 15.00),
    ("Guarana Joaninha 2 L",     "Bebidas", "UN", 10.00),
]

EMBALAGENS = [
    ("Saco de papel para pastel", "Saco"),
    ("Guardanapo",                "Guardanapo"),
    ("Sacola para delivery",      "Sacola"),
]

# ---------------------------------------------------------------------------
# Cardapio
# ---------------------------------------------------------------------------

# principal -> ingrediente correspondente
PRINCIPAIS = {
    "Carne": "Carne moida",
    "Frango": "Frango desfiado",
    "Calabresa": "Calabresa",
    "Costela": "Costela desfiada",
    "Palmito": "Palmito",
    "Brocolis": "Brocolis",
    "Queijo": "Queijo mussarela",
}

# complemento -> (ingrediente, quantidade, unidade)
COMPLEMENTOS = {
    "Queijo":   ("Queijo mussarela", QUEIJO, "G"),
    "Catupiry": ("Catupiry", CATUPIRY, "G"),
    "Bacon":    ("Bacon", BACON, "G"),
    "Milho":    ("Milho", MILHO, "G"),
    "Azeitona": ("Azeitona", AZEITONA, "G"),
    "Ovo":      ("Ovo", 1, "UN"),
    "Brocolis": ("Brocolis", BROCOLIS_COMP, "G"),
}

# (nome, categoria, preco, principal, [complementos])
SALGADOS = [
    # --- Tradicionais -----------------------------------------------------
    ("Carne",     "Pastel", 15.90, "Carne",     []),
    ("Queijo",    "Pastel", 15.90, "Queijo",    []),
    ("Frango",    "Pastel", 15.90, "Frango",    []),
    ("Calabresa", "Pastel", 15.90, "Calabresa", []),
    ("Palmito",   "Pastel", 15.90, "Palmito",   []),
    ("Costela",   "Pastel", 16.90, "Costela",   []),

    # --- Especiais - Linha Carne ------------------------------------------
    ("Carne com Queijo",            "Pastel", 16.90, "Carne", ["Queijo"]),
    ("Carne com Milho",             "Pastel", 16.90, "Carne", ["Milho"]),
    ("Carne com Azeitona",          "Pastel", 16.90, "Carne", ["Azeitona"]),
    ("Carne com Bacon",             "Pastel", 16.90, "Carne", ["Bacon"]),
    ("Carne com Ovo",               "Pastel", 16.90, "Carne", ["Ovo"]),
    ("Carne com Catupiry",          "Pastel", 16.90, "Carne", ["Catupiry"]),
    ("Carne com Queijo e Bacon",    "Pastel", 18.90, "Carne", ["Queijo", "Bacon"]),
    ("Carne com Queijo e Catupiry", "Pastel", 18.90, "Carne", ["Queijo", "Catupiry"]),

    # --- Especiais - Linha Frango -----------------------------------------
    ("Frango com Catupiry",          "Pastel", 16.90, "Frango", ["Catupiry"]),
    ("Frango com Milho",             "Pastel", 16.90, "Frango", ["Milho"]),
    ("Frango com Azeitona",          "Pastel", 16.90, "Frango", ["Azeitona"]),
    ("Frango com Bacon",             "Pastel", 16.90, "Frango", ["Bacon"]),
    ("Frango com Brocolis",          "Pastel", 16.90, "Frango", ["Brocolis"]),
    ("Frango com Queijo",            "Pastel", 16.90, "Frango", ["Queijo"]),
    ("Frango com Queijo e Bacon",    "Pastel", 18.90, "Frango", ["Queijo", "Bacon"]),
    ("Frango com Queijo e Catupiry", "Pastel", 18.90, "Frango", ["Queijo", "Catupiry"]),

    # --- Especiais - Linha Calabresa --------------------------------------
    ("Calabresa com Queijo",            "Pastel", 16.90, "Calabresa", ["Queijo"]),
    ("Calabresa com Milho",             "Pastel", 16.90, "Calabresa", ["Milho"]),
    ("Calabresa com Azeitona",          "Pastel", 16.90, "Calabresa", ["Azeitona"]),
    ("Calabresa com Bacon",             "Pastel", 16.90, "Calabresa", ["Bacon"]),
    ("Calabresa com Catupiry",          "Pastel", 16.90, "Calabresa", ["Catupiry"]),
    ("Calabresa com Queijo e Bacon",    "Pastel", 18.90, "Calabresa", ["Queijo", "Bacon"]),
    ("Calabresa com Queijo e Catupiry", "Pastel", 18.90, "Calabresa", ["Queijo", "Catupiry"]),

    # --- Especiais - Linha Costela ----------------------------------------
    ("Costela com Queijo",            "Pastel", 18.90, "Costela", ["Queijo"]),
    ("Costela com Milho",             "Pastel", 18.90, "Costela", ["Milho"]),
    ("Costela com Azeitona",          "Pastel", 18.90, "Costela", ["Azeitona"]),
    ("Costela com Bacon",             "Pastel", 18.90, "Costela", ["Bacon"]),
    ("Costela com Queijo e Bacon",    "Pastel", 20.90, "Costela", ["Queijo", "Bacon"]),
    ("Costela com Queijo e Catupiry", "Pastel", 20.90, "Costela", ["Queijo", "Catupiry"]),

    # --- Linha Fit --------------------------------------------------------
    ("Palmito com Queijo",   "Pastel Fit", 16.90, "Palmito",  ["Queijo"]),
    ("Palmito com Catupiry", "Pastel Fit", 16.90, "Palmito",  ["Catupiry"]),
    ("Brocolis com Bacon",   "Pastel Fit", 16.90, "Brocolis", ["Bacon"]),
    ("Brocolis com Catupiry","Pastel Fit", 16.90, "Brocolis", ["Catupiry"]),
    ("Palmito com Brocolis e Queijo", "Pastel Fit", 18.90, "Palmito",
     ["Brocolis", "Queijo"]),
]

# fichas montadas item a item (nome, categoria, preco, [(ingrediente, qtd, un)])
ESPECIAIS = [
    # --- Classicos da Casa ------------------------------------------------
    ("Pizza", "Pastel Classico", 15.90, [
        ("Queijo mussarela", 60, "G"), ("Tomate", TOMATE, "G"),
        ("Oregano", OREGANO, "G")]),
    ("Bauru", "Pastel Classico", 15.90, [
        ("Presunto", 35, "G"), ("Queijo mussarela", 45, "G"),
        ("Tomate", TOMATE, "G")]),
    ("Brasileiro", "Pastel Classico", 15.90, [
        ("Carne moida", COM_UM, "G"), ("Ovo", 1, "UN"),
        ("Azeitona", AZEITONA, "G")]),
    ("Caipira", "Pastel Classico", 16.90, [
        ("Frango desfiado", COM_DOIS, "G"), ("Milho", MILHO, "G"),
        ("Catupiry", CATUPIRY, "G")]),
    ("Caipira Bacon", "Pastel Classico", 18.90, [
        ("Frango desfiado", COM_DOIS, "G"), ("Milho", MILHO, "G"),
        ("Catupiry", CATUPIRY, "G"), ("Bacon", BACON, "G")]),
    ("Palmito Especial", "Pastel Classico", 16.90, [
        ("Palmito", COM_DOIS, "G"), ("Queijo mussarela", QUEIJO, "G"),
        ("Tomate", TOMATE, "G"), ("Oregano", OREGANO, "G")]),
    ("Portuguesa", "Pastel Classico", 18.90, [
        ("Presunto", PRESUNTO, "G"), ("Queijo mussarela", QUEIJO, "G"),
        ("Tomate", TOMATE, "G"), ("Cebola roxa", CEBOLA, "G"),
        ("Azeitona", AZEITONA, "G"), ("Ovo", 1, "UN"),
        ("Oregano", OREGANO, "G")]),

    # --- Premium ----------------------------------------------------------
    ("Los Pastelles", "Pastel Premium", 20.90, [
        ("Carne moida", COM_DOIS, "G"), ("Queijo mussarela", QUEIJO, "G"),
        ("Bacon", BACON, "G"), ("Catupiry", CATUPIRY, "G")]),
    ("Explosao de Frango", "Pastel Premium", 20.90, [
        ("Frango desfiado", COM_DOIS, "G"), ("Queijo mussarela", QUEIJO, "G"),
        ("Bacon", BACON, "G"), ("Catupiry", CATUPIRY, "G")]),
    ("Explosao de Calabresa", "Pastel Premium", 20.90, [
        ("Calabresa", COM_DOIS, "G"), ("Queijo mussarela", QUEIJO, "G"),
        ("Bacon", BACON, "G"), ("Catupiry", CATUPIRY, "G")]),
    ("Explosao de Costela", "Pastel Premium", 20.90, [
        ("Costela desfiada", COM_DOIS, "G"), ("Queijo mussarela", QUEIJO, "G"),
        ("Bacon", BACON, "G"), ("Catupiry", CATUPIRY, "G")]),
    ("Explosao de Brocolis", "Pastel Premium", 20.90, [
        ("Brocolis", COM_DOIS, "G"), ("Queijo mussarela", QUEIJO, "G"),
        ("Bacon", BACON, "G"), ("Catupiry", CATUPIRY, "G")]),
    ("Explosao de Palmito", "Pastel Premium", 20.90, [
        ("Palmito", COM_DOIS, "G"), ("Queijo mussarela", QUEIJO, "G"),
        ("Bacon", BACON, "G"), ("Catupiry", CATUPIRY, "G")]),
    ("Explosao de Queijo", "Pastel Premium", 16.90, [
        ("Queijo mussarela", 90, "G"), ("Bacon", BACON, "G"),
        ("Catupiry", CATUPIRY, "G")]),
    ("Explosao de Bacon", "Pastel Premium", 16.90, [
        ("Bacon", 60, "G"), ("Queijo mussarela", QUEIJO, "G"),
        ("Catupiry", CATUPIRY, "G")]),

    # --- Pasteis Doces ----------------------------------------------------
    ("Chocolate", "Pastel Doce", 16.90, [
        ("Chocolate", DOCE, "G")]),
    ("Chocolate com Morango", "Pastel Doce", 18.90, [
        ("Chocolate", DOCE, "G"), ("Morango", FRUTA, "G")]),
    ("Chocolate com Doce de Leite", "Pastel Doce", 18.90, [
        ("Chocolate", 30, "G"), ("Doce de leite", 30, "G")]),
    ("Chocolate com Banana", "Pastel Doce", 18.90, [
        ("Chocolate", DOCE, "G"), ("Banana", 40, "G")]),
    ("Doce de Leite", "Pastel Doce", 16.90, [
        ("Doce de leite", DOCE, "G")]),
    ("Banoffe", "Pastel Doce", 18.90, [
        ("Doce de leite", DOCE, "G"), ("Banana", 40, "G")]),
    ("Doce de Leite com Morango", "Pastel Doce", 18.90, [
        ("Doce de leite", DOCE, "G"), ("Morango", FRUTA, "G")]),
]


def base_do_pastel(doce=False):
    """Massa, oleo e embalagem entram em todo pastel."""
    itens = [("Massa de pastel", MASSA, "UN"), ("Oleo de soja", OLEO, "ML")]
    return itens


def montar_salgados():
    """Expande a tabela compacta em fichas completas."""
    resultado = []
    for nome, categoria, preco, principal, complementos in SALGADOS:
        quantidade = {0: SOLO, 1: COM_UM, 2: COM_DOIS}[len(complementos)]
        itens = [(PRINCIPAIS[principal], quantidade, "G")]
        for chave in complementos:
            ingrediente, qtd, unidade = COMPLEMENTOS[chave]
            itens.append((ingrediente, qtd, unidade))
        resultado.append((nome, categoria, preco, itens))
    return resultado


# ---------------------------------------------------------------------------
# Execucao
# ---------------------------------------------------------------------------

TABELAS_LIMPAS = [
    "receita_ingredientes", "receita_embalagens", "precificacao",
    "receitas", "historico_precos", "ingredientes", "embalagens",
]


def limpar(cur):
    for tabela in TABELAS_LIMPAS:
        cur.execute(f"DELETE FROM {tabela}")


def importar(limpar_antes=True):
    conexao.inicializar(com_backup=False)

    if limpar_antes:
        caminho = conexao.fazer_backup()
        print(f"  backup antes de limpar: {os.path.basename(caminho or '-')}")
        with conexao.conectar() as cur:
            limpar(cur)
        print("  dados anteriores removidos\n")

    OBS = "AJUSTAR: informe a quantidade e o valor da compra real."

    # --- ingredientes -----------------------------------------------------
    ids_ing = {}
    for nome, categoria, unidade in INGREDIENTES:
        ids_ing[nome] = ing_ctrl.criar({
            "nome": nome, "categoria": categoria, "qtd_comprada": "1",
            "unidade_compra": unidade, "valor_pago": "0",
            "fator_correcao": "1", "observacoes": OBS,
        })
    print(f"  {len(ids_ing)} ingredientes cadastrados")

    for nome, categoria, unidade, _preco in BEBIDAS:
        ids_ing[nome] = ing_ctrl.criar({
            "nome": nome, "categoria": categoria, "qtd_comprada": "1",
            "unidade_compra": unidade, "valor_pago": "0",
            "fator_correcao": "1", "observacoes": OBS,
        })
    print(f"  {len(BEBIDAS)} bebidas cadastradas como insumo de revenda")

    # --- embalagens -------------------------------------------------------
    ids_emb = {}
    for nome, tipo in EMBALAGENS:
        ids_emb[nome] = emb_ctrl.criar({
            "nome": nome, "tipo": tipo, "qtd_comprada": "1",
            "valor_pago": "0", "observacoes": OBS,
        })
    print(f"  {len(ids_emb)} embalagens cadastradas\n")

    # --- indice para montar as fichas -------------------------------------
    ingredientes = {i["nome"]: i for i in ing_ctrl.listar()}
    embalagens = {e["nome"]: e for e in emb_ctrl.listar()}

    def item_ing(nome, quantidade, unidade):
        base = ingredientes[nome]
        return {"tipo": "ingrediente", "item_id": base["id"], "nome": nome,
                "quantidade": quantidade, "unidade": unidade,
                "unidade_base": base["unidade_base"],
                "custo_unitario": base["custo_unitario"]}

    def item_emb(nome, quantidade=1):
        base = embalagens[nome]
        return {"tipo": "embalagem", "item_id": base["id"], "nome": nome,
                "quantidade": quantidade, "unidade": "UN",
                "unidade_base": "UN", "custo_unitario": base["custo_unitario"]}

    NOTA = ("FICHA DE RASCUNHO - as gramaturas sao referencia, nao medicao.\n"
            "Ajuste cada quantidade com a medida real da sua cozinha antes de\n"
            "usar o custo para decidir preco.")

    # --- fichas dos pasteis ----------------------------------------------
    criadas = 0
    precos = {}

    for nome, categoria, preco, itens in montar_salgados() + [
            (n, c, p, i) for n, c, p, i in ESPECIAIS]:
        ficha = [item_ing(*i) for i in itens]
        ficha += [item_ing(n, q, u) for n, q, u in base_do_pastel()]
        ficha += [item_emb("Saco de papel para pastel"),
                  item_emb("Guardanapo")]

        rec_ctrl.criar({
            "nome": nome, "categoria": categoria, "rendimento": 1,
            "unidade_rend": "UN", "modo_preparo": NOTA, "itens": ficha,
        })
        precos[nome] = preco
        criadas += 1

    print(f"  {criadas} fichas de pastel criadas")

    # --- fichas das bebidas ----------------------------------------------
    for nome, _categoria, _unidade, preco in BEBIDAS:
        rec_ctrl.criar({
            "nome": nome, "categoria": "Bebida", "rendimento": 1,
            "unidade_rend": "UN",
            "modo_preparo": "Revenda: o custo e o proprio preco de compra.",
            "itens": [item_ing(nome, 1, "UN")],
        })
        precos[nome] = preco

    print(f"  {len(BEBIDAS)} fichas de bebida criadas\n")
    return precos


if __name__ == "__main__":
    print("=" * 70)
    print("  Importando o cardapio Los Pastelles")
    print("=" * 70 + "\n")

    precos = importar()

    print(f"  Total: {len(precos)} produtos no sistema")
    print(f"  Banco: {conexao.CAMINHO_BANCO}\n")
    print("  PROXIMO PASSO")
    print("    1. Ingredientes -> informe a compra real de cada insumo")
    print("    2. Receitas     -> ajuste as gramaturas de cada ficha")
    print("    3. Precificacao -> defina o preco por canal")
