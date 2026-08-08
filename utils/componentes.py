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
    """Botao quadrado apenas com icone. Para dialogos e barras de acao."""

    def __init__(self, pai, icone, comando=None, cor=None, dica=None, **kw):
        super().__init__(
            pai, text=icone, command=comando, width=30, height=28,
            font=Fontes.icone(14), fg_color="transparent",
            hover_color=Cores.CARD_HOVER, text_color=cor or Cores.TEXTO_SECUNDARIO,
            corner_radius=Raio.PEQUENO, **kw,
        )
        if dica:
            Dica(self, dica)


class IconeAcao(ctk.CTkLabel):
    """
    Versao leve do BotaoIcone, para as linhas da tabela.

    Um CTkButton custa cerca de 3x um CTkLabel para criar. Numa tabela de
    68 linhas com 3 acoes cada sao 204 botoes por redesenho - o suficiente
    para travar a digitacao. Visualmente o resultado e o mesmo: icone que
    muda de cor no hover e responde ao clique.
    """

    def __init__(self, pai, icone, comando=None, cor=None, dica=None):
        self.cor = cor or Cores.TEXTO_SECUNDARIO
        super().__init__(pai, text=icone, font=Fontes.icone(14),
                         text_color=self.cor, width=28, cursor="hand2")

        if comando:
            self.bind("<Button-1>", lambda _e: comando())
        self.bind("<Enter>", lambda _e: self.configure(text_color=Cores.LARANJA))
        self.bind("<Leave>", lambda _e: self.configure(text_color=self.cor))

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
    """
    Rotulo + entrada + linha de erro/ajuda.

    ao_digitar roda a cada tecla. Quando o retorno de chamada e pesado
    (redesenhar uma grade inteira, por exemplo), passe `atraso` em ms
    para so executar quando o usuario parar de digitar.
    """

    def __init__(self, pai, rotulo, valor="", ajuda=None, largura=None,
                 obrigatorio=False, ao_digitar=None, atraso=0, **kw):
        super().__init__(pai, fg_color="transparent")
        self._agendado = None

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
            if atraso:
                self.variavel.trace_add(
                    "write", lambda *_: self._agendar(ao_digitar, atraso))
            else:
                self.variavel.trace_add("write", lambda *_: ao_digitar())

    def _agendar(self, retorno, atraso):
        if self._agendado:
            self.after_cancel(self._agendado)
        self._agendado = self.after(atraso, lambda: self._executar(retorno))

    def _executar(self, retorno):
        self._agendado = None
        retorno()

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
    """
    Campo de busca com atraso.

    Sem o atraso, cada tecla dispara uma reconstrucao inteira da tabela.
    Com 68 registros isso levava mais de 3 segundos por tecla e a
    digitacao travava. Agora a busca so roda quando o usuario para de
    digitar.
    """

    ATRASO = 250  # ms sem digitar antes de buscar

    def __init__(self, pai, ao_buscar, texto="Buscar...", largura=300,
                 atraso=None):
        super().__init__(pai, fg_color="transparent")

        self.ao_buscar = ao_buscar
        self.atraso = self.ATRASO if atraso is None else atraso
        self._agendado = None

        self.variavel = ctk.StringVar()
        self.variavel.trace_add("write", lambda *_: self._agendar())

        caixa = ctk.CTkFrame(self, fg_color=Cores.ENTRADA, corner_radius=Raio.PEQUENO,
                             border_color=Cores.BORDA, border_width=1,
                             height=Tamanhos.ENTRADA_ALTURA, width=largura)
        caixa.pack()
        caixa.pack_propagate(False)

        ctk.CTkLabel(caixa, text=Icone.BUSCAR, font=Fontes.icone(13),
                     text_color=Cores.TEXTO_APAGADO).pack(side="left", padx=(10, 4))
        entrada = ctk.CTkEntry(caixa, textvariable=self.variavel,
                               placeholder_text=texto, font=Fontes.corpo(),
                               fg_color="transparent", border_width=0,
                               text_color=Cores.TEXTO)
        entrada.pack(side="left", fill="both", expand=True, padx=(0, 6))
        entrada.bind("<Return>", lambda _: self._disparar())
        entrada.bind("<Escape>", lambda _: self.limpar())

    def _agendar(self):
        if self._agendado:
            self.after_cancel(self._agendado)
        self._agendado = self.after(self.atraso, self._disparar)

    def _disparar(self):
        self._agendado = None
        self.ao_buscar(self.get())

    def get(self):
        return self.variavel.get().strip()

    def limpar(self):
        self.variavel.set("")
        self._disparar()


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
        self._reserva = []          # linhas ja construidas, reaproveitadas
        self._vazio_widget = None

        # a fonte de cada coluna nao muda entre linhas: cria uma vez so
        self._fontes = [
            coluna["fonte"]() if callable(coluna.get("fonte")) else Fontes.corpo()
            for coluna in colunas
        ]

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

    def _configurar_colunas(self, container):
        """Larguras fixas por coluna, iguais no cabecalho e nas linhas."""
        for indice, coluna in enumerate(self.colunas):
            container.grid_columnconfigure(
                indice, minsize=coluna.get("largura", 120) + Espaco.MD)
        for extra in range(len(self.acoes)):
            container.grid_columnconfigure(len(self.colunas) + extra, minsize=34)

    def _montar_cabecalho(self):
        self._configurar_colunas(self.cabecalho)

        for indice, coluna in enumerate(self.colunas):
            rotulo = ctk.CTkLabel(
                self.cabecalho, text=coluna["titulo"].upper(), font=Fontes.micro(),
                text_color=Cores.TEXTO_APAGADO,
                anchor=coluna.get("alinhamento", "w"), cursor="hand2",
            )
            rotulo.grid(row=0, column=indice, sticky="nsew",
                        padx=(Espaco.MD, 0))
            rotulo.bind("<Button-1>",
                        lambda _e, c=coluna["chave"]: self._ordenar(c))
            self._cabecalhos[coluna["chave"]] = rotulo

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
        """
        Reaproveita as linhas ja construidas em vez de recriar tudo.

        Destruir e recriar 68 linhas custava segundos e travava a
        digitacao na busca. Agora as linhas existentes so trocam de texto
        e de cor; widget novo so nasce quando a lista cresce, e o excedente
        e escondido em vez de destruido.
        """
        self.linhas = list(linhas)

        if self._vazio_widget is not None:
            self._vazio_widget.destroy()
            self._vazio_widget = None

        dados = self.linhas
        if self.ordem_chave:
            def chave(l):
                v = l.get(self.ordem_chave)
                return (v is None, v.lower() if isinstance(v, str) else v)
            try:
                dados = sorted(dados, key=chave, reverse=self.ordem_desc)
            except TypeError:
                pass

        for registro in self._reserva:
            registro["frame"].pack_forget()

        if not dados:
            self._mostrar_vazio()
            self.rodape.configure(text="")
            return

        for indice, linha in enumerate(dados):
            registro = self._linha_reservada(indice)
            self._aplicar_linha(registro, indice, linha)
            registro["frame"].pack(fill="x")

        plural = "registro" if len(dados) == 1 else "registros"
        self.rodape.configure(text=f"{len(dados)} {plural}")

    def _linha_reservada(self, indice):
        """Devolve a linha do indice, criando se ainda nao existir."""
        while indice >= len(self._reserva):
            self._reserva.append(self._criar_linha(len(self._reserva)))
        return self._reserva[indice]

    def _criar_linha(self, indice):
        # Uma linha = 1 CTkFrame apenas. Cada CTkFrame desenha retangulo
        # arredondado com anti-aliasing num canvas; antes eram 9 por linha
        # (uma celula por coluna), o que dominava o tempo de montagem.
        item = ctk.CTkFrame(self.corpo, corner_radius=0, height=44)
        item.pack_propagate(False)
        self._configurar_colunas(item)

        registro = {"frame": item, "rotulos": [], "dados": {},
                    "fundo": Cores.TABELA_LINHA}

        for coluna_idx, coluna in enumerate(self.colunas):
            rotulo = ctk.CTkLabel(item, text="", font=self._fontes[coluna_idx],
                                  anchor=coluna.get("alinhamento", "w"))
            rotulo.grid(row=0, column=coluna_idx, sticky="nsew",
                        padx=(Espaco.MD, 0))
            registro["rotulos"].append(rotulo)

        for extra, acao in enumerate(self.acoes):
            IconeAcao(item, acao["icone"],
                      comando=lambda a=acao, r=registro: a["comando"](r["dados"]),
                      cor=acao.get("cor"), dica=acao.get("dica")).grid(
                row=0, column=len(self.colunas) + extra, sticky="ns", pady=8)

        def entrar(_=None):
            item.configure(fg_color=Cores.CARD_HOVER)

        def sair(_=None):
            item.configure(fg_color=registro["fundo"])

        # Um bind por LINHA em vez de um por widget: antes eram 3 eventos
        # x 15 widgets = 45 chamadas de bind(). Com uma bindtag propria da
        # linha sao 3 no total, e todos os filhos herdam.
        etiqueta = f"tl{id(self)}_{indice}"
        for widget in [item] + registro["rotulos"]:
            widget.bindtags((etiqueta,) + widget.bindtags())
            if self.ao_clicar:
                widget.configure(cursor="hand2")

        item.bind_class(etiqueta, "<Enter>", entrar)
        item.bind_class(etiqueta, "<Leave>", sair)
        if self.ao_clicar:
            item.bind_class(etiqueta, "<Button-1>",
                            lambda _e, r=registro: self.ao_clicar(r["dados"]))

        return registro

    def _aplicar_linha(self, registro, indice, linha):
        """Atualiza uma linha existente. So configure(), sem criar widget."""
        fundo = Cores.TABELA_LINHA if indice % 2 == 0 else Cores.TABELA_LINHA_ALT
        registro["fundo"] = fundo
        registro["dados"] = linha
        registro["frame"].configure(fg_color=fundo)

        for coluna_idx, coluna in enumerate(self.colunas):
            cor = coluna["cor"](linha) if callable(coluna.get("cor")) else Cores.TEXTO
            registro["rotulos"][coluna_idx].configure(
                text=self._valor_formatado(coluna, linha), text_color=cor)

    def _mostrar_vazio(self):
        caixa = ctk.CTkFrame(self.corpo, fg_color="transparent")
        caixa.pack(expand=True, pady=60)
        self._vazio_widget = caixa

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
