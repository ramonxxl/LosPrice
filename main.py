"""
LosPrice - Sistema Inteligente de Precificacao
===============================================

Ponto de entrada. Responsavel por:
    - Inicializar o banco
    - Mostrar a splash
    - Montar a janela: menu lateral + barra superior + area de conteudo
    - Rotear a navegacao entre as telas

As telas sao carregadas sob demanda. Enquanto uma tela ainda nao existe,
entra um placeholder no lugar - assim o sistema roda desde o primeiro dia
e cada tela nova e plugada sem tocar neste arquivo.

    python main.py
"""

import importlib
import os
import sys
import traceback

import customtkinter as ctk

PASTA_RAIZ = os.path.dirname(os.path.abspath(__file__))
if PASTA_RAIZ not in sys.path:
    sys.path.insert(0, PASTA_RAIZ)

from database import conexao
from utils.tema import (
    APP_FAMILIA, APP_NOME, APP_SLOGAN, APP_VERSAO,
    Cores, Espaco, Fontes, Icone, MENU, Raio, Tamanhos,
    aplicar_tema, estilo_card, montar_logo,
)

# ---------------------------------------------------------------------------
# Rotas
# ---------------------------------------------------------------------------

# chave -> (modulo, classe, subtitulo, o que a tela vai fazer)
ROTAS = {
    "dashboard": (
        "screens.dashboard", "TelaDashboard",
        "Visao geral do seu negocio",
        ["Total de ingredientes, receitas e produtos precificados",
         "Lucro medio e produtos vendendo no prejuizo",
         "Alertas de ingrediente que subiu de preco",
         "Receitas com custo desatualizado"],
    ),
    "ingredientes": (
        "screens.ingredientes", "TelaIngredientes",
        "Cadastro de insumos e custo real por unidade",
        ["Cadastro pela COMPRA: 5 kg por R$ 185,00",
         "Custo automatico por kg, grama, ml ou unidade",
         "Fator de correcao para perda de limpeza e coccao",
         "Historico de precos e variacao percentual"],
    ),
    "embalagens": (
        "screens.embalagens", "TelaEmbalagens",
        "Caixas, sacos, copos e descartaveis",
        ["Cadastro pela compra: 100 caixas por R$ 45,00",
         "Custo por unidade calculado automaticamente",
         "Vinculo direto com cada receita"],
    ),
    "receitas": (
        "screens.receitas", "TelaReceitas",
        "Fichas tecnicas e custo de producao",
        ["Montagem da ficha com ingredientes e embalagens",
         "Custo da receita calculado em tempo real",
         "Participacao de cada item no custo total",
         "Rendimento e custo por porcao"],
    ),
    "precificacao": (
        "screens.precificacao", "TelaPrecificacao",
        "Preco certo para cada canal de venda",
        ["Metodo divisor: taxas incidem sobre a venda",
         "Balcao, WhatsApp, iFood, 99Food e Rappi lado a lado",
         "Lucro liquido e margem real por canal",
         "Arredondamento psicologico para .90"],
    ),
    "simulador": (
        "screens.simulador", "TelaSimulador",
        "E se eu vender por outro preco?",
        ["Informe um preco e veja o lucro na hora",
         "Preco minimo antes do prejuizo",
         "Desconto maximo possivel em promocao",
         "Custo-alvo: quanto a ficha pode custar"],
    ),
    "fornecedores": (
        "screens.fornecedores", "TelaFornecedores",
        "De quem voce compra cada item",
        ["Cadastro completo de fornecedores",
         "Itens fornecidos por cada um",
         "Comparativo de preco entre fornecedores"],
    ),
    "relatorios": (
        "screens.relatorios", "TelaRelatorios",
        "Analises, PDF e Excel",
        ["Ficha tecnica em PDF para a cozinha",
         "Tabela de precos por canal",
         "Engenharia de cardapio: Estrela, Puxador, Enigma, Abacaxi",
         "Exportacao para Excel"],
    ),
    "configuracoes": (
        "screens.configuracoes", "TelaConfiguracoes",
        "Taxas, impostos e preferencias",
        ["Dados do estabelecimento e regime tributario",
         "Taxas padrao de cartao e comissao por canal",
         "Custos fixos mensais e rateio",
         "Backup e restauracao do banco"],
    ),
}


# ---------------------------------------------------------------------------
# Item do menu lateral
# ---------------------------------------------------------------------------


