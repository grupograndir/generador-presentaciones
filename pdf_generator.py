"""
Generador de PDF de presentación para informes de viabilidad.
Usa reportlab con layout horizontal (landscape A4), fondo blanco,
títulos con fondo azul claro, portada con imagen, e índice con links internos.
"""

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image,
    Table, TableStyle, LongTable, Flowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.utils import ImageReader
from PIL import Image as PILImage
import os
import traceback

# ── Constantes de diseño ──
AZUL_OSCURO = colors.HexColor('#0d233a')
AZUL_CLARO_BG = colors.HexColor('#d6eaf8')
AZUL_CLARO_TEXT = colors.HexColor('#1a5276')
COLOR_TEXTO = colors.HexColor('#333333')
PAGE_W, PAGE_H = landscape(A4)
MARGIN = 2 * cm
CONTENT_W = PAGE_W - 2 * MARGIN


# ── Flowable personalizado para bookmarks ──
class BookmarkAnchor(Flowable):
    """Flowable invisible que registra un bookmark/destino en el PDF."""
    def __init__(self, key):
        Flowable.__init__(self)
        self.key = key
        self.width = 0
        self.height = 0

    def draw(self):
        self.canv.bookmarkPage(self.key)


# ── Estilos ──
_styles_cache = None

def _get_styles():
    global _styles_cache
    if _styles_cache:
        return _styles_cache

    base = getSampleStyleSheet()
    _styles_cache = {
        'body': ParagraphStyle(
            'BodyCustom', parent=base['Normal'],
            fontName='Helvetica', fontSize=11, textColor=COLOR_TEXTO,
            alignment=TA_JUSTIFY, leading=17, spaceAfter=10,
        ),
        'body_center': ParagraphStyle(
            'BodyCenter', parent=base['Normal'],
            fontName='Helvetica', fontSize=11, textColor=COLOR_TEXTO,
            alignment=TA_CENTER, leading=17, spaceAfter=10,
        ),
    }
    return _styles_cache


# ── Componentes reutilizables ──
def _section_header(title_text):
    """Barra de título de sección con fondo azul claro."""
    para = Paragraph(
        title_text,
        ParagraphStyle(
            f'SH_{title_text[:10]}', fontName='Helvetica-Bold', fontSize=18,
            textColor=AZUL_OSCURO, alignment=TA_LEFT, leading=26,
        )
    )
    t = Table([[para]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), AZUL_CLARO_BG),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
    ]))
    return t


def _validate_image(path):
    """Verifica que un archivo de imagen sea válido y legible."""
    if not path or not os.path.exists(path):
        return False
    try:
        img = PILImage.open(path)
        img.verify()
        return True
    except Exception:
        return False


def _safe_image(path, width, height):
    """Crea un objeto Image de reportlab de forma segura."""
    try:
        img = Image(path, width=width, height=height)
        img.hAlign = 'CENTER'
        return img
    except Exception as e:
        print(f"[WARN] No se pudo cargar la imagen {path}: {e}")
        return None


def _add_gallery(story, image_paths, max_per_page=4):
    """Añade imágenes en grid de 2 columnas."""
    valid_images = [p for p in image_paths if _validate_image(p)]
    if not valid_images:
        return

    img_w = (CONTENT_W - 1 * cm) / 2
    img_h = img_w * 0.6
    col_w = img_w + 0.5 * cm

    row = []
    placed = 0
    for img_path in valid_images:
        img_obj = _safe_image(img_path, img_w, img_h)
        if img_obj is None:
            continue
        row.append(img_obj)
        placed += 1

        if len(row) == 2:
            t = Table([row], colWidths=[col_w, col_w])
            t.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.4 * cm))
            row = []
            if placed % max_per_page == 0 and placed < len(valid_images):
                story.append(PageBreak())

    # Fila incompleta
    if row:
        while len(row) < 2:
            row.append(Paragraph('', _get_styles()['body']))
        t = Table([row], colWidths=[col_w, col_w])
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(t)


def _property_table(story, title, items):
    """Tabla de propiedades (viviendas/garajes/trasteros)."""
    if not items:
        return
    styles = _get_styles()
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(f"<b>{title}</b>", styles['body']))
    story.append(Spacer(1, 0.2 * cm))

    data = [['Tipología', 'Planta', 'Puerta', 'Habs.', 'Superficie', 'Precio']]
    for it in items:
        habs_val = str(it.get("Habs", ""))
        if " Habs" in habs_val:
            habs_val = habs_val.replace(" Habs", "")
        data.append([
            str(it.get("Tipología original", "")),
            str(it.get("Planta", "")),
            str(it.get("Puerta", "")),
            habs_val,
            str(it.get("Constr.", "")),
            str(it.get("Precio", "")),
        ])

    t = LongTable(data, colWidths=[5*cm, 2.5*cm, 2.5*cm, 2*cm, 3.5*cm, 4*cm], repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL_OSCURO),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 7),
        ('TOPPADDING', (0, 0), (-1, 0), 7),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),
    ]))
    story.append(t)


