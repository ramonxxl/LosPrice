"""
LosPrice - Tela de Embalagens
==============================

Caixas, sacos, copos e descartaveis. Custo sempre por unidade.

Diferente dos ingredientes, aqui o problema tipico nao e o custo em si -
e o dono nao perceber que a embalagem come 15% do produto. Por isso o
painel mostra o peso da embalagem sobre faixas de custo de receita.
"""

import customtkinter as ctk

from controllers import embalagens as ctrl
from utils.componentes import (
    BarraBusca, BarraFerramentas, Botao, Campo, CampoSelecao,
    Tabela, confirmar, linha_resumo, notificar, separador,
)
from utils.tema import (
    Cores, Espaco, Fontes, Icone, Raio,
    formatar_moeda, formatar_pct,
)


class TelaEmbalagens(ctk.CTkFrame):
    def __init__(self, pai):
        super().__init__(pai, fg_color="transparent")

        self.busca = ""
        self.tipo = "Todos"

        self._montar_topo()
        self._montar_tabela()
        self.recarregar()

    # -- montagem ----------------------------------------------------------

    def _montar_topo(self):
        barra = BarraFerramentas(self)
        barra.pack(fill="x", pady=(0, Espaco.MD))

        BarraBusca(barra.esquerda, self._ao_buscar,
                   texto="Buscar embalagem").pack(side="left")

        self.filtro = CampoSelecao(barra.esquerda, "", ["Todos"],
                                   largura=170, ao_mudar=self._ao_filtrar)
        self.filtro.pack(side="left", padx=(Espaco.SM, 0))

        Botao(barra.direita, "Nova embalagem", icone=Icone.ADICIONAR,
              command=self._nova, width=190).pack(side="right")

        self.resumo = ctk.CTkLabel(barra.direita, text="", font=Fontes.pequeno(),
                                   text_color=Cores.TEXTO_SECUNDARIO)
        self.resumo.pack(side="right", padx=(0, Espaco.MD))

    def _montar_tabela(self):
        colunas = [
            {"chave": "nome", "titulo": "Embalagem", "largura": 230,
             "fonte": Fontes.corpo_forte},
            {"chave": "tipo", "titulo": "Tipo", "largura": 130,
             "cor": lambda _l: Cores.TEXTO_SECUNDARIO},
            {"chave": "compra", "titulo": "Compra", "largura": 170,
             "cor": lambda _l: Cores.TEXTO_SECUNDARIO},
            {"chave": "custo_unitario", "titulo": "Custo por un", "largura": 110,
             "alinhamento": "e", "formato": "moeda", "fonte": Fontes.numero_forte,
             "cor": lambda _l: Cores.LARANJA},
            {"chave": "fornecedor_nome", "titulo": "Fornecedor", "largura": 185,
             "cor": lambda _l: Cores.TEXTO_SECUNDARIO},
        ]

        acoes = [
            {"icone": Icone.EDITAR, "comando": self._editar, "dica": "Editar"},
            {"icone": Icone.EXCLUIR, "comando": self._excluir,
             "cor": Cores.PREJUIZO, "dica": "Excluir"},
        ]

        self.tabela = Tabela(
            self, colunas, ao_clicar=self._editar, acoes=acoes,
            vazio={
                "icone": Icone.CAIXA,
                "titulo": "Nenhuma embalagem cadastrada",
                "mensagem": "Caixa de pastel, saco de papel, copo, marmita. "
                            "Tudo que sai junto com o produto.",
                "acao": {"texto": "Cadastrar a primeira", "comando": self._nova},
            },
        )
        self.tabela.pack(fill="both", expand=True)

    # -- dados -------------------------------------------------------------

    def recarregar(self):
        registros = ctrl.listar(self.busca, self.tipo)
        for registro in registros:
            registro["compra"] = ctrl.descrever_compra(registro)
            registro["tipo"] = registro.get("tipo") or "--"
            registro["fornecedor_nome"] = registro.get("fornecedor_nome") or "--"

        self.tabela.preencher(registros)
        self.filtro.opcoes(["Todos"] + ctrl.tipos_em_uso())

        stats = ctrl.estatisticas()
        texto = f"{stats['total']} embalagens"
        if stats["total"]:
            texto += f"  ·  media {formatar_moeda(stats['media'])}"
        self.resumo.configure(text=texto)

    def _ao_buscar(self, termo):
        self.busca = termo
        self.recarregar()

    def _ao_filtrar(self):
        self.tipo = self.filtro.get()
        self.recarregar()

    # -- acoes -------------------------------------------------------------

    def _nova(self):
        DialogoEmbalagem(self, ao_salvar=self.recarregar)

    def _editar(self, linha):
        DialogoEmbalagem(self, embalagem=linha, ao_salvar=self.recarregar)

    def _excluir(self, linha):
        usos = ctrl.receitas_afetadas(linha["id"])

        if usos:
            nomes = ", ".join(r["nome"] for r in usos[:3])
            extra = f" e mais {len(usos) - 3}" if len(usos) > 3 else ""
            mensagem = (
                f"'{linha['nome']}' e usada em {len(usos)} receita(s): {nomes}{extra}.\n\n"
                "Sera desativada em vez de apagada, para nao quebrar as fichas tecnicas."
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
            f"'{linha['nome']}' foi {'excluida' if resultado['apagado'] else 'desativada'}.",
            "sucesso" if resultado["apagado"] else "aviso",
        )