class ItemMenu(ctk.CTkFrame):
    """Linha do menu com barra indicadora, icone e rotulo."""

    def __init__(self, pai, chave, rotulo, icone, ao_clicar):
        super().__init__(pai, fg_color="transparent", height=Tamanhos.ITEM_MENU_ALTURA)
        self.pack_propagate(False)

        self.chave = chave
        self.ao_clicar = ao_clicar
        self.ativo = False

        self.barra = ctk.CTkFrame(self, width=3, fg_color="transparent",
                                  corner_radius=Raio.PILULA)
        self.barra.pack(side="left", fill="y", pady=6)

        self.conteudo = ctk.CTkFrame(self, fg_color="transparent", corner_radius=Raio.PADRAO)
        self.conteudo.pack(side="left", fill="both", expand=True, padx=(9, 10))

        self.icone = ctk.CTkLabel(self.conteudo, text=icone, font=Fontes.icone(17),
                                  text_color=Cores.TEXTO_SECUNDARIO, width=26)
        self.icone.pack(side="left", padx=(12, 10))

        self.rotulo = ctk.CTkLabel(self.conteudo, text=rotulo, font=Fontes.corpo(),
                                   text_color=Cores.TEXTO_SECUNDARIO, anchor="w")
        self.rotulo.pack(side="left", fill="x", expand=True)

        for widget in (self, self.conteudo, self.icone, self.rotulo):
            widget.bind("<Button-1>", self._clique)
            widget.bind("<Enter>", self._entrar)
            widget.bind("<Leave>", self._sair)
            widget.configure(cursor="hand2")

    def _clique(self, _=None):
        self.ao_clicar(self.chave)

    def _entrar(self, _=None):
        if not self.ativo:
            self.conteudo.configure(fg_color=Cores.CARD_HOVER)

    def _sair(self, _=None):
        if not self.ativo:
            self.conteudo.configure(fg_color="transparent")

    def marcar(self, ativo):
        self.ativo = ativo
        if ativo:
            self.barra.configure(fg_color=Cores.LARANJA)
            self.conteudo.configure(fg_color=Cores.LARANJA_SUAVE)
            self.icone.configure(text_color=Cores.LARANJA)
            self.rotulo.configure(text_color=Cores.TEXTO, font=Fontes.corpo_forte())
        else:
            self.barra.configure(fg_color="transparent")
            self.conteudo.configure(fg_color="transparent")
            self.icone.configure(text_color=Cores.TEXTO_SECUNDARIO)
            self.rotulo.configure(text_color=Cores.TEXTO_SECUNDARIO, font=Fontes.corpo())


# ---------------------------------------------------------------------------
# Placeholder de tela ainda nao construida
# ---------------------------------------------------------------------------


class TelaEmConstrucao(ctk.CTkFrame):
    def __init__(self, pai, titulo, icone, recursos, erro=None):
        super().__init__(pai, fg_color="transparent")

        centro = ctk.CTkFrame(self, **estilo_card())
        centro.place(relx=0.5, rely=0.45, anchor="center")

        interno = ctk.CTkFrame(centro, fg_color="transparent")
        interno.pack(padx=44, pady=38)

        ctk.CTkLabel(interno, text=icone, font=Fontes.icone(38),
                     text_color=Cores.LARANJA).pack()
        ctk.CTkLabel(interno, text=titulo, font=Fontes.titulo(),
                     text_color=Cores.TEXTO).pack(pady=(Espaco.MD, 2))

        if erro:
            ctk.CTkLabel(interno, text="Erro ao carregar a tela", font=Fontes.corpo(),
                         text_color=Cores.PREJUIZO).pack(pady=(0, Espaco.MD))
            caixa = ctk.CTkTextbox(interno, width=560, height=180,
                                   font=Fontes.numero(), fg_color=Cores.ENTRADA,
                                   text_color=Cores.TEXTO_SECUNDARIO,
                                   border_color=Cores.BORDA, border_width=1)
            caixa.pack()
            caixa.insert("1.0", erro)
            caixa.configure(state="disabled")
            return

        ctk.CTkLabel(interno, text="Em construcao", font=Fontes.pequeno(),
                     text_color=Cores.TEXTO_APAGADO).pack(pady=(0, Espaco.LG))

        for recurso in recursos:
            linha = ctk.CTkFrame(interno, fg_color="transparent")
            linha.pack(fill="x", pady=3)
            ctk.CTkLabel(linha, text=Icone.OK, font=Fontes.icone(11),
                         text_color=Cores.VERDE, width=20).pack(side="left")
            ctk.CTkLabel(linha, text=recurso, font=Fontes.corpo(),
                         text_color=Cores.TEXTO_SECUNDARIO, anchor="w").pack(side="left")


# ---------------------------------------------------------------------------
# Splash
# ---------------------------------------------------------------------------


