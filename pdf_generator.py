from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Table, TableStyle, LongTable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
import os

def generate_presentation_pdf(output_path: str, financial_data: dict, image_paths: list, project_title: str, gestor_name: str, project_description: str):
    # Utilizamos pagesize landscape(A4) para la presentación horizontal
    doc = SimpleDocTemplate(
        output_path, 
        pagesize=landscape(A4),
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Styles adaptados para horizontal
    title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=32,
        textColor=colors.HexColor('#0d233a'),
        alignment=TA_CENTER,
        spaceAfter=30
    )
    
    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        textColor=colors.HexColor('#0d233a'),
        spaceAfter=15,
        spaceBefore=20
    )
    
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=13,
        textColor=colors.HexColor('#333333'),
        alignment=TA_JUSTIFY,
        leading=18,
        spaceAfter=15
    )
    
    story = []

    # --- PORTADA (Página 1) ---
    story.append(Spacer(1, 4 * cm))
    story.append(Paragraph("INFORME DE VIABILIDAD", title_style))
    story.append(Paragraph(project_title.upper(), title_style))
    
    if len(image_paths) > 0 and os.path.exists(image_paths[0]):
        try:
            # Ampliamos la imagen para formato horizontal
            img = Image(image_paths[0], width=20*cm, height=11*cm)
            story.append(Spacer(1, 1*cm))
            story.append(img)
        except Exception as e:
            print(f"Error loading cover image: {e}")

    story.append(PageBreak())

    # --- RESUMEN (Página 2) ---
    story.append(Paragraph("1. Resumen", h1_style))
    
    resumen_text = f"""
    El presente informe detalla la viabilidad técnica, comercial y financiera del {project_title}. 
    Una oportunidad de inversión inmobiliaria de alto atractivo por su inmejorable relación rentabilidad-riesgo. 
    """
    if project_description:
        resumen_text += f"<br/><br/>{project_description}"
        
    resumen_text += f"""
    <br/><br/>Basado en un desglose de costes exhaustivo y unas previsiones de venta conservadoras, el
    proyecto arroja un Beneficio Bruto estimado de {financial_data.get('beneficio_bruto', 0):,.2f} € y un 
    extraordinario Retorno sobre la Inversión (ROI) del {financial_data.get('roi', 0):.2f}%. 
    Estas métricas colocan a esta promoción como un activo defensivo y altamente lucrativo para los partícipes.
    """
    story.append(Paragraph(resumen_text, body_style))
    
    story.append(Paragraph("2. Características principales", h1_style))
    story.append(Paragraph("""
    El activo se ubica en una localización privilegiada, óptima para absorber la actual demanda inmobiliaria de la zona. 
    Las viviendas han sido diseñadas bajo los estándares más exigentes de calidad y eficiencia energética.
    """, body_style))

    story.append(PageBreak())

    # --- GALERÍA (Página 3) ---
    story.append(Paragraph("3. Galería del Proyecto", h1_style))
    
    # Intentamos añadir las otras imágenes de forma lado a lado usando una simple tabla para Layout
    gallery_images = []
    for img_path in image_paths[1:]:
        if os.path.exists(img_path):
            try:
                gallery_images.append(Image(img_path, width=12*cm, height=8*cm))
            except Exception as e:
                print(f"Error loading gallery image: {e}")
                
    if gallery_images:
        # Colocar imágenes en una sola fila si hay varias
        t_gallery = Table([gallery_images], colWidths=[13*cm] * len(gallery_images))
        t_gallery.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ]))
        story.append(t_gallery)

    story.append(PageBreak())

    # --- FINANCIERO (Página 4) ---
    story.append(Paragraph("4. Análisis Financiero", h1_style))
    story.append(Paragraph("""
    El modelo financiero se ha construido sobre presupuestos de ejecución material (PEM) rigurosos 
    y estimaciones de ventas sustentadas por transacciones reales en el área de influencia del proyecto.
    """, body_style))
    
    story.append(Spacer(1, 1*cm))

    # Crear tabla de datos financieros
    data = [
        ['CONCEPTO', 'IMPORTE (€)'],
        ['Coste Adquisición Suelo + Estruct.', f"{financial_data.get('coste_adquisicion', 0):,.2f} €"],
        ['Coste Terminación (Construcción)', f"{financial_data.get('coste_terminacion', 0):,.2f} €"],
        ['TOTAL INVERSIÓN ESTIMADA', f"{financial_data.get('total_inversion', 0):,.2f} €"],
        ['TOTAL INGRESOS POR VENTAS', f"{financial_data.get('total_ventas', 0):,.2f} €"],
        ['BENEFICIO BRUTO ESTIMADO', f"{financial_data.get('beneficio_bruto', 0):,.2f} €"],
        ['RENTABILIDAD (ROI)', f"{financial_data.get('roi', 0):.2f} %"]
    ]
    
    # Aumentar un poco el tamaño de las columnas para horizontal
    t = Table(data, colWidths=[15*cm, 6*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d233a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 14),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f2f2f2')),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 10),
        ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.white)
    ]))
    
    story.append(t)
    story.append(Spacer(1, 1*cm))
    
    story.append(Paragraph(f"""
    Como se observa, el proyecto es capaz de generar retornos del {financial_data.get('roi', 0):.2f}%, asumiendo
    un escenario conservador de venta. Este margen proporciona un colchón de seguridad excepcional.
    """, body_style))

    story.append(PageBreak())

    # --- PLAZOS Y GESTOR (Página 5) ---
    story.append(Paragraph("5. Gestor", h1_style))
    story.append(Paragraph(f"""
    El proyecto estará bajo la supervisión y ejecución de {gestor_name}, una entidad
    con dilatada experiencia en la promoción y gestión de activos residenciales. Con un historial
    impecable entregando proyectos rentables y en plazo, el gestor asume la dirección técnica, el
    control presupuestario y la comercialización del activo para asegurar el cumplimiento del plan de
    negocio expuesto.
    """, body_style))

    # --- ANEXOS: LISTADOS (Páginas dinámicas) ---
    def create_property_table(title, items, is_first=False):
        if not items:
            return
            
        story.append(PageBreak())
        if is_first:
            story.append(Paragraph("6. Anexos: Listado de Unidades", h1_style))
        else:
            story.append(Paragraph(title, h1_style))
            
        if is_first:
            story.append(Paragraph(f"<b>{title}</b>", body_style))
        
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
            
        t = LongTable(table_data, colWidths=[5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 4*cm, 4*cm], repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d233a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Tipologia a la izq
            ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'), # Precio a la der
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

    viviendas = financial_data.get("viviendas", [])
    garajes = financial_data.get("garajes", [])
    trasteros = financial_data.get("trasteros", [])

    create_property_table("Viviendas", viviendas, is_first=True)
    create_property_table("Garajes", garajes, is_first=False)
    create_property_table("Trasteros", trasteros, is_first=False)

    # Construir el PDF
    doc.build(story)
