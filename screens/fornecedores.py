"""
LosPrice - Tela de Fornecedores
================================

Cadastro de quem entrega cada insumo, com duas leituras uteis:
    - o que cada fornecedor entrega e quanto ja foi gasto com ele
    - comparativo de preco quando o mesmo item ja veio de mais de um lugar
"""

import customtkinter as ctk

from controllers import fornecedores as ctrl
from core.calculo import ROTULO_BASE
from utils.componentes import (
    BarraBusca, BarraFerramentas, Botao, Campo, Tabela,
    confirmar, notificar, separador,
)
from utils.tema import (
    Cores, Espaco, Fontes, Icone, Raio,
    estilo_card, formatar_moeda, formatar_moeda_precisa, formatar_pct,
)


class TelaFornecedores(ctk.CTkFrame):
    def __init__(self, pai):
        super().__init__(pai, fg_color="transparent")

        self.busca = ""

        self._montar_topo()
        self.area_aviso = ctk.CTkFrame(self, fg_color="transparent", height=0)
        self.area_aviso.pack(fill="x")
        self._montar_tabela()
        self.recarregar()

    # -- montagem ----------------------------------------------------------

    def _montar_topo(self):
        barra = BarraFerramentas(self)
        barra.pack(fill="x", pady=(0, Espaco.MD))

        BarraBusca(barra.esquerda, self._ao_buscar,
                   texto="Buscar fornecedor").pack(side="left")

        Botao(barra.direita, "Novo fornecedor", icone=Icone.ADICIONAR,
              command=self._novo, width=185).pack(side="right")

        Botao(barra.direita, "Comparar precos", icone=Icone.GRAFICO,
              variante="secundario", width=170,
              command=self._comparar).pack(side="right", padx=(0, Espaco.SM))

        self.resumo = ctk.CTkLabel(barra.direita, text="", font=Fontes.pequeno(),
                                   text_color=Cores.TEXTO_SECUNDARIO)
        self.resumo.pack(side="right", padx=(0, Espaco.MD))

    def _montar_tabela(self):
        colunas = [
            {"chave": "nome", "titulo": "Fornecedor", "largura": 215,
             "fonte": Fontes.corpo_forte},
            {"chave": "contato", "titulo": "Contato", "largura": 140,
             "cor": lambda _l: Cores.TEXTO_SECUNDARIO},
            {"chave": "telefone", "titulo": "Telefone", "largura": 125,
             "cor": lambda _l: Cores.TEXTO_SECUNDARIO},
            {"chave": "itens_texto", "titulo": "Fornece", "largura": 175,
             "cor": lambda _l: Cores.TEXTO_SECUNDARIO},
            {"chave": "gasto", "titulo": "Ja comprado", "largura": 120,
             "alinhamento": "e", "formato": "moeda", "fonte": Fontes.numero,
             "cor": lambda _l: Cores.LARANJA},
        ]

        acoes = [
            {"icone": Icone.EDITAR, "comando": self._editar, "dica": "Editar"},
            {"icone": Icone.CHECKLIST, "comando": self._ver_itens,
             "dica": "Ver o que fornece"},
            {"icone": Icone.EXCLUIR, "comando": self._excluir,
             "cor": Cores.PREJUIZO, "dica": "Excluir"},
        ]

        self.tabela = Tabela(
            self, colunas, ao_clicar=self._editar, acoes=acoes,
            vazio={
                "icone": Icone.VEICULO,
                "titulo": "Nenhum fornecedor cadastrado",
                "mensagem": "Cadastre de quem voce compra para acompanhar "
                            "gastos e comparar precos.",
                "acao": {"texto": "Cadastrar o primeiro", "comando": self._novo},
            },
        )
        self.tabela.pack(fill="both", expand=True)

    # -- dados -------------------------------------------------------------

    def recarregar(self):
        registros = ctrl.listar(self.busca)

        for registro in registros:
            partes = []
            if registro["qtd_ingredientes"]:
                partes.append(f"{registro['qtd_ingredientes']} insumos")
            if registro["qtd_embalagens"]:
                partes.append(f"{registro['qtd_embalagens']} embalagens")
            registro["itens_texto"] = " · ".join(partes) or "--"
            registro["contato"] = registro.get("contato") or "--"
            registro["telefone"] = registro.get("telefone") or "--"
            registro["gasto"] = ctrl.gasto_total(registro["id"])

        self.tabela.preencher(registros)

        stats = ctrl.estatisticas()
        texto = f"{stats['total']} fornecedores"
        self.resumo.configure(text=texto)
        self._atualizar_aviso(stats["itens_sem_fornecedor"])

    def _atualizar_aviso(self, sem_fornecedor):
        for widget in self.area_aviso.winfo_children():
            widget.destroy()

        if not sem_fornecedor:
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

        plural = "insumo esta" if sem_fornecedor == 1 else "insumos estao"
        ctk.CTkLabel(
            interno,
            text=f"{sem_fornecedor} {plural} sem fornecedor definido. "
                 "Sem isso nao da para comparar precos nem acompanhar gastos.",
            font=Fontes.corpo(), text_color=Cores.TEXTO,
        ).pack(side="left")

    def _ao_buscar(self, termo):
        self.busca = termo
        self.recarregar()

    # -- acoes -------------------------------------------------------------

    def _novo(self):
        DialogoFornecedor(self, ao_salvar=self.recarregar)

    def _editar(self, linha):
        DialogoFornecedor(self, fornecedor=linha, ao_salvar=self.recarregar)

    def _ver_itens(self, linha):
        DialogoItens(self, linha)

    def _comparar(self):
        DialogoComparativo(self)

    def _excluir(self, linha):
        vinculados = ctrl.itens(linha["id"])

        if vinculados:
            mensagem = (
                f"'{linha['nome']}' fornece {len(vinculados)} item(ns).\n\n"
                "Sera desativado em vez de apagado, para nao perder o registro "
                "de onde vieram os insumos."
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
            f"'{linha['nome']}' foi "
            f"{'excluido' if resultado['apagado'] else 'desativado'}.",
            "sucesso" if resultado["apagado"] else "aviso",
        )


