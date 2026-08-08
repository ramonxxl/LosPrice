"""
LosPrice - Identidade visual
=============================

Fonte unica de verdade para cores, fontes, espacamentos e formatacao.
Nenhuma tela deve escrever um codigo de cor na mao: sempre importar daqui.

    from utils.tema import Cores, Fontes, Espaco, formatar_moeda

Conceito da paleta:
    Laranja  = a marca, o custo, a acao
    Verde    = o lucro, o resultado positivo
    Vermelho = o prejuizo
    Amarelo  = a margem apertada

CustomTkinter aceita cor como tupla (modo_claro, modo_escuro).
Todas as cores compostas abaixo seguem esse formato.
"""

import os
import sys

import customtkinter as ctk

# ---------------------------------------------------------------------------
# Marca
# ---------------------------------------------------------------------------

APP_NOME = "LosPrice"
APP_SLOGAN = "Precifique com inteligencia. Lucre com confianca."
APP_FAMILIA = "Los Software"

VERSAO_PADRAO = "1.0.0"


def _ler_versao():
    """
    A build automatica grava assets/versao.txt com MAJOR.MINOR.BUILD.
    Rodando do codigo-fonte esse arquivo nao existe, entao cai no padrao.
    """
    base = getattr(sys, "_MEIPASS", None) or os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))
    caminho = os.path.join(base, "assets", "versao.txt")
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            return arquivo.read().strip() or VERSAO_PADRAO
    except OSError:
        return VERSAO_PADRAO


APP_VERSAO = _ler_versao()


# ---------------------------------------------------------------------------
# Cores
# ---------------------------------------------------------------------------


class Cores:
    """Tokens de cor. Tuplas = (modo claro, modo escuro)."""

    # --- Marca -------------------------------------------------------------
    LARANJA = "#FF6B00"
    LARANJA_HOVER = "#E25D00"
    LARANJA_CLARO = "#FF8B33"
    LARANJA_SUAVE = ("#FFF0E5", "#3A2410")

    VERDE = "#16A34A"
    VERDE_HOVER = "#128040"
    VERDE_CLARO = "#22C55E"
    VERDE_SUAVE = ("#E8F7EE", "#0F2A1B")

    # --- Estados -----------------------------------------------------------
    LUCRO = ("#16A34A", "#22C55E")
    ATENCAO = ("#D97706", "#F59E0B")
    PREJUIZO = ("#DC2626", "#EF4444")
    INFO = ("#2563EB", "#3B82F6")
    NEUTRO = ("#6B7280", "#9AA3B2")

    ATENCAO_SUAVE = ("#FEF6E7", "#332512")
    PREJUIZO_SUAVE = ("#FDECEC", "#3A1616")

    # --- Superficies -------------------------------------------------------
    FUNDO = ("#F4F5F7", "#0F1115")        # janela
    SIDEBAR = ("#FFFFFF", "#151821")      # menu lateral
    SUPERFICIE = ("#FFFFFF", "#171A21")   # area de conteudo
    CARD = ("#FFFFFF", "#1E222B")         # cartoes
    CARD_HOVER = ("#F7F8FA", "#252A35")
    ENTRADA = ("#FFFFFF", "#1A1E27")      # campos de formulario

    # --- Linhas ------------------------------------------------------------
    BORDA = ("#E3E6EB", "#2A2F3A")
    DIVISOR = ("#EDEFF2", "#232833")

    # --- Texto -------------------------------------------------------------
    TEXTO = ("#111827", "#F2F4F7")
    TEXTO_SECUNDARIO = ("#4B5563", "#9AA3B2")
    TEXTO_APAGADO = ("#9AA3B2", "#5D6675")
    TEXTO_SOBRE_COR = "#FFFFFF"

    # --- Tabela ------------------------------------------------------------
    TABELA_CABECALHO = ("#F0F2F5", "#1B1F28")
    TABELA_LINHA = ("#FFFFFF", "#1E222B")
    TABELA_LINHA_ALT = ("#FAFBFC", "#1A1E26")
    TABELA_SELECAO = ("#FFF0E5", "#3A2410")

    # --- Canais de venda (mesmas cores gravadas no banco) ------------------
    CANAIS = {
        "Balcao": "#2E9E5B",
        "WhatsApp / Delivery proprio": "#25D366",
        "iFood - Entrega propria": "#EA1D2C",
        "iFood - Entrega iFood": "#EA1D2C",
        "99Food": "#FFD400",
        "Rappi": "#FF441F",
    }

    # --- Graficos ----------------------------------------------------------
    SERIE = ["#FF6B00", "#16A34A", "#2563EB", "#F59E0B", "#8B5CF6", "#EC4899"]