class Splash(ctk.CTkToplevel):
    LARGURA, ALTURA = 460, 260

    def __init__(self, pai):
        super().__init__(pai)
        self.overrideredirect(True)
        self.configure(fg_color=Cores.CARD)
        self.attributes("-topmost", True)

        x = (self.winfo_screenwidth() - self.LARGURA) // 2
        y = (self.winfo_screenheight() - self.ALTURA) // 2
        self.geometry(f"{self.LARGURA}x{self.ALTURA}+{x}+{y}")

        borda = ctk.CTkFrame(self, fg_color=Cores.CARD, corner_radius=Raio.GRANDE,
                             border_color=Cores.LARANJA, border_width=2)
        borda.pack(fill="both", expand=True)

        montar_logo(borda, 40).pack(pady=(58, 6))
        ctk.CTkLabel(borda, text=APP_SLOGAN, font=Fontes.corpo(),
                     text_color=Cores.TEXTO_SECUNDARIO).pack()

        self.progresso = ctk.CTkProgressBar(borda, width=280, height=4,
                                            progress_color=Cores.LARANJA,
                                            fg_color=Cores.BORDA,
                                            corner_radius=Raio.PILULA)
        self.progresso.pack(pady=(32, 10))
        self.progresso.set(0)

        self.status = ctk.CTkLabel(borda, text="Iniciando...", font=Fontes.pequeno(),
                                   text_color=Cores.TEXTO_APAGADO)
        self.status.pack()

        ctk.CTkLabel(borda, text=f"{APP_FAMILIA}  ·  v{APP_VERSAO}", font=Fontes.micro(),
                     text_color=Cores.TEXTO_APAGADO).pack(side="bottom", pady=Espaco.MD)

    def etapa(self, texto, fracao):
        self.status.configure(text=texto)
        self.progresso.set(fracao)
        self.update()


# ---------------------------------------------------------------------------
# Janela principal
# ---------------------------------------------------------------------------