# ---------------------------------------------------------------------------
# Formulario
# ---------------------------------------------------------------------------


class DialogoFornecedor(ctk.CTkToplevel):
    LARGURA, ALTURA = 620, 480

    def __init__(self, pai, fornecedor=None, ao_salvar=None):
        super().__init__(pai)

        self.pai = pai
        self.fornecedor = fornecedor
        self.ao_salvar = ao_salvar
        self.editando = fornecedor is not None

        self.title("")
        self.overrideredirect(True)
        self.configure(fg_color=Cores.FUNDO)
        self.transient(pai.winfo_toplevel())
        self.grab_set()

        self._montar()
        if self.editando:
            self._preencher()

        self.bind("<Escape>", lambda _: self.destroy())
        self.bind("<Return>", lambda _: self._salvar())

        self._dimensionar()
        self.campo_nome.focar()

    def _dimensionar(self):
        self.geometry(f"{self.LARGURA}x{self.ALTURA}")
        self.update_idletasks()
        altura = min(max(self.ALTURA, self.winfo_reqheight()),
                     int(self.winfo_screenheight() * 0.92))
        janela = self.pai.winfo_toplevel()
        x = janela.winfo_rootx() + (janela.winfo_width() - self.LARGURA) // 2
        y = janela.winfo_rooty() + (janela.winfo_height() - altura) // 2
        self.geometry(f"{self.LARGURA}x{altura}+{max(x, 0)}+{max(y, 0)}")

    def _montar(self):
        moldura = ctk.CTkFrame(self, fg_color=Cores.CARD, corner_radius=Raio.GRANDE,
                               border_color=Cores.BORDA, border_width=1)
        moldura.pack(fill="both", expand=True)

        topo = ctk.CTkFrame(moldura, fg_color="transparent")
        topo.pack(fill="x", padx=Espaco.XL, pady=(Espaco.LG, 0))

        texto = ctk.CTkFrame(topo, fg_color="transparent")
        texto.pack(side="left")
        ctk.CTkLabel(texto,
                     text="Editar fornecedor" if self.editando else "Novo fornecedor",
                     font=Fontes.titulo(), text_color=Cores.TEXTO).pack(anchor="w")
        ctk.CTkLabel(texto, text="De quem voce compra os insumos.",
                     font=Fontes.pequeno(),
                     text_color=Cores.TEXTO_SECUNDARIO).pack(anchor="w")

        ctk.CTkButton(topo, text=Icone.FECHAR, width=32, height=32,
                      font=Fontes.icone(13), fg_color="transparent",
                      hover_color=Cores.CARD_HOVER, text_color=Cores.TEXTO_SECUNDARIO,
                      command=self.destroy).pack(side="right")

        separador(moldura).pack(fill="x", padx=Espaco.XL, pady=(Espaco.MD, 0))

        form = ctk.CTkFrame(moldura, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=Espaco.XL, pady=Espaco.LG)

        self.campo_nome = Campo(form, "Nome do fornecedor", obrigatorio=True,
                                ajuda="Ex: Atacadao Central")
        self.campo_nome.pack(fill="x")

        linha = ctk.CTkFrame(form, fg_color="transparent")
        linha.pack(fill="x", pady=(Espaco.XS, 0))

        self.campo_contato = Campo(linha, "Pessoa de contato")
        self.campo_contato.pack(side="left", fill="x", expand=True,
                                padx=(0, Espaco.SM))

        self.campo_telefone = Campo(linha, "Telefone", largura=160)
        self.campo_telefone.pack(side="left")

        linha2 = ctk.CTkFrame(form, fg_color="transparent")
        linha2.pack(fill="x", pady=(Espaco.XS, 0))

        self.campo_email = Campo(linha2, "E-mail")
        self.campo_email.pack(side="left", fill="x", expand=True, padx=(0, Espaco.SM))

        self.campo_cnpj = Campo(linha2, "CNPJ", largura=180)
        self.campo_cnpj.pack(side="left")

        self.campo_obs = Campo(form, "Observacoes",
                               ajuda="Ex: entrega as tercas, pedido minimo R$ 300")
        self.campo_obs.pack(fill="x", pady=(Espaco.XS, 0))

        separador(moldura).pack(fill="x", padx=Espaco.XL)

        rodape = ctk.CTkFrame(moldura, fg_color="transparent")
        rodape.pack(fill="x", padx=Espaco.XL, pady=Espaco.LG)

        self.erro = ctk.CTkLabel(rodape, text="", font=Fontes.pequeno(),
                                 text_color=Cores.PREJUIZO, anchor="w")
        self.erro.pack(side="left", fill="x", expand=True)

        Botao(rodape, "Cancelar", variante="secundario", width=120,
              command=self.destroy).pack(side="right", padx=(Espaco.SM, 0))
        Botao(rodape, "Salvar" if self.editando else "Cadastrar",
              icone=Icone.SALVAR, variante="sucesso", width=160,
              command=self._salvar).pack(side="right")

    def _preencher(self):
        f = self.fornecedor
        self.campo_nome.set(f["nome"])
        for campo, chave in ((self.campo_contato, "contato"),
                             (self.campo_telefone, "telefone"),
                             (self.campo_email, "email"),
                             (self.campo_cnpj, "cnpj"),
                             (self.campo_obs, "observacoes")):
            valor = f.get(chave)
            campo.set("" if not valor or valor == "--" else valor)

    def _salvar(self):
        self.erro.configure(text="")
        self.campo_nome.limpar_erro()

        dados = {
            "nome": self.campo_nome.get(),
            "contato": self.campo_contato.get(),
            "telefone": self.campo_telefone.get(),
            "email": self.campo_email.get(),
            "cnpj": self.campo_cnpj.get(),
            "observacoes": self.campo_obs.get(),
        }

        try:
            if self.editando:
                ctrl.atualizar(self.fornecedor["id"], dados)
                mensagem = f"'{dados['nome']}' atualizado."
            else:
                ctrl.criar(dados)
                mensagem = f"'{dados['nome']}' cadastrado."
        except ctrl.ErroValidacao as erro:
            self.erro.configure(text=str(erro))
            self.campo_nome.erro(str(erro))
            self.campo_nome.focar()
            return

        destino = self.pai
        self.destroy()
        if self.ao_salvar:
            self.ao_salvar()
        notificar(destino, mensagem, "sucesso")


