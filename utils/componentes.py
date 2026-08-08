"""
LosPrice - Componentes reutilizaveis
=====================================

Widgets padronizados usados por todas as telas. Nenhuma tela desenha
botao, card ou tabela na mao: sempre monta a partir daqui.

Observacao sobre icones: o Tk faz fallback automatico de fonte, entao
um caractere do Segoe MDL2 Assets renderiza corretamente mesmo dentro
de um widget configurado com Segoe UI. Por isso da para misturar
icone + texto no mesmo rotulo.
"""

import customtkinter as ctk

from utils.tema import (
    Cores, Espaco, Fontes, Icone, Raio, Tamanhos,
    estilo_botao_perigo, estilo_botao_primario, estilo_botao_secundario,
    estilo_botao_sucesso, estilo_card, estilo_entrada,
    formatar_moeda, formatar_pct,
)


# ---------------------------------------------------------------------------
# Botao
# ---------------------------------------------------------------------------

_VARIANTES = {
    "primario": estilo_botao_primario,
    "sucesso": estilo_botao_sucesso,
    "secundario": estilo_botao_secundario,
    "perigo": estilo_botao_perigo,
}


class Botao(ctk.CTkButton):
    def __init__(self, pai, texto="", icone=None, variante="primario", **kw):
        estilo = _VARIANTES.get(variante, estilo_botao_primario)()
        estilo.update(kw)
        rotulo = f"{icone}   {texto}" if icone and texto else (icone or texto)
        super().__init__(pai, text=rotulo, font=Fontes.corpo_forte(), **estilo)


class BotaoIcone(ctk.CTkButton):
    """Botao quadrado apenas com icone, para acoes de linha da tabela."""

    def __init__(self, pai, icone, comando=None, cor=None, dica=None, **kw):
        super().__init__(
            pai, text=icone, command=comando, width=30, height=28,
            font=Fontes.icone(14), fg_color="transparent",
            hover_color=Cores.CARD_HOVER, text_color=cor or Cores.TEXTO_SECUNDARIO,
            corner_radius=Raio.PEQUENO, **kw,
        )
        if dica:
            Dica(self, dica)


# ---------------------------------------------------------------------------
# Dica (tooltip)
# ---------------------------------------------------------------------------


class Dica:
    def __init__(self, widget, texto, atraso=450):
        self.widget = widget
        self.texto = texto
        self.atraso = atraso
        self.janela = None
        self.agendado = None
        widget.bind("<Enter>", self._agendar, add="+")
        widget.bind("<Leave>", self._cancelar, add="+")
        widget.bind("<Button-1>", self._cancelar, add="+")

    def _agendar(self, _=None):
        self._cancelar()
        self.agendado = self.widget.after(self.atraso, self._mostrar)

    def _cancelar(self, _=None):
        if self.agendado:
            self.widget.after_cancel(self.agendado)
            self.agendado = None
        if self.janela:
            self.janela.destroy()
            self.janela = None

    def _mostrar(self):
        if self.janela:
            return
        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6

        self.janela = ctk.CTkToplevel(self.widget)
        self.janela.overrideredirect(True)
        self.janela.attributes("-topmost", True)

        caixa = ctk.CTkFrame(self.janela, fg_color=Cores.CARD, corner_radius=Raio.PEQUENO,
                             border_color=Cores.BORDA, border_width=1)
        caixa.pack()
        ctk.CTkLabel(caixa, text=self.texto, font=Fontes.pequeno(),
                     text_color=Cores.TEXTO).pack(padx=Espaco.SM, pady=4)

        self.janela.update_idletasks()
        self.janela.geometry(f"+{x - self.janela.winfo_width() // 2}+{y}")


# ---------------------------------------------------------------------------
# Cartoes
# ---------------------------------------------------------------------------


