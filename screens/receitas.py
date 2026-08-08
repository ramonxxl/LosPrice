"""
LosPrice - Tela de Receitas (fichas tecnicas)
==============================================

Onde tudo se junta. O usuario monta a ficha linha a linha e ve o custo
se formar em tempo real, com a participacao de cada item.

A composicao e o que mais ensina: quando o dono descobre que a carne e
73% do custo do pastel, ele para de brigar com o preco da embalagem.
"""

import customtkinter as ctk

from controllers import receitas as ctrl
from core.calculo import ROTULO_BASE
from utils.componentes import (
    BarraBusca, BarraFerramentas, Botao, BotaoIcone, Campo, CampoSelecao,
    Tabela, confirmar, linha_resumo, notificar, separador,
)
from utils.tema import (
    Cores, Espaco, Fontes, Icone, Raio,
    estilo_card, formatar_moeda, formatar_pct, formatar_quantidade,
)


class TelaReceitas(ctk.CTkFrame):
    def __init__(self, pai):
        super().__init__(pai, fg_color="transparent")

        self.busca = ""
        self.categoria = "Todas"

        self._montar_topo()
        # height=0 e essencial: um CTkFrame vazio nasce com 200px reservados
        self.area_aviso = ctk.CTkFrame(self, fg_color="transparent", height=0)
        self.area_aviso.pack(fill="x")
        self._montar_tabela()
        self.recarregar()

    # -- montagem ----------------------------------------------------------

    def _montar_topo(self):
        barra = BarraFerramentas(self)
        barra.pack(fill="x", pady=(0, Espaco.MD))

        BarraBusca(barra.esquerda, self._ao_buscar,
                   texto="Buscar receita").pack(side="left")

        self.filtro = CampoSelecao(barra.esquerda, "", ["Todas"],
                                   largura=170, ao_mudar=self._ao_filtrar)
        self.filtro.pack(side="left", padx=(Espaco.SM, 0))

        Botao(barra.direita, "Nova receita", icone=Icone.ADICIONAR,
              command=self._nova, width=175).pack(side="right")

        self.resumo = ctk.CTkLabel(barra.direita, text="", font=Fontes.pequeno(),
                                   text_color=Cores.TEXTO_SECUNDARIO)
        self.resumo.pack(side="right", padx=(0, Espaco.MD))

    def _montar_tabela(self):
        colunas = [
            {"chave": "nome", "titulo": "Receita", "largura": 195,
             "fonte": Fontes.corpo_forte},
            {"chave": "categoria", "titulo": "Categoria", "largura": 100,
             "cor": lambda _l: Cores.TEXTO_SECUNDARIO},
            {"chave": "composicao", "titulo": "Ficha", "largura": 85,
             "cor": lambda _l: Cores.TEXTO_SECUNDARIO},
            {"chave": "rendimento_texto", "titulo": "Rende", "largura": 80,
             "cor": lambda _l: Cores.TEXTO_SECUNDARIO},
            {"chave": "custo_total", "titulo": "Custo do lote", "largura": 105,
             "alinhamento": "e", "formato": "moeda", "fonte": Fontes.numero,
             "cor": lambda _l: Cores.TEXTO_SECUNDARIO},
            {"chave": "custo_unitario", "titulo": "Custo por un", "largura": 105,
             "alinhamento": "e", "formato": "moeda", "fonte": Fontes.numero_forte,
             "cor": lambda _l: Cores.LARANJA},
            {"chave": "situacao", "titulo": "Situacao", "largura": 100,
             "cor": lambda l: Cores.ATENCAO if l.get("desatualizada") else Cores.LUCRO},
        ]

        acoes = [
            {"icone": Icone.EDITAR, "comando": self._editar, "dica": "Editar ficha"},
            {"icone": Icone.COPIAR, "comando": self._duplicar, "dica": "Duplicar"},
            {"icone": Icone.EXCLUIR, "comando": self._excluir,
             "cor": Cores.PREJUIZO, "dica": "Excluir"},
        ]

        self.tabela = Tabela(
            self, colunas, ao_clicar=self._editar, acoes=acoes,
            vazio={
                "icone": Icone.CHECKLIST,
                "titulo": "Nenhuma receita cadastrada",
                "mensagem": "Monte a ficha tecnica dos seus produtos e o "
                            "LosPrice calcula o custo exato de cada um.",
                "acao": {"texto": "Criar a primeira", "comando": self._nova},
            },
        )
        self.tabela.pack(fill="both", expand=True)

    # -- dados -------------------------------------------------------------

    def recarregar(self):
        registros = ctrl.listar(self.busca, self.categoria)

        for registro in registros:
            total = registro["qtd_ingredientes"] + registro["qtd_embalagens"]
            registro["composicao"] = f"{total} itens"
            registro["rendimento_texto"] = formatar_quantidade(
                registro["rendimento"], registro["unidade_rend"].lower())
            registro["categoria"] = registro.get("categoria") or "--"
            registro["situacao"] = ("Recalcular" if registro["desatualizada"]
                                    else "Atualizada")

        self.tabela.preencher(registros)
        self.filtro.opcoes(["Todas"] + ctrl.categorias())

        stats = ctrl.estatisticas()
        texto = f"{stats['total']} receitas"
        if stats["total"]:
            texto += f"  ·  custo medio {formatar_moeda(stats['custo_medio'])}"
        self.resumo.configure(text=texto)

        self._atualizar_aviso(stats["desatualizadas"])

    def _atualizar_aviso(self, quantidade):
        """Faixa de alerta quando algum insumo mudou de preco."""
        for widget in self.area_aviso.winfo_children():
            widget.destroy()

        if not quantidade:
            self.area_aviso.pack_configure(pady=0)
            return

        self.area_aviso.pack_configure(pady=(0, Espaco.MD))

        faixa = ctk.CTkFrame(self.area_aviso, fg_color=Cores.ATENCAO_SUAVE,
                             corner_radius=Raio.PADRAO,
                             border_color=Cores.ATENCAO, border_width=1)
        faixa.pack(fill="x")

        interno = ctk.CTkFrame(faixa, fg_color="transparent")
        interno.pack(fill="x", padx=Espaco.MD, pady=Espaco.SM)

        ctk.CTkLabel(interno, text=Icone.ALERTA, font=Fontes.icone(15),
                     text_color=Cores.ATENCAO).pack(side="left", padx=(0, Espaco.SM))

        plural = "ficha" if quantidade == 1 else "fichas"
        ctk.CTkLabel(
            interno,
            text=f"{quantidade} {plural} com custo defasado: algum insumo mudou de preco.",
            font=Fontes.corpo(), text_color=Cores.TEXTO,
        ).pack(side="left")

        Botao(interno, "Recalcular todas", icone=Icone.ATUALIZAR,
              variante="secundario", width=180, height=30,
              command=self._recalcular_todas).pack(side="right")

    def _recalcular_todas(self):
        quantidade = ctrl.recalcular_todas()
        self.recarregar()
        notificar(self, f"{quantidade} ficha(s) recalculada(s) com os precos de hoje.",
                  "sucesso")

    def _ao_buscar(self, termo):
        self.busca = termo
        self.recarregar()

    def _ao_filtrar(self):
        self.categoria = self.filtro.get()
        self.recarregar()

    # -- acoes -------------------------------------------------------------

    def _nova(self):
        DialogoReceita(self, ao_salvar=self.recarregar)

    def _editar(self, linha):
        DialogoReceita(self, receita_id=linha["id"], ao_salvar=self.recarregar)

    def _duplicar(self, linha):
        ctrl.duplicar(linha["id"])
        self.recarregar()
        notificar(self, f"'{linha['nome']}' duplicada.", "sucesso")

    def _excluir(self, linha):
        if not confirmar(self, "Confirmar exclusao",
                         f"Excluir a ficha tecnica de '{linha['nome']}'?",
                         "Excluir", perigo=True):
            return

        resultado = ctrl.excluir(linha["id"])
        self.recarregar()
        notificar(
            self,
            f"'{linha['nome']}' foi "
            f"{'excluida' if resultado['apagado'] else 'desativada (ja precificada)'}.",
            "sucesso" if resultado["apagado"] else "aviso",
        )


