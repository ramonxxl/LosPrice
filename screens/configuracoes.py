"""
LosPrice - Tela de Configuracoes
=================================

Quatro abas:
    Empresa      dados, regime tributario e padroes de precificacao
    Canais       taxa de cada plataforma - o que muda todo o resultado
    Custos fixos rateio real, a alternativa honesta ao "chuta 10%"
    Backup       copia e restauracao do banco
"""

import os
from datetime import datetime

import customtkinter as ctk

from controllers import configuracoes as ctrl
from utils.componentes import (
    Botao, BotaoIcone, Campo, CampoSelecao, confirmar, notificar, separador,
)
from utils.tema import (
    APP_VERSAO, Cores, Espaco, Fontes, Icone, Raio,
    estilo_card, formatar_moeda, formatar_pct,
)


class TelaConfiguracoes(ctk.CTkFrame):
    def __init__(self, pai):
        super().__init__(pai, fg_color="transparent")

        self.abas = ctk.CTkTabview(
            self, fg_color=Cores.CARD, corner_radius=Raio.GRANDE,
            border_color=Cores.BORDA, border_width=1,
            segmented_button_fg_color=Cores.SUPERFICIE,
            segmented_button_selected_color=Cores.LARANJA,
            segmented_button_selected_hover_color=Cores.LARANJA_HOVER,
            segmented_button_unselected_color=Cores.SUPERFICIE,
            segmented_button_unselected_hover_color=Cores.CARD_HOVER,
            text_color=Cores.TEXTO, anchor="w",
        )
        self.abas.pack(fill="both", expand=True)

        for nome in ("Empresa", "Canais de venda", "Custos fixos", "Backup"):
            self.abas.add(nome)

        self._montar_empresa(self.abas.tab("Empresa"))
        self._montar_canais(self.abas.tab("Canais de venda"))
        self._montar_custos(self.abas.tab("Custos fixos"))
        self._montar_backup(self.abas.tab("Backup"))

    # -- helpers -----------------------------------------------------------

    @staticmethod
    def _titulo(pai, texto, apoio=None):
        caixa = ctk.CTkFrame(pai, fg_color="transparent")
        caixa.pack(fill="x", pady=(0, Espaco.MD))
        ctk.CTkLabel(caixa, text=texto, font=Fontes.subtitulo(),
                     text_color=Cores.TEXTO, anchor="w").pack(anchor="w")
        if apoio:
            ctk.CTkLabel(caixa, text=apoio, font=Fontes.pequeno(),
                         text_color=Cores.TEXTO_SECUNDARIO,
                         anchor="w", justify="left").pack(anchor="w")

    # ------------------------------------------------------------------
    # Aba Empresa
    # ------------------------------------------------------------------

    def _montar_empresa(self, aba):
        area = ctk.CTkScrollableFrame(aba, fg_color="transparent")
        area.pack(fill="both", expand=True)

        dados = ctrl.empresa()

        self._titulo(area, "Estabelecimento",
                     "Aparece nos relatorios e fichas tecnicas impressas.")

        linha = ctk.CTkFrame(area, fg_color="transparent")
        linha.pack(fill="x")

        self.campo_empresa = Campo(linha, "Nome do estabelecimento",
                                   valor=dados["nome"], largura=320,
                                   ajuda="Ex: Los Pastelles")
        self.campo_empresa.pack(side="left", padx=(0, Espaco.MD))

        self.campo_cnpj = Campo(linha, "CNPJ", valor=dados["cnpj"], largura=200)
        self.campo_cnpj.pack(side="left")

        separador(area).pack(fill="x", pady=Espaco.LG)

        self._titulo(area, "Regime tributario",
                     "A aliquota entra automatica ao escolher o regime. "
                     "Confirme com seu contador antes de usar.")

        linha = ctk.CTkFrame(area, fg_color="transparent")
        linha.pack(fill="x")

        self.campo_regime = CampoSelecao(
            linha, "Regime", list(ctrl.REGIMES.keys()), valor=dados["regime"],
            largura=250, ao_mudar=self._ao_trocar_regime)
        self.campo_regime.pack(side="left", padx=(0, Espaco.MD))

        self.campo_imposto = Campo(linha, "Aliquota (%)",
                                   valor=f"{dados['imposto_pct']:g}", largura=120)
        self.campo_imposto.pack(side="left")

        separador(area).pack(fill="x", pady=Espaco.LG)

        self._titulo(area, "Padroes de precificacao",
                     "Valores que a tela de Precificacao carrega ao abrir.")

        linha = ctk.CTkFrame(area, fg_color="transparent")
        linha.pack(fill="x")

        self.campo_margem = Campo(linha, "Lucro desejado (%)",
                                  valor=f"{dados['margem_padrao_pct']:g}", largura=140)
        self.campo_margem.pack(side="left", padx=(0, Espaco.MD))

        self.campo_cartao = Campo(linha, "Taxa media de cartao (%)",
                                  valor=f"{dados['cartao_pct_padrao']:g}", largura=160)
        self.campo_cartao.pack(side="left", padx=(0, Espaco.MD))

        self.campo_fixo = Campo(linha, "Custo fixo (%)",
                                valor=f"{dados['custo_fixo_pct']:g}", largura=130,
                                ajuda="Calculavel na aba Custos fixos")
        self.campo_fixo.pack(side="left")

        opcoes = ctk.CTkFrame(area, fg_color="transparent")
        opcoes.pack(fill="x", pady=(Espaco.MD, 0))

        self.var_arredondar = ctk.BooleanVar(value=dados["arredondar"])
        self.var_backup = ctk.BooleanVar(value=dados["backup_automatico"])

        for texto, variavel in (
            ("Arredondar precos sugeridos para terminar em ,90", self.var_arredondar),
            ("Gerar backup do banco toda vez que o sistema abrir", self.var_backup),
        ):
            ctk.CTkCheckBox(opcoes, text=texto, variable=variavel,
                            font=Fontes.corpo(), checkbox_width=18, checkbox_height=18,
                            fg_color=Cores.LARANJA, hover_color=Cores.LARANJA_HOVER,
                            border_color=Cores.BORDA,
                            text_color=Cores.TEXTO_SECUNDARIO).pack(anchor="w", pady=3)

        separador(area).pack(fill="x", pady=Espaco.LG)

        rodape = ctk.CTkFrame(area, fg_color="transparent")
        rodape.pack(fill="x")

        self.erro_empresa = ctk.CTkLabel(rodape, text="", font=Fontes.pequeno(),
                                         text_color=Cores.PREJUIZO, anchor="w")
        self.erro_empresa.pack(side="left", fill="x", expand=True)

        Botao(rodape, "Salvar configuracoes", icone=Icone.SALVAR,
              variante="sucesso", width=210,
              command=self._salvar_empresa).pack(side="right")

    def _ao_trocar_regime(self):
        regime = self.campo_regime.get()
        if regime != "Personalizado":
            self.campo_imposto.set(f"{ctrl.aliquota_do_regime(regime):g}")

    def _salvar_empresa(self):
        self.erro_empresa.configure(text="")
        try:
            ctrl.salvar_empresa({
                "nome": self.campo_empresa.get(),
                "cnpj": self.campo_cnpj.get(),
                "regime": self.campo_regime.get(),
                "imposto_pct": self.campo_imposto.get(),
                "margem_padrao_pct": self.campo_margem.get(),
                "cartao_pct_padrao": self.campo_cartao.get(),
                "custo_fixo_pct": self.campo_fixo.get(),
                "arredondar": self.var_arredondar.get(),
                "backup_automatico": self.var_backup.get(),
            })
        except ctrl.ErroValidacao as erro:
            self.erro_empresa.configure(text=str(erro))
            return

        notificar(self, "Configuracoes salvas.", "sucesso")

    # ------------------------------------------------------------------
    # Aba Canais
    # ------------------------------------------------------------------

    def _montar_canais(self, aba):
        topo = ctk.CTkFrame(aba, fg_color="transparent")
        topo.pack(fill="x", pady=(0, Espaco.MD))

        texto = ctk.CTkFrame(topo, fg_color="transparent")
        texto.pack(side="left")
        ctk.CTkLabel(texto, text="Canais de venda", font=Fontes.subtitulo(),
                     text_color=Cores.TEXTO).pack(anchor="w")
        ctk.CTkLabel(texto,
                     text="Comissao e cartao incidem sobre o preco de venda. "
                          "Confira com seu contrato: as taxas mudam.",
                     font=Fontes.pequeno(),
                     text_color=Cores.TEXTO_SECUNDARIO).pack(anchor="w")

        Botao(topo, "Novo canal", icone=Icone.ADICIONAR, width=160,
              command=self._novo_canal).pack(side="right")

        self.lista_canais = ctk.CTkScrollableFrame(aba, fg_color="transparent")
        self.lista_canais.pack(fill="both", expand=True)

        self._recarregar_canais()

    def _recarregar_canais(self):
        for widget in self.lista_canais.winfo_children():
            widget.destroy()

        for canal in ctrl.canais():
            self._linha_canal(canal)

    def _linha_canal(self, canal):
        cartao = ctk.CTkFrame(self.lista_canais, **estilo_card())
        cartao.pack(fill="x", pady=3)

        interno = ctk.CTkFrame(cartao, fg_color="transparent")
        interno.pack(fill="x", padx=Espaco.MD, pady=Espaco.MD)

        ativo = bool(canal["ativo"])

        # identificacao
        # a altura e obrigatoria: com pack_propagate(False) e sem height,
        # o CTkFrame trava nos 200px padrao e a linha fica gigante
        esquerda = ctk.CTkFrame(interno, fg_color="transparent",
                                width=250, height=40)
        esquerda.pack(side="left", fill="y")
        esquerda.pack_propagate(False)

        cabeca = ctk.CTkFrame(esquerda, fg_color="transparent")
        cabeca.pack(anchor="w")
        ctk.CTkFrame(cabeca, fg_color=canal["cor"] if ativo else Cores.BORDA,
                     width=4, height=15,
                     corner_radius=Raio.PILULA).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(cabeca, text=canal["nome"], font=Fontes.corpo_forte(),
                     text_color=Cores.TEXTO if ativo else Cores.TEXTO_APAGADO).pack(
            side="left")

        total = canal["comissao_pct"] + canal["cartao_pct"]
        ctk.CTkLabel(esquerda,
                     text=f"desconta {formatar_pct(total)} da venda"
                          + (f" + {formatar_moeda(canal['taxa_fixa'])}"
                             if canal["taxa_fixa"] else ""),
                     font=Fontes.micro(),
                     text_color=Cores.TEXTO_APAGADO).pack(anchor="w", padx=(12, 0))

        # acoes
        BotaoIcone(interno, Icone.EXCLUIR,
                   comando=lambda c=canal: self._excluir_canal(c),
                   cor=Cores.PREJUIZO, dica="Excluir canal").pack(side="right")

        BotaoIcone(interno, Icone.EDITAR,
                   comando=lambda c=canal: self._editar_canal(c),
                   dica="Editar taxas").pack(side="right", padx=(0, Espaco.SM))

        variavel = ctk.BooleanVar(value=ativo)
        ctk.CTkSwitch(interno, text="", variable=variavel, width=42,
                      progress_color=Cores.VERDE, button_color=Cores.TEXTO_SOBRE_COR,
                      fg_color=Cores.BORDA,
                      command=lambda c=canal, v=variavel: self._alternar_canal(c, v)
                      ).pack(side="right", padx=(0, Espaco.MD))

        # numeros
        for rotulo, valor in (("Comissao", formatar_pct(canal["comissao_pct"])),
                              ("Cartao", formatar_pct(canal["cartao_pct"])),
                              ("Taxa fixa", formatar_moeda(canal["taxa_fixa"]))):
            caixa = ctk.CTkFrame(interno, fg_color="transparent",
                                 width=100, height=40)
            caixa.pack(side="left", fill="y")
            caixa.pack_propagate(False)
            ctk.CTkLabel(caixa, text=rotulo, font=Fontes.micro(),
                         text_color=Cores.TEXTO_APAGADO, anchor="w").pack(fill="x")
            ctk.CTkLabel(caixa, text=valor, font=Fontes.numero_forte(),
                         text_color=Cores.TEXTO if ativo else Cores.TEXTO_APAGADO,
                         anchor="w").pack(fill="x")

    def _novo_canal(self):
        DialogoCanal(self, ao_salvar=self._recarregar_canais)

    def _editar_canal(self, canal):
        DialogoCanal(self, canal=canal, ao_salvar=self._recarregar_canais)

    def _alternar_canal(self, canal, variavel):
        ctrl.alternar_canal(canal["id"], variavel.get())
        self._recarregar_canais()

    def _excluir_canal(self, canal):
        if not confirmar(self, "Excluir canal",
                         f"Remover o canal '{canal['nome']}'?\n\n"
                         "Se ele ja tiver precos gravados, sera apenas desativado.",
                         "Excluir", perigo=True):
            return

        resultado = ctrl.excluir_canal(canal["id"])
        self._recarregar_canais()
        notificar(self,
                  f"Canal {'excluido' if resultado['apagado'] else 'desativado'}.",
                  "sucesso" if resultado["apagado"] else "aviso")

    # ------------------------------------------------------------------
    # Aba Custos fixos
    # ------------------------------------------------------------------

    def _montar_custos(self, aba):
        aba.grid_columnconfigure(0, weight=3)
        aba.grid_columnconfigure(1, weight=2)
        aba.grid_rowconfigure(1, weight=1)

        topo = ctk.CTkFrame(aba, fg_color="transparent")
        topo.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, Espaco.MD))

        texto = ctk.CTkFrame(topo, fg_color="transparent")
        texto.pack(side="left")
        ctk.CTkLabel(texto, text="Custos fixos mensais", font=Fontes.subtitulo(),
                     text_color=Cores.TEXTO).pack(anchor="w")
        ctk.CTkLabel(texto,
                     text="Aluguel, energia, gas, salarios. Some tudo aqui e o "
                          "sistema calcula o rateio real por produto.",
                     font=Fontes.pequeno(),
                     text_color=Cores.TEXTO_SECUNDARIO).pack(anchor="w")

        Botao(topo, "Novo custo", icone=Icone.ADICIONAR, width=150,
              command=self._novo_custo).pack(side="right")

        self.lista_custos = ctk.CTkScrollableFrame(aba, fg_color="transparent")
        self.lista_custos.grid(row=1, column=0, sticky="nsew", padx=(0, Espaco.MD))

        # painel do rateio
        painel = ctk.CTkFrame(aba, fg_color=Cores.SUPERFICIE,
                              corner_radius=Raio.GRANDE,
                              border_color=Cores.BORDA, border_width=1)
        painel.grid(row=1, column=1, sticky="nsew")

        interno = ctk.CTkFrame(painel, fg_color="transparent")
        interno.pack(fill="both", expand=True, padx=Espaco.LG, pady=Espaco.MD)

        ctk.CTkLabel(interno, text="TOTAL POR MES", font=Fontes.micro(),
                     text_color=Cores.TEXTO_APAGADO).pack(anchor="w")
        self.total_custos = ctk.CTkLabel(interno, text="R$ 0,00",
                                         font=Fontes.display(),
                                         text_color=Cores.LARANJA)
        self.total_custos.pack(anchor="w")

        separador(interno).pack(fill="x", pady=Espaco.SM)

        ctk.CTkLabel(interno, text="CALCULAR O RATEIO EM VEZ DE CHUTAR",
                     font=Fontes.micro(),
                     text_color=Cores.TEXTO_APAGADO).pack(anchor="w",
                                                          pady=(0, Espaco.XS))

        self.campo_unidades = Campo(interno, "Unidades vendidas por mes",
                                    ao_digitar=self._calcular_rateio)
        self.campo_unidades.pack(fill="x")

        self.campo_faturamento = Campo(interno, "Faturamento mensal (R$)",
                                       ao_digitar=self._calcular_rateio)
        self.campo_faturamento.pack(fill="x")

        separador(interno).pack(fill="x", pady=Espaco.SM)

        self.resultado_rateio = ctk.CTkFrame(interno, fg_color="transparent")
        self.resultado_rateio.pack(fill="x")

        # logo abaixo do resultado, nao no rodape do painel: com side="bottom"
        # o botao caia fora quando o conteudo crescia
        self.botao_aplicar = Botao(interno, "Usar este percentual",
                                   icone=Icone.OK, variante="secundario",
                                   command=self._aplicar_rateio)
        self.botao_aplicar.pack(fill="x", pady=(Espaco.SM, 0))
        self.percentual_calculado = None

        self._recarregar_custos()

    def _recarregar_custos(self):
        for widget in self.lista_custos.winfo_children():
            widget.destroy()

        custos = ctrl.custos_fixos()

        if not custos:
            caixa = ctk.CTkFrame(self.lista_custos, fg_color="transparent")
            caixa.pack(expand=True, pady=50)
            ctk.CTkLabel(caixa, text=Icone.DINHEIRO, font=Fontes.icone(28),
                         text_color=Cores.TEXTO_APAGADO).pack()
            ctk.CTkLabel(caixa, text="Nenhum custo fixo lancado",
                         font=Fontes.subtitulo(),
                         text_color=Cores.TEXTO_SECUNDARIO).pack(pady=(Espaco.SM, 2))
            ctk.CTkLabel(caixa,
                         text="Sem isso, o custo fixo vira chute.",
                         font=Fontes.pequeno(),
                         text_color=Cores.TEXTO_APAGADO).pack()
        else:
            total = ctrl.total_custo_fixo()
            for custo in custos:
                self._linha_custo(custo, total)

        self.total_custos.configure(text=formatar_moeda(ctrl.total_custo_fixo()))
        self._calcular_rateio()

    def _linha_custo(self, custo, total):
        cartao = ctk.CTkFrame(self.lista_custos, **estilo_card())
        cartao.pack(fill="x", pady=3)

        interno = ctk.CTkFrame(cartao, fg_color="transparent")
        interno.pack(fill="x", padx=Espaco.MD, pady=Espaco.MD)

        esquerda = ctk.CTkFrame(interno, fg_color="transparent")
        esquerda.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(esquerda, text=custo["descricao"], font=Fontes.corpo_forte(),
                     text_color=Cores.TEXTO, anchor="w").pack(anchor="w")
        ctk.CTkLabel(esquerda, text=custo.get("categoria") or "Sem categoria",
                     font=Fontes.micro(),
                     text_color=Cores.TEXTO_APAGADO, anchor="w").pack(anchor="w")

        BotaoIcone(interno, Icone.EXCLUIR,
                   comando=lambda c=custo: self._excluir_custo(c),
                   cor=Cores.PREJUIZO, dica="Excluir").pack(side="right")
        BotaoIcone(interno, Icone.EDITAR,
                   comando=lambda c=custo: self._editar_custo(c),
                   dica="Editar").pack(side="right", padx=(0, Espaco.SM))

        direita = ctk.CTkFrame(interno, fg_color="transparent")
        direita.pack(side="right", padx=(0, Espaco.MD))
        ctk.CTkLabel(direita, text=formatar_moeda(custo["valor_mensal"]),
                     font=Fontes.numero_forte(),
                     text_color=Cores.TEXTO, anchor="e").pack(anchor="e")
        participacao = (custo["valor_mensal"] / total * 100) if total else 0
        ctk.CTkLabel(direita, text=formatar_pct(participacao), font=Fontes.micro(),
                     text_color=Cores.TEXTO_APAGADO, anchor="e").pack(anchor="e")

    def _calcular_rateio(self):
        for widget in self.resultado_rateio.winfo_children():
            widget.destroy()
        self.percentual_calculado = None

        total = ctrl.total_custo_fixo()
        if not total:
            self.botao_aplicar.configure(state="disabled")
            return

        try:
            por_unidade = ctrl.rateio(self.campo_unidades.get())
            percentual = ctrl.rateio_percentual(self.campo_faturamento.get())
        except Exception:
            self.botao_aplicar.configure(state="disabled")
            return

        if por_unidade["por_unidade"]:
            self._resultado("Por unidade vendida",
                            formatar_moeda(por_unidade["por_unidade"]), Cores.TEXTO)

        if percentual is not None:
            cor = Cores.PREJUIZO if percentual > 40 else Cores.LARANJA
            self._resultado("Sobre o faturamento", formatar_pct(percentual), cor)
            self.percentual_calculado = percentual
            self.botao_aplicar.configure(state="normal")

            if percentual > 40:
                ctk.CTkLabel(
                    self.resultado_rateio,
                    text="Custo fixo acima de 40% do faturamento e sinal de alerta.",
                    font=Fontes.micro(), text_color=Cores.PREJUIZO,
                    wraplength=250, justify="left").pack(anchor="w",
                                                         pady=(Espaco.SM, 0))
        else:
            self.botao_aplicar.configure(state="disabled")

    def _resultado(self, rotulo, valor, cor):
        linha = ctk.CTkFrame(self.resultado_rateio, fg_color="transparent")
        linha.pack(fill="x", pady=2)
        ctk.CTkLabel(linha, text=rotulo, font=Fontes.pequeno(),
                     text_color=Cores.TEXTO_SECUNDARIO).pack(side="left")
        ctk.CTkLabel(linha, text=valor, font=Fontes.numero_forte(),
                     text_color=cor).pack(side="right")

    def _aplicar_rateio(self):
        if self.percentual_calculado is None:
            return
        self.campo_fixo.set(f"{self.percentual_calculado:.1f}".replace(".", ","))
        self._salvar_empresa()
        self.abas.set("Empresa")
        notificar(self, f"Custo fixo de {formatar_pct(self.percentual_calculado)} "
                        "aplicado nos padroes.", "sucesso")

    def _novo_custo(self):
        DialogoCusto(self, ao_salvar=self._recarregar_custos)

    def _editar_custo(self, custo):
        DialogoCusto(self, custo=custo, ao_salvar=self._recarregar_custos)

    def _excluir_custo(self, custo):
        if not confirmar(self, "Excluir custo",
                         f"Remover '{custo['descricao']}' dos custos fixos?",
                         "Excluir", perigo=True):
            return
        ctrl.excluir_custo_fixo(custo["id"])
        self._recarregar_custos()
        notificar(self, "Custo removido.", "sucesso")

    # ------------------------------------------------------------------
    # Aba Backup
    # ------------------------------------------------------------------

    def _montar_backup(self, aba):
        aba.grid_columnconfigure(0, weight=3)
        aba.grid_columnconfigure(1, weight=2)
        aba.grid_rowconfigure(1, weight=1)

        topo = ctk.CTkFrame(aba, fg_color="transparent")
        topo.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, Espaco.MD))

        texto = ctk.CTkFrame(topo, fg_color="transparent")
        texto.pack(side="left")
        ctk.CTkLabel(texto, text="Backup do banco de dados",
                     font=Fontes.subtitulo(), text_color=Cores.TEXTO).pack(anchor="w")
        ctk.CTkLabel(texto,
                     text="Toda a sua informacao vive em um arquivo so. "
                          "Guarde copias fora do computador.",
                     font=Fontes.pequeno(),
                     text_color=Cores.TEXTO_SECUNDARIO).pack(anchor="w")

        Botao(topo, "Gerar backup agora", icone=Icone.SALVAR, width=195,
              command=self._gerar_backup).pack(side="right")

        self.lista_backups = ctk.CTkScrollableFrame(aba, fg_color="transparent")
        self.lista_backups.grid(row=1, column=0, sticky="nsew", padx=(0, Espaco.MD))

        painel = ctk.CTkFrame(aba, fg_color=Cores.SUPERFICIE,
                              corner_radius=Raio.GRANDE,
                              border_color=Cores.BORDA, border_width=1)
        painel.grid(row=1, column=1, sticky="nsew")

        interno = ctk.CTkFrame(painel, fg_color="transparent")
        interno.pack(fill="both", expand=True, padx=Espaco.LG, pady=Espaco.LG)

        ctk.CTkLabel(interno, text="O QUE ESTA GUARDADO", font=Fontes.micro(),
                     text_color=Cores.TEXTO_APAGADO).pack(anchor="w",
                                                          pady=(0, Espaco.SM))

        for rotulo, quantidade in ctrl.resumo_banco():
            linha = ctk.CTkFrame(interno, fg_color="transparent")
            linha.pack(fill="x", pady=2)
            ctk.CTkLabel(linha, text=rotulo, font=Fontes.pequeno(),
                         text_color=Cores.TEXTO_SECUNDARIO).pack(side="left")
            ctk.CTkLabel(linha, text=str(quantidade), font=Fontes.numero_forte(),
                         text_color=Cores.TEXTO).pack(side="right")

        separador(interno).pack(fill="x", pady=Espaco.MD)

        ctk.CTkLabel(interno, text=f"LosPrice v{APP_VERSAO}", font=Fontes.pequeno(),
                     text_color=Cores.TEXTO_SECUNDARIO).pack(anchor="w")
        ctk.CTkLabel(interno, text="Los Software", font=Fontes.micro(),
                     text_color=Cores.TEXTO_APAGADO).pack(anchor="w")

        self._recarregar_backups()

    def _recarregar_backups(self):
        for widget in self.lista_backups.winfo_children():
            widget.destroy()

        backups = ctrl.listar_backups()

        if not backups:
            caixa = ctk.CTkFrame(self.lista_backups, fg_color="transparent")
            caixa.pack(expand=True, pady=50)
            ctk.CTkLabel(caixa, text=Icone.SALVAR, font=Fontes.icone(28),
                         text_color=Cores.TEXTO_APAGADO).pack()
            ctk.CTkLabel(caixa, text="Nenhum backup ainda", font=Fontes.subtitulo(),
                         text_color=Cores.TEXTO_SECUNDARIO).pack(pady=(Espaco.SM, 2))
            ctk.CTkLabel(caixa, text="Gere o primeiro no botao acima.",
                         font=Fontes.pequeno(),
                         text_color=Cores.TEXTO_APAGADO).pack()
            return

        for backup in backups:
            self._linha_backup(backup)

    def _linha_backup(self, backup):
        cartao = ctk.CTkFrame(self.lista_backups, **estilo_card())
        cartao.pack(fill="x", pady=3)

        interno = ctk.CTkFrame(cartao, fg_color="transparent")
        interno.pack(fill="x", padx=Espaco.MD, pady=Espaco.MD)

        esquerda = ctk.CTkFrame(interno, fg_color="transparent")
        esquerda.pack(side="left")

        data = datetime.fromtimestamp(backup["data"])
        ctk.CTkLabel(esquerda, text=data.strftime("%d/%m/%Y as %H:%M"),
                     font=Fontes.corpo_forte(), text_color=Cores.TEXTO,
                     anchor="w").pack(anchor="w")
        ctk.CTkLabel(esquerda, text=f"{backup['tamanho'] / 1024:.0f} KB",
                     font=Fontes.micro(), text_color=Cores.TEXTO_APAGADO,
                     anchor="w").pack(anchor="w")

        Botao(interno, "Restaurar", variante="secundario", width=120, height=32,
              command=lambda b=backup: self._restaurar(b)).pack(side="right")

    def _gerar_backup(self):
        try:
            caminho = ctrl.gerar_backup()
        except ctrl.ErroValidacao as erro:
            notificar(self, str(erro), "erro")
            return

        self._recarregar_backups()
        notificar(self, f"Backup criado: {os.path.basename(caminho)}", "sucesso")

    def _restaurar(self, backup):
        data = datetime.fromtimestamp(backup["data"]).strftime("%d/%m/%Y as %H:%M")
        if not confirmar(
            self, "Restaurar backup",
            f"Substituir os dados atuais pelo backup de {data}?\n\n"
            "O estado de agora sera salvo como backup antes da troca.\n"
            "Feche e abra o LosPrice depois para ver os dados restaurados.",
            "Restaurar", perigo=True,
        ):
            return

        try:
            ctrl.restaurar(backup["caminho"])
        except Exception as erro:
            notificar(self, f"Falha ao restaurar: {erro}", "erro")
            return

        self._recarregar_backups()
        notificar(self, "Backup restaurado. Reinicie o LosPrice.", "aviso")