# ---------------------------------------------------------------------------
# Tipografia
# ---------------------------------------------------------------------------


class Fontes:
    """
    Fabricas de fonte. Sao funcoes porque CTkFont exige uma janela ja criada.

        titulo = ctk.CTkLabel(pai, text="Ingredientes", font=Fontes.titulo())
    """

    FAMILIA = "Segoe UI"
    FAMILIA_NUMERO = "Consolas"          # alinha digitos em tabelas de valores
    FAMILIA_ICONE = "Segoe MDL2 Assets"  # icones nativos do Windows

    @staticmethod
    def _f(tamanho, peso="normal", familia=None):
        return ctk.CTkFont(family=familia or Fontes.FAMILIA, size=tamanho, weight=peso)

    @staticmethod
    def icone(tamanho=17):
        """
        Fonte de icone. Usar com as constantes de ICONE.
        Nao usamos emoji porque o Tcl/Tk 8.6 do Windows nao renderiza
        caracteres fora do BMP de forma confiavel.
        """
        return ctk.CTkFont(family=Fontes.FAMILIA_ICONE, size=tamanho)

    @staticmethod
    def logo():
        return Fontes._f(30, "bold")

    @staticmethod
    def display():
        return Fontes._f(28, "bold")

    @staticmethod
    def titulo():
        return Fontes._f(21, "bold")

    @staticmethod
    def subtitulo():
        return Fontes._f(16, "bold")

    @staticmethod
    def secao():
        return Fontes._f(13, "bold")

    @staticmethod
    def corpo():
        return Fontes._f(13)

    @staticmethod
    def corpo_forte():
        return Fontes._f(13, "bold")

    @staticmethod
    def pequeno():
        return Fontes._f(11)

    @staticmethod
    def micro():
        return Fontes._f(10)

    @staticmethod
    def valor_destaque():
        """Numero grande dos cards do dashboard."""
        return Fontes._f(30, "bold")

    @staticmethod
    def numero():
        return Fontes._f(13, familia=Fontes.FAMILIA_NUMERO)

    @staticmethod
    def numero_forte():
        return Fontes._f(13, "bold", familia=Fontes.FAMILIA_NUMERO)


# ---------------------------------------------------------------------------
# Espacamento e formas
# ---------------------------------------------------------------------------


class Espaco:
    XS = 4
    SM = 8
    MD = 14
    LG = 20
    XL = 28
    XXL = 40

    PADDING_JANELA = 20
    PADDING_CARD = 18
    GAP_CARD = 14


class Raio:
    PEQUENO = 6
    PADRAO = 10
    GRANDE = 14
    PILULA = 999


class Tamanhos:
    JANELA_LARGURA = 1280
    JANELA_ALTURA = 760
    JANELA_MIN_LARGURA = 1100
    JANELA_MIN_ALTURA = 680

    SIDEBAR_LARGURA = 232
    TOPO_ALTURA = 68

    BOTAO_ALTURA = 38
    BOTAO_ALTURA_GRANDE = 44
    ENTRADA_ALTURA = 38
    ITEM_MENU_ALTURA = 42

    CARD_METRICA_ALTURA = 118
    BORDA_LARGURA = 1


# ---------------------------------------------------------------------------
# Icones (Segoe MDL2 Assets - caracteres da area privada, todos dentro do BMP)
# ---------------------------------------------------------------------------


