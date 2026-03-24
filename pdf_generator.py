from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, 
    Table, TableStyle, LongTable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
import os

# Colores del diseño
COLOR_AZUL_OSCURO = '#0d233a'
COLOR_AZUL_CLARO_BG = '#d6eaf8'
COLOR_AZUL_CLARO_TEXT = '#1a5276'
COLOR_TEXTO = '#333333'
COLOR_BLANCO = '#ffffff'


def _create_styles():
    """Crea los estilos personalizados para el PDF."""
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=36,
        textColor=colors.white,
        alignment=TA_CENTER,
        spaceAfter=10,
        leading=42
    )

    section_title = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        textColor=colors.HexColor(COLOR_AZUL_OSCURO),
        spaceAfter=20,
        spaceBefore=10,
    )

    body_style = ParagraphStyle(
        'BodyCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        textColor=colors.HexColor(COLOR_TEXTO),
        alignment=TA_JUSTIFY,
        leading=18,
        spaceAfter=12
    )

    index_style = ParagraphStyle(
        'IndexItem',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=14,
        textColor=colors.HexColor(COLOR_AZUL_OSCURO),
        spaceAfter=14,
        leading=20,
        leftIndent=40
    )

    return {
        'title': title_style,
        'section': section_title,
        'body': body_style,
        'index': index_style,
        'base': styles,
    }


def _section_header_table(title_text):
    """Crea una barra de título de sección con fondo azul claro."""
    title_para = Paragraph(
        title_text,
        ParagraphStyle(
            'SectionBar',
            fontName='Helvetica-Bold',
            fontSize=20,
            textColor=colors.HexColor(COLOR_AZUL_OSCURO),
            alignment=TA_LEFT,
            leading=28,
        )
    )
    page_w = landscape(A4)[0] - 4 * cm
    t = Table([[title_para]], colWidths=[page_w])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(COLOR_AZUL_CLARO_BG)),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
    ]))
    return t


def _add_photo_gallery(story, image_paths, title, styles, bookmark_key):
    """Agrega una sección de galería de fotos al story."""
    if not image_paths:
        return

    story.append(PageBreak())
    story.append(_section_header_table(title))
    story.append(Spacer(1, 0.8 * cm))

    # Colocar 2 imágenes por fila
    page_w = landscape(A4)[0] - 4 * cm
    img_w = (page_w - 1 * cm) / 2
    img_h = img_w * 0.65

    row = []
    for i, img_path in enumerate(image_paths):
        if os.path.exists(img_path):
            try:
                img = Image(img_path, width=img_w, height=img_h)
                img.hAlign = 'CENTER'
                row.append(img)
            except Exception as e:
                print(f"Error loading image {img_path}: {e}")
                continue

        if len(row) == 2:
            t = Table([row], colWidths=[img_w + 0.5 * cm, img_w + 0.5 * cm])
            t.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.5 * cm))
            row = []

            # Si hay más fotos, nueva página
            if i < len(image_paths) - 1 and (i + 1) % 4 == 0:
                story.append(PageBreak())

    # Fila incompleta
    if row:
        while len(row) < 2:
            row.append('')
        t = Table([row], colWidths=[img_w + 0.5 * cm, img_w + 0.5 * cm])
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(t)