# ---------------------------------------------------------------------------
# O que o fornecedor entrega
# ---------------------------------------------------------------------------


class DialogoItens(ctk.CTkToplevel):
    LARGURA, ALTURA = 660, 540

    def __init__(self, pai, fornecedor):
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
        ctk.CTkLabel(texto, text=fornecedor["nome"], font=Fontes.titulo(),
                     text_color=Cores.TEXTO).pack(anchor="w")
        ctk.CTkLabel(texto,
                     text=f"Ja comprado: {formatar_moeda(ctrl.gasto_total(fornecedor['id']))}",
                     font=Fontes.pequeno(),
                     text_color=Cores.TEXTO_SECUNDARIO).pack(anchor="w")

        ctk.CTkButton(topo, text=Icone.FECHAR, width=32, height=32,
                      font=Fontes.icone(13), fg_color="transparent",
                      hover_color=Cores.CARD_HOVER, text_color=Cores.TEXTO_SECUNDARIO,
                      command=self.destroy).pack(side="right")

        separador(moldura).pack(fill="x", padx=Espaco.XL, pady=Espaco.MD)

        lista = ctk.CTkScrollableFrame(moldura, fg_color="transparent")
        lista.pack(fill="both", expand=True, padx=Espaco.XL)

        itens = ctrl.itens(fornecedor["id"])
        if not itens:
            ctk.CTkLabel(lista, text=Icone.CAIXA, font=Fontes.icone(30),
                         text_color=Cores.TEXTO_APAGADO).pack(pady=(60, Espaco.MD))
            ctk.CTkLabel(lista, text="Nenhum item vinculado", font=Fontes.subtitulo(),
                         text_color=Cores.TEXTO_SECUNDARIO).pack()
            ctk.CTkLabel(lista,
                         text="Ao cadastrar um ingrediente ou embalagem,\n"
                              "escolha este fornecedor para ele aparecer aqui.",
                         font=Fontes.pequeno(), text_color=Cores.TEXTO_APAGADO,
                         justify="center").pack(pady=(4, 0))
        else:
            for item in itens:
                self._linha(lista, item)

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
        self.geometry(f"{self.LARGURA}x{self.ALTURA}+{max(x, 0)}+{max(y, 0)}")
        self.focus_force()

    def _linha(self, pai, item):
        cartao = ctk.CTkFrame(pai, **estilo_card())
        cartao.pack(fill="x", pady=3)

        interno = ctk.CTkFrame(cartao, fg_color="transparent")
        interno.pack(fill="x", padx=Espaco.MD, pady=Espaco.MD)

        esquerda = ctk.CTkFrame(interno, fg_color="transparent")
        esquerda.pack(side="left")

        cabeca = ctk.CTkFrame(esquerda, fg_color="transparent")
        cabeca.pack(anchor="w")
        cor = Cores.LARANJA if item["tipo"] == "Ingrediente" else Cores.INFO
        ctk.CTkFrame(cabeca, fg_color=cor, width=3, height=13,
                     corner_radius=Raio.PILULA).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(cabeca, text=item["nome"], font=Fontes.corpo_forte(),
                     text_color=Cores.TEXTO).pack(side="left")
        if not item.get("ativo", 1):
            ctk.CTkLabel(cabeca, text="  (inativo)", font=Fontes.micro(),
                         text_color=Cores.TEXTO_APAGADO).pack(side="left")

        ctk.CTkLabel(
            esquerda,
            text=f"{item['tipo']}  ·  {item.get('categoria') or 'sem categoria'}  ·  "
                 f"{item['qtd_comprada']:g} {item['unidade_compra'].lower()} por "
                 f"{formatar_moeda(item['valor_pago'])}",
            font=Fontes.micro(), text_color=Cores.TEXTO_SECUNDARIO,
        ).pack(anchor="w", padx=(9, 0))

        unidade = ROTULO_BASE.get(item.get("unidade_base", "UN"), "un")
        ctk.CTkLabel(interno,
                     text=f"{formatar_moeda_precisa(item['custo_unitario'])}/{unidade}",
                     font=Fontes.numero_forte(),
                     text_color=Cores.LARANJA).pack(side="right")