class Cartao(ctk.CTkFrame):
    """Cartao com cabecalho opcional. Filhos vao em .corpo."""

    def __init__(self, pai, titulo=None, subtitulo=None, acao=None, **kw):
        estilo = estilo_card()
        estilo.update(kw)
        super().__init__(pai, **estilo)

        if titulo:
            topo = ctk.CTkFrame(self, fg_color="transparent")
            topo.pack(fill="x", padx=Espaco.PADDING_CARD, pady=(Espaco.PADDING_CARD, 0))

            texto = ctk.CTkFrame(topo, fg_color="transparent")
            texto.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(texto, text=titulo, font=Fontes.subtitulo(),
                         text_color=Cores.TEXTO, anchor="w").pack(anchor="w")
            if subtitulo:
                ctk.CTkLabel(texto, text=subtitulo, font=Fontes.pequeno(),
                             text_color=Cores.TEXTO_SECUNDARIO, anchor="w").pack(anchor="w")
            if acao:
                acao(topo)

        self.corpo = ctk.CTkFrame(self, fg_color="transparent")
        self.corpo.pack(fill="both", expand=True,
                        padx=Espaco.PADDING_CARD, pady=Espaco.PADDING_CARD)


class CardMetrica(ctk.CTkFrame):
    """Card numerico do dashboard."""

    def __init__(self, pai, rotulo, valor="--", cor=None, icone=None, apoio=None):
        super().__init__(pai, **estilo_card())
        self.cor = cor or Cores.LARANJA

        ctk.CTkFrame(self, fg_color=self.cor, height=3, corner_radius=Raio.PILULA).pack(
            fill="x", padx=Espaco.PADDING_CARD, pady=(Espaco.PADDING_CARD, Espaco.MD))

        linha = ctk.CTkFrame(self, fg_color="transparent")
        linha.pack(fill="x", padx=Espaco.PADDING_CARD)

        self.valor = ctk.CTkLabel(linha, text=valor, font=Fontes.valor_destaque(),
                                  text_color=self.cor, anchor="w")
        self.valor.pack(side="left")
        if icone:
            ctk.CTkLabel(linha, text=icone, font=Fontes.icone(22),
                         text_color=Cores.TEXTO_APAGADO).pack(side="right")

        ctk.CTkLabel(self, text=rotulo, font=Fontes.pequeno(),
                     text_color=Cores.TEXTO_SECUNDARIO, anchor="w").pack(
            fill="x", padx=Espaco.PADDING_CARD)

        self.apoio = ctk.CTkLabel(self, text=apoio or "", font=Fontes.micro(),
                                  text_color=Cores.TEXTO_APAGADO, anchor="w")
        self.apoio.pack(fill="x", padx=Espaco.PADDING_CARD,
                        pady=(2, Espaco.PADDING_CARD))

    def atualizar(self, valor=None, apoio=None, cor=None):
        if cor:
            self.cor = cor
            self.valor.configure(text_color=cor)
        if valor is not None:
            self.valor.configure(text=valor)
        if apoio is not None:
            self.apoio.configure(text=apoio)


class Badge(ctk.CTkFrame):
    """Pilula colorida para status e margens."""

    def __init__(self, pai, texto, cor=None, fundo=None):
        super().__init__(pai, fg_color=fundo or Cores.CARD_HOVER, corner_radius=Raio.PILULA)
        self.rotulo = ctk.CTkLabel(self, text=texto, font=Fontes.micro(),
                                   text_color=cor or Cores.TEXTO_SECUNDARIO)
        self.rotulo.pack(padx=Espaco.SM, pady=2)


# ---------------------------------------------------------------------------
# Campos de formulario
# ---------------------------------------------------------------------------