# ---------------------------------------------------------------------------
# Dialogos auxiliares
# ---------------------------------------------------------------------------


class _DialogoBase(ctk.CTkToplevel):
    LARGURA, ALTURA = 520, 380

    def __init__(self, pai, titulo, subtitulo):
        super().__init__(pai)
        self.pai = pai

        self.title("")
        self.overrideredirect(True)
        self.configure(fg_color=Cores.FUNDO)
        self.transient(pai.winfo_toplevel())
        self.grab_set()

        self.moldura = ctk.CTkFrame(self, fg_color=Cores.CARD,
                                    corner_radius=Raio.GRANDE,
                                    border_color=Cores.BORDA, border_width=1)
        self.moldura.pack(fill="both", expand=True)

        topo = ctk.CTkFrame(self.moldura, fg_color="transparent")
        topo.pack(fill="x", padx=Espaco.XL, pady=(Espaco.LG, 0))

        texto = ctk.CTkFrame(topo, fg_color="transparent")
        texto.pack(side="left")
        ctk.CTkLabel(texto, text=titulo, font=Fontes.titulo(),
                     text_color=Cores.TEXTO).pack(anchor="w")
        ctk.CTkLabel(texto, text=subtitulo, font=Fontes.pequeno(),
                     text_color=Cores.TEXTO_SECUNDARIO).pack(anchor="w")

        ctk.CTkButton(topo, text=Icone.FECHAR, width=32, height=32,
                      font=Fontes.icone(13), fg_color="transparent",
                      hover_color=Cores.CARD_HOVER, text_color=Cores.TEXTO_SECUNDARIO,
                      command=self.destroy).pack(side="right")

        separador(self.moldura).pack(fill="x", padx=Espaco.XL, pady=(Espaco.MD, 0))

        self.corpo = ctk.CTkFrame(self.moldura, fg_color="transparent")
        self.corpo.pack(fill="both", expand=True, padx=Espaco.XL, pady=Espaco.LG)

    def montar_rodape(self, texto_ok, comando):
        separador(self.moldura).pack(fill="x", padx=Espaco.XL)
        rodape = ctk.CTkFrame(self.moldura, fg_color="transparent")
        rodape.pack(fill="x", padx=Espaco.XL, pady=Espaco.LG)

        self.erro = ctk.CTkLabel(rodape, text="", font=Fontes.pequeno(),
                                 text_color=Cores.PREJUIZO, anchor="w")
        self.erro.pack(side="left", fill="x", expand=True)

        Botao(rodape, "Cancelar", variante="secundario", width=110,
              command=self.destroy).pack(side="right", padx=(Espaco.SM, 0))
        Botao(rodape, texto_ok, icone=Icone.SALVAR, variante="sucesso",
              width=140, command=comando).pack(side="right")

        self.bind("<Escape>", lambda _: self.destroy())
        self.bind("<Return>", lambda _: comando())

        self.geometry(f"{self.LARGURA}x{self.ALTURA}")
        self.update_idletasks()
        altura = min(max(self.ALTURA, self.winfo_reqheight()),
                     int(self.winfo_screenheight() * 0.92))
        janela = self.pai.winfo_toplevel()
        x = janela.winfo_rootx() + (janela.winfo_width() - self.LARGURA) // 2
        y = janela.winfo_rooty() + (janela.winfo_height() - altura) // 2
        self.geometry(f"{self.LARGURA}x{altura}+{max(x, 0)}+{max(y, 0)}")
        self.focus_force()