class Icone:
    """
    Codepoints da area privada do Segoe MDL2 Assets.
    Escritos como \\uXXXX para ficarem visiveis e editaveis no codigo.
    Renderizar sempre com Fontes.icone().
    """

    # menu
    CASA        = "\uE80F"
    CARRINHO    = "\uE7BF"
    CAIXA       = "\uE14D"   # sacola
    CHECKLIST   = "\uE9D5"
    CALCULADORA = "\uE8EF"
    GRAFICO     = "\uE9D9"
    VEICULO     = "\uE804"
    RELATORIO   = "\uE9F9"
    ENGRENAGEM  = "\uE713"

    # apoio
    ADICIONAR   = "\uE710"
    EDITAR      = "\uE70F"
    EXCLUIR     = "\uE74D"
    BUSCAR      = "\uE721"
    ATUALIZAR   = "\uE72C"
    SALVAR      = "\uE74E"
    FECHAR      = "\uE711"
    ALERTA      = "\uE7BA"
    OK          = "\uE73E"
    SETA_CIMA   = "\uE74A"
    SETA_BAIXO  = "\uE74B"
    FILTRO      = "\uE71C"
    COPIAR      = "\uE8C8"
    PDF         = "\uE8A5"
    EXCEL       = "\uE9F9"
    DINHEIRO    = "\uE1D0"
    SOL         = "\uE706"
    LUA         = "\uE708"


# ---------------------------------------------------------------------------
# Menu
# ---------------------------------------------------------------------------

MENU = [
    ("dashboard",     "Dashboard",     Icone.CASA),
    ("ingredientes",  "Ingredientes",  Icone.CARRINHO),
    ("embalagens",    "Embalagens",    Icone.CAIXA),
    ("receitas",      "Receitas",      Icone.CHECKLIST),
    ("precificacao",  "Precificacao",  Icone.CALCULADORA),
    ("simulador",     "Simulador",     Icone.GRAFICO),
    ("fornecedores",  "Fornecedores",  Icone.VEICULO),
    ("relatorios",    "Relatorios",    Icone.RELATORIO),
    ("configuracoes", "Configuracoes", Icone.ENGRENAGEM),
]


# ---------------------------------------------------------------------------
# Regras de leitura de resultado
# ---------------------------------------------------------------------------

# Faixas de margem liquida usadas em todo o sistema.
FAIXA_CRITICA = 5.0    # abaixo disso, praticamente nao sobra nada
FAIXA_ATENCAO = 15.0   # abaixo disso, margem apertada
FAIXA_BOA = 30.0       # acima disso, margem saudavel


def cor_margem(margem_pct):
    """Cor do resultado conforme a margem liquida (%)."""
    if margem_pct is None:
        return Cores.NEUTRO
    if margem_pct < 0:
        return Cores.PREJUIZO
    if margem_pct < FAIXA_ATENCAO:
        return Cores.ATENCAO
    return Cores.LUCRO


def cor_fundo_margem(margem_pct):
    """Fundo suave correspondente, para badges e linhas de tabela."""
    if margem_pct is None:
        return Cores.CARD
    if margem_pct < 0:
        return Cores.PREJUIZO_SUAVE
    if margem_pct < FAIXA_ATENCAO:
        return Cores.ATENCAO_SUAVE
    return Cores.VERDE_SUAVE


def rotulo_margem(margem_pct):
    """Texto curto que explica a margem para o usuario."""
    if margem_pct is None:
        return "Sem calculo"
    if margem_pct < 0:
        return "Prejuizo"
    if margem_pct < FAIXA_CRITICA:
        return "Critica"
    if margem_pct < FAIXA_ATENCAO:
        return "Apertada"
    if margem_pct < FAIXA_BOA:
        return "Saudavel"
    return "Otima"


def cor_canal(nome):
    return Cores.CANAIS.get(nome, Cores.LARANJA)


# ---------------------------------------------------------------------------
# Formatacao brasileira
# ---------------------------------------------------------------------------


def formatar_moeda(valor, simbolo=True):
    """1234.5 -> 'R$ 1.234,50'"""
    if valor is None:
        return "R$ --" if simbolo else "--"
    texto = f"{float(valor):,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")
    return f"R$ {texto}" if simbolo else texto