# ---------------------------------------------------------------------------
# Comparativo de precos
# ---------------------------------------------------------------------------


class DialogoComparativo(ctk.CTkToplevel):
    LARGURA, ALTURA = 700, 520

    def __init__(self, pai):
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
        ctk.CTkLabel(texto, text="Comparativo de precos", font=Fontes.titulo(),
                     text_color=Cores.TEXTO).pack(anchor="w")
        ctk.CTkLabel(texto, text="Insumos ja comprados de mais de um fornecedor",
                     font=Fontes.pequeno(),
                     text_color=Cores.TEXTO_SECUNDARIO).pack(anchor="w")

        ctk.CTkButton(topo, text=Icone.FECHAR, width=32, height=32,
                      font=Fontes.icone(13), fg_color="transparent",
                      hover_color=Cores.CARD_HOVER, text_color=Cores.TEXTO_SECUNDARIO,
                      command=self.destroy).pack(side="right")

        separador(moldura).pack(fill="x", padx=Espaco.XL, pady=Espaco.MD)

        lista = ctk.CTkScrollableFrame(moldura, fg_color="transparent")
        lista.pack(fill="both", expand=True, padx=Espaco.XL)

        comparacoes = ctrl.comparativo()
        if not comparacoes:
            ctk.CTkLabel(lista, text=Icone.GRAFICO, font=Fontes.icone(30),
                         text_color=Cores.TEXTO_APAGADO).pack(pady=(60, Espaco.MD))
            ctk.CTkLabel(lista, text="Ainda nao ha o que comparar",
                         font=Fontes.subtitulo(),
                         text_color=Cores.TEXTO_SECUNDARIO).pack()
            ctk.CTkLabel(
                lista,
                text="Quando voce atualizar o preco de um insumo trocando o\n"
                     "fornecedor, o LosPrice guarda as duas compras e mostra\n"
                     "aqui qual saiu mais barato.",
                font=Fontes.pequeno(), text_color=Cores.TEXTO_APAGADO,
                justify="center").pack(pady=(4, 0))
        else:
            for comparacao in comparacoes:
                self._linha(lista, comparacao)

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
        self.geometry(f"{self.LARGURA}x{self.ALTURA}+{max(x, 0)}+{max(y, 0)}")
        self.focus_force()

    def _linha(self, pai, dados):
        cartao = ctk.CTkFrame(pai, **estilo_card())
        cartao.pack(fill="x", pady=3)

        interno = ctk.CTkFrame(cartao, fg_color="transparent")
        interno.pack(fill="x", padx=Espaco.MD, pady=Espaco.MD)

        ctk.CTkLabel(interno, text=dados["ingrediente"], font=Fontes.corpo_forte(),
                     text_color=Cores.TEXTO).pack(anchor="w")

        unidade = ROTULO_BASE.get(dados["unidade_base"], "un")

        for rotulo, fornecedor, custo, cor in (
            ("Melhor", dados["melhor_fornecedor"], dados["melhor_custo"], Cores.LUCRO),
            ("Pior", dados["pior_fornecedor"], dados["pior_custo"], Cores.PREJUIZO),
        ):
            linha = ctk.CTkFrame(interno, fg_color="transparent")
            linha.pack(fill="x", pady=1)
            ctk.CTkLabel(linha, text=rotulo, font=Fontes.micro(),
                         text_color=cor, width=48, anchor="w").pack(side="left")
            ctk.CTkLabel(linha, text=fornecedor, font=Fontes.pequeno(),
                         text_color=Cores.TEXTO_SECUNDARIO,
                         anchor="w").pack(side="left")
            ctk.CTkLabel(linha,
                         text=f"{formatar_moeda_precisa(custo)}/{unidade}",
                         font=Fontes.numero(), text_color=cor).pack(side="right")

        separador(interno).pack(fill="x", pady=Espaco.SM)

        rodape = ctk.CTkFrame(interno, fg_color="transparent")
        rodape.pack(fill="x")
        ctk.CTkLabel(rodape, text="Economia comprando no melhor",
                     font=Fontes.pequeno(),
                     text_color=Cores.TEXTO_SECUNDARIO).pack(side="left")
        ctk.CTkLabel(rodape, text=formatar_pct(dados["economia_pct"]),
                     font=Fontes.numero_forte(),
                     text_color=Cores.LUCRO).pack(side="right")
