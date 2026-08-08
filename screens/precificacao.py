"""
LosPrice - Tela de Precificacao
================================

A tela que da nome ao software.

Escolhe-se a receita a esquerda e os canais aparecem lado a lado a direita.
O ponto alto e o comparativo: o mesmo pastel rende R$ 7,80 no balcao e
R$ 2,10 no iFood. Ver isso em uma tabela unica costuma ser a primeira vez
que o dono entende para onde o dinheiro dele esta indo.

Todo o calculo vem de core.calculo pelo metodo divisor: as taxas incidem
sobre o preco de venda, nunca sobre o custo.
"""

import customtkinter as ctk

from controllers import precificacao as ctrl
from utils.componentes import BarraBusca, Botao, Campo, notificar, separador
from utils.tema import (
    Cores, Espaco, Fontes, Icone, Raio,
    cor_fundo_margem, cor_margem, estilo_card, estilo_entrada,
    formatar_moeda, formatar_pct, rotulo_margem,
)

# Larguras das colunas da grade de canais
COL_CANAL = 192
COL_VALOR = 92
COL_MARGEM = 74


class TelaPrecificacao(ctk.CTkFrame):
    def __init__(self, pai):
        super().__init__(pai, fg_color="transparent")

        self.receita = None
        self.dados = None
        self.linhas = {}
        self.busca = ""

        padrao = ctrl.parametros()
        self.arredondar = padrao["arredondar"]

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._montar_lista()
        self._montar_detalhe(padrao)
        self.recarregar()

    # -- painel esquerdo ---------------------------------------------------

    def _montar_lista(self):
        painel = ctk.CTkFrame(self, width=262, **estilo_card())
        painel.grid(row=0, column=0, sticky="nsw", padx=(0, Espaco.MD))
        painel.grid_propagate(False)

        topo = ctk.CTkFrame(painel, fg_color="transparent")
        topo.pack(fill="x", padx=Espaco.MD, pady=Espaco.MD)

        ctk.CTkLabel(topo, text="PRODUTOS", font=Fontes.micro(),
                     text_color=Cores.TEXTO_APAGADO).pack(anchor="w",
                                                          pady=(0, Espaco.SM))
        BarraBusca(topo, self._ao_buscar, texto="Buscar produto",
                   largura=222).pack()

        separador(painel).pack(fill="x")

        self.lista = ctk.CTkScrollableFrame(painel, fg_color="transparent")
        self.lista.pack(fill="both", expand=True)

    def _ao_buscar(self, termo):
        self.busca = termo
        self.recarregar(manter_selecao=True)

    # -- painel direito ----------------------------------------------------

    def _montar_detalhe(self, padrao):
        area = ctk.CTkFrame(self, fg_color="transparent")
        area.grid(row=0, column=1, sticky="nsew")
        area.grid_rowconfigure(2, weight=1)
        area.grid_columnconfigure(0, weight=1)

        # cabecalho do produto
        cabecalho = ctk.CTkFrame(area, **estilo_card())
        cabecalho.grid(row=0, column=0, sticky="ew")

        interno = ctk.CTkFrame(cabecalho, fg_color="transparent")
        interno.pack(fill="x", padx=Espaco.LG, pady=Espaco.MD)

        texto = ctk.CTkFrame(interno, fg_color="transparent")
        texto.pack(side="left")
        self.titulo = ctk.CTkLabel(texto, text="Selecione um produto",
                                   font=Fontes.subtitulo(), text_color=Cores.TEXTO,
                                   anchor="w")
        self.titulo.pack(anchor="w")
        self.subtitulo = ctk.CTkLabel(texto, text="A ficha tecnica define o custo",
                                      font=Fontes.pequeno(),
                                      text_color=Cores.TEXTO_SECUNDARIO, anchor="w")
        self.subtitulo.pack(anchor="w")

        custo_caixa = ctk.CTkFrame(interno, fg_color="transparent")
        custo_caixa.pack(side="right")
        ctk.CTkLabel(custo_caixa, text="CUSTO DA FICHA", font=Fontes.micro(),
                     text_color=Cores.TEXTO_APAGADO).pack(anchor="e")
        self.custo = ctk.CTkLabel(custo_caixa, text="--", font=Fontes.titulo(),
                                  text_color=Cores.LARANJA)
        self.custo.pack(anchor="e")

        # parametros
        parametros = ctk.CTkFrame(area, **estilo_card())
        parametros.grid(row=1, column=0, sticky="ew", pady=(Espaco.MD, 0))

        linha = ctk.CTkFrame(parametros, fg_color="transparent")
        linha.pack(fill="x", padx=Espaco.LG, pady=Espaco.MD)

        self.campo_margem = Campo(linha, "Lucro desejado (%)",
                                  valor=f"{padrao['margem_pct']:g}",
                                  ao_digitar=self._recalcular, largura=120)
        self.campo_margem.pack(side="left", padx=(0, Espaco.MD))

        self.campo_imposto = Campo(linha, "Imposto (%)",
                                   valor=f"{padrao['imposto_pct']:g}",
                                   ao_digitar=self._recalcular, largura=100)
        self.campo_imposto.pack(side="left", padx=(0, Espaco.MD))

        self.campo_custo_fixo = Campo(linha, "Custo fixo (%)",
                                      valor=f"{padrao['custo_fixo_pct']:g}",
                                      ao_digitar=self._recalcular, largura=100)
        self.campo_custo_fixo.pack(side="left", padx=(0, Espaco.MD))

        self.campo_custo_rs = Campo(linha, "Custo fixo (R$)", valor="0",
                                    ao_digitar=self._recalcular, largura=110,
                                    ajuda="Rateio por unidade")
        self.campo_custo_rs.pack(side="left", padx=(0, Espaco.MD))

        self.arredonda_var = ctk.BooleanVar(value=self.arredondar)
        ctk.CTkCheckBox(linha, text="Arredondar para ,90",
                        variable=self.arredonda_var, font=Fontes.pequeno(),
                        command=self._trocar_arredondamento,
                        checkbox_width=18, checkbox_height=18,
                        fg_color=Cores.LARANJA, hover_color=Cores.LARANJA_HOVER,
                        border_color=Cores.BORDA,
                        text_color=Cores.TEXTO_SECUNDARIO).pack(side="left",
                                                                pady=(14, 0))

        # grade de canais
        self.grade = ctk.CTkFrame(area, **estilo_card())
        self.grade.grid(row=2, column=0, sticky="nsew", pady=(Espaco.MD, 0))

        self.cabecalho_grade = ctk.CTkFrame(self.grade,
                                            fg_color=Cores.TABELA_CABECALHO,
                                            corner_radius=0, height=38)
        self.cabecalho_grade.pack(fill="x")
        self.cabecalho_grade.pack_propagate(False)
        self._montar_cabecalho_grade()

        separador(self.grade).pack(fill="x")

        self.canais = ctk.CTkScrollableFrame(self.grade, fg_color="transparent")
        self.canais.pack(fill="both", expand=True)

        # rodape
        rodape = ctk.CTkFrame(area, fg_color="transparent", height=0)
        rodape.grid(row=3, column=0, sticky="ew", pady=(Espaco.MD, 0))

        self.aviso = ctk.CTkLabel(rodape, text="", font=Fontes.pequeno(),
                                  text_color=Cores.TEXTO_SECUNDARIO, anchor="w")
        self.aviso.pack(side="left", fill="x", expand=True)

        self.botao_salvar = Botao(rodape, "Salvar precificacao", icone=Icone.SALVAR,
                                  variante="sucesso", width=200,
                                  command=self._salvar)
        self.botao_salvar.pack(side="right")

    def _montar_cabecalho_grade(self):
        colunas = [
            ("CANAL", COL_CANAL, "w"),
            ("SUGERIDO", COL_VALOR, "e"),
            ("VITRINE", COL_VALOR, "e"),
            ("VOCE COBRA", COL_VALOR, "e"),
            ("LUCRO", COL_VALOR, "e"),
            ("MARGEM", COL_MARGEM, "e"),
        ]
        for titulo, largura, alinhamento in colunas:
            celula = ctk.CTkFrame(self.cabecalho_grade, fg_color="transparent",
                                  width=largura)
            celula.pack(side="left", fill="y", padx=(Espaco.MD, 0))
            celula.pack_propagate(False)
            ctk.CTkLabel(celula, text=titulo, font=Fontes.micro(),
                         text_color=Cores.TEXTO_APAGADO,
                         anchor=alinhamento).pack(fill="both", expand=True)

    # -- dados -------------------------------------------------------------

    def recarregar(self, manter_selecao=False):
        for widget in self.lista.winfo_children():
            widget.destroy()

        receitas = ctrl.receitas(self.busca)

        if not receitas:
            self._lista_vazia()
            self._limpar_detalhe()
            return

        for receita in receitas:
            self._item_lista(receita)

        alvo = None
        if manter_selecao and self.receita:
            alvo = next((r for r in receitas if r["id"] == self.receita["id"]), None)
        self._selecionar(alvo or receitas[0])

    def _lista_vazia(self):
        caixa = ctk.CTkFrame(self.lista, fg_color="transparent")
        caixa.pack(expand=True, pady=40)
        ctk.CTkLabel(caixa, text=Icone.CHECKLIST, font=Fontes.icone(26),
                     text_color=Cores.TEXTO_APAGADO).pack()
        ctk.CTkLabel(caixa, text="Nenhuma receita", font=Fontes.corpo_forte(),
                     text_color=Cores.TEXTO_SECUNDARIO).pack(pady=(Espaco.SM, 2))
        ctk.CTkLabel(caixa, text="Monte uma ficha tecnica\npara poder precificar.",
                     font=Fontes.pequeno(), text_color=Cores.TEXTO_APAGADO,
                     justify="center").pack()

    def _item_lista(self, receita):
        selecionada = self.receita and self.receita["id"] == receita["id"]
        fundo = Cores.LARANJA_SUAVE if selecionada else "transparent"

        item = ctk.CTkFrame(self.lista, fg_color=fundo, corner_radius=Raio.PEQUENO,
                            height=52)
        item.pack(fill="x", padx=Espaco.SM, pady=1)
        item.pack_propagate(False)

        interno = ctk.CTkFrame(item, fg_color="transparent")
        interno.pack(fill="both", expand=True, padx=Espaco.SM, pady=6)

        topo = ctk.CTkFrame(interno, fg_color="transparent")
        topo.pack(fill="x")
        nome = ctk.CTkLabel(topo, text=receita["nome"],
                            font=Fontes.corpo_forte() if selecionada else Fontes.corpo(),
                            text_color=Cores.TEXTO, anchor="w")
        nome.pack(side="left")

        if receita["canais_precificados"]:
            ctk.CTkLabel(topo, text=Icone.OK, font=Fontes.icone(11),
                         text_color=Cores.VERDE).pack(side="right")

        apoio = ctk.CTkLabel(interno,
                             text=f"{receita.get('categoria') or 'Sem categoria'}"
                                  f"  ·  {formatar_moeda(receita['custo_unitario'])}",
                             font=Fontes.micro(),
                             text_color=Cores.TEXTO_SECUNDARIO, anchor="w")
        apoio.pack(fill="x")

        for widget in (item, interno, topo, nome, apoio):
            widget.configure(cursor="hand2")
            widget.bind("<Button-1>", lambda _e, r=receita: self._ao_clicar(r))
            if not selecionada:
                widget.bind("<Enter>", lambda _e, i=item: i.configure(
                    fg_color=Cores.CARD_HOVER), add="+")
                widget.bind("<Leave>", lambda _e, i=item: i.configure(
                    fg_color="transparent"), add="+")

    def _ao_clicar(self, receita):
        self.receita = receita
        self.recarregar(manter_selecao=True)

    def _selecionar(self, receita):
        self.receita = receita

        # redesenha a lista para refletir a selecao
        for widget in self.lista.winfo_children():
            widget.destroy()
        for item in ctrl.receitas(self.busca):
            self._item_lista(item)

        self.titulo.configure(text=receita["nome"])
        self.subtitulo.configure(
            text=f"{receita.get('categoria') or 'Sem categoria'}  ·  "
                 f"rende {receita['rendimento']:g} {receita['unidade_rend'].lower()}")
        self.custo.configure(text=formatar_moeda(receita["custo_unitario"]))

        # carrega parametros ja gravados desta receita
        salvos = ctrl.gravadas(receita["id"])
        if salvos:
            primeiro = next(iter(salvos.values()))
            self.campo_margem.set(f"{primeiro['margem_pct']:g}")
            self.campo_imposto.set(f"{primeiro['imposto_pct']:g}")
            self.campo_custo_fixo.set(f"{primeiro['custo_fixo_pct']:g}")
            self.campo_custo_rs.set(f"{primeiro['custo_fixo_rs']:g}")

        self._recalcular()

    def _limpar_detalhe(self):
        self.receita = None
        self.titulo.configure(text="Selecione um produto")
        self.subtitulo.configure(text="A ficha tecnica define o custo")
        self.custo.configure(text="--")
        for widget in self.canais.winfo_children():
            widget.destroy()

    # -- calculo -----------------------------------------------------------

    def _trocar_arredondamento(self):
        self.arredondar = self.arredonda_var.get()
        self._recalcular()

    def _recalcular(self):
        if not self.receita:
            return

        try:
            margem, imposto, custo_fixo = ctrl.validar_parametros(
                self.campo_margem.get(), self.campo_imposto.get(),
                self.campo_custo_fixo.get())
            custo_rs = float((self.campo_custo_rs.get() or "0").replace(",", ".") or 0)
        except Exception as erro:
            self.aviso.configure(text=str(erro), text_color=Cores.PREJUIZO)
            return

        self.aviso.configure(text="", text_color=Cores.TEXTO_SECUNDARIO)

        salvos = ctrl.gravadas(self.receita["id"])
        praticados = {cid: linha["preco_praticado"]
                      for cid, linha in salvos.items() if linha["preco_praticado"]}

        self.dados = ctrl.calcular(
            self.receita["id"], margem, imposto, custo_fixo,
            custo_rs, self.arredondar, praticados)

        self._desenhar_canais()

    def _desenhar_canais(self):
        for widget in self.canais.winfo_children():
            widget.destroy()
        self.linhas = {}

        for indice, linha in enumerate(self.dados["linhas"]):
            self._linha_canal(indice, linha)

        self._atualizar_aviso()

    def _linha_canal(self, indice, linha):
        fundo = Cores.TABELA_LINHA if indice % 2 == 0 else Cores.TABELA_LINHA_ALT
        item = ctk.CTkFrame(self.canais, fg_color=fundo, corner_radius=0, height=54)
        item.pack(fill="x")
        item.pack_propagate(False)

        # canal + taxas
        celula = ctk.CTkFrame(item, fg_color="transparent", width=COL_CANAL)
        celula.pack(side="left", fill="y", padx=(Espaco.MD, 0))
        celula.pack_propagate(False)

        caixa = ctk.CTkFrame(celula, fg_color="transparent")
        caixa.pack(fill="both", expand=True, pady=9)

        cabeca = ctk.CTkFrame(caixa, fg_color="transparent")
        cabeca.pack(fill="x")
        ctk.CTkFrame(cabeca, fg_color=linha["cor"], width=3, height=14,
                     corner_radius=Raio.PILULA).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(cabeca, text=linha["canal"], font=Fontes.corpo(),
                     text_color=Cores.TEXTO, anchor="w").pack(side="left")

        taxas = []
        if linha["comissao_pct"]:
            taxas.append(f"comissao {formatar_pct(linha['comissao_pct'], 0)}")
        if linha["cartao_pct"]:
            taxas.append(f"cartao {formatar_pct(linha['cartao_pct'], 1)}")
        if linha["taxa_fixa"]:
            taxas.append(f"+{formatar_moeda(linha['taxa_fixa'])}")
        ctk.CTkLabel(caixa, text="  ·  ".join(taxas) or "sem taxas",
                     font=Fontes.micro(), text_color=Cores.TEXTO_APAGADO,
                     anchor="w").pack(fill="x", padx=(9, 0))

        if linha["impossivel"]:
            aviso = ctk.CTkFrame(item, fg_color="transparent")
            aviso.pack(side="left", fill="both", expand=True, padx=Espaco.MD)
            ctk.CTkLabel(aviso, text=linha["motivo"], font=Fontes.pequeno(),
                         text_color=Cores.PREJUIZO, anchor="w",
                         wraplength=430, justify="left").pack(fill="both", expand=True)
            return

        # sugerido e vitrine
        for valor, cor, fonte in (
            (linha["preco_sugerido"], Cores.TEXTO_SECUNDARIO, Fontes.numero()),
            (linha["preco_vitrine"], Cores.TEXTO, Fontes.numero_forte()),
        ):
            celula = ctk.CTkFrame(item, fg_color="transparent", width=COL_VALOR)
            celula.pack(side="left", fill="y", padx=(Espaco.MD, 0))
            celula.pack_propagate(False)
            ctk.CTkLabel(celula, text=formatar_moeda(valor), font=fonte,
                         text_color=cor, anchor="e").pack(fill="both", expand=True)

        # preco praticado (editavel)
        celula = ctk.CTkFrame(item, fg_color="transparent", width=COL_VALOR)
        celula.pack(side="left", fill="y", padx=(Espaco.MD, 0))
        celula.pack_propagate(False)

        variavel = ctk.StringVar(value=f"{linha['preco_praticado']:.2f}".replace(".", ","))
        entrada = ctk.CTkEntry(celula, textvariable=variavel, justify="right",
                               font=Fontes.numero(), height=30,
                               **{k: v for k, v in estilo_entrada().items()
                                  if k != "height"})
        entrada.pack(fill="x", pady=12)
        variavel.trace_add("write",
                           lambda *_, c=linha["canal_id"]: self._ao_mudar_preco(c))

        # lucro
        celula = ctk.CTkFrame(item, fg_color="transparent", width=COL_VALOR)
        celula.pack(side="left", fill="y", padx=(Espaco.MD, 0))
        celula.pack_propagate(False)
        lucro = ctk.CTkLabel(celula, text=formatar_moeda(linha["lucro"]),
                             font=Fontes.numero_forte(),
                             text_color=cor_margem(linha["margem_pct"]), anchor="e")
        lucro.pack(fill="both", expand=True)

        # margem + leitura
        celula = ctk.CTkFrame(item, fg_color="transparent", width=COL_MARGEM)
        celula.pack(side="left", fill="y", padx=(Espaco.MD, 0))
        celula.pack_propagate(False)
        caixa = ctk.CTkFrame(celula, fg_color="transparent")
        caixa.pack(fill="both", expand=True, pady=9)
        margem = ctk.CTkLabel(caixa, text=formatar_pct(linha["margem_pct"]),
                              font=Fontes.numero_forte(),
                              text_color=cor_margem(linha["margem_pct"]), anchor="e")
        margem.pack(fill="x")
        leitura = ctk.CTkLabel(caixa, text=rotulo_margem(linha["margem_pct"]),
                               font=Fontes.micro(),
                               text_color=Cores.TEXTO_APAGADO, anchor="e")
        leitura.pack(fill="x")

        self.linhas[linha["canal_id"]] = {
            "dados": linha, "variavel": variavel, "entrada": entrada,
            "lucro": lucro, "margem": margem, "leitura": leitura, "item": item,
        }

    def _ao_mudar_preco(self, canal_id):
        """Recalcula so a linha alterada, sem redesenhar a grade inteira."""
        registro = self.linhas.get(canal_id)
        if not registro:
            return

        bruto = registro["variavel"].get().replace("R$", "").strip()
        if "," in bruto:
            bruto = bruto.replace(".", "").replace(",", ".")
        try:
            preco = float(bruto)
        except ValueError:
            return
        if preco <= 0:
            return

        linha = registro["dados"]
        real = ctrl.simular(linha["custo"], self._canal_bruto(linha), preco,
                            *self._parametros_atuais())

        linha["preco_praticado"] = preco
        linha["lucro"] = real.lucro
        linha["margem_pct"] = real.margem_pct

        cor = cor_margem(real.margem_pct)
        registro["lucro"].configure(text=formatar_moeda(real.lucro), text_color=cor)
        registro["margem"].configure(text=formatar_pct(real.margem_pct), text_color=cor)
        registro["leitura"].configure(text=rotulo_margem(real.margem_pct))

        self._atualizar_aviso()

    @staticmethod
    def _canal_bruto(linha):
        return {
            "comissao_pct": linha["comissao_pct"],
            "cartao_pct": linha["cartao_pct"],
            "taxa_fixa": linha["taxa_fixa"],
        }

    def _parametros_atuais(self):
        imposto = float((self.campo_imposto.get() or "0").replace(",", ".") or 0)
        fixo_pct = float((self.campo_custo_fixo.get() or "0").replace(",", ".") or 0)
        fixo_rs = float((self.campo_custo_rs.get() or "0").replace(",", ".") or 0)
        return imposto, fixo_pct, fixo_rs

    def _atualizar_aviso(self):
        validas = [l for l in self.dados["linhas"] if not l["impossivel"]]
        if not validas:
            return

        prejuizo = [l for l in validas if l["margem_pct"] < 0]
        if prejuizo:
            nomes = ", ".join(l["canal"] for l in prejuizo[:2])
            self.aviso.configure(
                text=f"{Icone.ALERTA}  Prejuizo em {nomes}"
                     f"{' e outros' if len(prejuizo) > 2 else ''}.",
                text_color=Cores.PREJUIZO)
            return

        melhor = max(validas, key=lambda l: l["lucro"])
        pior = min(validas, key=lambda l: l["lucro"])
        diferenca = melhor["lucro"] - pior["lucro"]

        self.aviso.configure(
            text=f"Melhor canal: {melhor['canal']} ({formatar_moeda(melhor['lucro'])} "
                 f"por venda)  ·  diferenca de {formatar_moeda(diferenca)} "
                 f"para {pior['canal']}",
            text_color=Cores.TEXTO_SECUNDARIO)

    # -- gravacao ----------------------------------------------------------

    def _salvar(self):
        if not self.receita or not self.dados:
            return

        try:
            margem, imposto, custo_fixo = ctrl.validar_parametros(
                self.campo_margem.get(), self.campo_imposto.get(),
                self.campo_custo_fixo.get())
            custo_rs = float((self.campo_custo_rs.get() or "0").replace(",", ".") or 0)
        except Exception as erro:
            self.aviso.configure(text=str(erro), text_color=Cores.PREJUIZO)
            return

        ctrl.salvar(self.receita["id"], margem, imposto, custo_fixo,
                    custo_rs, self.dados["linhas"])

        self.recarregar(manter_selecao=True)
        notificar(self, f"Precificacao de '{self.receita['nome']}' salva "
                        f"em {len(self.dados['linhas'])} canais.", "sucesso")