class Campo(ctk.CTkFrame):
    """Rotulo + entrada + linha de erro/ajuda."""

    def __init__(self, pai, rotulo, valor="", ajuda=None, largura=None,
                 obrigatorio=False, ao_digitar=None, **kw):
        super().__init__(pai, fg_color="transparent")

        cabeca = ctk.CTkFrame(self, fg_color="transparent")
        cabeca.pack(fill="x")
        ctk.CTkLabel(cabeca, text=rotulo, font=Fontes.pequeno(),
                     text_color=Cores.TEXTO_SECUNDARIO, anchor="w").pack(side="left")
        if obrigatorio:
            ctk.CTkLabel(cabeca, text=" *", font=Fontes.pequeno(),
                         text_color=Cores.LARANJA).pack(side="left")

        estilo = estilo_entrada()
        if largura:
            estilo["width"] = largura
        estilo.update(kw)

        self.variavel = ctk.StringVar(value=str(valor))
        self.entrada = ctk.CTkEntry(self, textvariable=self.variavel,
                                    font=Fontes.corpo(), **estilo)
        self.entrada.pack(fill="x", pady=(3, 0))

        self.rodape = ctk.CTkLabel(self, text=ajuda or "", font=Fontes.micro(),
                                   text_color=Cores.TEXTO_APAGADO, anchor="w")
        self.rodape.pack(fill="x", pady=(2, 0))
        self._ajuda = ajuda or ""

        if ao_digitar:
            self.variavel.trace_add("write", lambda *_: ao_digitar())

    def get(self):
        return self.variavel.get().strip()

    def set(self, valor):
        self.variavel.set("" if valor is None else str(valor))

    def erro(self, mensagem):
        self.entrada.configure(border_color=Cores.PREJUIZO)
        self.rodape.configure(text=mensagem, text_color=Cores.PREJUIZO)

    def limpar_erro(self):
        self.entrada.configure(border_color=Cores.BORDA)
        self.rodape.configure(text=self._ajuda, text_color=Cores.TEXTO_APAGADO)

    def focar(self):
        self.entrada.focus_set()


class CampoSelecao(ctk.CTkFrame):
    """Rotulo + lista suspensa."""

    def __init__(self, pai, rotulo, opcoes, valor=None, largura=None,
                 ao_mudar=None, ajuda=None):
        super().__init__(pai, fg_color="transparent")

        if rotulo:
            ctk.CTkLabel(self, text=rotulo, font=Fontes.pequeno(),
                         text_color=Cores.TEXTO_SECUNDARIO, anchor="w").pack(fill="x")

        self.variavel = ctk.StringVar(value=valor or (opcoes[0] if opcoes else ""))
        self.menu = ctk.CTkOptionMenu(
            self, values=list(opcoes) or [""], variable=self.variavel,
            font=Fontes.corpo(), dropdown_font=Fontes.corpo(),
            fg_color=Cores.ENTRADA, button_color=Cores.BORDA,
            button_hover_color=Cores.LARANJA, text_color=Cores.TEXTO,
            dropdown_fg_color=Cores.CARD, dropdown_text_color=Cores.TEXTO,
            dropdown_hover_color=Cores.CARD_HOVER,
            corner_radius=Raio.PEQUENO, height=Tamanhos.ENTRADA_ALTURA,
            width=largura or 140,
            command=(lambda _: ao_mudar()) if ao_mudar else None,
        )
        self.menu.pack(fill="x", pady=(3, 0) if rotulo else 0)

        if rotulo:
            self.rodape = ctk.CTkLabel(self, text=ajuda or "", font=Fontes.micro(),
                                       text_color=Cores.TEXTO_APAGADO, anchor="w")
            self.rodape.pack(fill="x", pady=(2, 0))

    def get(self):
        return self.variavel.get()

    def set(self, valor):
        if valor:
            self.variavel.set(valor)

    def opcoes(self, valores, manter=True):
        atual = self.get()
        self.menu.configure(values=list(valores) or [""])
        if manter and atual in valores:
            self.variavel.set(atual)
        elif valores:
            self.variavel.set(valores[0])


