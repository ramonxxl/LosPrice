"""
LosPrice - Motor de calculo
============================

Matematica pura. Nao importa customtkinter, nao importa banco de dados.
Tudo aqui pode ser testado sem abrir a interface.

REGRA DE OURO DO SISTEMA
------------------------
Comissao, cartao, imposto e rateio percentual incidem sobre o PRECO DE VENDA,
nunca sobre o custo. Por isso o preco sai por DIVISAO, nao por multiplicacao:

    preco = (custo + custos em R$) / (1 - soma dos percentuais)

Exemplo: custo R$ 5,00, iFood 27%, imposto 6%, lucro desejado 20%.

    ERRADO: 5,00 x 1,53 = R$ 7,65
            iFood 2,07 + imposto 0,46 + custo 5,00  ->  sobra R$ 0,12  (1,6%)

    CERTO:  5,00 / (1 - 0,53) = R$ 10,64
            iFood 2,87 + imposto 0,64 + custo 5,00  ->  sobra R$ 2,13  (20,0%)
"""

from dataclasses import dataclass, field
from math import floor

# ---------------------------------------------------------------------------
# Unidades
# ---------------------------------------------------------------------------

PESO = "G"
VOLUME = "ML"
UNIDADE = "UN"

# unidade digitada -> (grandeza, quanto vale na unidade base)
CONVERSOES = {
    "KG": (PESO, 1000.0),
    "G": (PESO, 1.0),
    "MG": (PESO, 0.001),
    "L": (VOLUME, 1000.0),
    "ML": (VOLUME, 1.0),
    "UN": (UNIDADE, 1.0),
    "DZ": (UNIDADE, 12.0),
    "PCT": (UNIDADE, 1.0),
    "CX": (UNIDADE, 1.0),
}

ROTULO_BASE = {PESO: "g", VOLUME: "ml", UNIDADE: "un"}


class ErroCalculo(Exception):
    """Erro de negocio: dado invalido ou combinacao impossivel."""


def _norm(unidade):
    return str(unidade or "").strip().upper()


def converter_para_base(quantidade, unidade):
    """
    2.5, 'KG'  ->  (2500.0, 'G')
    150, 'g'   ->  (150.0, 'G')
    """
    u = _norm(unidade)
    if u not in CONVERSOES:
        raise ErroCalculo(f"Unidade desconhecida: {unidade}")
    base, fator = CONVERSOES[u]
    return float(quantidade) * fator, base


def mesma_grandeza(unidade_a, unidade_b):
    """G e KG sao compativeis. G e ML nao sao."""
    a, b = _norm(unidade_a), _norm(unidade_b)
    if a not in CONVERSOES or b not in CONVERSOES:
        return False
    return CONVERSOES[a][0] == CONVERSOES[b][0]


# ---------------------------------------------------------------------------
# Ingredientes
# ---------------------------------------------------------------------------


def fator_correcao(peso_bruto, peso_liquido):
    """
    Perda de limpeza, descongelamento e coccao.
    Comprou 1000 g de carne, aproveita 700 g  ->  fator 1,4286.
    """
    if peso_bruto <= 0 or peso_liquido <= 0:
        raise ErroCalculo("Pesos devem ser maiores que zero.")
    if peso_liquido > peso_bruto:
        raise ErroCalculo("O peso liquido nao pode ser maior que o bruto.")
    return float(peso_bruto) / float(peso_liquido)


def custo_unitario(qtd_comprada, unidade_compra, valor_pago, fator=1.0):
    """
    O diferencial do LosPrice: o usuario informa a COMPRA e o sistema
    deriva o custo por grama / ml / unidade, ja corrigido pela perda.

        5 kg por R$ 185,00  ->  R$ 0,0370 por grama
        com fator 1,30      ->  R$ 0,0481 por grama

    Retorna (custo_por_unidade_base, unidade_base).
    """
    if qtd_comprada is None or float(qtd_comprada) <= 0:
        raise ErroCalculo("A quantidade comprada deve ser maior que zero.")
    if valor_pago is None or float(valor_pago) < 0:
        raise ErroCalculo("O valor pago nao pode ser negativo.")
    if fator is None or float(fator) <= 0:
        raise ErroCalculo("O fator de correcao deve ser maior que zero.")

    qtd_base, base = converter_para_base(qtd_comprada, unidade_compra)
    return (float(valor_pago) / qtd_base) * float(fator), base


