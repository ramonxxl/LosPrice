"""
LosPrice - Controller de precificacao
======================================

A tela que da nome ao software.

Toda a matematica ja esta em core.calculo (metodo divisor, testado).
Aqui e so orquestracao: pegar o custo da ficha, montar os encargos de
cada canal, calcular e gravar.

Lembrete do desenho: comissao, cartao, imposto e rateio percentual
incidem sobre o PRECO DE VENDA. Por isso o preco sai por divisao.
"""

from controllers.base import ErroValidacao, numero
from core.calculo import (
    Encargos, analisar_venda, arredondar_preco, calcular_preco,
    custo_maximo, desconto_maximo, preco_minimo,
)
from database.conexao import conectar, obter_config, salvar_config

# Regimes tributarios com aliquota tipica de partida (editavel nas configuracoes).
REGIMES = {
    "MEI": 0.0,
    "Simples Anexo I": 4.0,
    "Simples Anexo III": 6.0,
    "Simples Anexo V": 15.5,
    "Personalizado": 0.0,
}


# ---------------------------------------------------------------------------
# Canais
# ---------------------------------------------------------------------------


def canais(apenas_ativos=True):
    sql = "SELECT * FROM canais"
    if apenas_ativos:
        sql += " WHERE ativo = 1"
    sql += " ORDER BY ordem, id"

    with conectar() as cur:
        cur.execute(sql)
        return [dict(linha) for linha in cur.fetchall()]


def salvar_canal(canal_id, comissao_pct, cartao_pct, taxa_fixa):
    with conectar() as cur:
        cur.execute(
            "UPDATE canais SET comissao_pct = ?, cartao_pct = ?, taxa_fixa = ? "
            " WHERE id = ?",
            (comissao_pct, cartao_pct, taxa_fixa, canal_id),
        )


# ---------------------------------------------------------------------------
# Parametros padrao
# ---------------------------------------------------------------------------


def parametros():
    """Valores que a tela carrega ao abrir, vindos das configuracoes."""
    return {
        "margem_pct": float(obter_config("margem_padrao_pct", "30") or 30),
        "imposto_pct": float(obter_config("imposto_pct", "0") or 0),
        "custo_fixo_pct": float(obter_config("custo_fixo_pct", "0") or 0),
        "arredondar": obter_config("arredondar_preco", "1") == "1",
        "regime": obter_config("regime_tributario", "MEI"),
    }


def salvar_parametros(margem_pct, imposto_pct, custo_fixo_pct):
    salvar_config("margem_padrao_pct", margem_pct)
    salvar_config("imposto_pct", imposto_pct)
    salvar_config("custo_fixo_pct", custo_fixo_pct)


# ---------------------------------------------------------------------------
# Receitas para precificar
# ---------------------------------------------------------------------------


def receitas(busca=None):
    """Receitas ativas com indicacao de quantas ja foram precificadas."""
    sql = """
        SELECT r.id, r.nome, r.categoria, r.custo_unitario, r.rendimento,
               r.unidade_rend,
               (SELECT COUNT(*) FROM precificacao p WHERE p.receita_id = r.id)
                   AS canais_precificados
          FROM receitas r
         WHERE r.ativo = 1
    """
    parametros_sql = []
    if busca:
        sql += " AND (r.nome LIKE ? OR r.categoria LIKE ?)"
        parametros_sql += [f"%{busca}%", f"%{busca}%"]
    sql += " ORDER BY r.nome COLLATE NOCASE"

    with conectar() as cur:
        cur.execute(sql, parametros_sql)
        return [dict(linha) for linha in cur.fetchall()]


def gravadas(receita_id):
    """Precos ja salvos desta receita, indexados por canal."""
    with conectar() as cur:
        cur.execute("SELECT * FROM precificacao WHERE receita_id = ?", (receita_id,))
        return {linha["canal_id"]: dict(linha) for linha in cur.fetchall()}