class BarraBusca(ctk.CTkFrame):
    def __init__(self, pai, ao_buscar, texto="Buscar...", largura=300):
        super().__init__(pai, fg_color="transparent")

        self.variavel = ctk.StringVar()
        self.variavel.trace_add("write", lambda *_: ao_buscar(self.variavel.get().strip()))

        caixa = ctk.CTkFrame(self, fg_color=Cores.ENTRADA, corner_radius=Raio.PEQUENO,
                             border_color=Cores.BORDA, border_width=1,
                             height=Tamanhos.ENTRADA_ALTURA, width=largura)
        caixa.pack()
        caixa.pack_propagate(False)

        ctk.CTkLabel(caixa, text=Icone.BUSCAR, font=Fontes.icone(13),
                     text_color=Cores.TEXTO_APAGADO).pack(side="left", padx=(10, 4))
        ctk.CTkEntry(caixa, textvariable=self.variavel, placeholder_text=texto,
                     font=Fontes.corpo(), fg_color="transparent", border_width=0,
                     text_color=Cores.TEXTO).pack(side="left", fill="both",
                                                  expand=True, padx=(0, 6))

    def get(self):
        return self.variavel.get().strip()

    def limpar(self):
        self.variavel.set("")


# ---------------------------------------------------------------------------
# Tabela
# ---------------------------------------------------------------------------