# ---------------------------------------------------------------------------
# Formulario
# ---------------------------------------------------------------------------


class DialogoEmbalagem(ctk.CTkToplevel):
    LARGURA, ALTURA = 760, 480

    def __init__(self, pai, embalagem=None, ao_salvar=None):
        super().__init__(pai)

        self.pai = pai
        self.embalagem = embalagem
        self.ao_salvar = ao_salvar
        self.editando = embalagem is not None

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

        topo = ctk.CTkFrame(moldura, fg_color="transparent")
        topo.pack(fill="x", padx=Espaco.XL, pady=(Espaco.LG, 0))

        texto = ctk.CTkFrame(topo, fg_color="transparent")
        texto.pack(side="left")
        ctk.CTkLabel(texto, text="Editar embalagem" if self.editando else "Nova embalagem",
                     font=Fontes.titulo(), text_color=Cores.TEXTO).pack(anchor="w")
        ctk.CTkLabel(texto, text="Informe o pacote comprado. O custo por unidade sai sozinho.",
                     font=Fontes.pequeno(), text_color=Cores.TEXTO_SECUNDARIO).pack(anchor="w")

        ctk.CTkButton(topo, text=Icone.FECHAR, width=32, height=32,
                      font=Fontes.icone(13), fg_color="transparent",
                      hover_color=Cores.CARD_HOVER, text_color=Cores.TEXTO_SECUNDARIO,
                      command=self.destroy).pack(side="right")

        separador(moldura).pack(fill="x", padx=Espaco.XL, pady=(Espaco.MD, 0))

        corpo = ctk.CTkFrame(moldura, fg_color="transparent")
        corpo.pack(fill="both", expand=True, padx=Espaco.XL, pady=Espaco.LG)
        corpo.grid_columnconfigure(0, weight=3)
        corpo.grid_columnconfigure(1, weight=2)
        corpo.grid_rowconfigure(0, weight=1)

        self._montar_formulario(corpo)
        self._montar_painel(corpo)
        self._montar_rodape(moldura)

    def _montar_formulario(self, pai):
        form = ctk.CTkFrame(pai, fg_color="transparent")
        form.grid(row=0, column=0, sticky="nsew", padx=(0, Espaco.LG))

        self.campo_nome = Campo(form, "Nome da embalagem", obrigatorio=True,
                                ajuda="Ex: Caixa de pastel media")
        self.campo_nome.pack(fill="x")

        linha = ctk.CTkFrame(form, fg_color="transparent")
        linha.pack(fill="x", pady=(Espaco.XS, 0))

        self.campo_tipo = CampoSelecao(linha, "Tipo", ctrl.TIPOS,
                                       valor="Caixa", largura=150)
        self.campo_tipo.pack(side="left", fill="x", expand=True, padx=(0, Espaco.SM))

        self.campo_fornecedor = CampoSelecao(
            linha, "Fornecedor", list(self.mapa_fornecedores.keys()), valor="Nenhum")
        self.campo_fornecedor.pack(side="left", fill="x", expand=True)

        separador(form).pack(fill="x", pady=Espaco.MD)
        self._titulo_secao(form, "Como voce comprou", Icone.CAIXA)

        compra = ctk.CTkFrame(form, fg_color="transparent")
        compra.pack(fill="x", pady=(Espaco.SM, 0))

        self.campo_qtd = Campo(compra, "Quantidade (un)", obrigatorio=True,
                               ao_digitar=self._calcular, largura=140,
                               ajuda="Quantas unidades vieram")
        self.campo_qtd.pack(side="left", padx=(0, Espaco.SM))

        self.campo_valor = Campo(compra, "Valor pago (R$)", obrigatorio=True,
                                 ao_digitar=self._calcular, largura=140,
                                 ajuda="Total do pacote")
        self.campo_valor.pack(side="left")

        separador(form).pack(fill="x", pady=Espaco.MD)

        self.campo_obs = Campo(form, "Observacoes",
                               ajuda="Ex: modelo 18x18, so para pastel grande")
        self.campo_obs.pack(fill="x")

    def _titulo_secao(self, pai, texto, icone):
        caixa = ctk.CTkFrame(pai, fg_color="transparent")
        caixa.pack(fill="x", pady=(Espaco.SM, 0))
        ctk.CTkLabel(caixa, text=icone, font=Fontes.icone(12),
                     text_color=Cores.LARANJA).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(caixa, text=texto.upper(), font=Fontes.micro(),
                     text_color=Cores.TEXTO_APAGADO).pack(side="left")

    def _montar_painel(self, pai):
        painel = ctk.CTkFrame(pai, fg_color=Cores.SUPERFICIE,
                              corner_radius=Raio.GRANDE,
                              border_color=Cores.BORDA, border_width=1)
        painel.grid(row=0, column=1, sticky="nsew")

        interno = ctk.CTkFrame(painel, fg_color="transparent")
        interno.pack(fill="both", expand=True, padx=Espaco.LG, pady=Espaco.LG)

        ctk.CTkLabel(interno, text="CUSTO POR UNIDADE", font=Fontes.micro(),
                     text_color=Cores.TEXTO_APAGADO).pack(anchor="w")

        self.destaque = ctk.CTkLabel(interno, text="--", font=Fontes.display(),
                                     text_color=Cores.LARANJA)
        self.destaque.pack(anchor="w", pady=(Espaco.SM, 0))

        self.destaque_apoio = ctk.CTkLabel(interno, text="", font=Fontes.corpo(),
                                           text_color=Cores.TEXTO_SECUNDARIO)
        self.destaque_apoio.pack(anchor="w")

        separador(interno).pack(fill="x", pady=Espaco.MD)

        ctk.CTkLabel(interno, text="CUSTO EM LOTE", font=Fontes.micro(),
                     text_color=Cores.TEXTO_APAGADO).pack(anchor="w", pady=(0, Espaco.SM))
        self.lote_100 = linha_resumo(interno, "100 unidades", "--")
        self.lote_500 = linha_resumo(interno, "500 unidades", "--")
        self.lote_1000 = linha_resumo(interno, "1.000 unidades", "--")

        separador(interno).pack(fill="x", pady=Espaco.MD)

        ctk.CTkLabel(interno, text="PESO SOBRE O PRODUTO", font=Fontes.micro(),
                     text_color=Cores.TEXTO_APAGADO).pack(anchor="w")
        ctk.CTkLabel(interno, text="Quanto a embalagem representa do custo",
                     font=Fontes.micro(),
                     text_color=Cores.TEXTO_APAGADO).pack(anchor="w", pady=(0, Espaco.SM))

        self.peso = {}
        for referencia in (3.00, 8.00, 15.00):
            self.peso[referencia] = linha_resumo(
                interno, f"Receita de {formatar_moeda(referencia)}", "--")

        self.aviso = ctk.CTkLabel(interno, text="", font=Fontes.micro(),
                                  text_color=Cores.ATENCAO, wraplength=230,
                                  justify="left", anchor="w")
        self.aviso.pack(fill="x", pady=(Espaco.MD, 0))

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

    def _numero(self, valor, padrao=None):
        limpo = (valor or "").replace("R$", "").strip().replace(" ", "")
        if not limpo:
            return padrao
        if "," in limpo:
            limpo = limpo.replace(".", "").replace(",", ".")
        try:
            return float(limpo)
        except ValueError:
            return None

    def _calcular(self):
        qtd = self._numero(self.campo_qtd.get())
        valor = self._numero(self.campo_valor.get())

        if not qtd or qtd <= 0 or valor is None or valor < 0:
            self.destaque.configure(text="--")
            self.destaque_apoio.configure(text="Preencha quantidade e valor")
            for alvo in (self.lote_100, self.lote_500, self.lote_1000):
                alvo.configure(text="--")
            for alvo in self.peso.values():
                alvo.configure(text="--", text_color=Cores.TEXTO_SECUNDARIO)
            self.aviso.configure(text="")
            return

        unitario = valor / qtd

        self.destaque.configure(text=formatar_moeda(unitario))
        self.destaque_apoio.configure(text=f"cada uma, em {qtd:g} unidades")

        self.lote_100.configure(text=formatar_moeda(unitario * 100))
        self.lote_500.configure(text=formatar_moeda(unitario * 500))
        self.lote_1000.configure(text=formatar_moeda(unitario * 1000))

        pesado = False
        for referencia, rotulo in self.peso.items():
            pct, alerta = ctrl.peso_no_produto(unitario, referencia)
            rotulo.configure(
                text=formatar_pct(pct),
                text_color=Cores.ATENCAO if alerta else Cores.LUCRO,
            )
            pesado = pesado or alerta

        if pesado:
            self.aviso.configure(
                text=f"A {formatar_moeda(unitario)}, essa embalagem pesa mais de "
                     f"{ctrl.LIMITE_PESO_PCT:.0f}% em produtos baratos. "
                     "Vale negociar ou usar um modelo menor."
            )
        else:
            self.aviso.configure(text="")

    # -- persistencia ------------------------------------------------------

    def _preencher(self):
        emb = self.embalagem
        self.campo_nome.set(emb["nome"])
        tipo = emb.get("tipo")
        if tipo and tipo != "--":
            if tipo not in ctrl.TIPOS:
                self.campo_tipo.opcoes(ctrl.TIPOS + [tipo])
            self.campo_tipo.set(tipo)
        self.campo_qtd.set(f"{emb['qtd_comprada']:g}")
        self.campo_valor.set(f"{emb['valor_pago']:.2f}".replace(".", ","))
        self.campo_obs.set(emb.get("observacoes") or "")

        for nome, fid in self.mapa_fornecedores.items():
            if fid == emb.get("fornecedor_id"):
                self.campo_fornecedor.set(nome)
                break

    def _salvar(self):
        self.erro.configure(text="")
        for campo in (self.campo_nome, self.campo_qtd, self.campo_valor):
            campo.limpar_erro()

        dados = {
            "nome": self.campo_nome.get(),
            "tipo": self.campo_tipo.get(),
            "qtd_comprada": self.campo_qtd.get(),
            "valor_pago": self.campo_valor.get(),
            "observacoes": self.campo_obs.get(),
            "fornecedor_id": self.mapa_fornecedores.get(self.campo_fornecedor.get()),
        }

        try:
            if self.editando:
                resultado = ctrl.atualizar(self.embalagem["id"], dados)
                mensagem = f"'{dados['nome']}' atualizada."
                tipo = "sucesso"

                if resultado["mudou_preco"] and resultado["variacao_pct"] is not None:
                    variacao = resultado["variacao_pct"]
                    direcao = "subiu" if variacao > 0 else "caiu"
                    mensagem = (f"'{dados['nome']}': o custo {direcao} "
                                f"{formatar_pct(abs(variacao))}.")
                    afetadas = resultado["receitas_afetadas"]
                    if afetadas:
                        mensagem += f" {len(afetadas)} receita(s) precisam ser recalculadas."
                        tipo = "aviso"
            else:
                ctrl.criar(dados)
                mensagem = f"'{dados['nome']}' cadastrada."
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
        alvo = mensagem.lower()
        if "nome" in alvo:
            self.campo_nome.erro(mensagem)
            self.campo_nome.focar()
        elif "quantidade" in alvo:
            self.campo_qtd.erro(mensagem)
            self.campo_qtd.focar()
        elif "valor" in alvo:
            self.campo_valor.erro(mensagem)
            self.campo_valor.focar()