# ---------------------------------------------------------------------------
# Calculo
# ---------------------------------------------------------------------------


def encargos_do_canal(canal, imposto_pct, custo_fixo_pct):
    return Encargos(
        comissao_pct=canal["comissao_pct"],
        cartao_pct=canal["cartao_pct"],
        imposto_pct=imposto_pct,
        custo_fixo_pct=custo_fixo_pct,
        taxa_fixa_rs=canal["taxa_fixa"],
    )


def calcular(receita_id, margem_pct, imposto_pct, custo_fixo_pct,
             custo_fixo_rs=0.0, arredondar=True, praticados=None):
    """
    Calcula a receita em todos os canais.

    praticados: {canal_id: preco} com o que o usuario cobra de fato.
    Quando informado, a linha mostra o resultado REAL desse preco.

    Retorna lista de dicts prontos para a tela desenhar.
    """
    with conectar() as cur:
        cur.execute("SELECT id, nome, custo_unitario FROM receitas WHERE id = ?",
                    (receita_id,))
        receita = cur.fetchone()

    if not receita:
        raise ErroValidacao("Receita nao encontrada.")

    custo = receita["custo_unitario"]
    praticados = praticados or {}
    resultado = []

    for canal in canais():
        enc = encargos_do_canal(canal, imposto_pct, custo_fixo_pct)

        linha = {
            "canal_id": canal["id"],
            "canal": canal["nome"],
            "cor": canal["cor"],
            "comissao_pct": canal["comissao_pct"],
            "cartao_pct": canal["cartao_pct"],
            "taxa_fixa": canal["taxa_fixa"],
            "custo": custo,
            "encargos": enc,
        }

        try:
            calculado = calcular_preco(custo, enc, margem_pct, custo_fixo_rs)
        except Exception as erro:
            # taxas + margem passaram de 100%: canal impossivel nessa configuracao
            linha.update({
                "impossivel": True, "motivo": str(erro),
                "preco_sugerido": None, "preco_vitrine": None,
                "preco_praticado": None, "lucro": None, "margem_pct": None,
                "piso": None, "composicao": None,
            })
            resultado.append(linha)
            continue

        vitrine = arredondar_preco(calculado.preco) if arredondar else round(calculado.preco, 2)
        praticado = praticados.get(canal["id"]) or vitrine
        real = analisar_venda(custo, praticado, enc, custo_fixo_rs)

        linha.update({
            "impossivel": False,
            "motivo": None,
            "preco_sugerido": calculado.preco,
            "preco_vitrine": vitrine,
            "preco_praticado": praticado,
            "lucro": real.lucro,
            "margem_pct": real.margem_pct,
            "piso": preco_minimo(custo, enc, custo_fixo_rs),
            "composicao": real,
        })
        resultado.append(linha)

    return {"receita": dict(receita), "custo": custo, "linhas": resultado}


def simular(custo, canal, preco, imposto_pct, custo_fixo_pct, custo_fixo_rs=0.0):
    """Abertura de um preco qualquer. Base do Simulador."""
    enc = encargos_do_canal(canal, imposto_pct, custo_fixo_pct)
    return analisar_venda(custo, preco, enc, custo_fixo_rs)


def custo_alvo(preco_desejado, canal, margem_desejada, imposto_pct,
               custo_fixo_pct, custo_fixo_rs=0.0):
    """Quanto a ficha pode custar para bater um preco de venda com margem X."""
    enc = encargos_do_canal(canal, imposto_pct, custo_fixo_pct)
    return custo_maximo(preco_desejado, enc, margem_desejada, custo_fixo_rs)


def desconto_possivel(custo, canal, preco, imposto_pct, custo_fixo_pct,
                      margem_minima=0.0, custo_fixo_rs=0.0):
    enc = encargos_do_canal(canal, imposto_pct, custo_fixo_pct)
    return desconto_maximo(preco, custo, enc, custo_fixo_rs, margem_minima)


# ---------------------------------------------------------------------------
# Gravacao
# ---------------------------------------------------------------------------