class Tabela(ctk.CTkFrame):
    """
    Tabela com cabecalho fixo, corpo rolavel, zebra e ordenacao por clique.

    colunas: lista de dicts
        chave        nome do campo na linha de dados
        titulo       texto do cabecalho
        largura      em pixels
        alinhamento  'w' (padrao), 'e' para numeros, 'center'
        formato      'texto' | 'moeda' | 'moeda4' | 'pct' | 'numero'
        fonte        callable opcional -> objeto de fonte
        cor          callable(linha) -> cor do texto
    """

    def __init__(self, pai, colunas, ao_clicar=None, acoes=None, vazio=None):
        super().__init__(pai, **estilo_card())

        self.colunas = colunas
        self.ao_clicar = ao_clicar
        self.acoes = acoes or []
        self.vazio = vazio or {}
        self.linhas = []
        self.ordem_chave = None
        self.ordem_desc = False
        self._cabecalhos = {}

        # cabecalho
        self.cabecalho = ctk.CTkFrame(self, fg_color=Cores.TABELA_CABECALHO,
                                      corner_radius=0, height=40)
        self.cabecalho.pack(fill="x")
        self.cabecalho.pack_propagate(False)
        self._montar_cabecalho()

        ctk.CTkFrame(self, height=1, fg_color=Cores.BORDA).pack(fill="x")

        # corpo
        self.corpo = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.corpo.pack(fill="both", expand=True)

        # rodape com contagem
        self.rodape = ctk.CTkLabel(self, text="", font=Fontes.micro(),
                                   text_color=Cores.TEXTO_APAGADO, anchor="w")
        self.rodape.pack(fill="x", padx=Espaco.MD, pady=(4, 6))

    def _montar_cabecalho(self):
        for coluna in self.colunas:
            celula = ctk.CTkFrame(self.cabecalho, fg_color="transparent",
                                  width=coluna.get("largura", 120))
            celula.pack(side="left", fill="y", padx=(Espaco.MD, 0))
            celula.pack_propagate(False)

            rotulo = ctk.CTkLabel(
                celula, text=coluna["titulo"].upper(), font=Fontes.micro(),
                text_color=Cores.TEXTO_APAGADO,
                anchor=coluna.get("alinhamento", "w"),
            )
            rotulo.pack(fill="both", expand=True)
            self._cabecalhos[coluna["chave"]] = rotulo

            for widget in (celula, rotulo):
                widget.configure(cursor="hand2")
                widget.bind("<Button-1>",
                            lambda _e, c=coluna["chave"]: self._ordenar(c))

        if self.acoes:
            largura = 34 * len(self.acoes) + Espaco.MD
            reserva = ctk.CTkFrame(self.cabecalho, fg_color="transparent", width=largura)
            reserva.pack(side="left", fill="y")
            reserva.pack_propagate(False)

    def _ordenar(self, chave):
        self.ordem_desc = not self.ordem_desc if self.ordem_chave == chave else False
        self.ordem_chave = chave

        for c, rotulo in self._cabecalhos.items():
            titulo = next(x["titulo"] for x in self.colunas if x["chave"] == c).upper()
            if c == chave:
                seta = Icone.SETA_BAIXO if self.ordem_desc else Icone.SETA_CIMA
                rotulo.configure(text=f"{titulo} {seta}", text_color=Cores.LARANJA)
            else:
                rotulo.configure(text=titulo, text_color=Cores.TEXTO_APAGADO)

        self.preencher(self.linhas, reordenar=True)

    def _valor_formatado(self, coluna, linha):
        bruto = linha.get(coluna["chave"])
        formato = coluna.get("formato", "texto")
        if bruto is None:
            return "--"
        if formato == "moeda":
            return formatar_moeda(bruto)
        if formato == "moeda4":
            from utils.tema import formatar_moeda_precisa
            return formatar_moeda_precisa(bruto)
        if formato == "pct":
            return formatar_pct(bruto)
        if formato == "numero":
            from utils.tema import formatar_numero
            return formatar_numero(bruto)
        return str(bruto)

    def preencher(self, linhas, reordenar=False):
        self.linhas = list(linhas)

        for widget in self.corpo.winfo_children():
            widget.destroy()

        dados = self.linhas
        if self.ordem_chave:
            def chave(l):
                v = l.get(self.ordem_chave)
                return (v is None, v.lower() if isinstance(v, str) else v)
            try:
                dados = sorted(dados, key=chave, reverse=self.ordem_desc)
            except TypeError:
                pass

        if not dados:
            self._mostrar_vazio()
            self.rodape.configure(text="")
            return

        for i, linha in enumerate(dados):
            self._montar_linha(i, linha)

        plural = "registro" if len(dados) == 1 else "registros"
        self.rodape.configure(text=f"{len(dados)} {plural}")

    def _montar_linha(self, indice, linha):
        fundo = Cores.TABELA_LINHA if indice % 2 == 0 else Cores.TABELA_LINHA_ALT
        item = ctk.CTkFrame(self.corpo, fg_color=fundo, corner_radius=0, height=44)
        item.pack(fill="x")
        item.pack_propagate(False)

        celulas = []
        for coluna in self.colunas:
            celula = ctk.CTkFrame(item, fg_color="transparent",
                                  width=coluna.get("largura", 120))
            celula.pack(side="left", fill="y", padx=(Espaco.MD, 0))
            celula.pack_propagate(False)

            cor = coluna["cor"](linha) if callable(coluna.get("cor")) else Cores.TEXTO
            fonte = coluna["fonte"]() if callable(coluna.get("fonte")) else Fontes.corpo()

            rotulo = ctk.CTkLabel(celula, text=self._valor_formatado(coluna, linha),
                                  font=fonte, text_color=cor,
                                  anchor=coluna.get("alinhamento", "w"))
            rotulo.pack(fill="both", expand=True)
            celulas.extend([celula, rotulo])

        if self.acoes:
            caixa = ctk.CTkFrame(item, fg_color="transparent",
                                 width=34 * len(self.acoes) + Espaco.MD)
            caixa.pack(side="left", fill="y")
            caixa.pack_propagate(False)
            for acao in self.acoes:
                BotaoIcone(caixa, acao["icone"],
                           comando=lambda a=acao, l=linha: a["comando"](l),
                           cor=acao.get("cor"), dica=acao.get("dica")).pack(
                    side="left", pady=8, padx=2)

        def entrar(_=None):
            item.configure(fg_color=Cores.CARD_HOVER)

        def sair(_=None):
            item.configure(fg_color=fundo)

        for widget in [item] + celulas:
            widget.bind("<Enter>", entrar, add="+")
            widget.bind("<Leave>", sair, add="+")
            if self.ao_clicar:
                widget.configure(cursor="hand2")
                widget.bind("<Button-1>", lambda _e, l=linha: self.ao_clicar(l), add="+")

    def _mostrar_vazio(self):
        caixa = ctk.CTkFrame(self.corpo, fg_color="transparent")
        caixa.pack(expand=True, pady=60)

        ctk.CTkLabel(caixa, text=self.vazio.get("icone", Icone.BUSCAR),
                     font=Fontes.icone(34), text_color=Cores.TEXTO_APAGADO).pack()
        ctk.CTkLabel(caixa, text=self.vazio.get("titulo", "Nada por aqui"),
                     font=Fontes.subtitulo(), text_color=Cores.TEXTO_SECUNDARIO).pack(
            pady=(Espaco.MD, 2))
        if self.vazio.get("mensagem"):
            ctk.CTkLabel(caixa, text=self.vazio["mensagem"], font=Fontes.corpo(),
                         text_color=Cores.TEXTO_APAGADO).pack()
        if self.vazio.get("acao"):
            Botao(caixa, self.vazio["acao"]["texto"], icone=Icone.ADICIONAR,
                  command=self.vazio["acao"]["comando"], width=200).pack(
                pady=(Espaco.LG, 0))