def custo_do_item(custo_por_base, quantidade, unidade, unidade_base):
    """
    Custo de uma linha da ficha tecnica.
    custo_por_base ja vem corrigido pelo fator.
    """
    if not mesma_grandeza(unidade, unidade_base):
        raise ErroCalculo(
            f"Unidade incompativel: a receita pede '{unidade}' e o "
            f"ingrediente e medido em '{ROTULO_BASE.get(unidade_base, unidade_base)}'."
        )
    qtd_base, _ = converter_para_base(quantidade, unidade)
    return float(custo_por_base) * qtd_base


def variacao_percentual(valor_antigo, valor_novo):
    """Alimenta o alerta 'a mussarela subiu 18%'."""
    if not valor_antigo:
        return None
    return ((float(valor_novo) - float(valor_antigo)) / float(valor_antigo)) * 100.0


# ---------------------------------------------------------------------------
# Receita
# ---------------------------------------------------------------------------


@dataclass
class CustoReceita:
    custo_ingredientes: float = 0.0
    custo_embalagens: float = 0.0
    custo_total: float = 0.0        # lote inteiro
    rendimento: float = 1.0
    custo_unitario: float = 0.0     # custo_total / rendimento
    detalhes: list = field(default_factory=list)

    @property
    def peso_embalagem_pct(self):
        """Quanto da embalagem pesa no custo. Acima de 10% costuma ser problema."""
        if self.custo_total <= 0:
            return 0.0
        return (self.custo_embalagens / self.custo_total) * 100.0


def calcular_receita(ingredientes, embalagens=None, rendimento=1.0):
    """
    ingredientes: lista de dicts
        {nome, custo_por_base, unidade_base, quantidade, unidade}
    embalagens: lista de dicts
        {nome, custo_unitario, quantidade}
    """
    if rendimento is None or float(rendimento) <= 0:
        raise ErroCalculo("O rendimento da receita deve ser maior que zero.")

    resultado = CustoReceita(rendimento=float(rendimento))

    for item in ingredientes or []:
        custo = custo_do_item(
            item["custo_por_base"],
            item["quantidade"],
            item["unidade"],
            item["unidade_base"],
        )
        resultado.custo_ingredientes += custo
        resultado.detalhes.append(
            {
                "tipo": "ingrediente",
                "nome": item.get("nome", ""),
                "quantidade": item["quantidade"],
                "unidade": item["unidade"],
                "custo": round(custo, 4),
            }
        )

    for item in embalagens or []:
        qtd = float(item.get("quantidade", 1))
        custo = float(item["custo_unitario"]) * qtd
        resultado.custo_embalagens += custo
        resultado.detalhes.append(
            {
                "tipo": "embalagem",
                "nome": item.get("nome", ""),
                "quantidade": qtd,
                "unidade": "un",
                "custo": round(custo, 4),
            }
        )

    resultado.custo_total = resultado.custo_ingredientes + resultado.custo_embalagens
    resultado.custo_unitario = resultado.custo_total / resultado.rendimento

    # participacao de cada item no custo, util no grafico da ficha tecnica
    for d in resultado.detalhes:
        d["participacao_pct"] = (
            (d["custo"] / resultado.custo_total * 100.0) if resultado.custo_total else 0.0
        )

    return resultado


# ---------------------------------------------------------------------------
# Encargos do canal
# ---------------------------------------------------------------------------


