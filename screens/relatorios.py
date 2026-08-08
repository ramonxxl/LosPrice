"""
LosPrice - Tela de Relatorios
==============================

Quatro abas:
    Ficha tecnica   PDF por produto, para imprimir e colar na cozinha
    Tabela de precos PDF com todos os produtos x canais
    Engenharia      classificacao do cardapio a partir do volume de vendas
    Arquivos        exportacao Excel e historico do que ja foi gerado
"""

import os
from datetime import datetime

import customtkinter as ctk

from controllers import relatorios as ctrl
from utils.componentes import Botao, notificar
from utils.tema import (
    Cores, Espaco, Fontes, Icone, Raio,
    cor_margem, estilo_card, formatar_moeda, formatar_pct,
)


class TelaRelatorios(ctk.CTkFrame):
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

        for nome in ("Ficha tecnica", "Tabela de precos",
                     "Engenharia de cardapio", "Arquivos"):
            self.abas.add(nome)

        self._montar_fichas(self.abas.tab("Ficha tecnica"))
        self._montar_tabela(self.abas.tab("Tabela de precos"))
        self._montar_engenharia(self.abas.tab("Engenharia de cardapio"))
        self._montar_arquivos(self.abas.tab("Arquivos"))

    # -- helpers -----------------------------------------------------------

    def _gerar(self, funcao, *args, rotulo="Relatorio"):
        try:
            caminho = funcao(*args)
        except Exception as erro:
            notificar(self, str(erro) or f"Falha ao gerar {rotulo}.", "erro")
            return None

        self._recarregar_arquivos()
        aberto = ctrl.abrir_arquivo(caminho)
        notificar(
            self,
            f"{rotulo} gerado{'' if aberto else ' em relatorios/'}: "
            f"{os.path.basename(caminho)}",
            "sucesso",
        )
        return caminho

    @staticmethod
    def _cabecalho(pai, titulo, apoio):
        caixa = ctk.CTkFrame(pai, fg_color="transparent")
        caixa.pack(fill="x", pady=(0, Espaco.MD))
        ctk.CTkLabel(caixa, text=titulo, font=Fontes.subtitulo(),
                     text_color=Cores.TEXTO, anchor="w").pack(anchor="w")
        ctk.CTkLabel(caixa, text=apoio, font=Fontes.pequeno(),
                     text_color=Cores.TEXTO_SECUNDARIO, anchor="w",
                     justify="left").pack(anchor="w")
        return caixa

    # ------------------------------------------------------------------
    # Ficha tecnica
    # ------------------------------------------------------------------

    def _montar_fichas(self, aba):
        self._cabecalho(
            aba, "Ficha tecnica em PDF",
            "Imprima e cole na cozinha. E a gramatura na parede que faz o custo "
            "real bater com o custo calculado.")

        lista = ctk.CTkScrollableFrame(aba, fg_color="transparent")
        lista.pack(fill="both", expand=True)

        receitas = ctrl.receitas_disponiveis()
        if not receitas:
            self._vazio(lista, Icone.CHECKLIST, "Nenhuma receita cadastrada",
                        "Monte uma ficha tecnica em Receitas.")
            return

        for receita in receitas:
            cartao = ctk.CTkFrame(lista, **estilo_card())
            cartao.pack(fill="x", pady=3)

            interno = ctk.CTkFrame(cartao, fg_color="transparent")
            interno.pack(fill="x", padx=Espaco.MD, pady=Espaco.MD)

            texto = ctk.CTkFrame(interno, fg_color="transparent")
            texto.pack(side="left")
            ctk.CTkLabel(texto, text=receita["nome"], font=Fontes.corpo_forte(),
                         text_color=Cores.TEXTO, anchor="w").pack(anchor="w")
            ctk.CTkLabel(
                texto,
                text=f"{receita.get('categoria') or 'Sem categoria'}  ·  "
                     f"custo {formatar_moeda(receita['custo_unitario'])}",
                font=Fontes.micro(), text_color=Cores.TEXTO_SECUNDARIO,
                anchor="w").pack(anchor="w")

            Botao(interno, "Gerar PDF", icone=Icone.PDF, variante="secundario",
                  width=150, height=32,
                  command=lambda r=receita: self._gerar(
                      ctrl.ficha_tecnica_pdf, r["id"],
                      rotulo=f"Ficha de {r['nome']}")).pack(side="right")

    # ------------------------------------------------------------------
    # Tabela de precos
    # ------------------------------------------------------------------

    def _montar_tabela(self, aba):
        self._cabecalho(
            aba, "Tabela de precos por canal",
            "Todos os produtos e todos os canais em uma pagina. "
            "Util no balcao e para conferir cardapio de delivery.")

        cartao = ctk.CTkFrame(aba, **estilo_card())
        cartao.pack(fill="x")

        interno = ctk.CTkFrame(cartao, fg_color="transparent")
        interno.pack(fill="x", padx=Espaco.LG, pady=Espaco.LG)

        ctk.CTkLabel(interno, text=Icone.PDF, font=Fontes.icone(30),
                     text_color=Cores.LARANJA).pack()
        ctk.CTkLabel(interno, text="Tabela completa em PDF",
                     font=Fontes.subtitulo(),
                     text_color=Cores.TEXTO).pack(pady=(Espaco.SM, 2))
        ctk.CTkLabel(interno,
                     text="Uma linha por produto, uma coluna por canal, "
                          "em folha deitada.",
                     font=Fontes.pequeno(),
                     text_color=Cores.TEXTO_SECUNDARIO).pack()

        Botao(interno, "Gerar tabela de precos", icone=Icone.PDF, width=240,
              command=lambda: self._gerar(ctrl.tabela_precos_pdf,
                                          rotulo="Tabela de precos")).pack(
            pady=(Espaco.LG, 0))

    # ------------------------------------------------------------------
    # Engenharia de cardapio
    # ------------------------------------------------------------------

    def _montar_engenharia(self, aba):
        topo = self._cabecalho(
            aba, "Engenharia de cardapio",
            "Cruza margem com volume de vendas e diz o que fazer com cada produto. "
            "Informe quanto cada um vende por mes.")

        Botao(topo, "Gerar PDF", icone=Icone.PDF, variante="secundario",
              width=140, height=32,
              command=lambda: self._gerar(ctrl.engenharia_pdf,
                                          rotulo="Engenharia de cardapio")).pack(
            side="right")

        self.area_engenharia = ctk.CTkScrollableFrame(aba, fg_color="transparent")
        self.area_engenharia.pack(fill="both", expand=True)

        self.campos_vendas = {}
        self._recarregar_engenharia()

    def _recarregar_engenharia(self):
        for widget in self.area_engenharia.winfo_children():
            widget.destroy()
        self.campos_vendas = {}

        dados = ctrl.engenharia()

        if not dados["produtos"]:
            self._vazio(self.area_engenharia, Icone.CHECKLIST,
                        "Nenhuma receita cadastrada",
                        "Monte fichas tecnicas e defina precos primeiro.")
            return

        # resumo
        if dados["pronto"]:
            resumo = ctk.CTkFrame(self.area_engenharia, fg_color=Cores.SUPERFICIE,
                                  corner_radius=Raio.PADRAO)
            resumo.pack(fill="x", pady=(0, Espaco.MD))

            interno = ctk.CTkFrame(resumo, fg_color="transparent")
            interno.pack(fill="x", padx=Espaco.MD, pady=Espaco.SM)

            for rotulo, valor, cor in (
                ("Lucro estimado por mes",
                 formatar_moeda(dados["lucro_mes_total"]), Cores.LUCRO),
                ("Margem media", formatar_pct(dados["margem_media"]), Cores.TEXTO),
                ("Corte de popularidade",
                 f"{dados['vendas_corte']:.0f} un/mes", Cores.TEXTO_SECUNDARIO),
            ):
                caixa = ctk.CTkFrame(interno, fg_color="transparent")
                caixa.pack(side="left", padx=(0, Espaco.XL))
                ctk.CTkLabel(caixa, text=rotulo.upper(), font=Fontes.micro(),
                             text_color=Cores.TEXTO_APAGADO,
                             anchor="w").pack(anchor="w")
                ctk.CTkLabel(caixa, text=valor, font=Fontes.numero_forte(),
                             text_color=cor, anchor="w").pack(anchor="w")
        else:
            aviso = ctk.CTkFrame(self.area_engenharia, fg_color=Cores.ATENCAO_SUAVE,
                                 corner_radius=Raio.PADRAO,
                                 border_color=Cores.ATENCAO, border_width=1)
            aviso.pack(fill="x", pady=(0, Espaco.MD))
            interno = ctk.CTkFrame(aviso, fg_color="transparent")
            interno.pack(fill="x", padx=Espaco.MD, pady=Espaco.SM)
            ctk.CTkLabel(interno, text=Icone.ALERTA, font=Fontes.icone(14),
                         text_color=Cores.ATENCAO).pack(side="left",
                                                        padx=(0, Espaco.SM))
            ctk.CTkLabel(
                interno,
                text="Informe quantas unidades cada produto vende por mes "
                     "e clique em Recalcular. Sem volume nao ha classificacao.",
                font=Fontes.corpo(), text_color=Cores.TEXTO).pack(side="left")

        # produtos
        classificados = {p["id"]: p for p in dados["classificados"]}

        for produto in dados["produtos"]:
            self._linha_engenharia(produto, classificados.get(produto["id"]))

        Botao(self.area_engenharia, "Recalcular classificacao",
              icone=Icone.ATUALIZAR, width=230,
              command=self._salvar_vendas).pack(pady=(Espaco.MD, 0))

    def _linha_engenharia(self, produto, classificado):
        cartao = ctk.CTkFrame(self.area_engenharia, **estilo_card())
        cartao.pack(fill="x", pady=3)

        interno = ctk.CTkFrame(cartao, fg_color="transparent")
        interno.pack(fill="x", padx=Espaco.MD, pady=Espaco.MD)

        # nome + classe
        esquerda = ctk.CTkFrame(interno, fg_color="transparent",
                                width=250, height=40)
        esquerda.pack(side="left", fill="y")
        esquerda.pack_propagate(False)

        ctk.CTkLabel(esquerda, text=produto["nome"], font=Fontes.corpo_forte(),
                     text_color=Cores.TEXTO, anchor="w").pack(anchor="w")

        if classificado:
            ctk.CTkLabel(esquerda, text=classificado["classe_acao"],
                         font=Fontes.micro(),
                         text_color=Cores.TEXTO_APAGADO, anchor="w").pack(anchor="w")
        elif produto["margem"] is None:
            ctk.CTkLabel(esquerda, text="sem preco definido", font=Fontes.micro(),
                         text_color=Cores.ATENCAO, anchor="w").pack(anchor="w")

        # campo de vendas - inline em vez do widget Campo, que e alto demais
        # para uma linha de lista
        caixa = ctk.CTkFrame(interno, fg_color="transparent", width=110, height=40)
        caixa.pack(side="left", padx=(0, Espaco.MD))
        caixa.pack_propagate(False)

        ctk.CTkLabel(caixa, text="VENDE/MES", font=Fontes.micro(),
                     text_color=Cores.TEXTO_APAGADO, anchor="w").pack(fill="x")

        variavel = ctk.StringVar(
            value=f"{produto['vendas_mes']:g}" if produto["vendas_mes"] else "")
        ctk.CTkEntry(caixa, textvariable=variavel, justify="right", height=24,
                     font=Fontes.numero(), fg_color=Cores.ENTRADA,
                     border_color=Cores.BORDA, border_width=1,
                     text_color=Cores.TEXTO,
                     corner_radius=Raio.PEQUENO).pack(fill="x")

        self.campos_vendas[produto["id"]] = variavel

        # classe
        if classificado:
            badge = ctk.CTkFrame(interno, fg_color=Cores.SUPERFICIE,
                                 corner_radius=Raio.PILULA)
            badge.pack(side="right")
            ctk.CTkLabel(badge, text=classificado["classe"],
                         font=Fontes.corpo_forte(),
                         text_color=classificado["classe_cor"]).pack(
                padx=Espaco.MD, pady=5)

        # numeros
        if produto["margem"] is not None:
            for rotulo, valor, cor in (
                ("Margem", formatar_pct(produto["margem"]),
                 cor_margem(produto["margem"])),
                ("Lucro/un", formatar_moeda(produto["lucro"] or 0), Cores.TEXTO),
                ("Lucro/mes",
                 formatar_moeda(classificado["lucro_mes"]) if classificado else "--",
                 Cores.LUCRO if classificado else Cores.TEXTO_APAGADO),
            ):
                caixa = ctk.CTkFrame(interno, fg_color="transparent",
                                     width=95, height=40)
                caixa.pack(side="left", fill="y")
                caixa.pack_propagate(False)
                ctk.CTkLabel(caixa, text=rotulo.upper(), font=Fontes.micro(),
                             text_color=Cores.TEXTO_APAGADO,
                             anchor="w").pack(fill="x")
                ctk.CTkLabel(caixa, text=valor, font=Fontes.numero_forte(),
                             text_color=cor, anchor="w").pack(fill="x")

    def _salvar_vendas(self):
        for receita_id, variavel in self.campos_vendas.items():
            bruto = (variavel.get().strip() or "0").replace(".", "").replace(",", ".")
            try:
                valor = float(bruto)
            except ValueError:
                valor = 0
            ctrl.salvar_vendas(receita_id, valor)

        self._recarregar_engenharia()
        notificar(self, "Classificacao atualizada.", "sucesso")

    # ------------------------------------------------------------------
    # Arquivos
    # ------------------------------------------------------------------

    def _montar_arquivos(self, aba):
        aba.grid_columnconfigure(0, weight=3)
        aba.grid_columnconfigure(1, weight=2)
        aba.grid_rowconfigure(1, weight=1)

        topo = ctk.CTkFrame(aba, fg_color="transparent")
        topo.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, Espaco.MD))

        texto = ctk.CTkFrame(topo, fg_color="transparent")
        texto.pack(side="left")
        ctk.CTkLabel(texto, text="Arquivos gerados", font=Fontes.subtitulo(),
                     text_color=Cores.TEXTO).pack(anchor="w")
        ctk.CTkLabel(texto, text="Tudo fica na pasta relatorios/ do sistema.",
                     font=Fontes.pequeno(),
                     text_color=Cores.TEXTO_SECUNDARIO).pack(anchor="w")

        Botao(topo, "Abrir pasta", icone=Icone.CAIXA, variante="secundario",
              width=140, height=32,
              command=self._abrir_pasta).pack(side="right")

        self.lista_arquivos = ctk.CTkScrollableFrame(aba, fg_color="transparent")
        self.lista_arquivos.grid(row=1, column=0, sticky="nsew",
                                 padx=(0, Espaco.MD))

        painel = ctk.CTkFrame(aba, fg_color=Cores.SUPERFICIE,
                              corner_radius=Raio.GRANDE,
                              border_color=Cores.BORDA, border_width=1)
        painel.grid(row=1, column=1, sticky="nsew")

        interno = ctk.CTkFrame(painel, fg_color="transparent")
        interno.pack(fill="both", expand=True, padx=Espaco.LG, pady=Espaco.LG)

        ctk.CTkLabel(interno, text=Icone.EXCEL, font=Fontes.icone(26),
                     text_color=Cores.VERDE).pack(anchor="w")
        ctk.CTkLabel(interno, text="Exportar para Excel", font=Fontes.subtitulo(),
                     text_color=Cores.TEXTO).pack(anchor="w", pady=(Espaco.SM, 2))
        ctk.CTkLabel(
            interno,
            text="Uma planilha com quatro abas:\n"
                 "ingredientes, embalagens, fichas tecnicas e precos.\n\n"
                 "Util para backup, para o contador ou para trabalhar "
                 "os numeros por fora.",
            font=Fontes.pequeno(), text_color=Cores.TEXTO_SECUNDARIO,
            justify="left", anchor="w").pack(fill="x")

        Botao(interno, "Gerar planilha", icone=Icone.EXCEL, variante="sucesso",
              command=lambda: self._gerar(ctrl.exportar_excel,
                                          rotulo="Planilha")).pack(
            fill="x", pady=(Espaco.LG, 0))

        self._recarregar_arquivos()

    def _abrir_pasta(self):
        ctrl.abrir_arquivo(ctrl.garantir_pasta())

    def _recarregar_arquivos(self):
        if not hasattr(self, "lista_arquivos"):
            return

        for widget in self.lista_arquivos.winfo_children():
            widget.destroy()

        arquivos = ctrl.gerados()
        if not arquivos:
            self._vazio(self.lista_arquivos, Icone.RELATORIO,
                        "Nenhum arquivo gerado ainda",
                        "Gere uma ficha tecnica ou a tabela de precos.")
            return

        for arquivo in arquivos:
            cartao = ctk.CTkFrame(self.lista_arquivos, **estilo_card())
            cartao.pack(fill="x", pady=3)

            interno = ctk.CTkFrame(cartao, fg_color="transparent")
            interno.pack(fill="x", padx=Espaco.MD, pady=Espaco.SM)

            cor = Cores.PREJUIZO if arquivo["tipo"] == "PDF" else Cores.VERDE
            ctk.CTkLabel(interno,
                         text=Icone.PDF if arquivo["tipo"] == "PDF" else Icone.EXCEL,
                         font=Fontes.icone(16),
                         text_color=cor).pack(side="left", padx=(0, Espaco.MD))

            texto = ctk.CTkFrame(interno, fg_color="transparent")
            texto.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(texto, text=arquivo["nome"], font=Fontes.pequeno(),
                         text_color=Cores.TEXTO, anchor="w").pack(anchor="w")

            data = datetime.fromtimestamp(arquivo["data"])
            ctk.CTkLabel(
                texto,
                text=f"{data.strftime('%d/%m/%Y as %H:%M')}  ·  "
                     f"{arquivo['tamanho'] / 1024:.0f} KB",
                font=Fontes.micro(), text_color=Cores.TEXTO_APAGADO,
                anchor="w").pack(anchor="w")

            Botao(interno, "Abrir", variante="secundario", width=90, height=30,
                  command=lambda a=arquivo: ctrl.abrir_arquivo(a["caminho"])).pack(
                side="right")

    # -- auxiliar ----------------------------------------------------------

    @staticmethod
    def _vazio(pai, icone, titulo, mensagem):
        caixa = ctk.CTkFrame(pai, fg_color="transparent")
        caixa.pack(expand=True, pady=50)
        ctk.CTkLabel(caixa, text=icone, font=Fontes.icone(28),
                     text_color=Cores.TEXTO_APAGADO).pack()
        ctk.CTkLabel(caixa, text=titulo, font=Fontes.subtitulo(),
                     text_color=Cores.TEXTO_SECUNDARIO).pack(pady=(Espaco.SM, 2))
        ctk.CTkLabel(caixa, text=mensagem, font=Fontes.pequeno(),
                     text_color=Cores.TEXTO_APAGADO, justify="center").pack()