class DialogoCanal(_DialogoBase):
    def __init__(self, pai, canal=None, ao_salvar=None):
        self.canal = canal
        self.ao_salvar = ao_salvar
        self.editando = canal is not None

        super().__init__(
            pai,
            "Editar canal" if self.editando else "Novo canal",
            "As taxas incidem sobre o preco de venda.",
        )

        self.campo_nome = Campo(self.corpo, "Nome do canal", obrigatorio=True,
                                ajuda="Ex: iFood, Rappi, Balcao")
        self.campo_nome.pack(fill="x")

        linha = ctk.CTkFrame(self.corpo, fg_color="transparent")
        linha.pack(fill="x", pady=(Espaco.SM, 0))

        self.campo_comissao = Campo(linha, "Comissao (%)", valor="0", largura=130,
                                    ajuda="Taxa da plataforma")
        self.campo_comissao.pack(side="left", padx=(0, Espaco.SM))

        self.campo_cartao = Campo(linha, "Cartao (%)", valor="0", largura=130,
                                  ajuda="Maquininha")
        self.campo_cartao.pack(side="left", padx=(0, Espaco.SM))

        self.campo_fixa = Campo(linha, "Taxa fixa (R$)", valor="0", largura=130,
                                ajuda="Por pedido")
        self.campo_fixa.pack(side="left")

        if self.editando:
            self.campo_nome.set(canal["nome"])
            self.campo_comissao.set(f"{canal['comissao_pct']:g}")
            self.campo_cartao.set(f"{canal['cartao_pct']:g}")
            self.campo_fixa.set(f"{canal['taxa_fixa']:g}")

        self.montar_rodape("Salvar" if self.editando else "Criar", self._salvar)
        self.campo_nome.focar()

    def _salvar(self):
        self.erro.configure(text="")
        dados = {
            "nome": self.campo_nome.get(),
            "comissao_pct": self.campo_comissao.get(),
            "cartao_pct": self.campo_cartao.get(),
            "taxa_fixa": self.campo_fixa.get(),
            "cor": self.canal["cor"] if self.editando else Cores.LARANJA,
        }

        try:
            if self.editando:
                ctrl.atualizar_canal(self.canal["id"], dados)
            else:
                ctrl.criar_canal(dados)
        except ctrl.ErroValidacao as erro:
            self.erro.configure(text=str(erro))
            return

        destino = self.pai
        self.destroy()
        if self.ao_salvar:
            self.ao_salvar()
        notificar(destino, f"Canal '{dados['nome']}' salvo.", "sucesso")