def formatar_moeda_precisa(valor, casas=4):
    """Para custo por grama, onde 2 casas arredondam demais. -> 'R$ 0,0370'"""
    if valor is None:
        return "R$ --"
    texto = f"{float(valor):,.{casas}f}".replace(",", "@").replace(".", ",").replace("@", ".")
    return f"R$ {texto}"


def formatar_pct(valor, casas=1, sinal=False):
    """30.0 -> '30,0%'"""
    if valor is None:
        return "--"
    texto = f"{float(valor):+.{casas}f}" if sinal else f"{float(valor):.{casas}f}"
    return texto.replace(".", ",") + "%"


def formatar_numero(valor, casas=0):
    if valor is None:
        return "--"
    texto = f"{float(valor):,.{casas}f}".replace(",", "@").replace(".", ",").replace("@", ".")
    return texto


def formatar_quantidade(valor, unidade=""):
    """Remove zeros inuteis: 150.0 -> '150 g', 2.5 -> '2,5 kg'"""
    if valor is None:
        return "--"
    valor = float(valor)
    texto = f"{valor:.0f}" if valor == int(valor) else f"{valor:.3f}".rstrip("0").rstrip(".")
    texto = texto.replace(".", ",")
    return f"{texto} {unidade}".strip()


def converter_moeda(texto):
    """'R$ 1.234,50' -> 1234.5. Retorna None se nao der para converter."""
    if texto is None:
        return None
    limpo = str(texto).replace("R$", "").replace(" ", "").strip()
    if not limpo:
        return None
    limpo = limpo.replace(".", "").replace(",", ".")
    try:
        return float(limpo)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Aplicacao do tema
# ---------------------------------------------------------------------------


def aplicar_tema(modo="escuro"):
    """Chamado uma vez no main.py, antes de criar a janela."""
    ctk.set_appearance_mode("dark" if modo == "escuro" else "light")
    ctk.set_default_color_theme("blue")  # sobrescrevemos as cores manualmente
    ctk.set_widget_scaling(1.0)


def alternar_tema():
    """Troca claro <-> escuro e devolve o modo atual."""
    atual = ctk.get_appearance_mode()
    novo = "light" if atual == "Dark" else "dark"
    ctk.set_appearance_mode(novo)
    return "escuro" if novo == "dark" else "claro"


# ---------------------------------------------------------------------------
# Estilos prontos de widget
# ---------------------------------------------------------------------------


def estilo_botao_primario():
    return dict(
        fg_color=Cores.LARANJA,
        hover_color=Cores.LARANJA_HOVER,
        text_color=Cores.TEXTO_SOBRE_COR,
        corner_radius=Raio.PADRAO,
        height=Tamanhos.BOTAO_ALTURA,
        border_width=0,
    )


def estilo_botao_sucesso():
    return dict(
        fg_color=Cores.VERDE,
        hover_color=Cores.VERDE_HOVER,
        text_color=Cores.TEXTO_SOBRE_COR,
        corner_radius=Raio.PADRAO,
        height=Tamanhos.BOTAO_ALTURA,
        border_width=0,
    )


def estilo_botao_secundario():
    return dict(
        fg_color="transparent",
        hover_color=Cores.CARD_HOVER,
        text_color=Cores.TEXTO,
        border_color=Cores.BORDA,
        border_width=Tamanhos.BORDA_LARGURA,
        corner_radius=Raio.PADRAO,
        height=Tamanhos.BOTAO_ALTURA,
    )


def estilo_botao_perigo():
    return dict(
        fg_color="transparent",
        hover_color=Cores.PREJUIZO_SUAVE,
        text_color=Cores.PREJUIZO,
        border_color=Cores.PREJUIZO,
        border_width=Tamanhos.BORDA_LARGURA,
        corner_radius=Raio.PADRAO,
        height=Tamanhos.BOTAO_ALTURA,
    )


def estilo_card():
    return dict(
        fg_color=Cores.CARD,
        border_color=Cores.BORDA,
        border_width=Tamanhos.BORDA_LARGURA,
        corner_radius=Raio.GRANDE,
    )