class LosPrice(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"{APP_NOME} - Sistema Inteligente de Precificacao")
        self.configure(fg_color=Cores.FUNDO)
        self.minsize(Tamanhos.JANELA_MIN_LARGURA, Tamanhos.JANELA_MIN_ALTURA)
        self._centralizar(Tamanhos.JANELA_LARGURA, Tamanhos.JANELA_ALTURA)
        self._aplicar_icone()

        self.itens_menu = {}
        self.telas = {}          # cache: chave -> frame ja construido
        self.tela_atual = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._montar_sidebar()
        self._montar_area()

    # -- layout ------------------------------------------------------------

    def _centralizar(self, largura, altura):
        x = (self.winfo_screenwidth() - largura) // 2
        y = (self.winfo_screenheight() - altura) // 2 - 20
        self.geometry(f"{largura}x{altura}+{x}+{max(y, 0)}")

    def _aplicar_icone(self):
        """Icone da janela e da barra de tarefas. Ausencia nao impede o app de abrir."""
        caminho = conexao.caminho_recurso("assets", "icone.ico")
        if not os.path.exists(caminho):
            return
        try:
            self.iconbitmap(caminho)
            # o CustomTkinter reaplica o icone padrao depois da criacao da janela
            self.after(250, lambda: self.iconbitmap(caminho))
        except Exception:
            pass

    def _montar_sidebar(self):
        barra = ctk.CTkFrame(self, width=Tamanhos.SIDEBAR_LARGURA,
                             fg_color=Cores.SIDEBAR, corner_radius=0)
        barra.grid(row=0, column=0, sticky="nsw")
        barra.grid_propagate(False)

        # logo
        topo = ctk.CTkFrame(barra, fg_color="transparent", height=Tamanhos.TOPO_ALTURA)
        topo.pack(fill="x", pady=(Espaco.LG, Espaco.SM))
        topo.pack_propagate(False)
        montar_logo(topo, 25).pack(padx=Espaco.LG, anchor="w")
        ctk.CTkLabel(topo, text="Precificacao inteligente", font=Fontes.micro(),
                     text_color=Cores.TEXTO_APAGADO).pack(padx=Espaco.LG, anchor="w")

        ctk.CTkFrame(barra, height=1, fg_color=Cores.DIVISOR).pack(
            fill="x", padx=Espaco.MD, pady=(Espaco.SM, Espaco.MD))

        # itens
        for chave, rotulo, icone in MENU:
            item = ItemMenu(barra, chave, rotulo, icone, self.navegar)
            item.pack(fill="x", pady=1)
            self.itens_menu[chave] = item

        # rodape
        rodape = ctk.CTkFrame(barra, fg_color="transparent")
        rodape.pack(side="bottom", fill="x", padx=Espaco.MD, pady=Espaco.MD)

        ctk.CTkFrame(rodape, height=1, fg_color=Cores.DIVISOR).pack(
            fill="x", pady=(0, Espaco.MD))

        self.botao_tema = ctk.CTkButton(
            rodape, text=f"  {Icone.SOL}   Tema claro", command=self._alternar_tema,
            font=Fontes.corpo(), anchor="w", height=34,
            fg_color="transparent", hover_color=Cores.CARD_HOVER,
            text_color=Cores.TEXTO_SECUNDARIO, corner_radius=Raio.PADRAO,
        )
        self.botao_tema.pack(fill="x")

        ctk.CTkLabel(rodape, text=f"v{APP_VERSAO}  ·  {APP_FAMILIA}",
                     font=Fontes.micro(), text_color=Cores.TEXTO_APAGADO).pack(
            pady=(Espaco.SM, 0))

    def _montar_area(self):
        area = ctk.CTkFrame(self, fg_color="transparent")
        area.grid(row=0, column=1, sticky="nsew")
        area.grid_rowconfigure(1, weight=1)
        area.grid_columnconfigure(0, weight=1)

        # barra superior
        topo = ctk.CTkFrame(area, height=Tamanhos.TOPO_ALTURA,
                            fg_color=Cores.SUPERFICIE, corner_radius=0)
        topo.grid(row=0, column=0, sticky="ew")
        topo.grid_propagate(False)

        texto = ctk.CTkFrame(topo, fg_color="transparent")
        texto.pack(side="left", padx=Espaco.PADDING_JANELA, pady=Espaco.MD)

        self.titulo = ctk.CTkLabel(texto, text="", font=Fontes.titulo(),
                                   text_color=Cores.TEXTO, anchor="w")
        self.titulo.pack(anchor="w")
        self.subtitulo = ctk.CTkLabel(texto, text="", font=Fontes.pequeno(),
                                      text_color=Cores.TEXTO_SECUNDARIO, anchor="w")
        self.subtitulo.pack(anchor="w")

        ctk.CTkFrame(area, height=1, fg_color=Cores.BORDA).grid(
            row=0, column=0, sticky="sew")

        # conteudo
        self.conteudo = ctk.CTkFrame(area, fg_color="transparent")
        self.conteudo.grid(row=1, column=0, sticky="nsew",
                           padx=Espaco.PADDING_JANELA, pady=Espaco.PADDING_JANELA)

    # -- navegacao ---------------------------------------------------------

    def navegar(self, chave):
        if chave == self.tela_atual or chave not in ROTAS:
            return

        if self.tela_atual:
            self.telas[self.tela_atual].pack_forget()

        for c, item in self.itens_menu.items():
            item.marcar(c == chave)

        rotulo = next(r for k, r, _ in MENU if k == chave)
        self.titulo.configure(text=rotulo)
        self.subtitulo.configure(text=ROTAS[chave][2])

        if chave not in self.telas:
            self.telas[chave] = self._construir_tela(chave)
        self.telas[chave].pack(fill="both", expand=True)

        self.tela_atual = chave

    def _construir_tela(self, chave):
        """Tenta a tela real. Se ainda nao existe, entra o placeholder."""
        modulo, classe, _, recursos = ROTAS[chave]
        icone = next(i for k, _, i in MENU if k == chave)
        rotulo = next(r for k, r, _ in MENU if k == chave)

        try:
            mod = importlib.import_module(modulo)
            return getattr(mod, classe)(self.conteudo)
        except (ImportError, AttributeError):
            return TelaEmConstrucao(self.conteudo, rotulo, icone, recursos)
        except Exception:
            return TelaEmConstrucao(self.conteudo, rotulo, icone, recursos,
                                    erro=traceback.format_exc())

    # -- tema --------------------------------------------------------------

    def _alternar_tema(self):
        escuro = ctk.get_appearance_mode() == "Dark"
        ctk.set_appearance_mode("light" if escuro else "dark")
        self.botao_tema.configure(
            text=f"  {Icone.LUA}   Tema escuro" if escuro else f"  {Icone.SOL}   Tema claro"
        )
        conexao.salvar_config("tema", "claro" if escuro else "escuro")


# ---------------------------------------------------------------------------
# Inicializacao
# ---------------------------------------------------------------------------


def main():
    aplicar_tema("escuro")

    app = LosPrice()
    app.withdraw()

    splash = Splash(app)
    try:
        splash.etapa("Preparando o banco de dados...", 0.30)
        conexao.inicializar()

        splash.etapa("Carregando configuracoes...", 0.65)
        modo = conexao.obter_config("tema", "escuro")
        if modo == "claro":
            ctk.set_appearance_mode("light")
            app.botao_tema.configure(text=f"  {Icone.LUA}   Tema escuro")

        splash.etapa("Montando a interface...", 0.90)
        app.navegar("dashboard")

        splash.etapa("Pronto", 1.0)
        app.after(500, lambda: (splash.destroy(), app.deiconify(), app.focus_force()))
    except Exception:
        splash.destroy()
        app.deiconify()
        raise

    app.mainloop()


if __name__ == "__main__":
    main()