class DialogoCusto(_DialogoBase):
    def __init__(self, pai, custo=None, ao_salvar=None):
        self.custo = custo
        self.ao_salvar = ao_salvar
        self.editando = custo is not None

        super().__init__(
            pai,
            "Editar custo fixo" if self.editando else "Novo custo fixo",
            "Despesas que existem mesmo se voce nao vender nada.",
        )

        self.campo_descricao = Campo(self.corpo, "Descricao", obrigatorio=True,
                                     ajuda="Ex: Aluguel do ponto")
        self.campo_descricao.pack(fill="x")

        linha = ctk.CTkFrame(self.corpo, fg_color="transparent")
        linha.pack(fill="x", pady=(Espaco.SM, 0))

        self.campo_categoria = CampoSelecao(linha, "Categoria",
                                            ctrl.CATEGORIAS_CUSTO,
                                            valor="Aluguel", largura=170)
        self.campo_categoria.pack(side="left", padx=(0, Espaco.SM))

        self.campo_valor = Campo(linha, "Valor mensal (R$)", obrigatorio=True,
                                 largura=160)
        self.campo_valor.pack(side="left")

        if self.editando:
            self.campo_descricao.set(custo["descricao"])
            if custo.get("categoria"):
                if custo["categoria"] not in ctrl.CATEGORIAS_CUSTO:
                    self.campo_categoria.opcoes(
                        ctrl.CATEGORIAS_CUSTO + [custo["categoria"]])
                self.campo_categoria.set(custo["categoria"])
            self.campo_valor.set(f"{custo['valor_mensal']:.2f}".replace(".", ","))

        self.montar_rodape("Salvar" if self.editando else "Adicionar", self._salvar)
        self.campo_descricao.focar()

    def _salvar(self):
        self.erro.configure(text="")
        dados = {
            "descricao": self.campo_descricao.get(),
            "categoria": self.campo_categoria.get(),
            "valor_mensal": self.campo_valor.get(),
        }

        try:
            if self.editando:
                ctrl.atualizar_custo_fixo(self.custo["id"], dados)
            else:
                ctrl.criar_custo_fixo(dados)
        except ctrl.ErroValidacao as erro:
            self.erro.configure(text=str(erro))
            return

        destino = self.pai
        self.destroy()
        if self.ao_salvar:
            self.ao_salvar()
        notificar(destino, "Custo fixo salvo.", "sucesso")
