"""
LosPrice - Tela de Ingredientes
================================

O diferencial do sistema mora aqui: o usuario cadastra a COMPRA
(5 kg por R$ 185,00) e o LosPrice deriva o custo por grama em tempo real,
ja descontando a perda de limpeza e coccao.
"""

import customtkinter as ctk

from controllers import ingredientes as ctrl
from core.calculo import ErroCalculo, ROTULO_BASE, custo_unitario
from utils.componentes import (
    BarraBusca, BarraFerramentas, Botao, Cartao, Campo, CampoSelecao,
    Tabela, confirmar, linha_resumo, notificar, separador,
)
from utils.tema import (
    Cores, Espaco, Fontes, Icone, Raio, Tamanhos,
    estilo_card, formatar_moeda, formatar_moeda_precisa, formatar_pct,
)


# ---------------------------------------------------------------------------
# Tela
# ---------------------------------------------------------------------------


class TelaIngredientes(ctk.CTkFrame):
    def __init__(self, pai):
        super().__init__(pai, fg_color="transparent")

        self.busca = ""
        self.categoria = "Todas"

        self._montar_topo()
        self._montar_tabela()
        self.recarregar()

    # -- montagem ----------------------------------------------------------

    def _montar_topo(self):
        barra = BarraFerramentas(self)
        barra.pack(fill="x", pady=(0, Espaco.MD))

        BarraBusca(barra.esquerda, self._ao_buscar,
                   texto="Buscar por nome, marca ou categoria").pack(side="left")

        self.filtro = CampoSelecao(barra.esquerda, "", ["Todas"],
                                   largura=170, ao_mudar=self._ao_filtrar)
        self.filtro.pack(side="left", padx=(Espaco.SM, 0))

        Botao(barra.direita, "Novo ingrediente", icone=Icone.ADICIONAR,
              command=self._novo, width=190).pack(side="right")

        self.resumo = ctk.CTkLabel(barra.direita, text="", font=Fontes.pequeno(),
                                   text_color=Cores.TEXTO_SECUNDARIO)
        self.resumo.pack(side="right", padx=(0, Espaco.MD))

    def _montar_tabela(self):
        colunas = [
            {"chave": "nome", "titulo": "Ingrediente", "largura": 185,
             "fonte": Fontes.corpo_forte},
            {"chave": "categoria", "titulo": "Categoria", "largura": 125,
             "cor": lambda _l: Cores.TEXTO_SECUNDARIO},
            {"chave": "compra", "titulo": "Compra", "largura": 150,
             "cor": lambda _l: Cores.TEXTO_SECUNDARIO},
            {"chave": "fator_texto", "titulo": "Fator", "largura": 55,
             "alinhamento": "center", "cor": self._cor_fator},
            {"chave": "custo_texto", "titulo": "Custo real", "largura": 120,
             "alinhamento": "e", "fonte": Fontes.numero_forte,
             "cor": lambda _l: Cores.LARANJA},
            {"chave": "fornecedor_nome", "titulo": "Fornecedor", "largura": 145,
             "cor": lambda _l: Cores.TEXTO_SECUNDARIO},
        ]

        acoes = [
            {"icone": Icone.EDITAR, "comando": self._editar, "dica": "Editar"},
            {"icone": Icone.GRAFICO, "comando": self._ver_historico,
             "dica": "Historico de precos"},
            {"icone": Icone.EXCLUIR, "comando": self._excluir,
             "cor": Cores.PREJUIZO, "dica": "Excluir"},
        ]

        self.tabela = Tabela(
            self, colunas, ao_clicar=self._editar, acoes=acoes,
            vazio={
                "icone": Icone.CARRINHO,
                "titulo": "Nenhum ingrediente cadastrado",
                "mensagem": "Comece cadastrando o que voce compra. "
                            "O LosPrice calcula o custo por grama sozinho.",
                "acao": {"texto": "Cadastrar o primeiro", "comando": self._novo},
            },
        )
        self.tabela.pack(fill="both", expand=True)

    @staticmethod
    def _cor_fator(linha):
        return Cores.ATENCAO if (linha.get("fator_correcao") or 1) > 1 else Cores.TEXTO_APAGADO

    # -- dados -------------------------------------------------------------

    def recarregar(self):
        registros = ctrl.listar(self.busca, self.categoria)

        for registro in registros:
            registro["compra"] = ctrl.descrever_compra(registro)
            fator = registro.get("fator_correcao") or 1.0
            registro["fator_texto"] = "--" if fator == 1 else f"{fator:.2f}".replace(".", ",")
            unidade = ROTULO_BASE.get(registro["unidade_base"], "")
            registro["custo_texto"] = (
                f"{formatar_moeda_precisa(registro['custo_unitario'])}/{unidade}"
            )
            registro["fornecedor_nome"] = registro.get("fornecedor_nome") or "--"
            registro["categoria"] = registro.get("categoria") or "--"

        self.tabela.preencher(registros)

        self.filtro.opcoes(["Todas"] + ctrl.categorias())

        stats = ctrl.estatisticas()
        texto = f"{stats['total']} ingredientes"
        if stats["com_fator"]:
            texto += f"  ·  {stats['com_fator']} com perda"
        self.resumo.configure(text=texto)

    def _ao_buscar(self, termo):
        self.busca = termo
        self.recarregar()

    def _ao_filtrar(self):
        self.categoria = self.filtro.get()
        self.recarregar()

    # -- acoes -------------------------------------------------------------

    def _novo(self):
        DialogoIngrediente(self, ao_salvar=self.recarregar)

    def _editar(self, linha):
        DialogoIngrediente(self, ingrediente=linha, ao_salvar=self.recarregar)

    def _ver_historico(self, linha):
        DialogoHistorico(self, linha)

    def _excluir(self, linha):
        usos = ctrl.receitas_afetadas(linha["id"])

        if usos:
            nomes = ", ".join(r["nome"] for r in usos[:3])
            extra = f" e mais {len(usos) - 3}" if len(usos) > 3 else ""
            mensagem = (
                f"'{linha['nome']}' e usado em {len(usos)} receita(s): {nomes}{extra}.\n\n"
                "Ele sera desativado em vez de apagado, para nao quebrar as fichas tecnicas."
            )
            texto_ok = "Desativar"
        else:
            mensagem = f"Excluir '{linha['nome']}' definitivamente?"
            texto_ok = "Excluir"

        if not confirmar(self, "Confirmar exclusao", mensagem, texto_ok, perigo=True):
            return

        resultado = ctrl.excluir(linha["id"])
        self.recarregar()
        notificar(
            self,
            f"'{linha['nome']}' foi {'excluido' if resultado['apagado'] else 'desativado'}.",
            "sucesso" if resultado["apagado"] else "aviso",
        )