@dataclass
class Encargos:
    """Tudo que incide sobre a venda, por canal."""

    comissao_pct: float = 0.0     # taxa da plataforma (iFood, 99Food...)
    cartao_pct: float = 0.0       # maquininha / gateway
    imposto_pct: float = 0.0      # Simples, MEI...
    custo_fixo_pct: float = 0.0   # rateio de aluguel, energia, gas, salarios
    taxa_fixa_rs: float = 0.0     # valor em R$ cobrado por pedido

    @property
    def total_pct(self):
        return (
            self.comissao_pct
            + self.cartao_pct
            + self.imposto_pct
            + self.custo_fixo_pct
        )

    def validar(self):
        for nome, valor in (
            ("comissao", self.comissao_pct),
            ("cartao", self.cartao_pct),
            ("imposto", self.imposto_pct),
            ("custo fixo", self.custo_fixo_pct),
        ):
            if valor < 0:
                raise ErroCalculo(f"O percentual de {nome} nao pode ser negativo.")
        if self.taxa_fixa_rs < 0:
            raise ErroCalculo("A taxa fixa nao pode ser negativa.")


# ---------------------------------------------------------------------------
# Resultado da precificacao
# ---------------------------------------------------------------------------


@dataclass
class Composicao:
    """Abertura completa de um preco. E o que a tela mostra linha a linha."""

    preco: float = 0.0
    custo_produto: float = 0.0
    custo_fixo_rs: float = 0.0
    taxa_fixa: float = 0.0

    valor_comissao: float = 0.0
    valor_cartao: float = 0.0
    valor_imposto: float = 0.0
    valor_custo_fixo: float = 0.0

    lucro: float = 0.0
    margem_pct: float = 0.0     # lucro sobre o preco de venda
    markup: float = 0.0         # preco / custo do produto

    @property
    def custo_total(self):
        """Tudo que sai do preco, menos o lucro."""
        return (
            self.custo_produto
            + self.custo_fixo_rs
            + self.taxa_fixa
            + self.valor_comissao
            + self.valor_cartao
            + self.valor_imposto
            + self.valor_custo_fixo
        )

    @property
    def saudavel(self):
        return self.margem_pct > 0

    def arredondar(self, casas=2):
        for campo in (
            "preco", "custo_produto", "custo_fixo_rs", "taxa_fixa",
            "valor_comissao", "valor_cartao", "valor_imposto",
            "valor_custo_fixo", "lucro",
        ):
            setattr(self, campo, round(getattr(self, campo), casas))
        self.margem_pct = round(self.margem_pct, 2)
        self.markup = round(self.markup, 3)
        return self


def _abrir(preco, custo, encargos, custo_fixo_rs):
    """Dado um preco, quebra em cada componente."""
    preco = float(preco)
    c = Composicao(
        preco=preco,
        custo_produto=float(custo),
        custo_fixo_rs=float(custo_fixo_rs),
        taxa_fixa=float(encargos.taxa_fixa_rs),
        valor_comissao=preco * encargos.comissao_pct / 100.0,
        valor_cartao=preco * encargos.cartao_pct / 100.0,
        valor_imposto=preco * encargos.imposto_pct / 100.0,
        valor_custo_fixo=preco * encargos.custo_fixo_pct / 100.0,
    )
    c.lucro = preco - c.custo_total
    c.margem_pct = (c.lucro / preco * 100.0) if preco else 0.0
    c.markup = (preco / c.custo_produto) if c.custo_produto else 0.0
    return c.arredondar()


def calcular_preco(custo, encargos, margem_pct, custo_fixo_rs=0.0):
    """
    O calculo principal. Metodo divisor.

        preco = (custo + custos em R$) / (1 - percentuais totais)
    """
    encargos.validar()
    if custo is None or float(custo) < 0:
        raise ErroCalculo("O custo do produto nao pode ser negativo.")

    soma_pct = encargos.total_pct + float(margem_pct)
    divisor = 1.0 - (soma_pct / 100.0)

    if divisor <= 0:
        raise ErroCalculo(
            f"Impossivel precificar: taxas e margem somam {soma_pct:.1f}% da venda. "
            "Reduza a margem desejada ou renegocie as taxas."
        )

    preco = (float(custo) + float(custo_fixo_rs) + encargos.taxa_fixa_rs) / divisor
    return _abrir(preco, custo, encargos, custo_fixo_rs)


