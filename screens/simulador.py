"""
LosPrice - Simulador
=====================

"E se eu vender por R$ 18,90?"

A tela responde a pergunta que o dono realmente faz. Em vez de partir do
custo e chegar no preco, ela parte do preco e mostra para onde o dinheiro
vai - centavo por centavo, com uma barra que torna visivel quanto sobra.

Tres respostas complementares aparecem ao lado:
    piso        - abaixo de quanto e prejuizo garantido
    desconto    - quanto da para tirar em promocao sem sangrar
    custo-alvo  - quanto a ficha pode custar para bater um preco de venda
"""

import customtkinter as ctk

from controllers import precificacao as ctrl
from utils.componentes import Botao, Campo, CampoSelecao, separador
from utils.tema import (
    Cores, Espaco, Fontes, Icone, Raio,
    cor_margem, estilo_card, formatar_moeda, formatar_pct, rotulo_margem,
)

# Cores de cada fatia da barra "para onde vai o dinheiro"
FATIAS = [
    ("custo_produto",    "Custo da ficha", Cores.LARANJA),
    ("valor_comissao",   "Comissao",       "#EA1D2C"),
    ("valor_cartao",     "Cartao",         "#8B5CF6"),
    ("valor_imposto",    "Imposto",        "#3B82F6"),
    ("valor_custo_fixo", "Custo fixo",     "#6B7280"),
    ("custo_fixo_rs",    "Rateio fixo",    "#94A3B8"),
    ("taxa_fixa",        "Taxa por pedido", "#475569"),
]