# ---------------------------------------------------------------------------
# Avisos
# ---------------------------------------------------------------------------


class Notificacao(ctk.CTkFrame):
    """Aviso flutuante no canto inferior direito. Some sozinho."""

    CORES = {
        "sucesso": (Cores.VERDE, Icone.OK),
        "erro": (Cores.PREJUIZO, Icone.ALERTA),
        "aviso": (Cores.ATENCAO, Icone.ALERTA),
        "info": (Cores.INFO, Icone.ALERTA),
    }

    def __init__(self, pai, mensagem, tipo="sucesso", duracao=3200):
        super().__init__(pai, fg_color=Cores.CARD, corner_radius=Raio.PADRAO,
                         border_color=Cores.BORDA, border_width=1)
        cor, icone = self.CORES.get(tipo, self.CORES["info"])

        ctk.CTkFrame(self, fg_color=cor, width=3, corner_radius=Raio.PILULA).pack(
            side="left", fill="y", padx=(6, 0), pady=8)
        ctk.CTkLabel(self, text=icone, font=Fontes.icone(15),
                     text_color=cor).pack(side="left", padx=(10, 8))
        ctk.CTkLabel(self, text=mensagem, font=Fontes.corpo(),
                     text_color=Cores.TEXTO).pack(side="left", padx=(0, Espaco.MD),
                                                  pady=Espaco.MD)

        self.place(relx=0.98, rely=0.96, anchor="se")
        self.after(duracao, self.destroy)


def notificar(pai, mensagem, tipo="sucesso"):
    janela = pai.winfo_toplevel()
    return Notificacao(janela, mensagem, tipo)


