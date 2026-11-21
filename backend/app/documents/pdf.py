"""Documentos A4 imprimibles para el entorno de demostración.

No implementa registros ni códigos fiscales de VERI*FACTU.
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

INK = colors.HexColor("#0f172a")
MUTED = colors.HexColor("#64748b")
GREEN = colors.HexColor("#047857")
BORDER = colors.HexColor("#e2e8f0")
LIGHT = colors.HexColor("#f8fafc")
WARNING = colors.HexColor("#9f1239")


@dataclass(frozen=True)
class Party:
    name: str
    tax_id: str | None = None
    address: str | None = None
    postal_code: str | None = None
    city: str | None = None
    province: str | None = None
    country_code: str | None = None


@dataclass(frozen=True)
class Line:
    description: str
    quantity: Decimal
    unit_price: Decimal | None = None
    tax_rate: Decimal | None = None
    total_amount: Decimal | None = None


@dataclass(frozen=True)
class PrintableDocument:
    kind: str
    identifier: str
    status: str
    document_date: date | datetime
    issuer: Party
    recipient: Party
    lines: tuple[Line, ...]
    subtotal: Decimal | None = None
    tax_total: Decimal | None = None
    total_amount: Decimal | None = None
    notes: str | None = None
    references: tuple[str, ...] = ()
    operation_date: date | None = None


def money(value: Decimal | None) -> str:
    if value is None:
        return "-"
    formatted = f"{value:,.2f}".replace(",", "_").replace(".", ",")
    return f"{formatted.replace('_', '.')} EUR"


def quantity(value: Decimal) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".").replace(".", ",")


def spanish_date(value: date | datetime) -> str:
    if isinstance(value, datetime):
        value = value.date()
    return value.strftime("%d/%m/%Y")


def p(text: str | None, style: ParagraphStyle) -> Paragraph:
    # Escapar datos introducidos por clientes/negocios antes de construir ReportLab.
    return Paragraph(escape(str(text or "-")), style)


def _footer(canvas, document) -> None:
    canvas.saveState()
    width, _ = A4
    canvas.setStrokeColor(BORDER)
    canvas.line(17 * mm, 17 * mm, width - 17 * mm, 17 * mm)
    canvas.setFont("Helvetica-Bold", 7.5)
    canvas.setFillColor(WARNING)
    canvas.drawString(
        17 * mm,
        12 * mm,
        "DOCUMENTO DE DEMOSTRACIÓN - NO APTO PARA USO FISCAL",
    )
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(width - 17 * mm, 12 * mm, f"Página {document.page}")
    canvas.restoreState()


def _party_lines(party: Party) -> list[str]:
    result = [party.name]
    if party.tax_id:
        result.append(f"NIF/CIF: {party.tax_id}")
    if party.address:
        result.append(party.address)
    locality = " ".join(
        chunk for chunk in (party.postal_code, party.city) if chunk
    )
    if locality:
        result.append(locality)
    if party.province:
        result.append(party.province)
    if party.country_code:
        result.append(party.country_code)
    return result


def build_pdf(document: PrintableDocument) -> bytes:
    """Construye bytes PDF sin modificar ninguna entidad ni generar registros fiscales."""
    titles = {
        "order": "PEDIDO",
        "delivery_note": "ALBARÁN DE ENTREGA",
        "invoice": "FACTURA DE DEMOSTRACIÓN",
    }
    if document.kind not in titles:
        raise ValueError("Tipo de documento no admitido")
    if document.kind == "invoice" and document.status != "ISSUED":
        raise ValueError("Solo se pueden imprimir facturas emitidas")

    buffer = BytesIO()
    pdf = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=17 * mm,
        leftMargin=17 * mm,
        topMargin=23 * mm,
        bottomMargin=26 * mm,
        title=f"{titles[document.kind]} {document.identifier}",
        author="VeriFactu App - demostración",
        pageCompression=1,
    )

    title_style = ParagraphStyle(
        "TitlePDF", fontName="Helvetica-Bold", fontSize=20,
        leading=24, textColor=INK, spaceAfter=7,
    )
    subtitle_style = ParagraphStyle(
        "SubtitlePDF", fontName="Helvetica", fontSize=10,
        leading=14, textColor=MUTED,
    )
    label_style = ParagraphStyle(
        "LabelPDF", fontName="Helvetica-Bold", fontSize=9,
        leading=13, textColor=GREEN, spaceAfter=5,
    )
    text_style = ParagraphStyle(
        "TextPDF", fontName="Helvetica", fontSize=9,
        leading=13, textColor=INK, spaceAfter=3,
    )
    table_style = ParagraphStyle(
        "TablePDF", parent=text_style, fontSize=8.5, leading=11,
    )
    right_style = ParagraphStyle(
        "RightPDF", parent=table_style, alignment=TA_RIGHT,
    )
    notes_style = ParagraphStyle(
        "NotesPDF", parent=text_style, alignment=TA_LEFT,
        leading=14,
    )

    story = []
    header = Table(
        [[p(titles[document.kind], title_style),
          p(document.identifier, subtitle_style)]],
        colWidths=[118 * mm, 58 * mm],
    )
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.extend([header, Spacer(1, 5 * mm)])

    state_labels = {
        "DRAFT": "BORRADOR",
        "CONFIRMED": "CONFIRMADO",
        "CANCELLED": "CANCELADO",
        "ISSUED": "EMITIDO",
    }
    state = state_labels.get(document.status, document.status)
    story.append(p(f"Estado: {state}    |    Fecha: {spanish_date(document.document_date)}", subtitle_style))
    story.append(Spacer(1, 5 * mm))

    if document.kind == "invoice":
        warning = p(
            "IMPORTANTE: Factura generada en un prototipo. "
            "No cumple aún los requisitos de VERI*FACTU "
            "y no debe utilizarse como factura fiscal real.",
            ParagraphStyle(
                "WarningPDF", parent=text_style,
                fontName="Helvetica-Bold", textColor=WARNING,
                fontSize=9, leading=13,
            ),
        )
        box = Table([[warning]], colWidths=[176 * mm])
        box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff1f2")),
            ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#fecdd3")),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.extend([box, Spacer(1, 7 * mm)])

    def party_block(heading: str, value: Party):
        block = [p(heading, label_style)]
        for text in _party_lines(value):
            block.append(p(text, text_style))
        return block

    party_table = Table(
        [[party_block("EMISOR", document.issuer),
          party_block("CLIENTE", document.recipient)]],
        colWidths=[88 * mm, 88 * mm],
    )
    party_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.4, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.extend([party_table, Spacer(1, 7 * mm)])

    if document.references or document.operation_date:
        detail = []
        if document.operation_date:
            detail.append(f"Fecha de operación: {spanish_date(document.operation_date)}")
        detail.extend(document.references)
        story.append(p("  |  ".join(detail), text_style))
        story.append(Spacer(1, 3 * mm))

    story.append(p("DETALLE", label_style))
    if document.kind == "delivery_note":
        widths = [142 * mm, 34 * mm]
        rows = [[p("Descripción", table_style), p("Cantidad", right_style)]]
        for line in document.lines:
            rows.append([
                p(line.description, table_style),
                p(quantity(line.quantity), right_style),
            ])
    else:
        widths = [77 * mm, 19 * mm, 27 * mm, 20 * mm, 33 * mm]
        rows = [[p(x, table_style) for x in
                 ("Descripción", "Cantidad", "Precio", "IVA", "Importe")]]
        for line in document.lines:
            rows.append([
                p(line.description, table_style),
                p(quantity(line.quantity), right_style),
                p(money(line.unit_price), right_style),
                p(f"{str(line.tax_rate.normalize()).replace('.', ',')}%" if line.tax_rate is not None else "-", right_style),
                p(money(line.total_amount), right_style),
            ])
    table = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d1fae5")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, GREEN),
        ("LINEBELOW", (0, 1), (-1, -1), 0.25, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    story.extend([table, Spacer(1, 6 * mm)])

    if document.kind != "delivery_note":
        total_rows = [
            [p("Base imponible", text_style), p(money(document.subtotal), right_style)],
            [p("IVA", text_style), p(money(document.tax_total), right_style)],
            [p("TOTAL", label_style), p(money(document.total_amount), right_style)],
        ]
        total_table = Table(total_rows, colWidths=[48 * mm, 38 * mm], hAlign="RIGHT")
        total_table.setStyle(TableStyle([
            ("LINEABOVE", (0, 2), (-1, 2), 0.8, GREEN),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.extend([KeepTogether(total_table), Spacer(1, 6 * mm)])

    if document.notes:
        note_lines = str(document.notes).splitlines()
        note_block = [p("OBSERVACIONES", label_style)]
        note_block.extend(p(line or " ", notes_style) for line in note_lines)
        story.extend([HRFlowable(width="100%", color=BORDER), Spacer(1, 4 * mm), *note_block])

    if document.kind == "delivery_note":
        story.extend([
            Spacer(1, 10 * mm),
            p("Documento de entrega. No equivale a una factura.", subtitle_style),
        ])
    if document.status == "CANCELLED":
        story.append(p("DOCUMENTO CANCELADO - SIN EFECTOS COMERCIALES", label_style))
    elif document.status == "DRAFT":
        story.append(p("BORRADOR - NO ES UN DOCUMENTO DEFINITIVO", label_style))

    pdf.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()