def analisar_venda(custo, preco, encargos, custo_fixo_rs=0.0):
    """
    Caminho inverso: 'e se eu vender por R$ 18,90?'
    Alimenta o Simulador.
    """
    encargos.validar()
    if preco is None or float(preco) <= 0:
        raise ErroCalculo("O preco de venda deve ser maior que zero.")
    return _abrir(preco, custo, encargos, custo_fixo_rs)


def preco_minimo(custo, encargos, custo_fixo_rs=0.0):
    """Preco de lucro zero. Abaixo disso e prejuizo garantido."""
    return calcular_preco(custo, encargos, 0.0, custo_fixo_rs).preco


def custo_maximo(preco_alvo, encargos, margem_desejada, custo_fixo_rs=0.0):
    """
    Precificacao reversa (custo-alvo).
    'Quero vender a R$ 15,90 no iFood com 30% de lucro. Quanto a ficha pode custar?'
    Retorna None quando nao ha combinacao possivel.
    """
    encargos.validar()
    divisor = 1.0 - ((encargos.total_pct + float(margem_desejada)) / 100.0)
    teto = float(preco_alvo) * divisor - float(custo_fixo_rs) - encargos.taxa_fixa_rs
    return round(teto, 4) if teto > 0 else None


def desconto_maximo(preco, custo, encargos, custo_fixo_rs=0.0, margem_minima=0.0):
    """
    Ate quantos % de desconto da para dar sem furar a margem minima.
    Base do simulador de promocoes.
    """
    piso = calcular_preco(custo, encargos, margem_minima, custo_fixo_rs).preco
    if preco <= piso:
        return 0.0
    return round((preco - piso) / preco * 100.0, 2)


# ---------------------------------------------------------------------------
# Ajustes de preco
# ---------------------------------------------------------------------------


def arredondar_preco(valor, terminacao=0.90):
    """
    Preco psicologico. Sempre para CIMA, para nunca ficar abaixo do calculado.

        18,03  ->  18,90
        18,95  ->  19,90
    """
    valor = float(valor)
    inteiro = floor(valor)
    candidato = inteiro + float(terminacao)
    if candidato < valor - 1e-9:
        candidato = inteiro + 1 + float(terminacao)
    return round(candidato, 2)


def custo_por_porcao(custo_total, rendimento):
    if rendimento <= 0:
        raise ErroCalculo("O rendimento deve ser maior que zero.")
    return float(custo_total) / float(rendimento)


# ---------------------------------------------------------------------------
# Indicadores do negocio
# ---------------------------------------------------------------------------


def ponto_equilibrio(custo_fixo_mensal, lucro_por_unidade):
    """Quantas unidades precisam ser vendidas no mes so para empatar."""
    if lucro_por_unidade is None or lucro_por_unidade <= 0:
        return None
    from math import ceil

    return ceil(float(custo_fixo_mensal) / float(lucro_por_unidade))


def rateio_custo_fixo(custo_fixo_mensal, unidades_por_mes):
    """Converte o custo fixo do mes em R$ por unidade produzida."""
    if unidades_por_mes is None or unidades_por_mes <= 0:
        return 0.0
    return float(custo_fixo_mensal) / float(unidades_por_mes)


ESTRELA = "Estrela"
PUXADOR = "Puxador"
ENIGMA = "Enigma"
ABACAXI = "Abacaxi"