def salvar(receita_id, margem_pct, imposto_pct, custo_fixo_pct,
           custo_fixo_rs, linhas):
    """Grava uma linha de precificacao por canal."""
    with conectar() as cur:
        for linha in linhas:
            if linha.get("impossivel"):
                continue
            cur.execute(
                """
                INSERT INTO precificacao
                    (receita_id, canal_id, margem_pct, imposto_pct,
                     custo_fixo_pct, custo_fixo_rs, preco_sugerido,
                     preco_praticado, lucro_liquido, margem_real_pct)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (receita_id, canal_id) DO UPDATE SET
                    margem_pct      = excluded.margem_pct,
                    imposto_pct     = excluded.imposto_pct,
                    custo_fixo_pct  = excluded.custo_fixo_pct,
                    custo_fixo_rs   = excluded.custo_fixo_rs,
                    preco_sugerido  = excluded.preco_sugerido,
                    preco_praticado = excluded.preco_praticado,
                    lucro_liquido   = excluded.lucro_liquido,
                    margem_real_pct = excluded.margem_real_pct,
                    atualizado_em   = datetime('now', 'localtime')
                """,
                (receita_id, linha["canal_id"], margem_pct, imposto_pct,
                 custo_fixo_pct, custo_fixo_rs, linha["preco_sugerido"],
                 linha["preco_praticado"], linha["lucro"], linha["margem_pct"]),
            )

    salvar_parametros(margem_pct, imposto_pct, custo_fixo_pct)


def limpar(receita_id):
    with conectar() as cur:
        cur.execute("DELETE FROM precificacao WHERE receita_id = ?", (receita_id,))


# ---------------------------------------------------------------------------
# Panorama
# ---------------------------------------------------------------------------


def estatisticas():
    with conectar() as cur:
        cur.execute("SELECT COUNT(DISTINCT receita_id) AS n FROM precificacao")
        precificadas = cur.fetchone()["n"] or 0

        cur.execute("SELECT AVG(margem_real_pct) AS media FROM precificacao")
        media = cur.fetchone()["media"] or 0.0

        cur.execute(
            """
            SELECT COUNT(*) AS n FROM precificacao
             WHERE margem_real_pct < 0
            """
        )
        prejuizo = cur.fetchone()["n"] or 0

        cur.execute("SELECT COUNT(*) AS n FROM receitas WHERE ativo = 1")
        total_receitas = cur.fetchone()["n"] or 0

    return {
        "precificadas": precificadas,
        "total_receitas": total_receitas,
        "margem_media": media,
        "no_prejuizo": prejuizo,
    }


def alertas_prejuizo():
    """Produtos vendendo no vermelho, para o dashboard."""
    with conectar() as cur:
        cur.execute(
            """
            SELECT r.nome AS receita, c.nome AS canal,
                   p.preco_praticado, p.lucro_liquido, p.margem_real_pct
              FROM precificacao p
              JOIN receitas r ON r.id = p.receita_id
              JOIN canais   c ON c.id = p.canal_id
             WHERE p.margem_real_pct < 0 AND r.ativo = 1
             ORDER BY p.margem_real_pct
            """
        )
        return [dict(linha) for linha in cur.fetchall()]


def validar_parametros(margem, imposto, custo_fixo):
    """Converte e valida os campos do formulario da tela."""
    m = numero(margem, "Margem de lucro", minimo=-0.01, obrigatorio=False, padrao=0.0)
    i = numero(imposto, "Imposto", minimo=-0.01, obrigatorio=False, padrao=0.0)
    f = numero(custo_fixo, "Custo fixo", minimo=-0.01, obrigatorio=False, padrao=0.0)

    for rotulo, valor in (("Margem de lucro", m), ("Imposto", i), ("Custo fixo", f)):
        if valor >= 100:
            raise ErroValidacao(f"{rotulo} nao pode ser 100% ou mais.")

    return m, i, f
