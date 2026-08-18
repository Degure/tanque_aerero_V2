# pdf_generator.py - Geração de propostas comerciais profissionais
# Casa do Frentista / GP Company

import os
from io import BytesIO
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether, HRFlowable, ListFlowable, ListItem
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from data import EMPRESA, TEXTOS, TANQUES, BACIAS

# Cores elegantes
AZUL_ESCURO = colors.HexColor("#1a365d")
AZUL_MEDIO = colors.HexColor("#2c5282")
LARANJA = colors.HexColor("#e65c00")
CINZA_ESCURO = colors.HexColor("#2d3748")
CINZA_CLARO = colors.HexColor("#f7fafc")
CINZA_BORDA = colors.HexColor("#e2e8f0")
VERDE_DESCONTO = colors.HexColor("#276749")

LOGO_CASA = os.path.join(os.path.dirname(__file__), "logo_casa.png")
LOGO_GP = os.path.join(os.path.dirname(__file__), "logo_gp.png")


def format_brl(valor: float) -> str:
    """Formata valor em Real brasileiro."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _imagem_responsiva(path: str, max_w: float, max_h: float):
    """
    Carrega imagem e dimensiona mantendo proporção dentro de max_w x max_h.
    Retorna objeto Image do ReportLab ou None se falhar.
    """
    if not path or not os.path.exists(path):
        return None
    try:
        from PIL import Image as PILImage
        with PILImage.open(path) as pil_im:
            iw, ih = pil_im.size
        if iw <= 0 or ih <= 0:
            return None
        ratio = min(max_w / iw, max_h / ih)
        return Image(path, width=iw * ratio, height=ih * ratio)
    except Exception:
        return None


def _grade_imagens(imagens: list, styles, max_total_width: float = 180 * mm, max_h: float = 42 * mm):
    """
    Monta uma grade adaptativa de imagens (1 a 4 itens).
    - 1 imagem: larga e centralizada
    - 2 imagens: lado a lado
    - 3–4 imagens: grid proporcional
    Retorna lista de flowables ou lista vazia.
    """
    from PIL import Image as PILImage

    validas = [(t, p) for t, p in imagens if p and os.path.exists(p)]
    if not validas:
        return []

    # Até 5 imagens (tanque, bacia, bomba, filtro + opcional)
    n = min(len(validas), 5)
    validas = validas[:n]
    gap = 2.5 * mm
    cell_w = (max_total_width - gap * (n - 1)) / n
    if n >= 4:
        max_h = min(max_h, 36 * mm)

    cells = []
    for titulo, path in validas:
        img = _imagem_responsiva(path, cell_w - 2 * mm, max_h)
        if img is None:
            continue
        # Nome completo do produto — Paragraph quebra linha automaticamente se for longo
        estilo_legenda = ParagraphStyle(
            name="LegendaImg",
            parent=styles["CorpoPequeno"],
            fontSize=6.5,
            alignment=TA_CENTER,
            leading=8,
        )
        legenda = Paragraph(f"<b>{titulo}</b>", estilo_legenda)
        cell = Table([[img], [legenda]], colWidths=[cell_w])
        cell.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (0, 0), "MIDDLE"),
            ("VALIGN", (0, 1), (0, 1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ]))
        cells.append(cell)

    if not cells:
        return []

    # Completa células vazias para manter alinhamento visual se quiser 4 colunas fixas
    # Aqui usamos exatamente o número de imagens para layout mais limpo
    col_widths = [cell_w] * len(cells)
    row = Table([cells], colWidths=col_widths)
    row.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.5, CINZA_BORDA),
        ("BACKGROUND", (0, 0), (-1, -1), CINZA_CLARO),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    nota = Paragraph(
        "<i>* Imagens meramente ilustrativas – equipamentos GP Company</i>",
        styles["CorpoPequeno"],
    )
    return [row, Spacer(1, 2 * mm), nota, Spacer(1, 3 * mm)]


def criar_estilos():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="TituloPrincipal",
        fontName="Helvetica-Bold",
        fontSize=14,
        textColor=AZUL_ESCURO,
        alignment=TA_CENTER,
        spaceAfter=6,
        spaceBefore=4,
    ))

    styles.add(ParagraphStyle(
        name="Subtitulo",
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=AZUL_MEDIO,
        alignment=TA_LEFT,
        spaceBefore=10,
        spaceAfter=4,
    ))

    styles.add(ParagraphStyle(
        name="Corpo",
        fontName="Helvetica",
        fontSize=9,
        textColor=CINZA_ESCURO,
        alignment=TA_JUSTIFY,
        leading=12,
        spaceAfter=3,
    ))

    styles.add(ParagraphStyle(
        name="CorpoPequeno",
        fontName="Helvetica",
        fontSize=8,
        textColor=CINZA_ESCURO,
        alignment=TA_LEFT,
        leading=10,
    ))

    styles.add(ParagraphStyle(
        name="Label",
        fontName="Helvetica-Bold",
        fontSize=8,
        textColor=AZUL_ESCURO,
    ))

    styles.add(ParagraphStyle(
        name="ValorDestaque",
        fontName="Helvetica-Bold",
        fontSize=14,
        textColor=AZUL_ESCURO,
        alignment=TA_RIGHT,
        leading=16,
    ))

    styles.add(ParagraphStyle(
        name="Desconto",
        fontName="Helvetica-Bold",
        fontSize=13,
        textColor=VERDE_DESCONTO,
        alignment=TA_RIGHT,
        leading=15,
    ))

    styles.add(ParagraphStyle(
        name="ValorLabel",
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=AZUL_ESCURO,
        alignment=TA_LEFT,
        leading=13,
    ))

    styles.add(ParagraphStyle(
        name="ValorTotal",
        fontName="Helvetica-Bold",
        fontSize=16,
        textColor=AZUL_ESCURO,
        alignment=TA_RIGHT,
        leading=18,
    ))

    styles.add(ParagraphStyle(
        name="Rodape",
        fontName="Helvetica",
        fontSize=7,
        textColor=colors.gray,
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        name="ItemLista",
        fontName="Helvetica",
        fontSize=8.5,
        textColor=CINZA_ESCURO,
        leftIndent=10,
        leading=11,
    ))

    return styles


def cabecalho(canvas, doc):
    canvas.saveState()
    # Marca d'água ORÇAMENTO
    if getattr(doc, "marca_dagua", False):
        canvas.saveState()
        canvas.setFont("Helvetica-Bold", 48)
        canvas.setFillGray(0.88)
        canvas.translate(A4[0] / 2.0, A4[1] / 2.0)
        canvas.rotate(45)
        canvas.drawCentredString(0, 0, "ORÇAMENTO")
        canvas.restoreState()

    # Linha superior
    canvas.setStrokeColor(LARANJA)
    canvas.setLineWidth(3)
    canvas.line(15*mm, A4[1] - 12*mm, A4[0] - 15*mm, A4[1] - 12*mm)

    canvas.setStrokeColor(AZUL_ESCURO)
    canvas.setLineWidth(1)
    canvas.line(15*mm, A4[1] - 13.5*mm, A4[0] - 15*mm, A4[1] - 13.5*mm)

    # Rodapé
    canvas.setStrokeColor(CINZA_BORDA)
    canvas.setLineWidth(0.5)
    canvas.line(15*mm, 12*mm, A4[0] - 15*mm, 12*mm)

    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.gray)
    texto_rodape = f"{EMPRESA['nome']}  |  {EMPRESA['endereco']} - {EMPRESA['cidade']}  |  CNPJ {EMPRESA['cnpj']}"
    canvas.drawCentredString(A4[0]/2, 7*mm, texto_rodape)
    canvas.drawRightString(A4[0] - 15*mm, 7*mm, f"Pág. {doc.page}")

    canvas.restoreState()


def gerar_pdf(dados: Dict[str, Any], modo: str = "completa") -> bytes:
    """
    Gera PDF da proposta.
    modo: 'resumo' | 'completa' | 'condicoes'
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15*mm,
        rightMargin=15*mm,
        topMargin=18*mm,
        bottomMargin=18*mm,
    )
    doc.marca_dagua = bool(dados.get("marca_dagua", True))

    styles = criar_estilos()
    story = []
    cotacao = dados.get("cotacao") or {}
    cliente = dados.get("cliente") or {}

    # ========== CAPA (opcional) ==========
    if dados.get("capa") and modo != "condicoes":
        story.append(Spacer(1, 35*mm))
        if os.path.exists(LOGO_CASA):
            try:
                story.append(Image(LOGO_CASA, width=100*mm, height=22*mm))
            except Exception:
                pass
        story.append(Spacer(1, 8*mm))
        story.append(Paragraph(
            f"<font size='18'><b>{EMPRESA['nome'].upper()}</b></font>",
            styles["TituloPrincipal"],
        ))
        story.append(Paragraph(
            "<font size='11'>Equipamentos GP Company</font>",
            styles["TituloPrincipal"],
        ))
        story.append(Spacer(1, 12*mm))
        story.append(HRFlowable(width="60%", thickness=2, color=LARANJA, spaceBefore=2, spaceAfter=8))
        story.append(Paragraph(
            "<font size='14'><b>PROPOSTA COMERCIAL</b></font>",
            styles["TituloPrincipal"],
        ))
        story.append(Paragraph(
            f"<font size='11'>Cotação nº <b>{cotacao.get('numero', '—')}</b></font>",
            styles["TituloPrincipal"],
        ))
        story.append(Spacer(1, 8*mm))
        story.append(Paragraph(
            f"Cliente: <b>{cliente.get('razao_social', '—')}</b>",
            styles["Corpo"],
        ))
        story.append(Paragraph(
            f"Data: {cotacao.get('data', '—')} &nbsp;|&nbsp; "
            f"Validade: {cotacao.get('validade', '—')}"
            + (f" (até {cotacao.get('validade_ate')})" if cotacao.get("validade_ate") else ""),
            styles["Corpo"],
        ))
        story.append(Paragraph(
            f"Vendedor: {cotacao.get('vendedor', '—')}",
            styles["Corpo"],
        ))
        story.append(Spacer(1, 20*mm))
        story.append(Paragraph(
            f"<font size='8'>{EMPRESA['endereco']} – {EMPRESA['cidade']}<br/>CNPJ {EMPRESA['cnpj']}</font>",
            styles["Rodape"],
        ))
        story.append(PageBreak())

    # ========== CABEÇALHO COM LOGOS ==========
    logo_casa = None
    logo_gp = None
    if os.path.exists(LOGO_CASA):
        try:
            logo_casa = Image(LOGO_CASA, width=30*mm, height=10*mm)
        except Exception:
            pass
    if os.path.exists(LOGO_GP):
        try:
            # GP logo is large/black background – crop conceptually by sizing carefully
            logo_gp = Image(LOGO_GP, width=28*mm, height=18*mm)
        except Exception:
            pass

    header_data = []
    if logo_casa and logo_gp:
        header_data = [[logo_casa, Paragraph(
            f"<b>{EMPRESA['nome'].upper()}</b><br/>"
            f"<font size='8'>Equipamentos GP Company</font><br/>"
            f"<font size='7'>{EMPRESA['endereco']}<br/>{EMPRESA['cep']} - {EMPRESA['cidade']}<br/>CNPJ {EMPRESA['cnpj']}</font>",
            styles["CorpoPequeno"]
        ), logo_gp]]
        col_widths = [50*mm, 90*mm, 35*mm]
    elif logo_casa:
        header_data = [[logo_casa, Paragraph(
            f"<b>{EMPRESA['nome'].upper()}</b><br/>"
            f"<font size='8'>Equipamentos GP Company</font><br/>"
            f"<font size='7'>{EMPRESA['endereco']} - {EMPRESA['cidade']}<br/>CNPJ {EMPRESA['cnpj']}</font>",
            styles["CorpoPequeno"]
        )]]
        col_widths = [55*mm, 120*mm]
    else:
        header_data = [[Paragraph(
            f"<b>{EMPRESA['nome'].upper()}</b><br/>Equipamentos GP Company<br/>"
            f"{EMPRESA['endereco']} - {EMPRESA['cidade']}<br/>CNPJ {EMPRESA['cnpj']}",
            styles["Corpo"]
        )]]
        col_widths = [175*mm]

    t_header = Table(header_data, colWidths=col_widths)
    t_header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (-1, 0), (-1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(t_header)
    story.append(Spacer(1, 3*mm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=AZUL_ESCURO, spaceBefore=1, spaceAfter=4))

    # ========== TÍTULO ==========
    if modo == "resumo":
        titulo = "ORÇAMENTO COMERCIAL"
    elif modo == "condicoes":
        titulo = "CONDIÇÕES COMERCIAIS, GARANTIAS E CLÁUSULAS"
    else:
        titulo = "PROPOSTA TÉCNICA E COMERCIAL"

    story.append(Paragraph(titulo, styles["TituloPrincipal"]))
    story.append(Paragraph("Solução de Abastecimento Interno – Tanques Aéreos GP Company", styles["CorpoPequeno"]))
    story.append(Spacer(1, 3*mm))

    # ========== DADOS DO CLIENTE + COTAÇÃO ==========
    cliente = dados.get("cliente", {})
    cotacao = dados.get("cotacao", {})

    dados_cliente = [
        [Paragraph("<b>CLIENTE</b>", styles["Label"]), "",
         Paragraph("<b>Ag. Vendas</b>", styles["Label"]),
         Paragraph(cotacao.get("vendedor", "—"), styles["CorpoPequeno"])],
        [Paragraph("Razão Social", styles["CorpoPequeno"]),
         Paragraph(cliente.get("razao_social", "—"), styles["CorpoPequeno"]),
         Paragraph("<b>Cotação</b>", styles["Label"]),
         Paragraph(str(cotacao.get("numero", "—")), styles["CorpoPequeno"])],
        [Paragraph("CNPJ", styles["CorpoPequeno"]),
         Paragraph(cliente.get("cnpj", "—"), styles["CorpoPequeno"]),
         Paragraph("<b>Data</b>", styles["Label"]),
         Paragraph(cotacao.get("data", "—"), styles["CorpoPequeno"])],
        [Paragraph("Endereço", styles["CorpoPequeno"]),
         Paragraph(cliente.get("endereco", "—"), styles["CorpoPequeno"]),
         Paragraph("<b>Validade</b>", styles["Label"]),
         Paragraph(cotacao.get("validade", "7 dias"), styles["CorpoPequeno"])],
        [Paragraph("Telefone / E-mail", styles["CorpoPequeno"]),
         Paragraph(f"{cliente.get('telefone', '—')}  |  {cliente.get('email', '—')}", styles["CorpoPequeno"]),
         Paragraph("<b>Contato</b>", styles["Label"]),
         Paragraph(cliente.get("contato", "—"), styles["CorpoPequeno"])],
    ]

    t_cli = Table(dados_cliente, colWidths=[32*mm, 78*mm, 28*mm, 37*mm])
    t_cli.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), CINZA_CLARO),
        ("BOX", (0, 0), (-1, -1), 0.6, CINZA_BORDA),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, CINZA_BORDA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(t_cli)
    story.append(Spacer(1, 4*mm))

    # ========== IMAGENS RESPONSIVAS DOS PRODUTOS ==========
    if modo != "condicoes":
        from data import get_imagens_selecionadas

        imagens = dados.get("imagens")
        if not imagens:
            imagens = get_imagens_selecionadas(
                dados.get("tanque_key", "10.000L"),
                dados.get("bacia_key", "SEM BACIA"),
                dados.get("bomba_key", "SEM BOMBA"),
                dados.get("filtro_key", "SEM FILTRO"),
            )

        # Grade adapta automaticamente: 1, 2, 3 ou 4 colunas
        for flowable in _grade_imagens(imagens, styles):
            story.append(flowable)

    # ========== ITENS / VALORES (exceto modo condições) ==========
    if modo != "condicoes":
        story.append(Paragraph("DESCRIÇÃO DOS PRODUTOS", styles["Subtitulo"]))

        itens = dados.get("itens", [])
        header_itens = [
            Paragraph("<b>Descrição</b>", styles["CorpoPequeno"]),
            Paragraph("<b>Qtd</b>", styles["CorpoPequeno"]),
            Paragraph("<b>Valor Unit.</b>", styles["CorpoPequeno"]),
            Paragraph("<b>Valor Final</b>", styles["CorpoPequeno"]),
        ]
        rows = [header_itens]
        for item in itens:
            rows.append([
                Paragraph(item.get("descricao", ""), styles["CorpoPequeno"]),
                Paragraph(str(item.get("qtd", 1)), styles["CorpoPequeno"]),
                Paragraph(format_brl(item.get("unitario", 0)), styles["CorpoPequeno"]),
                Paragraph(format_brl(item.get("total", 0)), styles["CorpoPequeno"]),
            ])

        t_itens = Table(rows, colWidths=[105*mm, 15*mm, 30*mm, 30*mm])
        t_itens.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), AZUL_ESCURO),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CINZA_CLARO]),
            ("BOX", (0, 0), (-1, -1), 0.7, AZUL_ESCURO),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, CINZA_BORDA),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(t_itens)
        story.append(Spacer(1, 3*mm))

        # Totais
        total_produtos = dados.get("total_produtos", 0)
        desconto_pct = dados.get("desconto_pct", 5.0)
        valor_desconto = dados.get("valor_desconto", 0)
        total_avista = dados.get("total_avista", total_produtos)
        frete = dados.get("frete", 0)
        frete_obs = dados.get("frete_obs", "A COMBINAR")
        total_geral = dados.get("total_geral", total_produtos)

        # Tabela de valores — só inclui linhas com conteúdo relevante (sem zeros vazios)
        totais_data = [
            [Paragraph("VALOR TOTAL DOS PRODUTOS", styles["ValorLabel"]),
             Paragraph(format_brl(total_produtos), styles["ValorDestaque"])],
        ]
        row_styles_extra = []  # índices de linhas especiais para cor de fundo

        if valor_desconto and valor_desconto > 0:
            totais_data.append([
                Paragraph(f"Desconto à vista ({desconto_pct:.1f}%)", styles["ValorLabel"]),
                Paragraph(f"− {format_brl(valor_desconto)}", styles["Desconto"]),
            ])
            totais_data.append([
                Paragraph("VALOR ESPECIAL À VISTA", styles["ValorLabel"]),
                Paragraph(format_brl(total_avista), styles["Desconto"]),
            ])

        if frete and frete > 0:
            totais_data.append([
                Paragraph(f"Frete ({frete_obs})" if frete_obs else "Frete", styles["ValorLabel"]),
                Paragraph(format_brl(frete), styles["ValorDestaque"]),
            ])

        v_difal_pr = float(dados.get("valor_difal_prazo") or 0)
        v_difal_av = float(dados.get("valor_difal_avista") or 0)
        difal_pr = dados.get("difal_prazo") or {}
        difal_av = dados.get("difal_avista") or {}

        if v_difal_pr > 0:
            totais_data.append([
                Paragraph("DIFAL (à prazo)", styles["ValorLabel"]),
                Paragraph(format_brl(v_difal_pr), styles["ValorDestaque"]),
            ])
        if v_difal_av > 0:
            totais_data.append([
                Paragraph("DIFAL (à vista)", styles["ValorLabel"]),
                Paragraph(format_brl(v_difal_av), styles["ValorDestaque"]),
            ])

        tc_pr = dados.get("total_cliente_prazo")
        tc_av = dados.get("total_cliente_avista")
        if tc_pr is not None:
            idx_pr = len(totais_data)
            totais_data.append([
                Paragraph("TOTAL ESTIMADO À PRAZO (produtos + frete + DIFAL)", styles["ValorLabel"]),
                Paragraph(format_brl(tc_pr), styles["ValorTotal"]),
            ])
            row_styles_extra.append(idx_pr)
        if tc_av is not None and (valor_desconto > 0 or v_difal_av > 0 or frete > 0):
            idx_av = len(totais_data)
            totais_data.append([
                Paragraph("TOTAL ESTIMADO À VISTA (produtos − desc. + frete + DIFAL)", styles["ValorLabel"]),
                Paragraph(format_brl(tc_av), styles["ValorTotal"]),
            ])
            row_styles_extra.append(idx_av)

        t_tot = Table(totais_data, colWidths=[125*mm, 50*mm])
        style_cmds = [
            ("BOX", (0, 0), (-1, -1), 1.2, AZUL_ESCURO),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, CINZA_BORDA),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ebf0f7")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]
        for idx in row_styles_extra:
            style_cmds.append(("BACKGROUND", (0, idx), (-1, idx), colors.HexColor("#e6fffa")))
        t_tot.setStyle(TableStyle(style_cmds))
        story.append(t_tot)
        story.append(Spacer(1, 3*mm))

        # Detalhe do DIFAL só se houver valor
        uf = (dados.get("cliente") or {}).get("uf") or ""
        if (v_difal_pr > 0 or v_difal_av > 0) and uf:
            origem = (difal_pr or difal_av or {}).get("uf_origem") or (dados.get("cliente") or {}).get("uf_origem") or "SC"
            inter = (difal_pr or difal_av or {}).get("aliquota_interestadual", 0)
            interna = (difal_pr or difal_av or {}).get("aliquota_interna_destino", 0)
            story.append(Paragraph(
                f"<font size='9'><b>DIFAL</b> ({origem} → {uf}): "
                f"interna destino {interna:.1f}% − interestadual {inter:.1f}%. "
                f"Orientativo — validar com o fiscal na NF.</font>",
                styles["CorpoPequeno"],
            ))

        val_ate = (dados.get("cotacao") or {}).get("validade_ate")
        val_txt = (dados.get("cotacao") or {}).get("validade", "7 dias")
        story.append(Paragraph(
            f"<b>Validade:</b> {val_txt}"
            + (f" — até <b>{val_ate}</b>" if val_ate else ""),
            styles["CorpoPequeno"],
        ))
        if dados.get("obs_item"):
            story.append(Paragraph(f"<b>Obs. itens:</b> {dados['obs_item']}", styles["CorpoPequeno"]))
        story.append(Spacer(1, 2*mm))

        story.append(Paragraph(
            f"<b>Prazo de fabricação:</b> {EMPRESA['prazo_fabricacao']} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>NCM:</b> {EMPRESA['ncm']} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Norma:</b> {EMPRESA['norma']}",
            styles["CorpoPequeno"]
        ))
        story.append(Paragraph(
            f"* Guincho Munck para descarga por conta do cliente. Imagem meramente ilustrativa.",
            styles["CorpoPequeno"]
        ))
        # Contato / site
        contato_extra = []
        if EMPRESA.get("site"):
            contato_extra.append(f"Site: {EMPRESA['site']}")
        if EMPRESA.get("whatsapp"):
            contato_extra.append(f"WhatsApp: {EMPRESA['whatsapp']}")
        if contato_extra:
            story.append(Paragraph(" · ".join(contato_extra), styles["CorpoPequeno"]))

        # ========== SIMULAÇÃO DE ECONOMIA ==========
        eco = dados.get("economia") or {}
        if eco.get("incluir"):
            story.append(Spacer(1, 4*mm))
            story.append(HRFlowable(width="100%", thickness=1, color=LARANJA, spaceBefore=2, spaceAfter=4))
            story.append(Paragraph(
                "SIMULAÇÃO DE ECONOMIA — ABASTECIMENTO VIA TRR",
                styles["Subtitulo"],
            ))
            story.append(Paragraph(
                f"Comprando <b>{eco.get('fluido_ref', 'Diesel')}</b> direto de uma TRR (com tanque próprio) "
                f"em vez de abastecer no posto, sua frota economiza a cada litro.",
                styles["Corpo"],
            ))

            pp = float(eco.get("preco_posto") or 0)
            pt = float(eco.get("preco_trr") or 0)
            el = float(eco.get("economia_litro") or 0)
            ep = float(eco.get("economia_pct") or 0)
            vol = int(eco.get("volume_simulado") or 0)
            et = float(eco.get("economia_total") or 0)

            cards = [[
                Paragraph(
                    f"<font size='8'>Preço médio no posto</font><br/>"
                    f"<font size='12'><b>{format_brl(pp)}</b></font><font size='8'> /L</font>",
                    styles["CorpoPequeno"],
                ),
                Paragraph(
                    f"<font size='8'>Preço médio na TRR</font><br/>"
                    f"<font size='12'><b>{format_brl(pt)}</b></font><font size='8'> /L</font>",
                    styles["CorpoPequeno"],
                ),
                Paragraph(
                    f"<font size='8'>Economia por litro</font><br/>"
                    f"<font size='12' color='#e65c00'><b>{format_brl(el)}</b></font><font size='8'> /L</font>",
                    styles["CorpoPequeno"],
                ),
                Paragraph(
                    f"<font size='8'>Economia percentual</font><br/>"
                    f"<font size='12' color='#276749'><b>{ep:.2f}%</b></font>",
                    styles["CorpoPequeno"],
                ),
            ]]
            t_cards = Table(cards, colWidths=[44*mm, 44*mm, 44*mm, 43*mm])
            t_cards.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.8, AZUL_ESCURO),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, CINZA_BORDA),
                ("BACKGROUND", (0, 0), (-1, -1), CINZA_CLARO),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(t_cards)
            story.append(Spacer(1, 3*mm))

            # Destaque principal
            story.append(Paragraph(
                f"<font size='11'><b>Economize até {format_brl(et)}</b> ao abastecer "
                f"<b>{vol:,} litros</b> via TRR "
                f"(diferença de {format_brl(el)} por litro).</font>".replace(",", "."),
                styles["Corpo"],
            ))

            # Economia mensal / anual
            cons_m = int(eco.get("consumo_mensal") or 0)
            eco_m = float(eco.get("economia_mensal") or 0)
            eco_a = float(eco.get("economia_anual") or 0)
            if cons_m > 0 and eco_m > 0:
                story.append(Paragraph(
                    f"<font size='10'>Com consumo estimado de <b>{cons_m:,} L/mês</b>: "
                    f"economia de <font color='#e65c00'><b>{format_brl(eco_m)}</b></font> por mês · "
                    f"<font color='#276749'><b>{format_brl(eco_a)}</b></font> em 12 meses.</font>".replace(",", "."),
                    styles["Corpo"],
                ))
            story.append(Spacer(1, 2*mm))

            # Gráfico de economia mensal (barras + linha acumulada)
            try:
                import matplotlib
                matplotlib.use("Agg")
                import matplotlib.pyplot as plt
                from io import BytesIO as _Bio

                serie = eco.get("serie_mensal") or []
                if not serie and eco_m > 0:
                    acum = 0.0
                    serie = []
                    for m in range(1, 13):
                        acum += eco_m
                        serie.append({"mes": m, "economia_mes": eco_m, "acumulado": acum})

                if serie:
                    meses_lbl = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
                                 "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
                    vals_mes = [float(s.get("economia_mes") or 0) for s in serie[:12]]
                    vals_acum = [float(s.get("acumulado") or 0) for s in serie[:12]]
                    while len(vals_mes) < 12:
                        vals_mes.append(eco_m)
                    while len(vals_acum) < 12:
                        prev = vals_acum[-1] if vals_acum else 0
                        vals_acum.append(prev + eco_m)

                    fig, ax1 = plt.subplots(figsize=(7.2, 2.8), dpi=140)
                    x = list(range(12))
                    ax1.bar(x, vals_mes, color="#e65c00", alpha=0.88, width=0.65, label="Economia no mês")
                    ax1.set_ylabel("No mês (R$)", color="#e65c00", fontsize=8)
                    ax1.tick_params(axis="y", labelcolor="#e65c00", labelsize=7)
                    ax1.set_xticks(x)
                    ax1.set_xticklabels(meses_lbl, fontsize=7)
                    ax1.set_ylim(0, max(vals_mes) * 1.35 if max(vals_mes) > 0 else 1)
                    ax1.spines["top"].set_visible(False)
                    ax1.spines["right"].set_visible(False)

                    ax2 = ax1.twinx()
                    ax2.plot(x, vals_acum, color="#1a365d", marker="o", markersize=3.5,
                             linewidth=2, label="Acumulado")
                    ax2.set_ylabel("Acumulado (R$)", color="#1a365d", fontsize=8)
                    ax2.tick_params(axis="y", labelcolor="#1a365d", labelsize=7)
                    ax2.set_ylim(0, max(vals_acum) * 1.15 if max(vals_acum) > 0 else 1)
                    ax2.spines["top"].set_visible(False)

                    ax1.set_title(
                        "Economia mensal estimada com abastecimento via TRR",
                        fontsize=9, color="#1a365d", pad=6,
                    )
                    fig.tight_layout(pad=0.4)
                    buf = _Bio()
                    fig.savefig(buf, format="png", bbox_inches="tight", facecolor="white")
                    plt.close(fig)
                    buf.seek(0)
                    chart_img = Image(buf, width=170*mm, height=58*mm)
                    story.append(chart_img)
                    story.append(Spacer(1, 2*mm))
            except Exception:
                pass  # segue sem gráfico se matplotlib falhar

            # Tabela por volume
            tab = eco.get("tabela") or []
            if tab:
                rows_e = [[
                    Paragraph("<b>Volume abastecido</b>", styles["CorpoPequeno"]),
                    Paragraph("<b>Economia total</b>", styles["CorpoPequeno"]),
                ]]
                for row in tab:
                    v = int(row.get("volume") or 0)
                    e = float(row.get("economia") or 0)
                    destaque = v == vol
                    label_v = f"{v:,} L".replace(",", ".")
                    if destaque:
                        rows_e.append([
                            Paragraph(f"<b>{label_v}</b> ← tanque / simulação", styles["CorpoPequeno"]),
                            Paragraph(f"<b>{format_brl(e)}</b>", styles["Desconto"]),
                        ])
                    else:
                        rows_e.append([
                            Paragraph(label_v, styles["CorpoPequeno"]),
                            Paragraph(format_brl(e), styles["CorpoPequeno"]),
                        ])
                t_eco = Table(rows_e, colWidths=[90*mm, 85*mm])
                t_eco.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), AZUL_ESCURO),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("BOX", (0, 0), (-1, -1), 0.7, AZUL_ESCURO),
                    ("INNERGRID", (0, 0), (-1, -1), 0.3, CINZA_BORDA),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CINZA_CLARO]),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                story.append(t_eco)

            story.append(Paragraph(
                "<font size='7'><i>* Simulação orientativa com base nos preços médios informados nesta proposta. "
                "Valores de combustível oscilam conforme região e momento da compra.</i></font>",
                styles["CorpoPequeno"],
            ))

    # ========== ESPECIFICAÇÕES TÉCNICAS (modo completa) ==========
    if modo == "completa":
        story.append(Spacer(1, 4*mm))
        story.append(HRFlowable(width="100%", thickness=0.8, color=CINZA_BORDA, spaceBefore=2, spaceAfter=4))
        story.append(Paragraph("ESPECIFICAÇÕES TÉCNICAS", styles["Subtitulo"]))

        tanque_sel = dados.get("tanque_key", "10.000L")
        bacia_sel = dados.get("bacia_key", "10.000L")
        tinfo = TANQUES.get(tanque_sel, {})
        binfo = BACIAS.get(bacia_sel, {})

        story.append(Paragraph("<b>Tanque Aéreo Horizontal – Aço Carbono ASTM A-36</b>", styles["CorpoPequeno"]))
        specs_t = [
            f"• Capacidade: {tinfo.get('label', tanque_sel)}",
            f"• Diâmetro: {tinfo.get('diametro', '—')}",
            f"• Comprimento: {tinfo.get('comprimento', '—')}",
            f"• Espessura da chapa: {tinfo.get('chapa', '—')}",
            f"• Peso aproximado: {tinfo.get('peso', 0)} kg",
            f"• Fluido: {dados.get('fluido', TEXTOS['fluido_padrao'])}",
            f"• Tratamento interno: {TEXTOS['tratamento_interno_tanque']}",
            f"• Tratamento externo: {TEXTOS['tratamento_externo']}",
            f"• Pressão de trabalho: {TEXTOS['pressao']}",
            f"• Temperatura: {TEXTOS['temperatura']}",
            f"• Padrão de fabricação: {EMPRESA['norma']}",
        ]
        for s in specs_t:
            story.append(Paragraph(s, styles["ItemLista"]))

        if bacia_sel != "SEM BACIA":
            story.append(Spacer(1, 2*mm))
            story.append(Paragraph("<b>Bacia de Contenção</b>", styles["CorpoPequeno"]))
            specs_b = [
                f"• Capacidade: {binfo.get('label', bacia_sel)}",
                f"• Largura: {binfo.get('largura', '—')}",
                f"• Altura: {binfo.get('altura', '—')}",
                f"• Comprimento: {binfo.get('comprimento', '—')}",
                f"• Espessura da chapa: {binfo.get('chapa', '—')}",
                f"• Peso aproximado: {binfo.get('peso', 0)} kg",
                f"• Tratamento interno: Limpeza Mecânica (sem pintura)",
                f"• Tratamento externo: {TEXTOS['tratamento_externo']}",
            ]
            for s in specs_b:
                story.append(Paragraph(s, styles["ItemLista"]))

        story.append(Spacer(1, 2*mm))
        story.append(Paragraph("<b>Acessórios padrão inclusos</b>", styles["CorpoPequeno"]))
        acessorios = [
            "01 Bocal de saída 1.1/2''",
            "01 Bocal de entrada 4''",
            "03 Bocais para 2''",
            "02 Bocais de dreno 3/4''",
            "01 Bocal de visita",
            "02 Berços de apoio com 200mm de altura",
            "02 Alças de içamento",
            "01 Válvula de Segurança Get Fuel",
            "Todos os bocais em meia luva com rosca interna BSP + bujões em PVC",
        ]
        for a in acessorios:
            story.append(Paragraph(f"• {a}", styles["ItemLista"]))

        peso_total = tinfo.get("peso", 0) + binfo.get("peso", 0)
        story.append(Paragraph(f"<b>Peso total aproximado do conjunto:</b> {peso_total} kg", styles["CorpoPequeno"]))
        story.append(Paragraph(f"<b>Documentação que acompanha:</b> {TEXTOS['acompanha']}", styles["CorpoPequeno"]))

    # ========== CONDIÇÕES / GARANTIA / CONTRATO ==========
    if modo in ("completa", "condicoes"):
        if modo == "completa":
            story.append(PageBreak())
            # Mini cabeçalho na página 2
            story.append(Paragraph(f"<b>{EMPRESA['nome']}</b> – Condições Comerciais e Garantias", styles["Subtitulo"]))
            story.append(HRFlowable(width="100%", thickness=1, color=AZUL_ESCURO, spaceBefore=1, spaceAfter=4))

        story.append(Paragraph("1. CONDIÇÕES COMERCIAIS", styles["Subtitulo"]))
        story.append(Paragraph(
            "Os valores apresentados são para pagamento nas condições abaixo. "
            "<b>Caso o cliente não seja contribuinte de ICMS, poderá ser adicionado o diferencial de alíquota conforme o estado de destino.</b>",
            styles["Corpo"]
        ))

        # Forma de pagamento dinâmica (parcelas definidas pelo vendedor)
        parcelas = dados.get("parcelas") or []
        base_parc = dados.get("base_parcela", dados.get("total_produtos", 0))
        if parcelas:
            story.append(Paragraph(
                f"<b>Forma de pagamento:</b> (sobre {format_brl(base_parc)})",
                styles["Corpo"],
            ))
            rows_p = [[
                Paragraph("<b>Etapa</b>", styles["CorpoPequeno"]),
                Paragraph("<b>%</b>", styles["CorpoPequeno"]),
                Paragraph("<b>Valor</b>", styles["CorpoPequeno"]),
            ]]
            for p in parcelas:
                rows_p.append([
                    Paragraph(str(p.get("label", "")), styles["CorpoPequeno"]),
                    Paragraph(f"{p.get('pct', 0):.1f}%", styles["CorpoPequeno"]),
                    Paragraph(format_brl(p.get("valor", 0)), styles["CorpoPequeno"]),
                ])
            t_parc = Table(rows_p, colWidths=[90*mm, 30*mm, 50*mm])
            t_parc.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), AZUL_ESCURO),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.6, AZUL_ESCURO),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, CINZA_BORDA),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CINZA_CLARO]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            story.append(t_parc)
            story.append(Spacer(1, 2*mm))
            story.append(Paragraph(
                "Alternativamente: parcelamento no cartão de crédito em até 6x (sujeito a juros da operadora).",
                styles["Corpo"],
            ))
        else:
            story.append(Paragraph(
                "<b>Forma de pagamento sugerida:</b> 30% de entrada no ato do pedido + 30% no embarque + 40% faturado "
                "mediante análise financeira e aprovação de cadastro. "
                "Alternativamente: parcelamento no cartão de crédito em até 6x (sujeito a juros da operadora).",
                styles["Corpo"],
            ))

        story.append(Paragraph(
            f"<b>Prazo de fabricação:</b> {EMPRESA['prazo_fabricacao']} após confirmação do pagamento da entrada e formalização do pedido.",
            styles["Corpo"]
        ))
        _val = cotacao.get("validade", "7 dias")
        _ate = cotacao.get("validade_ate")
        story.append(Paragraph(
            f"<b>Validade desta proposta:</b> {_val}"
            + (f" (até <b>{_ate}</b>)." if _ate else "."),
            styles["Corpo"]
        ))

        story.append(Paragraph("2. GARANTIA", styles["Subtitulo"]))
        story.append(Paragraph(
            f"Garantimos o tanque e a bacia de contenção contra defeitos de fabricação pelo período de "
            f"<b>{EMPRESA['garantia_meses']} (seis) meses</b>, contados a partir da data de emissão da Nota Fiscal, "
            "desde que observados os procedimentos de instalação, operação e manutenção recomendados. "
            "Em caso de necessidade de reparo, o equipamento deverá ser enviado à fábrica.",
            styles["Corpo"]
        ))
        story.append(Paragraph(
            "Bombas e filtros: garantia conforme o fabricante do equipamento (geralmente 90 dias a 12 meses). "
            "Estão excluídos da garantia: desgaste normal, uso inadequado, líquidos incompatíveis, influências climáticas, "
            "modificações ou consertos realizados por terceiros sem autorização prévia por escrito.",
            styles["Corpo"]
        ))

        story.append(Paragraph("3. RESPONSABILIDADES", styles["Subtitulo"]))
        story.append(Paragraph("<b>Do Fornecedor (Casa do Frentista / GP Company):</b>", styles["CorpoPequeno"]))
        story.append(Paragraph("• Fabricação, soldagem e pintura do tanque e bacia conforme normas aplicáveis.", styles["ItemLista"]))
        story.append(Paragraph("• Fornecimento da documentação técnica listada (Data book, ART, etc.).", styles["ItemLista"]))
        story.append(Paragraph("• Transporte até o local combinado (quando incluso no valor ou frete contratado).", styles["ItemLista"]))

        story.append(Paragraph("<b>Do Comprador:</b>", styles["CorpoPequeno"]))
        story.append(Paragraph("<font size='9'><b>• Acesso rodoviário livre e desimpedido para descarga.</b></font>", styles["ItemLista"]))
        story.append(Paragraph("<font size='9'><b>• Descarregamento com guincho Munck por conta do cliente.</b></font>", styles["ItemLista"]))
        story.append(Paragraph("<font size='9'><b>• Preparação da base de apoio (concreto ou estrutura adequada).</b></font>", styles["ItemLista"]))
        story.append(Paragraph("<font size='9'><b>• Obtenção de licenças e alvarás locais, quando exigidos.</b></font>", styles["ItemLista"]))


        story.append(Paragraph("4. OBSERVAÇÕES GERAIS / CLÁUSULAS", styles["Subtitulo"]))
        story.append(Paragraph(
            "• Todo item não descrito expressamente nesta proposta não está incluso no escopo e no valor.",
            styles["ItemLista"]
        ))
        story.append(Paragraph(
            "• Exigências adicionais de testes, documentação extra ou plano de rigging serão cobradas à parte e devem ser informadas no fechamento.",
            styles["ItemLista"]
        ))
        story.append(Paragraph(
            "• Em caso de cancelamento do pedido pelo comprador após confirmação, será aplicada multa de 10% sobre o valor do contrato.",
            styles["ItemLista"]
        ))
        story.append(Paragraph(
            "• A presente proposta tem caráter comercial e técnico. A formalização se dará mediante pedido de compra ou contrato assinado pelas partes.",
            styles["ItemLista"]
        ))

        story.append(Spacer(1, 8*mm))
        story.append(Paragraph(
            "Agradecemos a oportunidade e colocamo-nos à disposição para quaisquer esclarecimentos.",
            styles["Corpo"]
        ))
        story.append(Spacer(1, 10*mm))

        # Assinaturas
        ass_data = [
            [Paragraph("_________________________________<br/><b>Casa do Frentista</b><br/>GP Company", styles["CorpoPequeno"]),
             Paragraph("_________________________________<br/><b>Cliente / Representante</b>", styles["CorpoPequeno"])],
        ]
        t_ass = Table(ass_data, colWidths=[90*mm, 90*mm])
        t_ass.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(t_ass)

    # Build
    doc.build(story, onFirstPage=cabecalho, onLaterPages=cabecalho)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