# ---------------------------------------------------------------------------
# Formulario da ficha tecnica
# ---------------------------------------------------------------------------


class DialogoReceita(ctk.CTkToplevel):
    LARGURA, ALTURA = 1080, 700

    def __init__(self, pai, receita_id=None, ao_salvar=None):
        super().__init__(pai)

        self.pai = pai
        self.receita_id = receita_id
        self.ao_salvar = ao_salvar
        self.editando = receita_id is not None
        self.itens = []

        self.title("")
        self.overrideredirect(True)
        self.configure(fg_color=Cores.FUNDO)
        self.transient(pai.winfo_toplevel())
        self.grab_set()

        self.ingredientes, self.embalagens = ctrl.disponiveis()
        self.mapa = {}

        self._montar()
        if self.editando:
            self._preencher()
        self._trocar_tipo("Ingrediente")
        self._atualizar_ficha()

        self.bind("<Escape>", lambda _: self.destroy())

        self._dimensionar()
        self.campo_nome.focar()

    def _dimensionar(self):
        self.geometry(f"{self.LARGURA}x{self.ALTURA}")
        self.update_idletasks()

        altura = min(max(self.ALTURA, self.winfo_reqheight()),
                     int(self.winfo_screenheight() * 0.92))
        largura = min(self.LARGURA, int(self.winfo_screenwidth() * 0.95))

        janela = self.pai.winfo_toplevel()
        x = janela.winfo_rootx() + (janela.winfo_width() - largura) // 2
        y = janela.winfo_rooty() + (janela.winfo_height() - altura) // 2
        self.geometry(f"{largura}x{altura}+{max(x, 0)}+{max(y, 0)}")

    # -- montagem ----------------------------------------------------------

    def _montar(self):
        moldura = ctk.CTkFrame(self, fg_color=Cores.CARD, corner_radius=Raio.GRANDE,
                               border_color=Cores.BORDA, border_width=1)
        moldura.pack(fill="both", expand=True)

        self._montar_cabecalho(moldura)

        corpo = ctk.CTkFrame(moldura, fg_color="transparent")
        corpo.pack(fill="both", expand=True, padx=Espaco.XL, pady=Espaco.MD)
        corpo.grid_columnconfigure(0, weight=3)
        corpo.grid_columnconfigure(1, weight=2)
        corpo.grid_rowconfigure(0, weight=1)

        self._montar_ficha(corpo)
        self._montar_painel(corpo)
        self._montar_rodape(moldura)

    def _montar_cabecalho(self, pai):
        topo = ctk.CTkFrame(pai, fg_color="transparent")
        topo.pack(fill="x", padx=Espaco.XL, pady=(Espaco.LG, 0))

        texto = ctk.CTkFrame(topo, fg_color="transparent")
        texto.pack(side="left")
        ctk.CTkLabel(texto, text="Editar ficha tecnica" if self.editando
                                 else "Nova ficha tecnica",
                     font=Fontes.titulo(), text_color=Cores.TEXTO).pack(anchor="w")
        ctk.CTkLabel(texto, text="Monte o produto e veja o custo se formar.",
                     font=Fontes.pequeno(),
                     text_color=Cores.TEXTO_SECUNDARIO).pack(anchor="w")

        ctk.CTkButton(topo, text=Icone.FECHAR, width=32, height=32,
                      font=Fontes.icone(13), fg_color="transparent",
                      hover_color=Cores.CARD_HOVER, text_color=Cores.TEXTO_SECUNDARIO,
                      command=self.destroy).pack(side="right")

        # identificacao
        dados = ctk.CTkFrame(pai, fg_color="transparent")
        dados.pack(fill="x", padx=Espaco.XL, pady=(Espaco.MD, 0))

        self.campo_nome = Campo(dados, "Nome do produto", obrigatorio=True,
                                largura=280, ajuda="Ex: Pastel de Carne")
        self.campo_nome.pack(side="left", padx=(0, Espaco.SM))

        self.campo_categoria = CampoSelecao(dados, "Categoria", ctrl.CATEGORIAS,
                                            valor="Pastel", largura=140)
        self.campo_categoria.pack(side="left", padx=(0, Espaco.SM))

        self.campo_rendimento = Campo(dados, "Rendimento", valor="1",
                                      ao_digitar=self._atualizar_ficha, largura=90,
                                      ajuda="Quanto o lote produz")
        self.campo_rendimento.pack(side="left", padx=(0, Espaco.SM))

        self.campo_unidade_rend = CampoSelecao(dados, "Unidade",
                                               ctrl.UNIDADES_RENDIMENTO,
                                               valor="UN", largura=110)
        self.campo_unidade_rend.pack(side="left", padx=(0, Espaco.SM))

        self.campo_tempo = Campo(dados, "Preparo (min)", largura=100,
                                 ajuda="Opcional")
        self.campo_tempo.pack(side="left")

        separador(pai).pack(fill="x", padx=Espaco.XL, pady=(Espaco.MD, 0))

    def _montar_ficha(self, pai):
        area = ctk.CTkFrame(pai, fg_color="transparent")
        area.grid(row=0, column=0, sticky="nsew", padx=(0, Espaco.LG))

        # --- barra de adicionar -------------------------------------------
        adicionar = ctk.CTkFrame(area, fg_color=Cores.SUPERFICIE,
                                 corner_radius=Raio.PADRAO,
                                 border_color=Cores.BORDA, border_width=1)
        adicionar.pack(fill="x")

        interno = ctk.CTkFrame(adicionar, fg_color="transparent")
        interno.pack(fill="x", padx=Espaco.MD, pady=Espaco.MD)

        self.seletor_tipo = ctk.CTkSegmentedButton(
            interno, values=["Ingrediente", "Embalagem"],
            command=self._trocar_tipo, font=Fontes.pequeno(),
            selected_color=Cores.LARANJA, selected_hover_color=Cores.LARANJA_HOVER,
            unselected_color=Cores.ENTRADA, unselected_hover_color=Cores.CARD_HOVER,
            fg_color=Cores.ENTRADA, text_color=Cores.TEXTO, height=30,
        )
        self.seletor_tipo.set("Ingrediente")
        self.seletor_tipo.pack(fill="x", pady=(0, Espaco.SM))

        linha = ctk.CTkFrame(interno, fg_color="transparent")
        linha.pack(fill="x")

        self.campo_item = CampoSelecao(linha, "", ["Nenhum item cadastrado"],
                                       largura=250, ao_mudar=self._ao_trocar_item)
        self.campo_item.pack(side="left", fill="x", expand=True, padx=(0, Espaco.SM))

        self.campo_qtd = Campo(linha, "", valor="", largura=70)
        self.campo_qtd.pack(side="left", padx=(0, Espaco.SM))
        self.campo_qtd.entrada.configure(placeholder_text="Qtd")
        self.campo_qtd.entrada.bind("<Return>", lambda _: self._adicionar())

        self.campo_unidade = CampoSelecao(linha, "", ["G"], largura=75)
        self.campo_unidade.pack(side="left", padx=(0, Espaco.SM))

        Botao(linha, "", icone=Icone.ADICIONAR, width=42, height=38,
              command=self._adicionar).pack(side="left")

        # --- lista da ficha -----------------------------------------------
        cartao = ctk.CTkFrame(area, **estilo_card())
        cartao.pack(fill="both", expand=True, pady=(Espaco.MD, 0))

        cabecalho = ctk.CTkFrame(cartao, fg_color=Cores.TABELA_CABECALHO,
                                 corner_radius=0, height=32)
        cabecalho.pack(fill="x")
        cabecalho.pack_propagate(False)
        for titulo, largura, alinhamento in (
            ("ITEM", 190, "w"), ("QTD", 80, "e"),
            ("CUSTO", 90, "e"), ("PESO", 60, "e"), ("", 34, "w"),
        ):
            celula = ctk.CTkFrame(cabecalho, fg_color="transparent", width=largura)
            celula.pack(side="left", fill="y", padx=(Espaco.SM, 0))
            celula.pack_propagate(False)
            ctk.CTkLabel(celula, text=titulo, font=Fontes.micro(),
                         text_color=Cores.TEXTO_APAGADO,
                         anchor=alinhamento).pack(fill="both", expand=True)

        separador(cartao).pack(fill="x")

        self.lista = ctk.CTkScrollableFrame(cartao, fg_color="transparent")
        self.lista.pack(fill="both", expand=True)

    def _montar_painel(self, pai):
        painel = ctk.CTkFrame(pai, fg_color=Cores.SUPERFICIE,
                              corner_radius=Raio.GRANDE,
                              border_color=Cores.BORDA, border_width=1)
        painel.grid(row=0, column=1, sticky="nsew")

        interno = ctk.CTkFrame(painel, fg_color="transparent")
        interno.pack(fill="both", expand=True, padx=Espaco.LG, pady=Espaco.LG)

        ctk.CTkLabel(interno, text="CUSTO POR UNIDADE", font=Fontes.micro(),
                     text_color=Cores.TEXTO_APAGADO).pack(anchor="w")

        self.destaque = ctk.CTkLabel(interno, text="R$ 0,00", font=Fontes.display(),
                                     text_color=Cores.LARANJA)
        self.destaque.pack(anchor="w", pady=(Espaco.SM, 0))

        self.destaque_apoio = ctk.CTkLabel(interno, text="", font=Fontes.corpo(),
                                           text_color=Cores.TEXTO_SECUNDARIO)
        self.destaque_apoio.pack(anchor="w")

        separador(interno).pack(fill="x", pady=Espaco.MD)

        self.valor_ingredientes = linha_resumo(interno, "Ingredientes", "R$ 0,00")
        self.valor_embalagens = linha_resumo(interno, "Embalagens", "R$ 0,00")
        separador(interno).pack(fill="x", pady=Espaco.SM)
        self.valor_lote = linha_resumo(interno, "Custo do lote", "R$ 0,00",
                                       forte=True, cor=Cores.TEXTO)

        separador(interno).pack(fill="x", pady=Espaco.MD)

        ctk.CTkLabel(interno, text="COMPOSICAO DO CUSTO", font=Fontes.micro(),
                     text_color=Cores.TEXTO_APAGADO).pack(anchor="w",
                                                          pady=(0, Espaco.SM))
        self.composicao = ctk.CTkFrame(interno, fg_color="transparent")
        self.composicao.pack(fill="both", expand=True)

        self.aviso = ctk.CTkLabel(interno, text="", font=Fontes.micro(),
                                  text_color=Cores.ATENCAO, wraplength=250,
                                  justify="left", anchor="w")
        self.aviso.pack(fill="x", side="bottom")

    def _montar_rodape(self, pai):
        separador(pai).pack(fill="x", padx=Espaco.XL)

        rodape = ctk.CTkFrame(pai, fg_color="transparent")
        rodape.pack(fill="x", padx=Espaco.XL, pady=Espaco.LG)

        self.erro = ctk.CTkLabel(rodape, text="", font=Fontes.pequeno(),
                                 text_color=Cores.PREJUIZO, anchor="w")
        self.erro.pack(side="left", fill="x", expand=True)

        Botao(rodape, "Cancelar", variante="secundario", width=120,
              command=self.destroy).pack(side="right", padx=(Espaco.SM, 0))
        Botao(rodape, "Salvar ficha" if self.editando else "Criar ficha",
              icone=Icone.SALVAR, variante="sucesso", width=170,
              command=self._salvar).pack(side="right")

    # -- seletor de item ---------------------------------------------------

    def _trocar_tipo(self, tipo):
        origem = self.ingredientes if tipo == "Ingrediente" else self.embalagens
        self.mapa = {item["nome"]: item for item in origem}

        if not origem:
            self.campo_item.opcoes([f"Nenhuma {tipo.lower()} cadastrada"], manter=False)
            self.campo_unidade.opcoes(["UN"], manter=False)
            return

        self.campo_item.opcoes([item["nome"] for item in origem], manter=False)
        self._ao_trocar_item()

    def _ao_trocar_item(self):
        item = self.mapa.get(self.campo_item.get())
        if not item:
            return
        unidades = ctrl.unidades_para(item.get("unidade_base", "UN"))
        self.campo_unidade.opcoes(unidades, manter=False)

    def _adicionar(self):
        item = self.mapa.get(self.campo_item.get())
        if not item:
            self.erro.configure(text="Cadastre ingredientes antes de montar a ficha.")
            return

        quantidade = self._numero(self.campo_qtd.get())
        if not quantidade or quantidade <= 0:
            self.erro.configure(text="Informe a quantidade do item.")
            self.campo_qtd.focar()
            return

        self.erro.configure(text="")
        self.itens.append({
            "tipo": item["tipo"],
            "item_id": item["id"],
            "nome": item["nome"],
            "quantidade": quantidade,
            "unidade": self.campo_unidade.get(),
            "unidade_base": item.get("unidade_base", "UN"),
            "custo_unitario": item["custo_unitario"],
        })

        self.campo_qtd.set("")
        self.campo_qtd.focar()
        self._atualizar_ficha()

    def _remover(self, indice):
        del self.itens[indice]
        self._atualizar_ficha()

    @staticmethod
    def _numero(valor, padrao=None):
        limpo = (valor or "").replace("R$", "").strip().replace(" ", "")
        if not limpo:
            return padrao
        if "," in limpo:
            limpo = limpo.replace(".", "").replace(",", ".")
        try:
            return float(limpo)
        except ValueError:
            return None

    # -- calculo ao vivo ---------------------------------------------------

    def _atualizar_ficha(self):
        for widget in self.lista.winfo_children():
            widget.destroy()
        for widget in self.composicao.winfo_children():
            widget.destroy()

        rendimento = self._numero(self.campo_rendimento.get(), 1.0) or 1.0

        if not self.itens:
            self._ficha_vazia()
            self.destaque.configure(text="R$ 0,00")
            self.destaque_apoio.configure(text="Adicione itens a ficha")
            for alvo in (self.valor_ingredientes, self.valor_embalagens,
                         self.valor_lote):
                alvo.configure(text="R$ 0,00")
            self.aviso.configure(text="")
            return

        try:
            resultado = ctrl.calcular(self.itens, rendimento)
        except Exception as erro:
            self.erro.configure(text=str(erro))
            return

        for indice, (item, detalhe) in enumerate(
                zip(self._ordem_calculo(), self._detalhes_ordenados(resultado))):
            self._linha_item(indice, item, detalhe)

        self.destaque.configure(text=formatar_moeda(resultado.custo_unitario))
        unidade = self.campo_unidade_rend.get().lower()
        self.destaque_apoio.configure(
            text=f"por {unidade}" if rendimento == 1
                 else f"por {unidade} · lote de {rendimento:g}")

        self.valor_ingredientes.configure(
            text=formatar_moeda(resultado.custo_ingredientes))
        self.valor_embalagens.configure(
            text=formatar_moeda(resultado.custo_embalagens))
        self.valor_lote.configure(text=formatar_moeda(resultado.custo_total))

        self._montar_composicao(resultado)

        peso = resultado.peso_embalagem_pct
        if peso > 10:
            self.aviso.configure(
                text=f"A embalagem representa {formatar_pct(peso)} do custo. "
                     "Em produto barato isso pesa: vale rever o modelo."
            )
        else:
            self.aviso.configure(text="")

    def _ordem_calculo(self):
        """Mesma ordem que core.calculo usa: ingredientes, depois embalagens."""
        return ([i for i in self.itens if i["tipo"] == "ingrediente"]
                + [i for i in self.itens if i["tipo"] == "embalagem"])

    @staticmethod
    def _detalhes_ordenados(resultado):
        return ([d for d in resultado.detalhes if d["tipo"] == "ingrediente"]
                + [d for d in resultado.detalhes if d["tipo"] == "embalagem"])

    def _ficha_vazia(self):
        caixa = ctk.CTkFrame(self.lista, fg_color="transparent")
        caixa.pack(expand=True, pady=50)
        ctk.CTkLabel(caixa, text=Icone.CHECKLIST, font=Fontes.icone(28),
                     text_color=Cores.TEXTO_APAGADO).pack()
        ctk.CTkLabel(caixa, text="Ficha vazia", font=Fontes.subtitulo(),
                     text_color=Cores.TEXTO_SECUNDARIO).pack(pady=(Espaco.SM, 2))
        ctk.CTkLabel(caixa, text="Escolha um item acima e informe a quantidade.",
                     font=Fontes.pequeno(),
                     text_color=Cores.TEXTO_APAGADO).pack()

    def _linha_item(self, indice, item, detalhe):
        fundo = Cores.TABELA_LINHA if indice % 2 == 0 else Cores.TABELA_LINHA_ALT
        linha = ctk.CTkFrame(self.lista, fg_color=fundo, corner_radius=0, height=38)
        linha.pack(fill="x")
        linha.pack_propagate(False)

        # nome
        celula = ctk.CTkFrame(linha, fg_color="transparent", width=190)
        celula.pack(side="left", fill="y", padx=(Espaco.SM, 0))
        celula.pack_propagate(False)
        cor = (Cores.TEXTO_SECUNDARIO if item["tipo"] == "embalagem" else Cores.TEXTO)
        ctk.CTkLabel(celula, text=item["nome"], font=Fontes.corpo(),
                     text_color=cor, anchor="w").pack(fill="both", expand=True)

        # quantidade
        unidade = (item["unidade"].lower() if item["tipo"] == "ingrediente" else "un")
        for texto, largura, fonte, cor_texto in (
            (formatar_quantidade(item["quantidade"], unidade), 80,
             Fontes.numero(), Cores.TEXTO_SECUNDARIO),
            (formatar_moeda(detalhe["custo"]), 90,
             Fontes.numero(), Cores.TEXTO),
            (formatar_pct(detalhe["participacao_pct"], 0), 60,
             Fontes.numero(), self._cor_peso(detalhe["participacao_pct"])),
        ):
            celula = ctk.CTkFrame(linha, fg_color="transparent", width=largura)
            celula.pack(side="left", fill="y", padx=(Espaco.SM, 0))
            celula.pack_propagate(False)
            ctk.CTkLabel(celula, text=texto, font=fonte, text_color=cor_texto,
                         anchor="e").pack(fill="both", expand=True)

        # remover
        caixa = ctk.CTkFrame(linha, fg_color="transparent", width=34)
        caixa.pack(side="left", fill="y")
        caixa.pack_propagate(False)
        posicao = self.itens.index(item)
        BotaoIcone(caixa, Icone.EXCLUIR, comando=lambda p=posicao: self._remover(p),
                   cor=Cores.PREJUIZO, dica="Remover da ficha").pack(pady=5)

    @staticmethod
    def _cor_peso(pct):
        if pct >= 50:
            return Cores.LARANJA
        if pct >= 25:
            return Cores.TEXTO
        return Cores.TEXTO_SECUNDARIO

    def _montar_composicao(self, resultado):
        detalhes = sorted(resultado.detalhes, key=lambda d: d["custo"], reverse=True)

        for detalhe in detalhes[:6]:
            bloco = ctk.CTkFrame(self.composicao, fg_color="transparent")
            bloco.pack(fill="x", pady=(0, Espaco.SM))

            topo = ctk.CTkFrame(bloco, fg_color="transparent")
            topo.pack(fill="x")
            ctk.CTkLabel(topo, text=detalhe["nome"], font=Fontes.pequeno(),
                         text_color=Cores.TEXTO_SECUNDARIO, anchor="w").pack(side="left")
            ctk.CTkLabel(topo, text=formatar_pct(detalhe["participacao_pct"], 1),
                         font=Fontes.micro(),
                         text_color=Cores.TEXTO).pack(side="right")

            barra = ctk.CTkProgressBar(bloco, height=5, corner_radius=Raio.PILULA,
                                       fg_color=Cores.BORDA,
                                       progress_color=self._cor_peso(
                                           detalhe["participacao_pct"]))
            barra.pack(fill="x", pady=(3, 0))
            barra.set(min(detalhe["participacao_pct"] / 100.0, 1.0))

        if len(detalhes) > 6:
            ctk.CTkLabel(self.composicao,
                         text=f"+ {len(detalhes) - 6} itens menores",
                         font=Fontes.micro(),
                         text_color=Cores.TEXTO_APAGADO).pack(anchor="w")

    # -- persistencia ------------------------------------------------------

    def _preencher(self):
        receita = ctrl.obter(self.receita_id)
        if not receita:
            return

        self.campo_nome.set(receita["nome"])
        if receita.get("categoria"):
            if receita["categoria"] not in ctrl.CATEGORIAS:
                self.campo_categoria.opcoes(ctrl.CATEGORIAS + [receita["categoria"]])
            self.campo_categoria.set(receita["categoria"])
        self.campo_rendimento.set(f"{receita['rendimento']:g}")
        self.campo_unidade_rend.set(receita["unidade_rend"])
        self.campo_tempo.set(receita.get("tempo_preparo") or "")

        for item in receita["itens"]:
            self.itens.append({
                "tipo": item["tipo"],
                "item_id": item["item_id"],
                "nome": item["nome"],
                "quantidade": item["quantidade"],
                "unidade": item["unidade"],
                "unidade_base": item["unidade_base"],
                "custo_unitario": item["custo_unitario"],
            })

    def _salvar(self):
        self.erro.configure(text="")
        self.campo_nome.limpar_erro()

        dados = {
            "nome": self.campo_nome.get(),
            "categoria": self.campo_categoria.get(),
            "rendimento": self.campo_rendimento.get() or "1",
            "unidade_rend": self.campo_unidade_rend.get(),
            "tempo_preparo": self.campo_tempo.get(),
            "itens": self.itens,
        }

        try:
            if self.editando:
                ctrl.atualizar(self.receita_id, dados)
                mensagem = f"Ficha de '{dados['nome']}' atualizada."
            else:
                ctrl.criar(dados)
                mensagem = f"Ficha de '{dados['nome']}' criada."
        except ctrl.ErroValidacao as erro:
            self.erro.configure(text=str(erro))
            if "nome" in str(erro).lower():
                self.campo_nome.erro(str(erro))
                self.campo_nome.focar()
            return

        destino = self.pai
        self.destroy()
        if self.ao_salvar:
            self.ao_salvar()
        notificar(destino, mensagem, "sucesso")