# ── Función principal ──
def generate_presentation_pdf(
    output_path,
    financial_data,
    image_paths_by_category,
    project_title,
    text_sections,
):
    """
    Genera el PDF de presentación de viabilidad.

    Args:
        output_path: ruta del PDF de salida
        financial_data: dict con datos financieros del Excel
        image_paths_by_category: dict con keys 'portada','fachada','interior'
        project_title: nombre del proyecto
        text_sections: dict con keys 'resumen','estudio_mercado','gestor','riesgos'
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(A4),
        rightMargin=MARGIN, leftMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
    )
    styles = _get_styles()
    story = []

    portada_images = image_paths_by_category.get('portada', [])
    fachada_images = image_paths_by_category.get('fachada', [])
    interior_images = image_paths_by_category.get('interior', [])
    viviendas = financial_data.get("viviendas", [])
    garajes = financial_data.get("garajes", [])
    trasteros = financial_data.get("trasteros", [])

    # ════════════════════════════════════════
    # PÁGINA 1 — PORTADA
    # ════════════════════════════════════════
    cover_img_path = portada_images[0] if portada_images else None
    if cover_img_path and _validate_image(cover_img_path):
        img = _safe_image(cover_img_path, CONTENT_W, 12 * cm)
        if img:
            story.append(Spacer(1, 0.5 * cm))
            story.append(img)
        else:
            story.append(Spacer(1, 6 * cm))
    else:
        story.append(Spacer(1, 6 * cm))

    # Título en barra azul oscura
    title_para = Paragraph(
        project_title.upper(),
        ParagraphStyle(
            'CoverTitle', fontName='Helvetica-Bold', fontSize=28,
            textColor=colors.white, alignment=TA_CENTER, leading=36,
        )
    )
    title_table = Table([[title_para]], colWidths=[CONTENT_W])
    title_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), AZUL_OSCURO),
        ('TOPPADDING', (0, 0), (-1, -1), 16),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 16),
        ('LEFTPADDING', (0, 0), (-1, -1), 20),
        ('RIGHTPADDING', (0, 0), (-1, -1), 20),
    ]))
    story.append(Spacer(1, 0.8 * cm))
    story.append(title_table)

    # Subtítulo
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(
        "INFORME DE VIABILIDAD",
        ParagraphStyle(
            'CoverSub', fontName='Helvetica', fontSize=14,
            textColor=AZUL_OSCURO, alignment=TA_CENTER, spaceAfter=20,
        )
    ))
    story.append(PageBreak())

    # ════════════════════════════════════════
    # PÁGINA 2 — ÍNDICE
    # ════════════════════════════════════════
    story.append(_section_header("ÍNDICE"))
    story.append(Spacer(1, 1.2 * cm))

    # Construir lista de secciones dinámicamente
    toc = []
    n = 1
    if text_sections.get('resumen'):
        toc.append((n, "Resumen", "sec_resumen")); n += 1
    if text_sections.get('estudio_mercado'):
        toc.append((n, "Estudio de Mercado", "sec_estudio")); n += 1
    toc.append((n, "Análisis Financiero", "sec_financiero")); n += 1
    if fachada_images:
        toc.append((n, "Galería: Fachada", "sec_fachada")); n += 1
    if interior_images:
        toc.append((n, "Galería: Interior", "sec_interior")); n += 1
    if text_sections.get('gestor'):
        toc.append((n, "Gestor", "sec_gestor")); n += 1
    if text_sections.get('riesgos'):
        toc.append((n, "Riesgos", "sec_riesgos")); n += 1
    if viviendas or garajes or trasteros:
        toc.append((n, "Anexos: Listado de Unidades", "sec_anexos"))

    # Tabla de índice con links internos
    idx_rows = []
    for num, name, key in toc:
        link = f'<a href="#{key}" color="#1a5276">{num}. {name}</a>'
        idx_rows.append([Paragraph(
            link,
            ParagraphStyle(
                f'Idx_{key}', fontName='Helvetica', fontSize=13,
                textColor=AZUL_CLARO_TEXT, leading=20, leftIndent=15,
            )
        )])

    if idx_rows:
        idx_t = Table(idx_rows, colWidths=[CONTENT_W * 0.75])
        idx_t.setStyle(TableStyle([
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ('LEFTPADDING', (0, 0), (-1, -1), 25),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#e5e7eb')),
        ]))
        story.append(idx_t)

    story.append(PageBreak())

    # ════════════════════════════════════════
    # SECCIÓN: RESUMEN
    # ════════════════════════════════════════
    if text_sections.get('resumen'):
        story.append(BookmarkAnchor("sec_resumen"))
        story.append(_section_header("Resumen"))
        story.append(Spacer(1, 0.6 * cm))
        txt = text_sections['resumen'].replace('\n', '<br/>')
        story.append(Paragraph(txt, styles['body']))
        story.append(PageBreak())

    # ════════════════════════════════════════
    # SECCIÓN: ESTUDIO DE MERCADO
    # ════════════════════════════════════════
    if text_sections.get('estudio_mercado'):
        story.append(BookmarkAnchor("sec_estudio"))
        story.append(_section_header("Estudio de Mercado"))
        story.append(Spacer(1, 0.6 * cm))
        txt = text_sections['estudio_mercado'].replace('\n', '<br/>')
        story.append(Paragraph(txt, styles['body']))
        story.append(PageBreak())

    # ════════════════════════════════════════
    # SECCIÓN: ANÁLISIS FINANCIERO
    # ════════════════════════════════════════
    story.append(BookmarkAnchor("sec_financiero"))
    story.append(_section_header("Análisis Financiero"))
    story.append(Spacer(1, 0.6 * cm))

    story.append(Paragraph(
        "El modelo financiero se ha construido sobre presupuestos de ejecución material (PEM) "
        "rigurosos y estimaciones de ventas sustentadas por transacciones reales en el área "
        "de influencia del proyecto.",
        styles['body']
    ))
    story.append(Spacer(1, 0.4 * cm))

    fin_rows = [
        ['CONCEPTO', 'IMPORTE (€)'],
        ['Coste Adquisición Suelo + Estruct.', f"{financial_data.get('coste_adquisicion', 0):,.2f} €"],
        ['Coste Terminación (Construcción)', f"{financial_data.get('coste_terminacion', 0):,.2f} €"],
        ['TOTAL INVERSIÓN ESTIMADA', f"{financial_data.get('total_inversion', 0):,.2f} €"],
        ['TOTAL INGRESOS POR VENTAS', f"{financial_data.get('total_ventas', 0):,.2f} €"],
        ['BENEFICIO BRUTO ESTIMADO', f"{financial_data.get('beneficio_bruto', 0):,.2f} €"],
        ['RENTABILIDAD (ROI)', f"{financial_data.get('roi', 0):.2f} %"],
    ]
    fin_t = Table(fin_rows, colWidths=[14 * cm, 6 * cm])
    fin_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL_OSCURO),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
    ]))
    story.append(fin_t)
    story.append(Spacer(1, 0.6 * cm))

    roi = financial_data.get('roi', 0)
    story.append(Paragraph(
        f"El proyecto genera retornos del <b>{roi:.2f}%</b>, asumiendo un escenario "
        "conservador de venta.",
        styles['body']
    ))

    # ════════════════════════════════════════
    # GALERÍAS DE FOTOS
    # ════════════════════════════════════════
    if fachada_images:
        story.append(PageBreak())
        story.append(BookmarkAnchor("sec_fachada"))
        story.append(_section_header("Galería: Fachada"))
        story.append(Spacer(1, 0.6 * cm))
        _add_gallery(story, fachada_images)

    if interior_images:
        story.append(PageBreak())
        story.append(BookmarkAnchor("sec_interior"))
        story.append(_section_header("Galería: Interior"))
        story.append(Spacer(1, 0.6 * cm))
        _add_gallery(story, interior_images)

    # ════════════════════════════════════════
    # SECCIÓN: GESTOR
    # ════════════════════════════════════════
    if text_sections.get('gestor'):
        story.append(PageBreak())
        story.append(BookmarkAnchor("sec_gestor"))
        story.append(_section_header("Gestor"))
        story.append(Spacer(1, 0.6 * cm))
        txt = text_sections['gestor'].replace('\n', '<br/>')
        story.append(Paragraph(txt, styles['body']))

    # ════════════════════════════════════════
    # SECCIÓN: RIESGOS
    # ════════════════════════════════════════
    if text_sections.get('riesgos'):
        story.append(PageBreak())
        story.append(BookmarkAnchor("sec_riesgos"))
        story.append(_section_header("Riesgos"))
        story.append(Spacer(1, 0.6 * cm))
        txt = text_sections['riesgos'].replace('\n', '<br/>')
        story.append(Paragraph(txt, styles['body']))

    # ════════════════════════════════════════
    # ANEXOS
    # ════════════════════════════════════════
    if viviendas or garajes or trasteros:
        story.append(PageBreak())
        story.append(BookmarkAnchor("sec_anexos"))
        story.append(_section_header("Anexos: Listado de Unidades"))
        story.append(Spacer(1, 0.6 * cm))
        _property_table(story, "Viviendas", viviendas)
        _property_table(story, "Garajes", garajes)
        _property_table(story, "Trasteros", trasteros)

    # ── BUILD ──
    doc.build(story)
