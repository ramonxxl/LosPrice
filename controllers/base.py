"""
LosPrice - Base dos controllers
================================

Validacao e conversao compartilhadas. Tudo que mais de um controller
precisa mora aqui, para nao existirem duas versoes da mesma regra.
"""


class ErroValidacao(Exception):
    """Dado invalido vindo do formulario. A tela mostra a mensagem ao usuario."""


def numero(texto, rotulo, minimo=None, maximo=None, obrigatorio=True, padrao=None):
    """
    Converte texto do formulario em numero.
    Aceita os dois formatos que o usuario costuma digitar: '1.234,56' e '1234.56'.
    """
    if texto is None or str(texto).strip() == "":
        if obrigatorio:
            raise ErroValidacao(f"Preencha o campo {rotulo}.")
        return padrao

    limpo = str(texto).replace("R$", "").strip().replace(" ", "")
    if "," in limpo:
        limpo = limpo.replace(".", "").replace(",", ".")

    try:
        valor = float(limpo)
    except ValueError:
        raise ErroValidacao(f"{rotulo} invalido: '{texto}'.")

    if minimo is not None and valor <= minimo:
        raise ErroValidacao(f"{rotulo} deve ser maior que {minimo:g}.")
    if maximo is not None and valor > maximo:
        raise ErroValidacao(f"{rotulo} nao pode passar de {maximo:g}.")
    return valor


def texto(valor, rotulo, minimo=2, obrigatorio=True):
    """Normaliza um campo de texto e valida o tamanho minimo."""
    limpo = (valor or "").strip()
    if not limpo:
        if obrigatorio:
            raise ErroValidacao(f"Informe {rotulo}.")
        return None
    if minimo and len(limpo) < minimo:
        raise ErroValidacao(f"{rotulo.capitalize()} precisa ter pelo menos "
                            f"{minimo} caracteres.")
    return limpo


def opcional(valor):
    """Devolve None em vez de string vazia, para o campo ficar NULL no banco."""
    limpo = (valor or "").strip()
    return limpo or None


def nome_repetido(tabela, nome, registro_id=None):
    """Checa duplicidade de nome, ignorando maiusculas/minusculas."""
    from database.conexao import conectar

    sql = f"SELECT id FROM {tabela} WHERE nome = ? COLLATE NOCASE"
    parametros = [nome]
    if registro_id:
        sql += " AND id <> ?"
        parametros.append(registro_id)

    with conectar() as cur:
        cur.execute(sql, parametros)
        return cur.fetchone() is not None


def fornecedores_ativos():
    """[(id, nome)] dos fornecedores ativos. Usado por varios formularios."""
    from database.conexao import conectar

    with conectar() as cur:
        cur.execute("SELECT id, nome FROM fornecedores WHERE ativo = 1 "
                    "ORDER BY nome COLLATE NOCASE")
        return [(linha["id"], linha["nome"]) for linha in cur.fetchall()]