def estilo_entrada():
    return dict(
        fg_color=Cores.ENTRADA,
        border_color=Cores.BORDA,
        border_width=Tamanhos.BORDA_LARGURA,
        text_color=Cores.TEXTO,
        corner_radius=Raio.PEQUENO,
        height=Tamanhos.ENTRADA_ALTURA,
    )


# ---------------------------------------------------------------------------
# Logo tipografico
# ---------------------------------------------------------------------------


def montar_logo(pai, tamanho=30, horizontal=True):
    """
    Monta o logo 'LosPrice' com Los em laranja e Price em verde.
    Retorna o frame, pronto para .pack() ou .grid().
    """
    caixa = ctk.CTkFrame(pai, fg_color="transparent")
    fonte = ctk.CTkFont(family=Fontes.FAMILIA, size=tamanho, weight="bold")

    los = ctk.CTkLabel(caixa, text="Los", font=fonte, text_color=Cores.LARANJA)
    price = ctk.CTkLabel(caixa, text="Price", font=fonte, text_color=Cores.VERDE_CLARO)

    if horizontal:
        los.pack(side="left")
        price.pack(side="left")
    else:
        los.pack()
        price.pack()

    return caixa


# ---------------------------------------------------------------------------
# Vitrine da identidade visual
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    aplicar_tema("escuro")

    app = ctk.CTk()
    app.title(f"{APP_NOME} - Identidade Visual")
    app.geometry("980x720")
    app.configure(fg_color=Cores.FUNDO)

    raiz = ctk.CTkScrollableFrame(app, fg_color="transparent")
    raiz.pack(fill="both", expand=True, padx=Espaco.LG, pady=Espaco.LG)

    # Cabecalho ------------------------------------------------------------
    topo = ctk.CTkFrame(raiz, fg_color="transparent")
    topo.pack(fill="x", pady=(0, Espaco.LG))
    montar_logo(topo, 34).pack(anchor="w")
    ctk.CTkLabel(topo, text=APP_SLOGAN, font=Fontes.corpo(),
                 text_color=Cores.TEXTO_SECUNDARIO).pack(anchor="w", pady=(2, 0))

    def secao(titulo):
        ctk.CTkLabel(raiz, text=titulo.upper(), font=Fontes.secao(),
                     text_color=Cores.TEXTO_APAGADO).pack(anchor="w", pady=(Espaco.LG, Espaco.SM))

    # Cards de metrica -----------------------------------------------------
    secao("Cards do dashboard")
    linha = ctk.CTkFrame(raiz, fg_color="transparent")
    linha.pack(fill="x")

    metricas = [
        ("Ingredientes", "42", Cores.LARANJA),
        ("Receitas", "18", Cores.INFO),
        ("Lucro medio", "34,2%", Cores.LUCRO),
        ("No prejuizo", "3", Cores.PREJUIZO),
    ]
    for rotulo, valor, cor in metricas:
        card = ctk.CTkFrame(linha, **estilo_card())
        card.pack(side="left", expand=True, fill="both", padx=(0, Espaco.GAP_CARD))
        faixa = ctk.CTkFrame(card, fg_color=cor, height=4, corner_radius=Raio.PILULA)
        faixa.pack(fill="x", padx=Espaco.PADDING_CARD, pady=(Espaco.PADDING_CARD, Espaco.MD))
        ctk.CTkLabel(card, text=valor, font=Fontes.valor_destaque(),
                     text_color=cor).pack(anchor="w", padx=Espaco.PADDING_CARD)
        ctk.CTkLabel(card, text=rotulo, font=Fontes.pequeno(),
                     text_color=Cores.TEXTO_SECUNDARIO).pack(
            anchor="w", padx=Espaco.PADDING_CARD, pady=(0, Espaco.PADDING_CARD))

    # Botoes ---------------------------------------------------------------
    secao("Botoes")
    botoes = ctk.CTkFrame(raiz, fg_color="transparent")
    botoes.pack(fill="x")
    for texto, estilo in [
        ("Novo ingrediente", estilo_botao_primario()),
        ("Calcular preco", estilo_botao_sucesso()),
        ("Cancelar", estilo_botao_secundario()),
        ("Excluir", estilo_botao_perigo()),
    ]:
        ctk.CTkButton(botoes, text=texto, font=Fontes.corpo_forte(),
                      width=160, **estilo).pack(side="left", padx=(0, Espaco.SM))

    # Leitura de margem ----------------------------------------------------
    secao("Leitura de margem")
    faixas = ctk.CTkFrame(raiz, fg_color="transparent")
    faixas.pack(fill="x")
    for pct in (-8.5, 3.0, 11.4, 24.7, 41.2):
        badge = ctk.CTkFrame(faixas, fg_color=cor_fundo_margem(pct),
                             corner_radius=Raio.PILULA)
        badge.pack(side="left", padx=(0, Espaco.SM))
        ctk.CTkLabel(badge, text=f"{formatar_pct(pct, sinal=True)}  {rotulo_margem(pct)}",
                     font=Fontes.corpo_forte(), text_color=cor_margem(pct)).pack(
            padx=Espaco.MD, pady=Espaco.SM)

    # Canais ---------------------------------------------------------------
    secao("Canais de venda")
    canais = ctk.CTkFrame(raiz, **estilo_card())
    canais.pack(fill="x")
    exemplos = [
        ("Balcao", 18.90, 7.82, 41.4),
        ("WhatsApp / Delivery proprio", 18.90, 7.16, 37.9),
        ("iFood - Entrega propria", 21.90, 6.03, 27.5),
        ("iFood - Entrega iFood", 24.90, 2.14, 8.6),
    ]
    for i, (nome, preco, lucro, margem) in enumerate(exemplos):
        item = ctk.CTkFrame(canais, fg_color="transparent")
        item.pack(fill="x", padx=Espaco.PADDING_CARD,
                  pady=(Espaco.PADDING_CARD if i == 0 else 0, Espaco.MD))
        ctk.CTkFrame(item, fg_color=cor_canal(nome), width=4, height=26,
                     corner_radius=Raio.PILULA).pack(side="left", padx=(0, Espaco.MD))
        ctk.CTkLabel(item, text=nome, font=Fontes.corpo(),
                     text_color=Cores.TEXTO, width=230, anchor="w").pack(side="left")
        ctk.CTkLabel(item, text=formatar_moeda(preco), font=Fontes.numero_forte(),
                     text_color=Cores.TEXTO, width=100, anchor="e").pack(side="left")
        ctk.CTkLabel(item, text=formatar_moeda(lucro), font=Fontes.numero(),
                     text_color=cor_margem(margem), width=100, anchor="e").pack(side="left")
        ctk.CTkLabel(item, text=formatar_pct(margem), font=Fontes.numero_forte(),
                     text_color=cor_margem(margem), width=80, anchor="e").pack(side="left")

    # Tipografia -----------------------------------------------------------
    secao("Tipografia")
    tipo = ctk.CTkFrame(raiz, **estilo_card())
    tipo.pack(fill="x", pady=(0, Espaco.LG))
    amostras = [
        ("Display 28", Fontes.display(), Cores.TEXTO),
        ("Titulo 21", Fontes.titulo(), Cores.TEXTO),
        ("Subtitulo 16", Fontes.subtitulo(), Cores.TEXTO),
        ("Corpo 13 - texto normal das telas", Fontes.corpo(), Cores.TEXTO),
        ("Pequeno 11 - legendas e apoio", Fontes.pequeno(), Cores.TEXTO_SECUNDARIO),
        ("Numero  R$ 0,0370 / g", Fontes.numero(), Cores.TEXTO_SECUNDARIO),
    ]
    for texto, fonte, cor in amostras:
        ctk.CTkLabel(tipo, text=texto, font=fonte, text_color=cor).pack(
            anchor="w", padx=Espaco.PADDING_CARD, pady=Espaco.XS)

    # Alternar tema --------------------------------------------------------
    rodape = ctk.CTkFrame(raiz, fg_color="transparent")
    rodape.pack(fill="x")
    ctk.CTkButton(rodape, text="Alternar claro / escuro", command=alternar_tema,
                  font=Fontes.corpo_forte(), width=200,
                  **estilo_botao_secundario()).pack(side="left")

    app.mainloop()