class TelaSimulador(ctk.CTkFrame):
    def __init__(self, pai):
        super().__init__(pai, fg_color="transparent")

        self.receitas = ctrl.receitas()
        self.canais = ctrl.canais()
        self.receita = None
        self.canal = None
        self.ajustando = False

        padrao = ctrl.parametros()

        if not self.receitas:
            self._estado_vazio()
            return

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=1)

        self._montar_controles(padrao)
        self._montar_resultado()
        self._montar_respostas()

        self._trocar_receita()

    def _estado_vazio(self):
        caixa = ctk.CTkFrame(self, **estilo_card())
        caixa.place(relx=0.5, rely=0.42, anchor="center")

        interno = ctk.CTkFrame(caixa, fg_color="transparent")
        interno.pack(padx=48, pady=40)

        ctk.CTkLabel(interno, text=Icone.GRAFICO, font=Fontes.icone(36),
                     text_color=Cores.LARANJA).pack()
        ctk.CTkLabel(interno, text="Nada para simular ainda", font=Fontes.titulo(),
                     text_color=Cores.TEXTO).pack(pady=(Espaco.MD, 4))
        ctk.CTkLabel(interno,
                     text="Monte uma ficha tecnica em Receitas e volte aqui\n"
                          "para descobrir quanto sobra em cada preco.",
                     font=Fontes.corpo(), text_color=Cores.TEXTO_SECUNDARIO,
                     justify="center").pack()

    # -- controles ---------------------------------------------------------

    def _montar_controles(self, padrao):
        cartao = ctk.CTkFrame(self, **estilo_card())
        cartao.grid(row=0, column=0, columnspan=2, sticky="ew")

        linha = ctk.CTkFrame(cartao, fg_color="transparent")
        linha.pack(fill="x", padx=Espaco.LG, pady=Espaco.MD)

        self.campo_receita = CampoSelecao(
            linha, "Produto", [r["nome"] for r in self.receitas],
            largura=230, ao_mudar=self._trocar_receita)
        self.campo_receita.pack(side="left", padx=(0, Espaco.MD))

        self.campo_canal = CampoSelecao(
            linha, "Canal de venda", [c["nome"] for c in self.canais],
            largura=210, ao_mudar=self._recalcular)
        self.campo_canal.pack(side="left", padx=(0, Espaco.MD))

        self.campo_preco = Campo(linha, "Vender por (R$)", valor="0",
                                 ao_digitar=self._ao_digitar_preco, largura=120)
        self.campo_preco.pack(side="left", padx=(0, Espaco.MD))

        self.campo_imposto = Campo(linha, "Imposto (%)",
                                   valor=f"{padrao['imposto_pct']:g}",
                                   ao_digitar=self._recalcular, largura=95)
        self.campo_imposto.pack(side="left", padx=(0, Espaco.MD))

        self.campo_fixo = Campo(linha, "Custo fixo (%)",
                                valor=f"{padrao['custo_fixo_pct']:g}",
                                ao_digitar=self._recalcular, largura=95)
        self.campo_fixo.pack(side="left")

        # deslizador de preco
        faixa = ctk.CTkFrame(cartao, fg_color="transparent")
        faixa.pack(fill="x", padx=Espaco.LG, pady=(0, Espaco.MD))

        self.rotulo_min = ctk.CTkLabel(faixa, text="", font=Fontes.micro(),
                                       text_color=Cores.TEXTO_APAGADO, width=70)
        self.rotulo_min.pack(side="left")

        self.deslizador = ctk.CTkSlider(
            faixa, from_=0, to=100, command=self._ao_deslizar,
            progress_color=Cores.LARANJA, button_color=Cores.LARANJA,
            button_hover_color=Cores.LARANJA_HOVER, fg_color=Cores.BORDA,
            height=14,
        )
        self.deslizador.pack(side="left", fill="x", expand=True, padx=Espaco.MD)

        self.rotulo_max = ctk.CTkLabel(faixa, text="", font=Fontes.micro(),
                                       text_color=Cores.TEXTO_APAGADO, width=70,
                                       anchor="e")
        self.rotulo_max.pack(side="left")

    # -- resultado ---------------------------------------------------------

    def _montar_resultado(self):
        cartao = ctk.CTkFrame(self, **estilo_card())
        cartao.grid(row=1, column=0, sticky="nsew", pady=(Espaco.MD, 0),
                    padx=(0, Espaco.MD))

        interno = ctk.CTkFrame(cartao, fg_color="transparent")
        interno.pack(fill="both", expand=True, padx=Espaco.LG, pady=Espaco.LG)

        # sobra em destaque
        topo = ctk.CTkFrame(interno, fg_color="transparent")
        topo.pack(fill="x")

        esquerda = ctk.CTkFrame(topo, fg_color="transparent")
        esquerda.pack(side="left")
        ctk.CTkLabel(esquerda, text="SOBRA POR VENDA", font=Fontes.micro(),
                     text_color=Cores.TEXTO_APAGADO).pack(anchor="w")
        self.sobra = ctk.CTkLabel(esquerda, text="--", font=Fontes.display(),
                                  text_color=Cores.LUCRO)
        self.sobra.pack(anchor="w")

        direita = ctk.CTkFrame(topo, fg_color="transparent")
        direita.pack(side="right")
        ctk.CTkLabel(direita, text="MARGEM", font=Fontes.micro(),
                     text_color=Cores.TEXTO_APAGADO).pack(anchor="e")
        self.margem = ctk.CTkLabel(direita, text="--", font=Fontes.titulo(),
                                   text_color=Cores.LUCRO)
        self.margem.pack(anchor="e")
        self.leitura = ctk.CTkLabel(direita, text="", font=Fontes.pequeno(),
                                    text_color=Cores.TEXTO_SECUNDARIO)
        self.leitura.pack(anchor="e")

        # barra proporcional
        ctk.CTkLabel(interno, text="PARA ONDE VAI O DINHEIRO", font=Fontes.micro(),
                     text_color=Cores.TEXTO_APAGADO).pack(anchor="w",
                                                          pady=(Espaco.LG, Espaco.SM))

        self.barra = ctk.CTkFrame(interno, fg_color=Cores.BORDA, height=26,
                                  corner_radius=Raio.PEQUENO)
        self.barra.pack(fill="x")
        self.barra.pack_propagate(False)

        self.legenda = ctk.CTkFrame(interno, fg_color="transparent")
        self.legenda.pack(fill="x", pady=(Espaco.SM, 0))

        separador(interno).pack(fill="x", pady=Espaco.MD)

        # detalhamento
        self.detalhe = ctk.CTkFrame(interno, fg_color="transparent")
        self.detalhe.pack(fill="both", expand=True)

    # -- respostas laterais ------------------------------------------------

    def _montar_respostas(self):
        coluna = ctk.CTkFrame(self, fg_color="transparent")
        coluna.grid(row=1, column=1, sticky="nsew", pady=(Espaco.MD, 0))

        self.cartao_piso = self._cartao_resposta(
            coluna, "PRECO MINIMO", Icone.SETA_BAIXO,
            "Abaixo disso voce paga para trabalhar.")

        self.cartao_desconto = self._cartao_resposta(
            coluna, "DESCONTO MAXIMO", Icone.DINHEIRO,
            "Quanto da para tirar em promocao sem ficar no prejuizo.")

        self.cartao_alvo = self._cartao_resposta(
            coluna, "CUSTO-ALVO", Icone.CHECKLIST,
            "Quanto a ficha pode custar para esse preco render 30% de lucro.")

    def _cartao_resposta(self, pai, titulo, icone, explicacao):
        cartao = ctk.CTkFrame(pai, **estilo_card())
        cartao.pack(fill="x", pady=(0, Espaco.MD))

        interno = ctk.CTkFrame(cartao, fg_color="transparent")
        interno.pack(fill="x", padx=Espaco.LG, pady=Espaco.MD)

        cabeca = ctk.CTkFrame(interno, fg_color="transparent")
        cabeca.pack(fill="x")
        ctk.CTkLabel(cabeca, text=icone, font=Fontes.icone(12),
                     text_color=Cores.TEXTO_APAGADO).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(cabeca, text=titulo, font=Fontes.micro(),
                     text_color=Cores.TEXTO_APAGADO).pack(side="left")

        valor = ctk.CTkLabel(interno, text="--", font=Fontes.titulo(),
                             text_color=Cores.TEXTO)
        valor.pack(anchor="w", pady=(Espaco.SM, 2))

        apoio = ctk.CTkLabel(interno, text=explicacao, font=Fontes.micro(),
                             text_color=Cores.TEXTO_APAGADO, wraplength=250,
                             justify="left", anchor="w")
        apoio.pack(fill="x")

        return {"valor": valor, "apoio": apoio, "padrao": explicacao}

    # -- dados -------------------------------------------------------------

    def _receita_atual(self):
        nome = self.campo_receita.get()
        return next((r for r in self.receitas if r["nome"] == nome), None)

    def _canal_atual(self):
        nome = self.campo_canal.get()
        return next((c for c in self.canais if c["nome"] == nome), None)

    def _numero(self, valor, padrao=0.0):
        limpo = (valor or "").replace("R$", "").strip().replace(" ", "")
        if not limpo:
            return padrao
        if "," in limpo:
            limpo = limpo.replace(".", "").replace(",", ".")
        try:
            return float(limpo)
        except ValueError:
            return None

    def _trocar_receita(self):
        """Ao trocar de produto, parte do preco sugerido com 30% de lucro."""
        receita = self._receita_atual()
        canal = self._canal_atual()
        if not receita or not canal:
            return

        imposto = self._numero(self.campo_imposto.get()) or 0.0
        fixo = self._numero(self.campo_fixo.get()) or 0.0

        try:
            partida = ctrl.sugerido(receita["custo_unitario"], canal, 30.0,
                                    imposto, fixo)
        except Exception:
            partida = receita["custo_unitario"] * 2

        self.ajustando = True
        self.campo_preco.set(f"{partida:.2f}".replace(".", ","))
        self.ajustando = False

        self._recalcular()

    def _ao_digitar_preco(self):
        if self.ajustando:
            return
        self._recalcular(mover_deslizador=True)

    def _ao_deslizar(self, valor):
        if self.ajustando:
            return
        self.ajustando = True
        self.campo_preco.set(f"{float(valor):.2f}".replace(".", ","))
        self.ajustando = False
        self._recalcular(mover_deslizador=False)

    def _recalcular(self, mover_deslizador=True):
        receita = self._receita_atual()
        canal = self._canal_atual()
        if not receita or not canal:
            return

        custo = receita["custo_unitario"]
        preco = self._numero(self.campo_preco.get())
        imposto = self._numero(self.campo_imposto.get()) or 0.0
        fixo = self._numero(self.campo_fixo.get()) or 0.0

        piso = ctrl.piso(custo, canal, imposto, fixo)
        self._ajustar_faixa(piso, mover_deslizador, preco)

        if not preco or preco <= 0:
            self.sobra.configure(text="--", text_color=Cores.NEUTRO)
            self.margem.configure(text="--", text_color=Cores.NEUTRO)
            self.leitura.configure(text="Informe um preco")
            return

        composicao = ctrl.simular(custo, canal, preco, imposto, fixo)
        cor = cor_margem(composicao.margem_pct)

        self.sobra.configure(text=formatar_moeda(composicao.lucro), text_color=cor)
        self.margem.configure(text=formatar_pct(composicao.margem_pct), text_color=cor)
        self.leitura.configure(text=rotulo_margem(composicao.margem_pct),
                               text_color=cor)

        self._desenhar_barra(composicao, preco)
        self._desenhar_detalhe(composicao)
        self._atualizar_respostas(custo, canal, preco, imposto, fixo, piso)

    def _ajustar_faixa(self, piso, mover, preco):
        """A faixa do deslizador acompanha o piso do canal escolhido."""
        minimo = max(piso * 0.6, 0.5)
        maximo = max(piso * 2.6, minimo + 1)

        self.deslizador.configure(from_=minimo, to=maximo)
        self.rotulo_min.configure(text=formatar_moeda(minimo))
        self.rotulo_max.configure(text=formatar_moeda(maximo))

        if mover and preco:
            self.ajustando = True
            self.deslizador.set(min(max(preco, minimo), maximo))
            self.ajustando = False

    # -- desenho -----------------------------------------------------------

    def _desenhar_barra(self, composicao, preco):
        for widget in self.barra.winfo_children():
            widget.destroy()
        for widget in self.legenda.winfo_children():
            widget.destroy()

        partes = []
        for chave, rotulo, cor in FATIAS:
            valor = getattr(composicao, chave, 0) or 0
            if valor > 0.004:
                partes.append((rotulo, valor, cor))

        lucro = composicao.lucro
        if lucro > 0:
            partes.append(("Sobra", lucro, Cores.VERDE_CLARO))

        total = sum(p[1] for p in partes) or preco
        posicao = 0.0

        for indice, (rotulo, valor, cor) in enumerate(partes):
            fracao = valor / total
            fatia = ctk.CTkFrame(self.barra, fg_color=cor, corner_radius=0)
            fatia.place(relx=posicao, rely=0, relwidth=fracao, relheight=1)
            posicao += fracao

            item = ctk.CTkFrame(self.legenda, fg_color="transparent")
            item.pack(side="left", padx=(0, Espaco.MD))
            ctk.CTkFrame(item, fg_color=cor, width=9, height=9,
                         corner_radius=2).pack(side="left", padx=(0, 5), pady=3)
            ctk.CTkLabel(item, text=f"{rotulo} {formatar_pct(fracao * 100, 0)}",
                         font=Fontes.micro(),
                         text_color=Cores.TEXTO_SECUNDARIO).pack(side="left")

        if lucro <= 0:
            aviso = ctk.CTkFrame(self.legenda, fg_color="transparent")
            aviso.pack(side="left")
            ctk.CTkLabel(aviso,
                         text=f"{Icone.ALERTA}  Falta {formatar_moeda(abs(lucro))} "
                              "so para empatar",
                         font=Fontes.micro(),
                         text_color=Cores.PREJUIZO).pack(side="left")

    def _desenhar_detalhe(self, composicao):
        for widget in self.detalhe.winfo_children():
            widget.destroy()

        def linha(rotulo, valor, cor=None, forte=False, sinal="-"):
            caixa = ctk.CTkFrame(self.detalhe, fg_color="transparent")
            caixa.pack(fill="x", pady=1)
            ctk.CTkLabel(caixa, text=rotulo,
                         font=Fontes.corpo_forte() if forte else Fontes.corpo(),
                         text_color=cor or (Cores.TEXTO if forte
                                            else Cores.TEXTO_SECUNDARIO),
                         anchor="w").pack(side="left")
            ctk.CTkLabel(caixa, text=f"{sinal} {formatar_moeda(valor)}".strip(),
                         font=Fontes.numero_forte() if forte else Fontes.numero(),
                         text_color=cor or (Cores.TEXTO if forte
                                            else Cores.TEXTO_SECUNDARIO),
                         anchor="e").pack(side="right")

        linha("Preco de venda", composicao.preco, Cores.TEXTO, forte=True, sinal="")

        for chave, rotulo, _cor in FATIAS:
            valor = getattr(composicao, chave, 0) or 0
            if valor > 0.004:
                linha(rotulo, valor)

        separador(self.detalhe).pack(fill="x", pady=Espaco.SM)
        linha("Sobra", composicao.lucro, cor_margem(composicao.margem_pct),
              forte=True, sinal="=")

    def _atualizar_respostas(self, custo, canal, preco, imposto, fixo, piso):
        # preco minimo
        self.cartao_piso["valor"].configure(text=formatar_moeda(piso))
        if preco < piso:
            self.cartao_piso["apoio"].configure(
                text=f"Voce esta {formatar_moeda(piso - preco)} abaixo do piso.",
                text_color=Cores.PREJUIZO)
        else:
            self.cartao_piso["apoio"].configure(
                text=f"Voce esta {formatar_moeda(preco - piso)} acima do piso.",
                text_color=Cores.TEXTO_APAGADO)

        # desconto maximo
        desconto = ctrl.desconto_possivel(custo, canal, preco, imposto, fixo)
        self.cartao_desconto["valor"].configure(
            text=formatar_pct(desconto),
            text_color=Cores.LUCRO if desconto > 0 else Cores.PREJUIZO)
        if desconto > 0:
            self.cartao_desconto["apoio"].configure(
                text=f"Da para vender ate {formatar_moeda(preco * (1 - desconto / 100))} "
                     "sem perder dinheiro.",
                text_color=Cores.TEXTO_APAGADO)
        else:
            self.cartao_desconto["apoio"].configure(
                text="Nao ha espaco para desconto neste preco.",
                text_color=Cores.PREJUIZO)

        # custo-alvo
        alvo = ctrl.custo_alvo(preco, canal, 30.0, imposto, fixo)
        if alvo:
            self.cartao_alvo["valor"].configure(text=formatar_moeda(alvo),
                                                text_color=Cores.TEXTO)
            diferenca = custo - alvo
            if diferenca > 0.01:
                self.cartao_alvo["apoio"].configure(
                    text=f"Sua ficha custa {formatar_moeda(custo)}. "
                         f"Precisa cortar {formatar_moeda(diferenca)} para "
                         "chegar a 30% de lucro.",
                    text_color=Cores.ATENCAO)
            elif diferenca > -0.01:
                # o preco atual entrega exatamente os 30%
                self.cartao_alvo["apoio"].configure(
                    text=f"Sua ficha custa {formatar_moeda(custo)}: este preco "
                         "entrega exatamente 30% de lucro.",
                    text_color=Cores.LUCRO)
            else:
                self.cartao_alvo["apoio"].configure(
                    text=f"Sua ficha custa {formatar_moeda(custo)} e ja cabe "
                         f"com folga de {formatar_moeda(-diferenca)}.",
                    text_color=Cores.LUCRO)
        else:
            self.cartao_alvo["valor"].configure(text="Impossivel",
                                                text_color=Cores.PREJUIZO)
            self.cartao_alvo["apoio"].configure(
                text="As taxas deste canal nao deixam espaco para 30% de lucro "
                     "neste preco.",
                text_color=Cores.PREJUIZO)
