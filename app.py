# app.py - Sistema de Propostas Comerciais
# Casa do Frentista / GP Company

import streamlit as st
import json
import os
from datetime import datetime, timedelta
from typing import List
import pandas as pd

from data import (
    TANQUES, BACIAS, BOMBAS, FILTROS, ELEMENTOS, OPCIONAIS,
    EMPRESA, VENDEDORES_INICIAL, TEMPLATES, UFS_BRASIL,
    UF_ORIGEM_PADRAO, calcular_difal,
    get_imagem_tanque, get_imagens_selecionadas,
)
from pdf_generator import gerar_pdf, format_brl
from storage import (
    proximo_numero_cotacao, salvar_proposta,
    listar_propostas, carregar_proposta, numero_existe,
)

# ==================== CONFIG ====================
st.set_page_config(
    page_title="Casa do Frentista | Propostas",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="expanded",
)

VENDEDORES_FILE = os.path.join(os.path.dirname(__file__), "vendedores.json")


def carregar_vendedores() -> List[str]:
    if os.path.exists(VENDEDORES_FILE):
        try:
            with open(VENDEDORES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return VENDEDORES_INICIAL.copy()


def salvar_vendedores(lista: List[str]):
    with open(VENDEDORES_FILE, "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=2)


# ==================== SIDEBAR - CONFIGURAÇÕES ====================
with st.sidebar:
    st.image("logo_casa.png", width=180)
    st.markdown("### Configurações")

    # Gestão de vendedores
    with st.expander("👥 Vendedores", expanded=False):
        vendedores = carregar_vendedores()
        novo_vendedor = st.text_input("Adicionar vendedor", key="novo_vend")
        if st.button("Adicionar") and novo_vendedor.strip():
            if novo_vendedor.strip() not in vendedores:
                vendedores.append(novo_vendedor.strip())
                salvar_vendedores(vendedores)
                st.success(f"Adicionado: {novo_vendedor}")
                st.rerun()
        remover = st.selectbox("Remover vendedor", ["—"] + vendedores, key="rem_vend")
        if st.button("Remover") and remover != "—":
            vendedores = [v for v in vendedores if v != remover]
            salvar_vendedores(vendedores)
            st.success(f"Removido: {remover}")
            st.rerun()
        st.caption("Lista atual: " + ", ".join(vendedores) if vendedores else "Nenhum")

    st.markdown("---")
    st.caption(f"{EMPRESA['nome']} · GP Company")
    st.caption(EMPRESA["cidade"])


# ==================== TÍTULO ====================
st.title("⛽ Proposta Comercial – Tanques Aéreos")
st.markdown(f"**{EMPRESA['nome']}** · Equipamentos **GP Company**")
st.markdown("---")

# ==================== TEMPLATE + HISTÓRICO ====================
col_tpl, col_hist = st.columns(2)
with col_tpl:
    template_nome = st.selectbox("Template rápido", list(TEMPLATES.keys()))
    template = TEMPLATES.get(template_nome)
with col_hist:
    propostas = listar_propostas()
    opcoes_hist = ["— Nova proposta —"] + [
        f"{p['numero']} | {p['cliente'][:30]} | {p['salvo_em'][:10]}"
        for p in propostas[:30]
    ]
    escolha_hist = st.selectbox("Carregar / duplicar proposta salva", opcoes_hist)
    proposta_carregada = None
    if escolha_hist != "— Nova proposta —" and propostas:
        idx = opcoes_hist.index(escolha_hist) - 1
        if 0 <= idx < len(propostas):
            proposta_carregada = carregar_proposta(propostas[idx]["path"])
            if proposta_carregada:
                st.caption("Proposta carregada — revise os campos e gere um **novo** número ao salvar.")

# Defaults a partir do template ou histórico
_def = {}
if proposta_carregada:
    _def = proposta_carregada
elif template:
    _def = {"_template": template}

# ==================== DADOS DO CLIENTE ====================
st.subheader("1. Dados do Cliente")
col1, col2, col3 = st.columns(3)

_cli = (_def.get("cliente") or {}) if proposta_carregada else {}
_cot = (_def.get("cotacao") or {}) if proposta_carregada else {}

with col1:
    razao_social = st.text_input("Razão Social *", value=_cli.get("razao_social", "") if _cli.get("razao_social") != "—" else "")
    cnpj = st.text_input("CNPJ", value=_cli.get("cnpj", "") if _cli.get("cnpj") != "—" else "")
    contato = st.text_input("A/c (Contato)", value=_cli.get("contato", "") if _cli.get("contato") != "—" else "")

with col2:
    endereco = st.text_input("Endereço / Cidade", value=_cli.get("endereco", "") if _cli.get("endereco") != "—" else "")
    telefone = st.text_input("Telefone", value=_cli.get("telefone", "") if _cli.get("telefone") != "—" else "")
    email = st.text_input("E-mail", value=_cli.get("email", "") if _cli.get("email") != "—" else "")
    uf_origem = st.selectbox(
        "UF origem (ICMS)",
        UFS_BRASIL,
        index=UFS_BRASIL.index(UF_ORIGEM_PADRAO) if UF_ORIGEM_PADRAO in UFS_BRASIL else UFS_BRASIL.index("SC"),
        help="Padrão: SC (fábrica). Altere se a saída fiscal for de outro estado.",
    )
    uf_destino = st.selectbox(
        "UF destino (DIFAL/ICMS)",
        ["—"] + UFS_BRASIL,
        index=0,
    )

with col3:
    vendedores = carregar_vendedores()
    vend_default = _cot.get("vendedor") if _cot.get("vendedor") in vendedores else (vendedores[0] if vendedores else "—")
    vendedor = st.selectbox(
        "Agente de Vendas *",
        vendedores if vendedores else ["—"],
        index=(vendedores.index(vend_default) if vend_default in vendedores else 0),
    )
    if "numero_auto" not in st.session_state:
        st.session_state.numero_auto = proximo_numero_cotacao()
    if st.button("Gerar novo nº de cotação"):
        st.session_state.numero_auto = proximo_numero_cotacao()
        st.rerun()
    numero_cotacao = st.text_input("Nº da Cotação *", value=st.session_state.numero_auto)
    # Validação em tempo real: número já usado no histórico
    if numero_cotacao.strip() and numero_existe(numero_cotacao):
        st.error(
            f"O número **{numero_cotacao.strip()}** já foi usado em outra proposta. "
            "Clique em **Gerar novo nº de cotação** antes de emitir o PDF."
        )
    elif numero_cotacao.strip():
        st.caption("Número disponível ✓")
    data_cotacao = st.date_input("Data", value=datetime.now())
    validade_dias = st.number_input("Validade (dias)", min_value=1, max_value=60, value=7)
    data_validade_fim = data_cotacao + timedelta(days=int(validade_dias))
    st.caption(f"Válido até **{data_validade_fim.strftime('%d/%m/%Y')}**")


# ==================== SELEÇÃO DE PRODUTOS ====================
st.subheader("2. Seleção de Produtos")

def _idx(options, key, fallback=0):
    try:
        return list(options).index(key)
    except (ValueError, AttributeError):
        return fallback

# Preferência: template > padrão
_tpl = template or {}
_tk = _tpl.get("tanque", "10.000L")
_bk = _tpl.get("bacia", "10.000L")
_bok = _tpl.get("bomba", "SEM BOMBA")
_fk = _tpl.get("filtro", "SEM FILTRO")
_ek = _tpl.get("elemento", "SEM ELEMENTO")

col_t, col_b = st.columns(2)

st.caption(
    "Desconto **por item** reduz o valor do produto (já entra no total). "
    "O desconto **à vista** (mais abaixo) é um benefício extra, só se o cliente pagar à vista."
)

with col_t:
    tanque_key = st.selectbox(
        "Tanque Aéreo",
        options=list(TANQUES.keys()),
        index=_idx(TANQUES.keys(), _tk, list(TANQUES.keys()).index("10.000L") if "10.000L" in TANQUES else 0),
    )
    tinfo = TANQUES[tanque_key]
    st.caption(
        f"Tabela: {format_brl(float(tinfo['preco']))} · "
        f"Ø {tinfo['diametro']} · Comp. {tinfo['comprimento']} · Chapa {tinfo['chapa']} · {tinfo['peso']} kg"
    )
    desc_tanque = st.number_input(
        "Desconto tanque (%)",
        min_value=0.0, max_value=100.0, value=0.0, step=0.5,
        key=f"d_tanque_{tanque_key}",
    )
    preco_sug_t = float(tinfo["preco"]) * (1 - desc_tanque / 100.0)
    preco_tanque = st.number_input(
        "Preço final Tanque (R$)",
        value=float(preco_sug_t),
        min_value=0.0,
        step=10.0,
        key=f"p_tanque_{tanque_key}_{desc_tanque}",
        help="Pode ajustar manualmente além do % de desconto.",
    )

with col_b:
    bacia_key = st.selectbox(
        "Bacia de Contenção",
        options=list(BACIAS.keys()),
        index=_idx(BACIAS.keys(), _bk, list(BACIAS.keys()).index("10.000L") if "10.000L" in BACIAS else 0),
    )
    binfo = BACIAS[bacia_key]
    if bacia_key != "SEM BACIA":
        st.caption(
            f"Tabela: {format_brl(float(binfo['preco']))} · "
            f"L {binfo['largura']} · A {binfo['altura']} · C {binfo['comprimento']} · {binfo['peso']} kg"
        )
    else:
        st.caption("Sem bacia de contenção")
    desc_bacia = st.number_input(
        "Desconto bacia (%)",
        min_value=0.0, max_value=100.0, value=0.0, step=0.5,
        key=f"d_bacia_{bacia_key}",
    )
    preco_sug_b = float(binfo["preco"]) * (1 - desc_bacia / 100.0)
    preco_bacia = st.number_input(
        "Preço final Bacia (R$)",
        value=float(preco_sug_b),
        min_value=0.0,
        step=10.0,
        key=f"p_bacia_{bacia_key}_{desc_bacia}",
    )

col_bo, col_f, col_e = st.columns(3)

with col_bo:
    bomba_key = st.selectbox("Bomba de Abastecimento", options=list(BOMBAS.keys()), index=_idx(BOMBAS.keys(), _bok, 0))
    st.caption(f"Tabela: {format_brl(float(BOMBAS[bomba_key]))}")
    desc_bomba = st.number_input(
        "Desconto bomba (%)",
        min_value=0.0, max_value=100.0, value=0.0, step=0.5,
        key=f"d_bomba_{bomba_key}",
    )
    preco_sug_bo = float(BOMBAS[bomba_key]) * (1 - desc_bomba / 100.0)
    preco_bomba = st.number_input(
        "Preço final Bomba (R$)",
        value=float(preco_sug_bo),
        min_value=0.0,
        step=10.0,
        key=f"p_bomba_{bomba_key}_{desc_bomba}",
    )

with col_f:
    filtro_key = st.selectbox("Filtro", options=list(FILTROS.keys()), index=_idx(FILTROS.keys(), _fk, 0))
    st.caption(f"Tabela: {format_brl(float(FILTROS[filtro_key]))}")
    desc_filtro = st.number_input(
        "Desconto filtro (%)",
        min_value=0.0, max_value=100.0, value=0.0, step=0.5,
        key=f"d_filtro_{filtro_key}",
    )
    preco_sug_f = float(FILTROS[filtro_key]) * (1 - desc_filtro / 100.0)
    preco_filtro = st.number_input(
        "Preço final Filtro (R$)",
        value=float(preco_sug_f),
        min_value=0.0,
        step=10.0,
        key=f"p_filtro_{filtro_key}_{desc_filtro}",
    )

with col_e:
    elemento_key = st.selectbox("Elemento Filtrante", options=list(ELEMENTOS.keys()), index=_idx(ELEMENTOS.keys(), _ek, 0))
    st.caption(f"Tabela: {format_brl(float(ELEMENTOS[elemento_key]))}")
    desc_elemento = st.number_input(
        "Desconto elemento (%)",
        min_value=0.0, max_value=100.0, value=0.0, step=0.5,
        key=f"d_elem_{elemento_key}",
    )
    preco_sug_e = float(ELEMENTOS[elemento_key]) * (1 - desc_elemento / 100.0)
    preco_elemento = st.number_input(
        "Preço final Elemento (R$)",
        value=float(preco_sug_e),
        min_value=0.0,
        step=10.0,
        key=f"p_elem_{elemento_key}_{desc_elemento}",
    )

# ==================== PRODUTOS OPCIONAIS (checkbox) ====================
st.markdown("**Produtos opcionais**")
st.caption("Marque os itens que deseja incluir no orçamento. O preço pode ser ajustado.")

opcionais_selecionados = {}  # nome -> preco final
if OPCIONAIS:
    for nome_op, info_op in OPCIONAIS.items():
        col_ck, col_pr, col_ds = st.columns([2, 1, 3])
        with col_ck:
            marcado = st.checkbox(nome_op, value=False, key=f"opt_{nome_op}")
        with col_pr:
            preco_op = st.number_input(
                "R$",
                value=float(info_op.get("preco", 0)),
                min_value=0.0,
                step=50.0,
                key=f"opt_preco_{nome_op}",
                label_visibility="collapsed",
            )
        with col_ds:
            if info_op.get("descricao"):
                st.caption(info_op["descricao"])
            # Mini preview da foto do opcional (se existir)
            img_op = info_op.get("imagem")
            if img_op and os.path.exists(img_op):
                st.image(img_op, width=120)
            elif img_op:
                st.caption(f"⚠️ Imagem não encontrada: {img_op}")
        if marcado:
            opcionais_selecionados[nome_op] = {
                "preco": preco_op,
                "descricao": info_op.get("descricao", ""),
                "imagem": info_op.get("imagem"),
            }
else:
    st.caption("Nenhum opcional cadastrado em data.py")

# Item extra livre (fora da lista de opcionais)
st.markdown("**Item avulso (texto livre)**")
extra_desc = st.text_input("Descrição do item extra", value="")
extra_qtd = st.number_input("Qtd extra", min_value=0, value=0, step=1)
extra_valor = st.number_input("Valor unitário extra (R$)", min_value=0.0, value=0.0, step=10.0)

# ==================== GALERIA DE IMAGENS (produtos + opcionais marcados) ====================
st.markdown("**Imagens dos produtos selecionados**")
imagens_sel = get_imagens_selecionadas(tanque_key, bacia_key, bomba_key, filtro_key)

# Inclui fotos dos opcionais marcados
for nome_op, info_op in opcionais_selecionados.items():
    img_op = info_op.get("imagem")
    if img_op:
        imagens_sel.append((f"Opcional: {nome_op}", img_op))

imagens_existentes = [(titulo, path) for titulo, path in imagens_sel if path and os.path.exists(path)]

if imagens_existentes:
    cols_img = st.columns(min(len(imagens_existentes), 4))
    for idx, (titulo, path) in enumerate(imagens_existentes):
        with cols_img[idx % len(cols_img)]:
            st.image(path, use_container_width=True, caption=titulo)
    st.caption("* Imagens meramente ilustrativas – GP Company · entram no PDF da proposta")
else:
    st.caption(
        "Nenhuma imagem encontrada. Coloque fotos em "
        "`imagens_produtos/tanques|bacias|bombas|filtros|opcionais/`."
    )


# ==================== DESCONTOS E FRETE ====================
st.subheader("3. Descontos, Frete e Observações")

col_d1, col_d2, col_d3 = st.columns(3)

with col_d1:
    desconto_pct = st.number_input(
        "Desconto à vista — plus (%)",
        min_value=0.0,
        max_value=30.0,
        value=5.0,
        step=0.5,
        help=(
            "Benefício extra só no pagamento à vista. "
            "Descontos negociados por produto ficam nos campos de cada item acima "
            "e já compõem o total dos produtos (à prazo)."
        ),
    )

with col_d2:
    frete_valor = st.number_input("Valor do Frete (R$)", min_value=0.0, value=0.0, step=50.0)
    frete_obs = st.text_input("Observação do Frete", value="A COMBINAR")

with col_d3:
    fluido = st.text_input("Fluido a ser armazenado", value="Diesel")
    obs_gerais = st.text_area("Observações gerais (aparecem no PDF)", value="", height=80)

obs_item = st.text_input(
    "Observação extra nos itens (PDF)",
    value="",
    help="Texto livre que aparece junto à descrição dos produtos.",
)

# ==================== SIMULAÇÃO DE ECONOMIA (DIESEL TRR × POSTO) ====================
st.markdown("**Simulação de economia — abastecimento via TRR**")
st.caption(
    "Demonstra ao cliente a economia de comprar diesel em TRR (com tanque próprio) "
    "em vez de abastecer no posto. Valores editáveis; a tabela usa o volume do tanque selecionado."
)
incluir_economia = st.checkbox("Incluir simulação de economia na proposta", value=True)

# Volume do tanque selecionado (ex.: "10.000L" → 10000)
def _volume_litros(chave: str) -> int:
    digitos = "".join(c for c in (chave or "") if c.isdigit())
    try:
        return int(digitos) if digitos else 5000
    except Exception:
        return 5000

vol_tanque = _volume_litros(tanque_key)

col_e1, col_e2, col_e3, col_e4 = st.columns(4)
with col_e1:
    preco_posto = st.number_input(
        "Preço médio no posto (R$/L)",
        min_value=0.0, value=7.59, step=0.01, format="%.2f",
        disabled=not incluir_economia,
    )
with col_e2:
    preco_trr = st.number_input(
        "Preço médio na TRR (R$/L)",
        min_value=0.0, value=6.92, step=0.01, format="%.2f",
        disabled=not incluir_economia,
    )
with col_e3:
    volume_simulado = st.number_input(
        "Volume p/ tabela (L)",
        min_value=100, value=int(vol_tanque), step=500,
        help="Por padrão usa a capacidade do tanque selecionado.",
        disabled=not incluir_economia,
    )
with col_e4:
    # Consumo mensal estimado da frota (para gráfico de economia ao longo do ano)
    consumo_mensal = st.number_input(
        "Consumo mensal da frota (L)",
        min_value=100, value=min(int(vol_tanque), 5000), step=100,
        help="Litros abastecidos por mês — base do gráfico de economia mensal.",
        disabled=not incluir_economia,
    )

economia_litro = max(0.0, preco_posto - preco_trr)
economia_pct = (economia_litro / preco_posto * 100.0) if preco_posto > 0 else 0.0
economia_total = economia_litro * float(volume_simulado)
economia_mensal = economia_litro * float(consumo_mensal)
economia_anual = economia_mensal * 12

# Tabela de referência por volume
_vols_ref = [1000, 2000, 3000, 4000, 5000]
if volume_simulado not in _vols_ref and volume_simulado > 0:
    _vols_ref = sorted(set(_vols_ref + [int(volume_simulado)]))
tabela_economia = [
    {"volume": v, "economia": economia_litro * v}
    for v in _vols_ref
    if v <= max(int(volume_simulado), 5000) or v == int(volume_simulado)
]

# Série mensal acumulada (12 meses) para o gráfico
serie_mensal = []
acum = 0.0
for m in range(1, 13):
    acum += economia_mensal
    serie_mensal.append({"mes": m, "economia_mes": economia_mensal, "acumulado": acum})

if incluir_economia:
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Economia / litro", format_brl(economia_litro))
    m2.metric("Economia %", f"{economia_pct:.2f}%")
    m3.metric("Economia mensal", format_brl(economia_mensal))
    m4.metric("Economia em 12 meses", format_brl(economia_anual))

    # Gráfico visual na tela
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        meses_lbl = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
                     "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        vals_mes = [economia_mensal] * 12
        vals_acum = [s["acumulado"] for s in serie_mensal]

        fig, ax1 = plt.subplots(figsize=(9, 3.6))
        x = range(12)
        bars = ax1.bar(x, vals_mes, color="#e65c00", alpha=0.85, label="Economia no mês")
        ax1.set_ylabel("Economia no mês (R$)", color="#e65c00")
        ax1.tick_params(axis="y", labelcolor="#e65c00")
        ax1.set_xticks(list(x))
        ax1.set_xticklabels(meses_lbl)
        ax1.set_ylim(0, max(vals_mes) * 1.35 if vals_mes else 1)

        ax2 = ax1.twinx()
        ax2.plot(x, vals_acum, color="#1a365d", marker="o", linewidth=2.2, label="Acumulado")
        ax2.set_ylabel("Economia acumulada (R$)", color="#1a365d")
        ax2.tick_params(axis="y", labelcolor="#1a365d")
        ax2.set_ylim(0, max(vals_acum) * 1.15 if vals_acum else 1)

        ax1.set_title(
            f"Economia mensal estimada — {int(consumo_mensal):,} L/mês × {format_brl(economia_litro)}/L".replace(",", "."),
            fontsize=11, color="#1a365d", pad=10,
        )
        ax1.spines["top"].set_visible(False)
        fig.tight_layout()
        st.pyplot(fig, clear_figure=True)
        plt.close(fig)
    except Exception as e_chart:
        st.caption(f"Gráfico indisponível neste ambiente: {e_chart}")

economia_dados = {
    "incluir": incluir_economia,
    "preco_posto": preco_posto,
    "preco_trr": preco_trr,
    "economia_litro": economia_litro,
    "economia_pct": economia_pct,
    "volume_simulado": int(volume_simulado),
    "economia_total": economia_total,
    "consumo_mensal": int(consumo_mensal),
    "economia_mensal": economia_mensal,
    "economia_anual": economia_anual,
    "serie_mensal": serie_mensal,
    "tabela": tabela_economia,
    "fluido_ref": fluido or "Diesel",
} if incluir_economia else {"incluir": False}

# ==================== FORMA DE PAGAMENTO ====================
st.markdown("**Forma de pagamento (parcelas)**")
st.caption(
    "Defina as etapas e o percentual de cada uma. "
    "A soma dos % deve dar 100%. Os valores em R$ aparecem no resumo abaixo."
)

base_pagamento = st.radio(
    "Calcular parcelas sobre:",
    options=["Valor à prazo (sem desconto)", "Valor à vista (com desconto)"],
    index=0,
    horizontal=True,
)

# Quantidade de parcelas configuráveis
n_parcelas = st.number_input(
    "Quantidade de etapas de pagamento",
    min_value=1,
    max_value=8,
    value=3,
    step=1,
)

# Padrão clássico: 30% / 30% / 40%
_defaults_label = [
    "Entrada (ato do pedido)",
    "No embarque",
    "Faturado (após análise)",
    "Parcela 4",
    "Parcela 5",
    "Parcela 6",
    "Parcela 7",
    "Parcela 8",
]
_defaults_pct = [30.0, 30.0, 40.0, 0.0, 0.0, 0.0, 0.0, 0.0]

parcelas_cfg = []  # lista de {label, pct}
cols_parc = st.columns(min(int(n_parcelas), 4))
for i in range(int(n_parcelas)):
    with cols_parc[i % len(cols_parc)]:
        lab = st.text_input(
            f"Etapa {i+1} – nome",
            value=_defaults_label[i] if i < len(_defaults_label) else f"Parcela {i+1}",
            key=f"parc_lab_{i}",
        )
        pct = st.number_input(
            f"Etapa {i+1} – %",
            min_value=0.0,
            max_value=100.0,
            value=float(_defaults_pct[i]) if i < len(_defaults_pct) else 0.0,
            step=1.0,
            key=f"parc_pct_{i}",
        )
        parcelas_cfg.append({"label": lab, "pct": pct})

soma_pct = sum(p["pct"] for p in parcelas_cfg)
if abs(soma_pct - 100.0) > 0.05:
    st.warning(f"A soma dos percentuais está em **{soma_pct:.1f}%** (ideal: 100%).")
else:
    st.success(f"Soma dos percentuais: **{soma_pct:.1f}%**")


# ==================== CÁLCULOS ====================
itens = []

# Tanque
itens.append({
    "descricao": f"TANQUE AÉREO – AÇO CARBONO ASTM A-36 – {tanque_key} (GP Company)",
    "qtd": 1,
    "unitario": preco_tanque,
    "total": preco_tanque,
})

# Bacia
if bacia_key != "SEM BACIA" or preco_bacia > 0:
    itens.append({
        "descricao": f"BACIA DE CONTENÇÃO – {bacia_key} (GP Company)",
        "qtd": 1,
        "unitario": preco_bacia,
        "total": preco_bacia,
    })

# Bomba
if bomba_key != "SEM BOMBA" or preco_bomba > 0:
    itens.append({
        "descricao": bomba_key,
        "qtd": 1,
        "unitario": preco_bomba,
        "total": preco_bomba,
    })

# Filtro
if filtro_key != "SEM FILTRO" or preco_filtro > 0:
    itens.append({
        "descricao": filtro_key,
        "qtd": 1,
        "unitario": preco_filtro,
        "total": preco_filtro,
    })

# Elemento
if elemento_key != "SEM ELEMENTO" or preco_elemento > 0:
    itens.append({
        "descricao": elemento_key,
        "qtd": 1,
        "unitario": preco_elemento,
        "total": preco_elemento,
    })

# Opcionais marcados (checkbox) — descrição completa, sem corte
for nome_op, info_op in opcionais_selecionados.items():
    if info_op.get("descricao"):
        desc_op = f"OPCIONAL: {nome_op} – {info_op['descricao']}"
    else:
        desc_op = f"OPCIONAL: {nome_op}"
    itens.append({
        "descricao": desc_op,
        "qtd": 1,
        "unitario": info_op["preco"],
        "total": info_op["preco"],
    })

# Item avulso (texto livre)
if extra_qtd > 0 and extra_desc.strip():
    itens.append({
        "descricao": extra_desc.strip(),
        "qtd": extra_qtd,
        "unitario": extra_valor,
        "total": extra_qtd * extra_valor,
    })

total_produtos = sum(i["total"] for i in itens)
valor_desconto = total_produtos * (desconto_pct / 100.0)
total_avista = total_produtos - valor_desconto
total_geral = total_avista + frete_valor  # frete normalmente não entra no desconto à vista

peso_total = tinfo.get("peso", 0) + binfo.get("peso", 0)

# ----- DIFAL -----
# À vista → base NF = (produtos − desc. à vista) + frete
# À prazo → base NF = produtos (já com desconto por item, SEM desc. à vista) + frete
eh_avista = base_pagamento.startswith("Valor à vista")
_uf_d = uf_destino if uf_destino != "—" else ""
_uf_o = uf_origem or UF_ORIGEM_PADRAO

difal_info_avista = calcular_difal(total_avista + frete_valor, _uf_d, _uf_o)
difal_info_prazo = calcular_difal(total_produtos + frete_valor, _uf_d, _uf_o)

# DIFAL e base usados conforme a modalidade de pagamento selecionada
difal_info = difal_info_avista if eh_avista else difal_info_prazo
base_difal = float(difal_info.get("valor_base") or 0)
valor_difal = float(difal_info.get("valor_difal") or 0)

valor_difal_avista = float(difal_info_avista.get("valor_difal") or 0)
valor_difal_prazo = float(difal_info_prazo.get("valor_difal") or 0)

# Totais estimados para o cliente (cada um com seu próprio DIFAL)
total_cliente_avista = total_avista + frete_valor + valor_difal_avista
total_cliente_prazo = total_produtos + frete_valor + valor_difal_prazo

# Parcelas: modalidade escolhida + frete + DIFAL dessa modalidade
base_parcela = total_cliente_avista if eh_avista else total_cliente_prazo

parcelas_calc = []
for p in parcelas_cfg:
    if p["pct"] > 0:
        valor_p = base_parcela * (p["pct"] / 100.0)
        parcelas_calc.append({
            "label": p["label"],
            "pct": p["pct"],
            "valor": valor_p,
        })

primeira_parcela = parcelas_calc[0]["valor"] if parcelas_calc else 0.0

# Resumo fixo na sidebar (sempre visível)
with st.sidebar:
    st.markdown("---")
    st.markdown("### Resumo rápido")
    st.metric("Total produtos", format_brl(total_produtos))
    if valor_desconto > 0:
        st.metric("À vista", format_brl(total_avista))
    if primeira_parcela:
        st.metric("1ª parcela", format_brl(primeira_parcela))
    if valor_difal_prazo > 0:
        st.metric("DIFAL à prazo", format_brl(valor_difal_prazo))
    if valor_difal_avista > 0:
        st.metric("DIFAL à vista", format_brl(valor_difal_avista))
    st.metric("Total c/ DIFAL (modalidade)", format_brl(base_parcela))


# ==================== RESUMO EM TEMPO REAL ====================
st.subheader("4. Resumo do Orçamento")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Produtos", format_brl(total_produtos))
if valor_desconto > 0:
    c2.metric(f"Desc. à vista {desconto_pct:.1f}%", f"- {format_brl(valor_desconto)}")
    c3.metric("Valor à Vista", format_brl(total_avista))
else:
    c2.metric("Desc. à vista", "—")
    c3.metric("Valor à Vista", format_brl(total_avista))
c4.metric("Peso aprox.", f"{peso_total} kg")

# ----- DIFAL: mostra os dois valores (à vista e à prazo) -----
st.markdown("**DIFAL estimado (ICMS interestadual)**")
st.caption(
    "À **prazo**: base = produtos + frete. "
    "À **vista**: base = (produtos − desc. à vista) + frete. "
    "Parcelas usam a modalidade selecionada em “Calcular parcelas sobre”."
)
if uf_destino and uf_destino != "—":
    d1, d2, d3, d4 = st.columns(4)
    d1.metric("UF", f"{uf_origem} → {uf_destino}")
    d2.metric("Interna destino", f"{difal_info['aliquota_interna_destino']:.1f}%")
    d3.metric("Interestadual", f"{difal_info['aliquota_interestadual']:.1f}%")
    d4.metric("Δ alíquota", f"{difal_info.get('diferenca_pp', 0):.1f} p.p.")
    if valor_difal_prazo > 0 or valor_difal_avista > 0:
        x1, x2 = st.columns(2)
        x1.metric("DIFAL à prazo", format_brl(valor_difal_prazo))
        x2.metric("DIFAL à vista", format_brl(valor_difal_avista))
        st.caption("Orientativo — confirmar com o fiscal na NF.")
    else:
        st.info(difal_info.get("observacao") or "Sem DIFAL para esta combinação de UFs.")
else:
    st.warning("Selecione a **UF destino** para calcular o DIFAL (senão ele não entra na proposta).")

st.markdown("**Total estimado para o cliente**")
t1, t2 = st.columns(2)
t1.metric("À prazo + frete + DIFAL", format_brl(total_cliente_prazo))
t2.metric("À vista + frete + DIFAL", format_brl(total_cliente_avista))

if frete_valor > 0:
    st.info(f"Frete: {format_brl(frete_valor)} → **Total geral: {format_brl(total_geral)}**")

# Parcelas em tempo real
if parcelas_calc:
    st.markdown(
        f"**Parcelas** (sobre {format_brl(base_parcela)} — "
        f"{'à vista' if base_pagamento.startswith('Valor à vista') else 'à prazo'}"
        f" + frete + DIFAL)"
    )
    cols_v = st.columns(min(len(parcelas_calc), 4))
    for idx, p in enumerate(parcelas_calc):
        with cols_v[idx % len(cols_v)]:
            st.metric(
                f"{p['label']} ({p['pct']:.0f}%)",
                format_brl(p["valor"]),
            )
    # Tabela detalhada
    df_parc = pd.DataFrame([
        {
            "Etapa": p["label"],
            "%": f"{p['pct']:.1f}%",
            "Valor": format_brl(p["valor"]),
        }
        for p in parcelas_calc
    ])
    st.dataframe(df_parc, use_container_width=True, hide_index=True)

# Tabela de itens
df = pd.DataFrame([
    {
        "Descrição": i["descricao"],
        "Qtd": i["qtd"],
        "Unitário": format_brl(i["unitario"]),
        "Total": format_brl(i["total"]),
    }
    for i in itens
])
st.dataframe(df, use_container_width=True, hide_index=True)


# ==================== GERAÇÃO DO PDF ====================
st.subheader("5. Gerar Proposta PDF")

modo = st.radio(
    "Tipo de documento",
    options=[
        "Orçamento resumido (1 página – valores + dados)",
        "Proposta completa (valores + especificações + condições/garantia)",
        "Somente condições, garantias e cláusulas",
    ],
    index=1,
    horizontal=True,
)

modo_map = {
    "Orçamento resumido (1 página – valores + dados)": "resumo",
    "Proposta completa (valores + especificações + condições/garantia)": "completa",
    "Somente condições, garantias e cláusulas": "condicoes",
}
modo_pdf = modo_map[modo]

# Monta dict de dados para o PDF / histórico
dados_pdf = {
    "cliente": {
        "razao_social": razao_social or "—",
        "cnpj": cnpj or "—",
        "endereco": endereco or "—",
        "telefone": telefone or "—",
        "email": email or "—",
        "contato": contato or "—",
        "uf": uf_destino if uf_destino != "—" else "",
        "uf_origem": uf_origem or UF_ORIGEM_PADRAO,
    },
    "cotacao": {
        "vendedor": vendedor,
        "numero": numero_cotacao,
        "data": data_cotacao.strftime("%d/%m/%Y"),
        "validade": f"{validade_dias} dias",
        "validade_ate": data_validade_fim.strftime("%d/%m/%Y"),
    },
    "itens": itens,
    "total_produtos": total_produtos,
    "desconto_pct": desconto_pct,
    "valor_desconto": valor_desconto,
    "total_avista": total_avista,
    "frete": frete_valor,
    "frete_obs": frete_obs,
    "total_geral": total_geral if frete_valor > 0 else total_avista,
    "tanque_key": tanque_key,
    "bacia_key": bacia_key,
    "bomba_key": bomba_key,
    "filtro_key": filtro_key,
    "fluido": fluido,
    "obs": obs_gerais,
    "obs_item": obs_item,
    "imagem_produto": get_imagem_tanque(tanque_key),
    "imagens": imagens_sel,
    "opcionais": opcionais_selecionados,
    "parcelas": parcelas_calc,
    "base_pagamento": base_pagamento,
    "base_parcela": base_parcela,
    "marca_dagua": True,
    "capa": True,
    "difal": difal_info,
    "difal_avista": difal_info_avista,
    "difal_prazo": difal_info_prazo,
    "valor_difal_avista": valor_difal_avista,
    "valor_difal_prazo": valor_difal_prazo,
    "total_cliente_avista": total_cliente_avista,
    "total_cliente_prazo": total_cliente_prazo,
    "economia": economia_dados,
}

incluir_capa = st.checkbox("Incluir capa no PDF", value=True)
marca_dagua = st.checkbox("Marca d'água ORÇAMENTO no PDF", value=True)
dados_pdf["capa"] = incluir_capa
dados_pdf["marca_dagua"] = marca_dagua

col_btn1, col_btn2 = st.columns([1, 3])

with col_btn1:
    gerar = st.button("📄 Gerar PDF", type="primary", use_container_width=True)

if gerar:
    erros = []
    if not razao_social.strip():
        erros.append("Razão Social do cliente")
    if not numero_cotacao.strip():
        erros.append("Número da cotação")
    elif numero_existe(numero_cotacao):
        erros.append(
            f"Número de cotação **{numero_cotacao.strip()}** já existe no histórico. "
            "Clique em «Gerar novo nº de cotação» e tente de novo."
        )
    if not vendedor or vendedor == "—":
        erros.append("Agente de vendas")
    soma_pct = sum(p["pct"] for p in parcelas_cfg)
    if parcelas_cfg and abs(soma_pct - 100.0) > 0.5:
        erros.append(f"Soma das parcelas = {soma_pct:.1f}% (precisa ser 100%)")

    if erros:
        st.error("Corrija antes de gerar o PDF:\n- " + "\n- ".join(erros))
    else:
        with st.spinner("Gerando proposta profissional..."):
            try:
                # Revalida no momento do save (outro vendedor pode ter gravado no meio tempo)
                if numero_existe(numero_cotacao):
                    novo = proximo_numero_cotacao()
                    st.warning(
                        f"O número {numero_cotacao} foi usado por outro vendedor enquanto você preenchia. "
                        f"Foi reservado o novo número **{novo}** para esta proposta."
                    )
                    numero_cotacao = novo
                    st.session_state.numero_auto = novo
                    dados_pdf["cotacao"]["numero"] = novo

                pdf_bytes = gerar_pdf(dados_pdf, modo=modo_pdf)
                try:
                    path_salvo = salvar_proposta(numero_cotacao, dados_pdf, pdf_bytes, sobrescrever=False)
                    st.caption(f"Salvo no histórico: `{path_salvo}`")
                except FileExistsError as e_dup:
                    # Última linha de defesa
                    novo = proximo_numero_cotacao()
                    dados_pdf["cotacao"]["numero"] = novo
                    numero_cotacao = novo
                    st.session_state.numero_auto = novo
                    pdf_bytes = gerar_pdf(dados_pdf, modo=modo_pdf)
                    path_salvo = salvar_proposta(numero_cotacao, dados_pdf, pdf_bytes, sobrescrever=False)
                    st.warning(f"Número ajustado automaticamente para **{novo}** (evitou duplicidade).")
                    st.caption(f"Salvo no histórico: `{path_salvo}`")
                except Exception as e_hist:
                    st.warning(f"PDF ok, mas histórico não gravou: {e_hist}")

                nome_arquivo = f"Proposta_{numero_cotacao.replace('/', '-')}_{razao_social[:30].replace(' ', '_')}.pdf"
                st.success(f"Proposta **{numero_cotacao}** gerada com sucesso!")
                st.download_button(
                    label="⬇️ Baixar PDF",
                    data=pdf_bytes,
                    file_name=nome_arquivo,
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"Erro ao gerar PDF: {e}")
                st.exception(e)

st.markdown("---")
st.caption("Sistema de propostas · Casa do Frentista · GP Company · Uso interno")