# ---------------------------------------------------------------------------
# Formulario
# ---------------------------------------------------------------------------


class DialogoIngrediente(ctk.CTkToplevel):
    LARGURA, ALTURA = 800, 620

    def __init__(self, pai, ingrediente=None, ao_salvar=None):
        super().__init__(pai)

        self.pai = pai
        self.ingrediente = ingrediente
        self.ao_salvar = ao_salvar
        self.editando = ingrediente is not None

        self.title("")
        self.overrideredirect(True)
        self.configure(fg_color=Cores.FUNDO)
        self.transient(pai.winfo_toplevel())
        self.grab_set()

        self.mapa_fornecedores = {"Nenhum": None}
        for fid, nome in ctrl.fornecedores():
            self.mapa_fornecedores[nome] = fid

        self._montar()
        if self.editando:
            self._preencher()
        self._calcular()

        self.bind("<Escape>", lambda _: self.destroy())
        self.bind("<Return>", lambda _: self._salvar())

        self._dimensionar()
        self.campo_nome.focar()

    def _dimensionar(self):
        """
        Mede o conteudo em vez de assumir uma altura fixa: assim o rodape
        nunca fica cortado quando o formulario cresce.
        """
        self.geometry(f"{self.LARGURA}x{self.ALTURA}")
        self.update_idletasks()

        altura = max(self.ALTURA, self.winfo_reqheight())
        altura = min(altura, int(self.winfo_screenheight() * 0.92))

        janela = self.pai.winfo_toplevel()
        x = janela.winfo_rootx() + (janela.winfo_width() - self.LARGURA) // 2
        y = janela.winfo_rooty() + (janela.winfo_height() - altura) // 2
        self.geometry(f"{self.LARGURA}x{altura}+{max(x, 0)}+{max(y, 0)}")

    # -- montagem ----------------------------------------------------------

    def _montar(self):
        moldura = ctk.CTkFrame(self, fg_color=Cores.CARD, corner_radius=Raio.GRANDE,
                               border_color=Cores.BORDA, border_width=1)
        moldura.pack(fill="both", expand=True)

        self._montar_cabecalho(moldura)

        corpo = ctk.CTkFrame(moldura, fg_color="transparent")
        corpo.pack(fill="both", expand=True, padx=Espaco.XL, pady=Espaco.LG)
        corpo.grid_columnconfigure(0, weight=3)
        corpo.grid_columnconfigure(1, weight=2)
        corpo.grid_rowconfigure(0, weight=1)

        self._montar_formulario(corpo)
        self._montar_painel(corpo)
        self._montar_rodape(moldura)

    def _montar_cabecalho(self, pai):
        topo = ctk.CTkFrame(pai, fg_color="transparent")
        topo.pack(fill="x", padx=Espaco.XL, pady=(Espaco.LG, 0))

        texto = ctk.CTkFrame(topo, fg_color="transparent")
        texto.pack(side="left")
        ctk.CTkLabel(texto, text="Editar ingrediente" if self.editando else "Novo ingrediente",
                     font=Fontes.titulo(), text_color=Cores.TEXTO).pack(anchor="w")
        ctk.CTkLabel(texto, text="Informe a compra. O custo por unidade sai automatico.",
                     font=Fontes.pequeno(), text_color=Cores.TEXTO_SECUNDARIO).pack(anchor="w")

        ctk.CTkButton(topo, text=Icone.FECHAR, width=32, height=32,
                      font=Fontes.icone(13), fg_color="transparent",
                      hover_color=Cores.CARD_HOVER, text_color=Cores.TEXTO_SECUNDARIO,
                      command=self.destroy).pack(side="right")

        separador(pai).pack(fill="x", padx=Espaco.XL, pady=(Espaco.MD, 0))

    def _montar_formulario(self, pai):
        form = ctk.CTkFrame(pai, fg_color="transparent")
        form.grid(row=0, column=0, sticky="nsew", padx=(0, Espaco.LG))

        # identificacao
        self.campo_nome = Campo(form, "Nome do ingrediente", obrigatorio=True,
                                ajuda="Ex: Mussarela fatiada")
        self.campo_nome.pack(fill="x")

        linha = ctk.CTkFrame(form, fg_color="transparent")
        linha.pack(fill="x", pady=(Espaco.XS, 0))

        self.campo_categoria = CampoSelecao(
            linha, "Categoria", ctrl.CATEGORIAS_SUGERIDAS, valor="Outros", largura=150)
        self.campo_categoria.pack(side="left", fill="x", expand=True, padx=(0, Espaco.SM))

        self.campo_marca = Campo(linha, "Marca")
        self.campo_marca.pack(side="left", fill="x", expand=True)

        self.campo_fornecedor = CampoSelecao(
            form, "Fornecedor", list(self.mapa_fornecedores.keys()), valor="Nenhum")
        self.campo_fornecedor.pack(fill="x", pady=(Espaco.XS, 0))

        separador(form).pack(fill="x", pady=Espaco.MD)
        self._titulo_secao(form, "Como voce comprou", Icone.CARRINHO)

        compra = ctk.CTkFrame(form, fg_color="transparent")
        compra.pack(fill="x", pady=(Espaco.SM, 0))

        self.campo_qtd = Campo(compra, "Quantidade", obrigatorio=True,
                               ao_digitar=self._calcular, largura=100)
        self.campo_qtd.pack(side="left", padx=(0, Espaco.SM))

        self.campo_unidade = CampoSelecao(compra, "Unidade", ctrl.UNIDADES_COMPRA,
                                          valor="KG", largura=95, ao_mudar=self._calcular)
        self.campo_unidade.pack(side="left", padx=(0, Espaco.SM))

        self.campo_valor = Campo(compra, "Valor pago (R$)", obrigatorio=True,
                                 ao_digitar=self._calcular, largura=130)
        self.campo_valor.pack(side="left")

        separador(form).pack(fill="x", pady=Espaco.MD)
        self._titulo_secao(form, "Aproveitamento", Icone.ALERTA)

        ctk.CTkLabel(
            form,
            text="Perdeu peso na limpeza ou no cozimento? Informe os pesos "
                 "e o fator entra sozinho.",
            font=Fontes.micro(), text_color=Cores.TEXTO_APAGADO,
            justify="left", anchor="w", wraplength=400,
        ).pack(fill="x", pady=(Espaco.SM, Espaco.XS))

        perda = ctk.CTkFrame(form, fg_color="transparent")
        perda.pack(fill="x")

        self.campo_bruto = Campo(perda, "Peso bruto", ao_digitar=self._calcular_fator,
                                 largura=100, ajuda="Ex: 1000 g")
        self.campo_bruto.pack(side="left", padx=(0, Espaco.SM))

        self.campo_liquido = Campo(perda, "Peso limpo", ao_digitar=self._calcular_fator,
                                   largura=100, ajuda="Ex: 700 g")
        self.campo_liquido.pack(side="left", padx=(0, Espaco.SM))

        self.campo_fator = Campo(perda, "Fator", valor="1,00",
                                 ao_digitar=self._calcular, largura=90,
                                 ajuda="1,00 = sem perda")
        self.campo_fator.pack(side="left")

    def _titulo_secao(self, pai, texto, icone):
        caixa = ctk.CTkFrame(pai, fg_color="transparent")
        caixa.pack(fill="x", pady=(Espaco.SM, 0))
        ctk.CTkLabel(caixa, text=icone, font=Fontes.icone(12),
                     text_color=Cores.LARANJA).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(caixa, text=texto.upper(), font=Fontes.micro(),
                     text_color=Cores.TEXTO_APAGADO).pack(side="left")

    def _montar_painel(self, pai):
        """Painel de resultado, atualizado a cada tecla."""
        painel = ctk.CTkFrame(pai, fg_color=Cores.SUPERFICIE,
                              corner_radius=Raio.GRANDE,
                              border_color=Cores.BORDA, border_width=1)
        painel.grid(row=0, column=1, sticky="nsew")

        interno = ctk.CTkFrame(painel, fg_color="transparent")
        interno.pack(fill="both", expand=True, padx=Espaco.LG, pady=Espaco.LG)

        ctk.CTkLabel(interno, text="CUSTO CALCULADO", font=Fontes.micro(),
                     text_color=Cores.TEXTO_APAGADO).pack(anchor="w")

        self.destaque = ctk.CTkLabel(interno, text="--", font=Fontes.display(),
                                     text_color=Cores.LARANJA)
        self.destaque.pack(anchor="w", pady=(Espaco.SM, 0))

        self.destaque_unidade = ctk.CTkLabel(interno, text="", font=Fontes.corpo(),
                                             text_color=Cores.TEXTO_SECUNDARIO)
        self.destaque_unidade.pack(anchor="w")

        separador(interno).pack(fill="x", pady=Espaco.MD)

        self.valor_sem_perda = linha_resumo(interno, "Custo da nota", "--")
        self.valor_perda = linha_resumo(interno, "Perda estimada", "--")
        separador(interno).pack(fill="x", pady=Espaco.SM)
        self.valor_final = linha_resumo(interno, "Custo real", "--", forte=True,
                                        cor=Cores.LARANJA)

        separador(interno).pack(fill="x", pady=Espaco.MD)

        ctk.CTkLabel(interno, text="EQUIVALENCIAS", font=Fontes.micro(),
                     text_color=Cores.TEXTO_APAGADO).pack(anchor="w", pady=(0, Espaco.SM))
        self.equivalencias = ctk.CTkFrame(interno, fg_color="transparent")
        self.equivalencias.pack(fill="x")

        self.aviso = ctk.CTkLabel(interno, text="", font=Fontes.micro(),
                                  text_color=Cores.ATENCAO, wraplength=240,
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
        Botao(rodape, "Salvar" if self.editando else "Cadastrar",
              icone=Icone.SALVAR, variante="sucesso", width=160,
              command=self._salvar).pack(side="right")

    # -- calculo ao vivo ---------------------------------------------------

    def _numero(self, texto, padrao=None):
        limpo = (texto or "").replace("R$", "").strip().replace(" ", "")
        if not limpo:
            return padrao
        if "," in limpo:
            limpo = limpo.replace(".", "").replace(",", ".")
        try:
            return float(limpo)
        except ValueError:
            return None

    def _calcular_fator(self):
        bruto = self._numero(self.campo_bruto.get())
        liquido = self._numero(self.campo_liquido.get())
        if bruto and liquido and 0 < liquido <= bruto:
            self.campo_fator.set(f"{bruto / liquido:.2f}".replace(".", ","))
        self._calcular()

    def _calcular(self):
        qtd = self._numero(self.campo_qtd.get())
        valor = self._numero(self.campo_valor.get())
        fator = self._numero(self.campo_fator.get(), 1.0) or 1.0
        unidade = self.campo_unidade.get()

        for widget in self.equivalencias.winfo_children():
            widget.destroy()

        if not qtd or qtd <= 0 or valor is None or valor < 0:
            self.destaque.configure(text="--")
            self.destaque_unidade.configure(text="Preencha quantidade e valor")
            for alvo in (self.valor_sem_perda, self.valor_perda, self.valor_final):
                alvo.configure(text="--")
            self.aviso.configure(text="")
            return

        try:
            bruto, base = custo_unitario(qtd, unidade, valor, 1.0)
            real, _ = custo_unitario(qtd, unidade, valor, fator)
        except ErroCalculo as erro:
            self.destaque.configure(text="--")
            self.destaque_unidade.configure(text=str(erro))
            return

        rotulo = ROTULO_BASE.get(base, base)
        self.destaque.configure(text=formatar_moeda_precisa(real))
        self.destaque_unidade.configure(text=f"por {rotulo}")

        self.valor_sem_perda.configure(text=f"{formatar_moeda_precisa(bruto)}/{rotulo}")
        self.valor_final.configure(text=f"{formatar_moeda_precisa(real)}/{rotulo}")

        if fator > 1:
            perda_pct = (1 - 1 / fator) * 100
            self.valor_perda.configure(text=formatar_pct(perda_pct),
                                       text_color=Cores.ATENCAO)
            self.aviso.configure(
                text=f"Com fator {fator:.2f}, o custo real fica "
                     f"{formatar_pct((real / bruto - 1) * 100)} acima da nota."
            )
        else:
            self.valor_perda.configure(text="Sem perda", text_color=Cores.TEXTO_SECUNDARIO)
            self.aviso.configure(text="")

        self._montar_equivalencias(real, base)

    def _montar_equivalencias(self, custo, base):
        if base == "G":
            escalas = [("100 g", 100), ("500 g", 500), ("1 kg", 1000)]
        elif base == "ML":
            escalas = [("100 ml", 100), ("500 ml", 500), ("1 L", 1000)]
        else:
            escalas = [("1 un", 1), ("10 un", 10), ("1 duzia", 12)]

        for rotulo, fator in escalas:
            linha = ctk.CTkFrame(self.equivalencias, fg_color="transparent")
            linha.pack(fill="x", pady=1)
            ctk.CTkLabel(linha, text=rotulo, font=Fontes.pequeno(),
                         text_color=Cores.TEXTO_SECUNDARIO).pack(side="left")
            ctk.CTkLabel(linha, text=formatar_moeda(custo * fator),
                         font=Fontes.numero(), text_color=Cores.TEXTO).pack(side="right")

    # -- persistencia ------------------------------------------------------

    def _preencher(self):
        ing = self.ingrediente
        self.campo_nome.set(ing["nome"])
        self.campo_marca.set(ing.get("marca") or "")
        categoria = ing.get("categoria")
        if categoria and categoria != "--":
            if categoria not in ctrl.CATEGORIAS_SUGERIDAS:
                self.campo_categoria.opcoes(ctrl.CATEGORIAS_SUGERIDAS + [categoria])
            self.campo_categoria.set(categoria)
        self.campo_qtd.set(f"{ing['qtd_comprada']:g}".replace(".", ","))
        self.campo_unidade.set(ing["unidade_compra"])
        self.campo_valor.set(f"{ing['valor_pago']:.2f}".replace(".", ","))
        self.campo_fator.set(f"{ing['fator_correcao']:.2f}".replace(".", ","))

        for nome, fid in self.mapa_fornecedores.items():
            if fid == ing.get("fornecedor_id"):
                self.campo_fornecedor.set(nome)
                break

    def _salvar(self):
        self.erro.configure(text="")
        for campo in (self.campo_nome, self.campo_qtd, self.campo_valor):
            campo.limpar_erro()

        dados = {
            "nome": self.campo_nome.get(),
            "categoria": self.campo_categoria.get(),
            "marca": self.campo_marca.get(),
            "qtd_comprada": self.campo_qtd.get(),
            "unidade_compra": self.campo_unidade.get(),
            "valor_pago": self.campo_valor.get(),
            "fator_correcao": self.campo_fator.get() or "1",
            "fornecedor_id": self.mapa_fornecedores.get(self.campo_fornecedor.get()),
        }

        try:
            if self.editando:
                resultado = ctrl.atualizar(self.ingrediente["id"], dados)
                mensagem = f"'{dados['nome']}' atualizado."
                tipo = "sucesso"

                if resultado["mudou_preco"] and resultado["variacao_pct"] is not None:
                    variacao = resultado["variacao_pct"]
                    direcao = "subiu" if variacao > 0 else "caiu"
                    mensagem = f"'{dados['nome']}': o custo {direcao} {formatar_pct(abs(variacao))}."
                    afetadas = resultado["receitas_afetadas"]
                    if afetadas:
                        mensagem += f" {len(afetadas)} receita(s) precisam ser recalculadas."
                        tipo = "aviso"
            else:
                ctrl.criar(dados)
                mensagem = f"'{dados['nome']}' cadastrado."
                tipo = "sucesso"
        except ctrl.ErroValidacao as erro:
            self.erro.configure(text=str(erro))
            self._marcar_campo(str(erro))
            return

        destino = self.pai
        self.destroy()
        if self.ao_salvar:
            self.ao_salvar()
        notificar(destino, mensagem, tipo)

    def _marcar_campo(self, mensagem):
        texto = mensagem.lower()
        if "nome" in texto:
            self.campo_nome.erro(mensagem)
            self.campo_nome.focar()
        elif "quantidade" in texto:
            self.campo_qtd.erro(mensagem)
            self.campo_qtd.focar()
        elif "valor" in texto:
            self.campo_valor.erro(mensagem)
            self.campo_valor.focar()
        elif "fator" in texto:
            self.campo_fator.erro(mensagem)
            self.campo_fator.focar()


# ---------------------------------------------------------------------------
# Historico de precos
# ---------------------------------------------------------------------------


class DialogoHistorico(ctk.CTkToplevel):
    LARGURA, ALTURA = 620, 520

    def __init__(self, pai, ingrediente):
        super().__init__(pai)
        self.pai = pai

        self.title("")
        self.overrideredirect(True)
        self.configure(fg_color=Cores.FUNDO)
        self.transient(pai.winfo_toplevel())
        self.grab_set()

        moldura = ctk.CTkFrame(self, fg_color=Cores.CARD, corner_radius=Raio.GRANDE,
                               border_color=Cores.BORDA, border_width=1)
        moldura.pack(fill="both", expand=True)

        topo = ctk.CTkFrame(moldura, fg_color="transparent")
        topo.pack(fill="x", padx=Espaco.XL, pady=(Espaco.LG, 0))

        texto = ctk.CTkFrame(topo, fg_color="transparent")
        texto.pack(side="left")
        ctk.CTkLabel(texto, text="Historico de precos", font=Fontes.titulo(),
                     text_color=Cores.TEXTO).pack(anchor="w")
        ctk.CTkLabel(texto, text=ingrediente["nome"], font=Fontes.pequeno(),
                     text_color=Cores.TEXTO_SECUNDARIO).pack(anchor="w")

        ctk.CTkButton(topo, text=Icone.FECHAR, width=32, height=32,
                      font=Fontes.icone(13), fg_color="transparent",
                      hover_color=Cores.CARD_HOVER, text_color=Cores.TEXTO_SECUNDARIO,
                      command=self.destroy).pack(side="right")

        separador(moldura).pack(fill="x", padx=Espaco.XL, pady=Espaco.MD)

        registros = ctrl.historico(ingrediente["id"])
        rotulo = ROTULO_BASE.get(ingrediente["unidade_base"], "")

        lista = ctk.CTkScrollableFrame(moldura, fg_color="transparent")
        lista.pack(fill="both", expand=True, padx=Espaco.XL)

        if len(registros) < 2:
            ctk.CTkLabel(lista, text=Icone.GRAFICO, font=Fontes.icone(30),
                         text_color=Cores.TEXTO_APAGADO).pack(pady=(60, Espaco.MD))
            ctk.CTkLabel(lista, text="Ainda sem variacao registrada",
                         font=Fontes.subtitulo(),
                         text_color=Cores.TEXTO_SECUNDARIO).pack()
            ctk.CTkLabel(lista, text="Cada vez que voce atualizar o preco de compra,\n"
                                     "o LosPrice registra aqui e mostra a variacao.",
                         font=Fontes.pequeno(), text_color=Cores.TEXTO_APAGADO,
                         justify="center").pack(pady=(4, 0))
        else:
            for i, registro in enumerate(registros):
                anterior = registros[i + 1] if i + 1 < len(registros) else None
                self._linha(lista, registro, anterior, rotulo)

        rodape = ctk.CTkFrame(moldura, fg_color="transparent")
        rodape.pack(fill="x", padx=Espaco.XL, pady=Espaco.LG)
        Botao(rodape, "Fechar", variante="secundario", width=120,
              command=self.destroy).pack(side="right")

        self.bind("<Escape>", lambda _: self.destroy())
        self.geometry(f"{self.LARGURA}x{self.ALTURA}")
        self.update_idletasks()

        janela = pai.winfo_toplevel()
        x = janela.winfo_rootx() + (janela.winfo_width() - self.LARGURA) // 2
        y = janela.winfo_rooty() + (janela.winfo_height() - self.ALTURA) // 2
        self.geometry(f"{self.LARGURA}x{self.ALTURA}+{x}+{max(y, 0)}")
        self.focus_force()

    def _linha(self, pai, registro, anterior, rotulo):
        from core.calculo import variacao_percentual

        item = ctk.CTkFrame(pai, **estilo_card())
        item.pack(fill="x", pady=3)

        interno = ctk.CTkFrame(item, fg_color="transparent")
        interno.pack(fill="x", padx=Espaco.MD, pady=Espaco.MD)

        esquerda = ctk.CTkFrame(interno, fg_color="transparent")
        esquerda.pack(side="left")
        ctk.CTkLabel(esquerda, text=registro["data_registro"][:16],
                     font=Fontes.pequeno(), text_color=Cores.TEXTO).pack(anchor="w")
        ctk.CTkLabel(
            esquerda,
            text=f"{registro['qtd_comprada']:g} {registro['unidade_compra'].lower()}"
                 f" · {formatar_moeda(registro['valor_pago'])}",
            font=Fontes.micro(), text_color=Cores.TEXTO_SECUNDARIO,
        ).pack(anchor="w")

        direita = ctk.CTkFrame(interno, fg_color="transparent")
        direita.pack(side="right")
        ctk.CTkLabel(direita,
                     text=f"{formatar_moeda_precisa(registro['custo_unitario'])}/{rotulo}",
                     font=Fontes.numero_forte(), text_color=Cores.TEXTO).pack(anchor="e")

        if anterior:
            variacao = variacao_percentual(anterior["custo_unitario"],
                                           registro["custo_unitario"])
            if variacao is not None and abs(variacao) > 0.01:
                subiu = variacao > 0
                ctk.CTkLabel(
                    direita,
                    text=f"{Icone.SETA_CIMA if subiu else Icone.SETA_BAIXO} "
                         f"{formatar_pct(abs(variacao))}",
                    font=Fontes.micro(),
                    text_color=Cores.PREJUIZO if subiu else Cores.LUCRO,
                ).pack(anchor="e")