def classificar_cardapio(margem, popularidade, margem_media, popularidade_media):
    """
    Engenharia de cardapio.

        Estrela : vende muito e lucra muito   -> destacar
        Puxador : vende muito e lucra pouco   -> subir preco ou baratear a ficha
        Enigma  : lucra muito e vende pouco   -> divulgar
        Abacaxi : nao vende e nao lucra       -> tirar do cardapio
    """
    lucra = margem >= margem_media
    vende = popularidade >= popularidade_media
    if lucra and vende:
        return ESTRELA
    if vende:
        return PUXADOR
    if lucra:
        return ENIGMA
    return ABACAXI


# ---------------------------------------------------------------------------
# Conferencia
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os
    import sys

    # Permite rodar direto de qualquer lugar: python core/calculo.py
    # Sem isso o import de utils/ so funciona com PYTHONPATH apontando
    # para a raiz do projeto.
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from utils.tema import formatar_moeda, formatar_moeda_precisa, formatar_pct, rotulo_margem

    print("=" * 74)
    print("  LosPrice - conferencia do motor de calculo")
    print("=" * 74)

    # 1. Ingredientes -------------------------------------------------------
    compras = [
        # nome,        qtd,  un,   valor,  fator de correcao
        ("Carne moida", 5,   "KG", 185.00, 1.30),   # perde 30% na limpeza/fritura
        ("Mussarela",   3,   "KG", 108.00, 1.00),
        ("Massa",       100, "UN",  22.00, 1.00),
        ("Catupiry",    1.05,"KG",  38.90, 1.00),
        ("Bacon",       1,   "KG",  32.90, 1.00),
    ]

    print("\n  INGREDIENTES\n")
    print(f"  {'Item':<14}{'Compra':>14}{'Pago':>12}{'Fator':>8}{'Custo real':>16}")
    print("  " + "-" * 62)

    tabela = {}
    for nome, qtd, un, valor, fator in compras:
        custo, base = custo_unitario(qtd, un, valor, fator)
        tabela[nome] = (custo, base)
        print(f"  {nome:<14}{f'{qtd} {un}':>14}{formatar_moeda(valor):>12}"
              f"{fator:>8.2f}{formatar_moeda_precisa(custo) + '/' + ROTULO_BASE[base]:>16}")

    # 2. Receita ------------------------------------------------------------
    ficha = [
        ("Carne moida", 150, "G"),
        ("Mussarela",    40, "G"),
        ("Massa",         1, "UN"),
        ("Catupiry",     15, "G"),
        ("Bacon",         5, "G"),
    ]
    itens = [
        {"nome": n, "custo_por_base": tabela[n][0], "unidade_base": tabela[n][1],
         "quantidade": q, "unidade": u}
        for n, q, u in ficha
    ]
    embalagem = [{"nome": "Saco kraft", "custo_unitario": 0.18, "quantidade": 1}]

    receita = calcular_receita(itens, embalagem, rendimento=1)

    print("\n  RECEITA: Pastel de Carne\n")
    for d in receita.detalhes:
        marca = "+" if d["tipo"] == "embalagem" else " "
        print(f"  {marca} {d['nome']:<14}{d['quantidade']:>6g} {d['unidade']:<4}"
              f"{formatar_moeda(d['custo']):>10}{d['participacao_pct']:>8.1f}%")
    print("  " + "-" * 44)
    print(f"    {'CUSTO DA RECEITA':<20}{formatar_moeda(receita.custo_total):>18}")

    # 3. Preco por canal ----------------------------------------------------
    canais = [
        ("Balcao",                       0.0, 0.0),
        ("WhatsApp / Delivery proprio",  0.0, 3.5),
        ("iFood - Entrega propria",     12.0, 0.0),
        ("iFood - Entrega iFood",       27.0, 0.0),
        ("99Food",                      20.0, 0.0),
        ("Rappi",                       25.0, 0.0),
    ]
    IMPOSTO, CUSTO_FIXO, MARGEM = 6.0, 8.0, 25.0

    print(f"\n  PRECIFICACAO  (imposto {IMPOSTO}% | custo fixo {CUSTO_FIXO}% | "
          f"margem desejada {MARGEM}%)\n")
    print(f"  {'Canal':<30}{'Calculado':>11}{'Vitrine':>10}{'Lucro':>10}{'Margem':>9}  Leitura")
    print("  " + "-" * 82)

    for nome, comissao, cartao in canais:
        enc = Encargos(comissao_pct=comissao, cartao_pct=cartao,
                       imposto_pct=IMPOSTO, custo_fixo_pct=CUSTO_FIXO)
        calc = calcular_preco(receita.custo_total, enc, MARGEM)
        vitrine = arredondar_preco(calc.preco)
        real = analisar_venda(receita.custo_total, vitrine, enc)
        print(f"  {nome:<30}{formatar_moeda(calc.preco):>11}{formatar_moeda(vitrine):>10}"
              f"{formatar_moeda(real.lucro):>10}{formatar_pct(real.margem_pct):>9}"
              f"  {rotulo_margem(real.margem_pct)}")

    # 4. Prova do metodo divisor -------------------------------------------
    print("\n  PROVA DO METODO DIVISOR  (custo R$ 5,00 | iFood 27% | imposto 6% | lucro 20%)\n")
    enc = Encargos(comissao_pct=27.0, imposto_pct=6.0)

    errado = 5.00 * 1.53
    r_errado = analisar_venda(5.00, errado, enc)
    print(f"    Multiplicando  {formatar_moeda(errado):>9}"
          f"   ->  lucro {formatar_moeda(r_errado.lucro):>8}"
          f"   margem {formatar_pct(r_errado.margem_pct):>7}")

    r_certo = calcular_preco(5.00, enc, 20.0)
    print(f"    Dividindo      {formatar_moeda(r_certo.preco):>9}"
          f"   ->  lucro {formatar_moeda(r_certo.lucro):>8}"
          f"   margem {formatar_pct(r_certo.margem_pct):>7}")

    # 5. Simulador ----------------------------------------------------------
    print("\n  SIMULADOR  ('e se eu vender por R$ 24,90 no iFood?')\n")
    enc = Encargos(comissao_pct=27.0, imposto_pct=IMPOSTO, custo_fixo_pct=CUSTO_FIXO)
    sim = analisar_venda(receita.custo_total, 24.90, enc)
    print(f"    Preco de venda ........ {formatar_moeda(sim.preco):>10}")
    print(f"    Custo da receita ...... {formatar_moeda(sim.custo_produto):>10}")
    print(f"    Comissao iFood 27% .... {formatar_moeda(sim.valor_comissao):>10}")
    print(f"    Imposto 6% ............ {formatar_moeda(sim.valor_imposto):>10}")
    print(f"    Custo fixo 8% ......... {formatar_moeda(sim.valor_custo_fixo):>10}")
    print(f"    {'-' * 34}")
    print(f"    SOBRA ................. {formatar_moeda(sim.lucro):>10}   "
          f"{formatar_pct(sim.margem_pct)}  ({rotulo_margem(sim.margem_pct)})")

    piso = preco_minimo(receita.custo_total, enc)
    print(f"\n    Preco minimo (lucro zero) .... {formatar_moeda(piso)}")
    print(f"    Desconto maximo possivel ..... "
          f"{formatar_pct(desconto_maximo(24.90, receita.custo_total, enc))}")

    # 6. Custo-alvo ---------------------------------------------------------
    alvo = custo_maximo(19.90, enc, margem_desejada=25.0)
    print(f"\n  CUSTO-ALVO  (vender a R$ 19,90 no iFood com 25% de lucro)")
    print(f"    A ficha tecnica pode custar no maximo ... {formatar_moeda(alvo)}")
    print(f"    Sua ficha custa hoje ................... {formatar_moeda(receita.custo_total)}")
    if alvo and receita.custo_total > alvo:
        print(f"    -> Precisa reduzir {formatar_moeda(receita.custo_total - alvo)} da receita.")

    print()