class Confirmacao(ctk.CTkToplevel):
    """Modal de sim/nao. Use a funcao confirmar()."""

    def __init__(self, pai, titulo, mensagem, texto_ok="Confirmar", perigo=False):
        super().__init__(pai)
        self.resultado = False

        self.title("")
        self.overrideredirect(True)
        self.configure(fg_color=Cores.FUNDO)
        self.transient(pai.winfo_toplevel())
        self.grab_set()

        caixa = ctk.CTkFrame(self, fg_color=Cores.CARD, corner_radius=Raio.GRANDE,
                             border_color=Cores.BORDA, border_width=1)
        caixa.pack(fill="both", expand=True)

        interno = ctk.CTkFrame(caixa, fg_color="transparent")
        interno.pack(padx=Espaco.XL, pady=Espaco.XL)

        ctk.CTkLabel(interno, text=Icone.ALERTA, font=Fontes.icone(28),
                     text_color=Cores.PREJUIZO if perigo else Cores.ATENCAO).pack()
        ctk.CTkLabel(interno, text=titulo, font=Fontes.subtitulo(),
                     text_color=Cores.TEXTO).pack(pady=(Espaco.MD, 4))
        ctk.CTkLabel(interno, text=mensagem, font=Fontes.corpo(),
                     text_color=Cores.TEXTO_SECUNDARIO, wraplength=380,
                     justify="center").pack()

        acoes = ctk.CTkFrame(interno, fg_color="transparent")
        acoes.pack(pady=(Espaco.XL, 0))
        Botao(acoes, "Cancelar", variante="secundario", width=130,
              command=self._negar).pack(side="left", padx=(0, Espaco.SM))
        Botao(acoes, texto_ok, variante="perigo" if perigo else "primario",
              width=130, command=self._aceitar).pack(side="left")

        self.bind("<Escape>", lambda _: self._negar())
        self.bind("<Return>", lambda _: self._aceitar())

        self.update_idletasks()
        self._centralizar(pai)
        self.focus_force()

    def _centralizar(self, pai):
        janela = pai.winfo_toplevel()
        x = janela.winfo_rootx() + (janela.winfo_width() - self.winfo_width()) // 2
        y = janela.winfo_rooty() + (janela.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _aceitar(self):
        self.resultado = True
        self.destroy()

    def _negar(self):
        self.resultado = False
        self.destroy()


def confirmar(pai, titulo, mensagem, texto_ok="Confirmar", perigo=False):
    dialogo = Confirmacao(pai, titulo, mensagem, texto_ok, perigo)
    pai.wait_window(dialogo)
    return dialogo.resultado


# ---------------------------------------------------------------------------
# Auxiliares de layout
# ---------------------------------------------------------------------------


class BarraFerramentas(ctk.CTkFrame):
    """Linha de topo das telas: busca e filtros a esquerda, acoes a direita."""

    def __init__(self, pai):
        super().__init__(pai, fg_color="transparent")
        self.esquerda = ctk.CTkFrame(self, fg_color="transparent")
        self.esquerda.pack(side="left")
        self.direita = ctk.CTkFrame(self, fg_color="transparent")
        self.direita.pack(side="right")


def separador(pai, vertical=False, **kw):
    if vertical:
        return ctk.CTkFrame(pai, width=1, fg_color=Cores.DIVISOR, **kw)
    return ctk.CTkFrame(pai, height=1, fg_color=Cores.DIVISOR, **kw)


def linha_resumo(pai, rotulo, valor, cor=None, forte=False, icone=None):
    """Linha 'rotulo .......... valor' usada em paineis de calculo."""
    caixa = ctk.CTkFrame(pai, fg_color="transparent")
    caixa.pack(fill="x", pady=2)

    esquerda = ctk.CTkFrame(caixa, fg_color="transparent")
    esquerda.pack(side="left")
    if icone:
        ctk.CTkLabel(esquerda, text=icone, font=Fontes.icone(12),
                     text_color=cor or Cores.TEXTO_APAGADO).pack(side="left", padx=(0, 6))
    ctk.CTkLabel(esquerda, text=rotulo,
                 font=Fontes.corpo_forte() if forte else Fontes.corpo(),
                 text_color=Cores.TEXTO if forte else Cores.TEXTO_SECUNDARIO).pack(side="left")

    rotulo_valor = ctk.CTkLabel(
        caixa, text=valor,
        font=Fontes.numero_forte() if forte else Fontes.numero(),
        text_color=cor or (Cores.TEXTO if forte else Cores.TEXTO_SECUNDARIO),
    )
    rotulo_valor.pack(side="right")
    return rotulo_valor
