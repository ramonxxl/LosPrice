"""
LosPrice - Dashboard
=====================

Tela de abertura. O criterio dela e simples: o que exige acao aparece
primeiro, o que so informa aparece depois.

Cada alerta leva direto para a tela onde o problema se resolve.
"""

import customtkinter as ctk

from controllers import dashboard as ctrl
from core.calculo import ROTULO_BASE
from utils.componentes import Botao, CardMetrica, separador
from utils.tema import (
    APP_SLOGAN, Cores, Espaco, Fontes, Icone, Raio,
    cor_margem, estilo_card, formatar_moeda, formatar_moeda_precisa,
    formatar_pct, rotulo_margem,
)

GRAVIDADE = {
    "prejuizo": (Cores.PREJUIZO, Cores.PREJUIZO_SUAVE, Icone.ALERTA),
    "atencao": (Cores.ATENCAO, Cores.ATENCAO_SUAVE, Icone.ALERTA),
    "info": (Cores.INFO, Cores.CARD_HOVER, Icone.CHECKLIST),
}


class TelaDashboard(ctk.CTkFrame):
    def __init__(self, pai):
        super().__init__(pai, fg_color="transparent")

        self.area = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.area.pack(fill="both", expand=True)

        self.recarregar()

    # -- navegacao ---------------------------------------------------------

    def _ir_para(self, destino):
        janela = self.winfo_toplevel()
        if hasattr(janela, "navegar"):
            janela.navegar(destino)

    # -- montagem ----------------------------------------------------------

    def recarregar(self):
        for widget in self.area.winfo_children():
            widget.destroy()

        dados = ctrl.resumo()

        if not dados["receitas"] and not dados["ingredientes"]:
            self._primeiros_passos()
            return

        self._cards(dados)
        self._alertas()

        colunas = ctk.CTkFrame(self.area, fg_color="transparent")
        colunas.pack(fill="both", expand=True, pady=(Espaco.MD, 0))
        colunas.grid_columnconfigure(0, weight=3)
        colunas.grid_columnconfigure(1, weight=2)

        self._ranking(colunas)
        self._lateral(colunas)

    # -- estado inicial ----------------------------------------------------

    def _primeiros_passos(self):
        cartao = ctk.CTkFrame(self.area, **estilo_card())
        cartao.pack(fill="x", pady=Espaco.XL, padx=Espaco.XXL)

        interno = ctk.CTkFrame(cartao, fg_color="transparent")
        interno.pack(padx=Espaco.XXL, pady=Espaco.XL)

        ctk.CTkLabel(interno, text="Bem-vindo ao LosPrice", font=Fontes.display(),
                     text_color=Cores.TEXTO).pack()
        ctk.CTkLabel(interno, text=APP_SLOGAN, font=Fontes.corpo(),
                     text_color=Cores.TEXTO_SECUNDARIO).pack(pady=(4, Espaco.XL))

        passos = [
            (Icone.CARRINHO, "Cadastre seus ingredientes",
             "Informe a compra: 5 kg por R$ 185,00. O custo por grama sai sozinho.",
             "ingredientes"),
            (Icone.CAIXA, "Cadastre as embalagens",
             "Caixa, saco, copo. Tudo que sai junto com o produto.", "embalagens"),
            (Icone.CHECKLIST, "Monte a ficha tecnica",
             "Escolha os itens e as quantidades. O custo se forma na hora.",
             "receitas"),
            (Icone.CALCULADORA, "Defina o preco por canal",
             "Balcao, WhatsApp, iFood. Cada um com sua taxa e seu preco certo.",
             "precificacao"),
        ]

        for indice, (icone, titulo, texto, destino) in enumerate(passos, 1):
            linha = ctk.CTkFrame(interno, fg_color="transparent")
            linha.pack(fill="x", pady=Espaco.SM)

            numero = ctk.CTkFrame(linha, fg_color=Cores.LARANJA_SUAVE,
                                  width=32, height=32, corner_radius=Raio.PILULA)
            numero.pack(side="left", padx=(0, Espaco.MD))
            numero.pack_propagate(False)
            ctk.CTkLabel(numero, text=str(indice), font=Fontes.corpo_forte(),
                         text_color=Cores.LARANJA).pack(expand=True)

            texto_caixa = ctk.CTkFrame(linha, fg_color="transparent")
            texto_caixa.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(texto_caixa, text=titulo, font=Fontes.corpo_forte(),
                         text_color=Cores.TEXTO, anchor="w").pack(anchor="w")
            ctk.CTkLabel(texto_caixa, text=texto, font=Fontes.pequeno(),
                         text_color=Cores.TEXTO_SECUNDARIO, anchor="w").pack(anchor="w")

            Botao(linha, "Abrir", variante="secundario", width=100, height=32,
                  command=lambda d=destino: self._ir_para(d)).pack(side="right")

    # -- cards -------------------------------------------------------------

    def _cards(self, dados):
        linha = ctk.CTkFrame(self.area, fg_color="transparent")
        linha.pack(fill="x")

        margem = dados["margem_media"]
        cor_lucro = cor_margem(margem) if dados["precificadas"] else Cores.NEUTRO

        cartoes = [
            ("Produtos com ficha", str(dados["receitas"]), Cores.LARANJA,
             Icone.CHECKLIST,
             f"custo medio {formatar_moeda(dados['custo_medio'])}"),

            ("Lucro medio", formatar_pct(margem) if dados["precificadas"] else "--",
             cor_lucro, Icone.DINHEIRO,
             rotulo_margem(margem) if dados["precificadas"] else "sem precificacao"),

            ("Precificados", f"{dados['precificadas']}/{dados['receitas']}",
             Cores.INFO, Icone.CALCULADORA,
             f"{dados['receitas'] - dados['precificadas']} sem preco"
             if dados["receitas"] > dados["precificadas"] else "todos com preco"),

            ("Insumos cadastrados", str(dados["ingredientes"]), Cores.VERDE,
             Icone.CARRINHO,
             f"{dados['embalagens']} embalagens · {dados['fornecedores']} fornecedores"),
        ]

        for indice, (rotulo, valor, cor, icone, apoio) in enumerate(cartoes):
            card = CardMetrica(linha, rotulo, valor, cor, icone, apoio)
            card.pack(side="left", expand=True, fill="both",
                      padx=(0, Espaco.GAP_CARD if indice < 3 else 0))

    # -- alertas -----------------------------------------------------------

    def _alertas(self):
        lista = ctrl.alertas()
        if not lista:
            self._tudo_certo()
            return

        cartao = ctk.CTkFrame(self.area, **estilo_card())
        cartao.pack(fill="x", pady=(Espaco.MD, 0))

        topo = ctk.CTkFrame(cartao, fg_color="transparent")
        topo.pack(fill="x", padx=Espaco.LG, pady=(Espaco.MD, Espaco.SM))
        ctk.CTkLabel(topo, text="PRECISA DA SUA ATENCAO", font=Fontes.micro(),
                     text_color=Cores.TEXTO_APAGADO).pack(side="left")
        ctk.CTkLabel(topo, text=f"{len(lista)} ponto(s)", font=Fontes.micro(),
                     text_color=Cores.TEXTO_APAGADO).pack(side="right")

        for indice, alerta in enumerate(lista):
            self._linha_alerta(cartao, alerta, indice == len(lista) - 1)

    def _linha_alerta(self, pai, alerta, ultimo):
        cor, fundo, icone = GRAVIDADE.get(alerta["gravidade"], GRAVIDADE["info"])

        linha = ctk.CTkFrame(pai, fg_color="transparent")
        linha.pack(fill="x", padx=Espaco.LG, pady=(0, Espaco.MD if ultimo else 0))

        interno = ctk.CTkFrame(linha, fg_color=fundo, corner_radius=Raio.PADRAO)
        interno.pack(fill="x", pady=3)

        conteudo = ctk.CTkFrame(interno, fg_color="transparent")
        conteudo.pack(fill="x", padx=Espaco.MD, pady=Espaco.SM)

        cabeca = ctk.CTkFrame(conteudo, fg_color="transparent")
        cabeca.pack(fill="x")

        ctk.CTkLabel(cabeca, text=icone, font=Fontes.icone(14),
                     text_color=cor).pack(side="left", padx=(0, Espaco.SM))
        ctk.CTkLabel(cabeca, text=alerta["titulo"], font=Fontes.corpo_forte(),
                     text_color=Cores.TEXTO, anchor="w").pack(side="left")

        Botao(cabeca, "Resolver", variante="secundario", width=100, height=28,
              command=lambda d=alerta["destino"]: self._ir_para(d)).pack(side="right")

        detalhe = "   ·   ".join(alerta["detalhes"])
        if alerta.get("extra", 0) > 0:
            detalhe += f"   ·   + {alerta['extra']}"

        ctk.CTkLabel(conteudo, text=detalhe, font=Fontes.micro(),
                     text_color=Cores.TEXTO_SECUNDARIO, anchor="w",
                     justify="left").pack(fill="x", padx=(26, 0))

    def _tudo_certo(self):
        cartao = ctk.CTkFrame(self.area, fg_color=Cores.VERDE_SUAVE,
                              corner_radius=Raio.GRANDE,
                              border_color=Cores.VERDE, border_width=1)
        cartao.pack(fill="x", pady=(Espaco.MD, 0))

        interno = ctk.CTkFrame(cartao, fg_color="transparent")
        interno.pack(fill="x", padx=Espaco.LG, pady=Espaco.MD)

        ctk.CTkLabel(interno, text=Icone.OK, font=Fontes.icone(16),
                     text_color=Cores.VERDE).pack(side="left", padx=(0, Espaco.SM))
        ctk.CTkLabel(interno, text="Tudo em ordem", font=Fontes.corpo_forte(),
                     text_color=Cores.TEXTO).pack(side="left")
        ctk.CTkLabel(interno,
                     text="Nenhum produto no prejuizo e nenhuma ficha defasada.",
                     font=Fontes.pequeno(),
                     text_color=Cores.TEXTO_SECUNDARIO).pack(side="left",
                                                             padx=(Espaco.SM, 0))

    # -- ranking -----------------------------------------------------------

    def _ranking(self, pai):
        cartao = ctk.CTkFrame(pai, **estilo_card())
        cartao.grid(row=0, column=0, sticky="nsew", padx=(0, Espaco.MD))

        topo = ctk.CTkFrame(cartao, fg_color="transparent")
        topo.pack(fill="x", padx=Espaco.LG, pady=(Espaco.MD, Espaco.SM))
        ctk.CTkLabel(topo, text="PRODUTOS POR MARGEM", font=Fontes.micro(),
                     text_color=Cores.TEXTO_APAGADO).pack(side="left")
        ctk.CTkLabel(topo, text="menor primeiro", font=Fontes.micro(),
                     text_color=Cores.TEXTO_APAGADO).pack(side="right")

        produtos = ctrl.ranking()

        if not produtos:
            self._vazio(cartao, Icone.CALCULADORA, "Nenhum produto precificado",
                        "Defina precos em Precificacao para ver o ranking.",
                        "precificacao")
            return

        for produto in produtos:
            self._linha_produto(cartao, produto)

        ctk.CTkFrame(cartao, fg_color="transparent", height=Espaco.SM).pack()

    def _linha_produto(self, pai, produto):
        linha = ctk.CTkFrame(pai, fg_color="transparent")
        linha.pack(fill="x", padx=Espaco.LG, pady=4)

        topo = ctk.CTkFrame(linha, fg_color="transparent")
        topo.pack(fill="x")

        ctk.CTkLabel(topo, text=produto["nome"], font=Fontes.corpo(),
                     text_color=Cores.TEXTO, anchor="w").pack(side="left")

        cor = cor_margem(produto["margem"])
        ctk.CTkLabel(topo, text=formatar_pct(produto["margem"]),
                     font=Fontes.numero_forte(), text_color=cor).pack(side="right")
        ctk.CTkLabel(topo, text=f"{formatar_moeda(produto['lucro'])}  ·  ",
                     font=Fontes.numero(),
                     text_color=Cores.TEXTO_SECUNDARIO).pack(side="right")

        barra = ctk.CTkProgressBar(linha, height=5, corner_radius=Raio.PILULA,
                                   fg_color=Cores.BORDA, progress_color=cor)
        barra.pack(fill="x", pady=(3, 0))
        barra.set(min(max(produto["margem"], 0) / 50.0, 1.0))

        ctk.CTkLabel(linha,
                     text=f"custo {formatar_moeda(produto['custo_unitario'])}  ·  "
                          f"{produto['canais']} canais  ·  "
                          f"{rotulo_margem(produto['margem'])}",
                     font=Fontes.micro(), text_color=Cores.TEXTO_APAGADO,
                     anchor="w").pack(fill="x", pady=(2, 0))

    # -- coluna lateral ----------------------------------------------------

    def _lateral(self, pai):
        coluna = ctk.CTkFrame(pai, fg_color="transparent")
        coluna.grid(row=0, column=1, sticky="nsew")

        self._variacoes(coluna)
        self._pesados(coluna)
        self._canais(coluna)

    def _variacoes(self, pai):
        cartao = ctk.CTkFrame(pai, **estilo_card())
        cartao.pack(fill="x")

        ctk.CTkLabel(cartao, text="MOVIMENTACAO DE PRECOS", font=Fontes.micro(),
                     text_color=Cores.TEXTO_APAGADO).pack(
            anchor="w", padx=Espaco.LG, pady=(Espaco.MD, Espaco.SM))

        lista = ctrl.variacoes()

        if not lista:
            ctk.CTkLabel(cartao,
                         text="Nenhuma variacao registrada ainda.\n"
                              "Ao atualizar o preco de um insumo, a mudanca "
                              "aparece aqui.",
                         font=Fontes.pequeno(), text_color=Cores.TEXTO_APAGADO,
                         justify="left", anchor="w").pack(
                fill="x", padx=Espaco.LG, pady=(0, Espaco.MD))
            return

        for item in lista:
            self._linha_variacao(cartao, item)

        ctk.CTkFrame(cartao, fg_color="transparent", height=Espaco.SM).pack()

    def _linha_variacao(self, pai, item):
        linha = ctk.CTkFrame(pai, fg_color="transparent")
        linha.pack(fill="x", padx=Espaco.LG, pady=3)

        subiu = item["variacao_pct"] > 0
        cor = Cores.PREJUIZO if subiu else Cores.LUCRO
        unidade = ROTULO_BASE.get(item["unidade_base"], "un")

        topo = ctk.CTkFrame(linha, fg_color="transparent")
        topo.pack(fill="x")
        ctk.CTkLabel(topo, text=item["nome"], font=Fontes.corpo(),
                     text_color=Cores.TEXTO, anchor="w").pack(side="left")

        ctk.CTkLabel(topo,
                     text=f"{Icone.SETA_CIMA if subiu else Icone.SETA_BAIXO} "
                          f"{formatar_pct(abs(item['variacao_pct']))}",
                     font=Fontes.numero_forte(), text_color=cor).pack(side="right")

        ctk.CTkLabel(
            linha,
            text=f"{formatar_moeda_precisa(item['custo_anterior'])} -> "
                 f"{formatar_moeda_precisa(item['custo_atual'])} /{unidade}",
            font=Fontes.micro(), text_color=Cores.TEXTO_APAGADO, anchor="w",
        ).pack(fill="x")

    def _pesados(self, pai):
        itens = ctrl.insumos_mais_pesados()
        if not itens:
            return

        cartao = ctk.CTkFrame(pai, **estilo_card())
        cartao.pack(fill="x", pady=(Espaco.MD, 0))

        ctk.CTkLabel(cartao, text="ONDE NEGOCIAR RENDE MAIS", font=Fontes.micro(),
                     text_color=Cores.TEXTO_APAGADO).pack(
            anchor="w", padx=Espaco.LG, pady=(Espaco.MD, 2))
        ctk.CTkLabel(cartao, text="Insumos que mais pesam nas suas fichas",
                     font=Fontes.micro(), text_color=Cores.TEXTO_APAGADO,
                     anchor="w").pack(anchor="w", padx=Espaco.LG,
                                      pady=(0, Espaco.SM))

        for item in itens:
            linha = ctk.CTkFrame(cartao, fg_color="transparent")
            linha.pack(fill="x", padx=Espaco.LG, pady=2)

            topo = ctk.CTkFrame(linha, fg_color="transparent")
            topo.pack(fill="x")
            ctk.CTkLabel(topo, text=item["nome"], font=Fontes.pequeno(),
                         text_color=Cores.TEXTO, anchor="w").pack(side="left")
            ctk.CTkLabel(topo, text=formatar_pct(item["participacao_pct"], 0),
                         font=Fontes.micro(),
                         text_color=Cores.TEXTO_SECUNDARIO).pack(side="right")

            barra = ctk.CTkProgressBar(linha, height=4, corner_radius=Raio.PILULA,
                                       fg_color=Cores.BORDA,
                                       progress_color=Cores.LARANJA)
            barra.pack(fill="x", pady=(2, 0))
            barra.set(min(item["participacao_pct"] / 100.0, 1.0))

        ctk.CTkFrame(cartao, fg_color="transparent", height=Espaco.SM).pack()

    def _canais(self, pai):
        canais = ctrl.por_canal()
        if not canais:
            return

        cartao = ctk.CTkFrame(pai, **estilo_card())
        cartao.pack(fill="x", pady=(Espaco.MD, 0))

        ctk.CTkLabel(cartao, text="RESULTADO POR CANAL", font=Fontes.micro(),
                     text_color=Cores.TEXTO_APAGADO).pack(
            anchor="w", padx=Espaco.LG, pady=(Espaco.MD, Espaco.SM))

        for canal in canais:
            linha = ctk.CTkFrame(cartao, fg_color="transparent")
            linha.pack(fill="x", padx=Espaco.LG, pady=3)

            ctk.CTkFrame(linha, fg_color=canal["cor"], width=3, height=13,
                         corner_radius=Raio.PILULA).pack(side="left", padx=(0, 8))
            ctk.CTkLabel(linha, text=canal["nome"], font=Fontes.pequeno(),
                         text_color=Cores.TEXTO, anchor="w").pack(side="left")

            cor = cor_margem(canal["margem"])
            ctk.CTkLabel(linha, text=formatar_pct(canal["margem"]),
                         font=Fontes.numero_forte(),
                         text_color=cor).pack(side="right")
            ctk.CTkLabel(linha, text=f"{formatar_moeda(canal['lucro'])}  ·  ",
                         font=Fontes.numero(),
                         text_color=Cores.TEXTO_SECUNDARIO).pack(side="right")

        ctk.CTkFrame(cartao, fg_color="transparent", height=Espaco.SM).pack()

    # -- auxiliar ----------------------------------------------------------

    def _vazio(self, pai, icone, titulo, mensagem, destino):
        caixa = ctk.CTkFrame(pai, fg_color="transparent")
        caixa.pack(expand=True, pady=Espaco.XL)

        ctk.CTkLabel(caixa, text=icone, font=Fontes.icone(26),
                     text_color=Cores.TEXTO_APAGADO).pack()
        ctk.CTkLabel(caixa, text=titulo, font=Fontes.corpo_forte(),
                     text_color=Cores.TEXTO_SECUNDARIO).pack(pady=(Espaco.SM, 2))
        ctk.CTkLabel(caixa, text=mensagem, font=Fontes.pequeno(),
                     text_color=Cores.TEXTO_APAGADO, justify="center").pack()
        Botao(caixa, "Abrir", variante="secundario", width=120, height=30,
              command=lambda: self._ir_para(destino)).pack(pady=(Espaco.MD, 0))