def generate_presentation_pdf(
    output_path: str, 
    financial_data: dict, 
    image_paths_by_category: dict,
    project_title: str, 
    text_sections: dict
):
    """
    Genera el PDF de presentación.
    
    Args:
        output_path: ruta del PDF de salida
        financial_data: datos financieros del Excel
        image_paths_by_category: dict con keys 'portada', 'fachada', 'interior', cada una con lista de paths
        project_title: título del proyecto
        text_sections: dict con keys 'resumen', 'estudio_mercado', 'gestor', 'riesgos'
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(A4),
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm
    )

    styles = _create_styles()
    story = []

    # ========================================
    # PÁGINA 1 — PORTADA
    # ========================================
    portada_images = image_paths_by_category.get('portada', [])
    
    if portada_images and os.path.exists(portada_images[0]):
        try:
            page_w = landscape(A4)[0] - 4 * cm
            img = Image(portada_images[0], width=page_w, height=12 * cm)
            img.hAlign = 'CENTER'
            story.append(Spacer(1, 1 * cm))
            story.append(img)
        except Exception as e:
            print(f"Error loading cover image: {e}")
            story.append(Spacer(1, 6 * cm))
    else:
        story.append(Spacer(1, 6 * cm))

    # Título sobre fondo azul oscuro
    title_bar = Paragraph(
        project_title.upper(),
        ParagraphStyle(
            'TitleBar',
            fontName='Helvetica-Bold',
            fontSize=30,
            textColor=colors.white,
            alignment=TA_CENTER,
            leading=38,
        )
    )
    page_w = landscape(A4)[0] - 4 * cm
    t_title = Table([[title_bar]], colWidths=[page_w])
    t_title.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(COLOR_AZUL_OSCURO)),
        ('TOPPADDING', (0, 0), (-1, -1), 18),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 18),
        ('LEFTPADDING', (0, 0), (-1, -1), 20),
        ('RIGHTPADDING', (0, 0), (-1, -1), 20),
    ]))
    story.append(Spacer(1, 1 * cm))
    story.append(t_title)

    # Subtítulo
    subtitle = Paragraph(
        "INFORME DE VIABILIDAD",
        ParagraphStyle(
            'Subtitle',
            fontName='Helvetica',
            fontSize=16,
            textColor=colors.HexColor(COLOR_AZUL_OSCURO),
            alignment=TA_CENTER,
            spaceAfter=20,
        )
    )
    story.append(Spacer(1, 0.5 * cm))
    story.append(subtitle)

    story.append(PageBreak())

    # ========================================
    # PÁGINA 2 — ÍNDICE
    # ========================================
    story.append(_section_header_table("ÍNDICE"))
    story.append(Spacer(1, 1.5 * cm))

    # Definir secciones del índice
    sections_list = []
    section_num = 1
    
    if text_sections.get('resumen'):
        sections_list.append((section_num, "Resumen", "sec_resumen"))
        section_num += 1
    
    if text_sections.get('estudio_mercado'):
        sections_list.append((section_num, "Estudio de Mercado", "sec_estudio"))
        section_num += 1

    sections_list.append((section_num, "Análisis Financiero", "sec_financiero"))
    section_num += 1
    
    fachada_images = image_paths_by_category.get('fachada', [])
    if fachada_images:
        sections_list.append((section_num, "Galería: Fachada", "sec_fachada"))
        section_num += 1
    
    interior_images = image_paths_by_category.get('interior', [])
    if interior_images:
        sections_list.append((section_num, "Galería: Interior", "sec_interior"))
        section_num += 1
    
    if text_sections.get('gestor'):
        sections_list.append((section_num, "Gestor", "sec_gestor"))
        section_num += 1
    
    if text_sections.get('riesgos'):
        sections_list.append((section_num, "Riesgos", "sec_riesgos"))
        section_num += 1

    viviendas = financial_data.get("viviendas", [])
    garajes = financial_data.get("garajes", [])
    trasteros = financial_data.get("trasteros", [])
    if viviendas or garajes or trasteros:
        sections_list.append((section_num, "Anexos: Listado de Unidades", "sec_anexos"))

    # Crear tabla de índice
    index_data = []
    for num, name, key in sections_list:
        link_text = f'<link href="#{key}" color="#1a5276"><u>{num}. {name}</u></link>'
        index_data.append([Paragraph(
            link_text,
            ParagraphStyle(
                'IndexLink',
                fontName='Helvetica',
                fontSize=14,
                textColor=colors.HexColor(COLOR_AZUL_OSCURO),
                leading=22,
                leftIndent=20,
            )
        )])

    if index_data:
        idx_table = Table(index_data, colWidths=[page_w * 0.8])
        idx_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 30),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#e5e7eb')),
        ]))
        story.append(idx_table)

    story.append(PageBreak())

    # ========================================
    # SECCIÓN: RESUMEN
    # ========================================
    if text_sections.get('resumen'):
        story.append(_section_header_table("Resumen"))
        # Add bookmark anchor
        story[-1]._bookmarkName = "sec_resumen"
        story.append(Spacer(1, 0.8 * cm))
        
        resumen_text = text_sections['resumen'].replace('\n', '<br/>')
        story.append(Paragraph(resumen_text, styles['body']))
        story.append(PageBreak())

    # ========================================
    # SECCIÓN: ESTUDIO DE MERCADO
    # ========================================
    if text_sections.get('estudio_mercado'):
        story.append(_section_header_table("Estudio de Mercado"))
        story[-1]._bookmarkName = "sec_estudio"
        story.append(Spacer(1, 0.8 * cm))
        
        estudio_text = text_sections['estudio_mercado'].replace('\n', '<br/>')
        story.append(Paragraph(estudio_text, styles['body']))
        story.append(PageBreak())

    # ========================================
    # SECCIÓN: ANÁLISIS FINANCIERO
    # ========================================
    story.append(_section_header_table("Análisis Financiero"))
    story[-1]._bookmarkName = "sec_financiero"
    story.append(Spacer(1, 0.8 * cm))

    story.append(Paragraph(
        "El modelo financiero se ha construido sobre presupuestos de ejecución material (PEM) rigurosos "
        "y estimaciones de ventas sustentadas por transacciones reales en el área de influencia del proyecto.",
        styles['body']
    ))
    story.append(Spacer(1, 0.5 * cm))

    fin_data = [
        ['CONCEPTO', 'IMPORTE (€)'],
        ['Coste Adquisición Suelo + Estruct.', f"{financial_data.get('coste_adquisicion', 0):,.2f} €"],
        ['Coste Terminación (Construcción)', f"{financial_data.get('coste_terminacion', 0):,.2f} €"],
        ['TOTAL INVERSIÓN ESTIMADA', f"{financial_data.get('total_inversion', 0):,.2f} €"],
        ['TOTAL INGRESOS POR VENTAS', f"{financial_data.get('total_ventas', 0):,.2f} €"],
        ['BENEFICIO BRUTO ESTIMADO', f"{financial_data.get('beneficio_bruto', 0):,.2f} €"],
        ['RENTABILIDAD (ROI)', f"{financial_data.get('roi', 0):.2f} %"]
    ]

    t_fin = Table(fin_data, colWidths=[15 * cm, 6 * cm])
    t_fin.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLOR_AZUL_OSCURO)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 13),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 10),
        ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
    ]))
    story.append(t_fin)
    story.append(Spacer(1, 0.8 * cm))

    roi_val = financial_data.get('roi', 0)
    story.append(Paragraph(
        f"El proyecto es capaz de generar retornos del <b>{roi_val:.2f}%</b>, asumiendo un escenario "
        "conservador de venta. Este margen proporciona un colchón de seguridad excepcional.",
        styles['body']
    ))

    # ========================================
    # GALERÍAS DE FOTOS
    # ========================================
    if fachada_images:
        story.append(PageBreak())
        header = _section_header_table("Galería: Fachada")
        header._bookmarkName = "sec_fachada"
        story.append(header)
        story.append(Spacer(1, 0.8 * cm))
        # Add photos inline (not via _add_photo_gallery to keep bookmark)
        _add_photos_inline(story, fachada_images)

    if interior_images:
        story.append(PageBreak())
        header = _section_header_table("Galería: Interior")
        header._bookmarkName = "sec_interior"
        story.append(header)
        story.append(Spacer(1, 0.8 * cm))
        _add_photos_inline(story, interior_images)

    # ========================================
    # SECCIÓN: GESTOR
    # ========================================
    if text_sections.get('gestor'):
        story.append(PageBreak())
        header = _section_header_table("Gestor")
        header._bookmarkName = "sec_gestor"
        story.append(header)
        story.append(Spacer(1, 0.8 * cm))
        
        gestor_text = text_sections['gestor'].replace('\n', '<br/>')
        story.append(Paragraph(gestor_text, styles['body']))

    # ========================================
    # SECCIÓN: RIESGOS
    # ========================================
    if text_sections.get('riesgos'):
        story.append(PageBreak())
        header = _section_header_table("Riesgos")
        header._bookmarkName = "sec_riesgos"
        story.append(header)
        story.append(Spacer(1, 0.8 * cm))
        
        riesgos_text = text_sections['riesgos'].replace('\n', '<br/>')
        story.append(Paragraph(riesgos_text, styles['body']))

    # ========================================
    # ANEXOS: LISTADOS
    # ========================================
    if viviendas or garajes or trasteros:
        story.append(PageBreak())
        header = _section_header_table("Anexos: Listado de Unidades")
        header._bookmarkName = "sec_anexos"
        story.append(header)
        story.append(Spacer(1, 0.8 * cm))

        _create_property_table(story, "Viviendas", viviendas, styles)
        _create_property_table(story, "Garajes", garajes, styles)
        _create_property_table(story, "Trasteros", trasteros, styles)

    # ========================================
    # BUILD con bookmarks
    # ========================================
    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)


def _on_page(canvas_obj, doc):
    """Callback para añadir bookmarks a cada página."""
    # Recorrer los flowables de la página y registrar bookmarks
    pass


def _add_photos_inline(story, image_paths):
    """Agrega fotos en grid de 2 columnas al story actual."""
    page_w = landscape(A4)[0] - 4 * cm
    img_w = (page_w - 1 * cm) / 2
    img_h = img_w * 0.65

    row = []
    count = 0
    for img_path in image_paths:
        if os.path.exists(img_path):
            try:
                img = Image(img_path, width=img_w, height=img_h)
                img.hAlign = 'CENTER'
                row.append(img)
                count += 1
            except Exception as e:
                print(f"Error loading image {img_path}: {e}")
                continue

        if len(row) == 2:
            t = Table([row], colWidths=[img_w + 0.5 * cm, img_w + 0.5 * cm])
            t.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.5 * cm))
            row = []

            # Nueva página cada 4 fotos
            if count % 4 == 0 and count < len(image_paths):
                story.append(PageBreak())

    if row:
        while len(row) < 2:
            row.append('')
        t = Table([row], colWidths=[img_w + 0.5 * cm, img_w + 0.5 * cm])
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(t)


def _create_property_table(story, title, items, styles):
    """Crea una tabla de propiedades (viviendas/garajes/trasteros)."""
    if not items:
        return

    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(f"<b>{title}</b>", styles['body']))
    story.append(Spacer(1, 0.3 * cm))

    table_data = [['Tipología', 'Planta', 'Puerta', 'Habs.', 'Superficie', 'Precio C/U']]
    for item in items:
        table_data.append([
            item.get("Tipología original", ""),
            item.get("Planta", ""),
            item.get("Puerta", ""),
            item.get("Habs", "").replace(" Habs", ""),
            item.get("Constr.", ""),
            item.get("Precio", "")
        ])

    t = LongTable(table_data, colWidths=[5 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 4 * cm, 4 * cm], repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLOR_AZUL_OSCURO)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')])
    ]))
    story.append(t)
