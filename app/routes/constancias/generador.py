from datetime import datetime
import io
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape, portrait
from reportlab.lib.utils import ImageReader  # <-- Import agregado
from PyPDF2 import PdfWriter, PdfReader
os.makedirs('static/constancias', exist_ok=True)

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

# Ruta absoluta desde el archivo actual
base_dir = os.path.dirname(os.path.abspath(__file__))
font_dir = os.path.join(base_dir, '..', '..', 'static', 'fonts')

# Registro de fuentes
pdfmetrics.registerFont(TTFont('Montserrat-Regular', os.path.join(font_dir, 'Montserrat-Regular.ttf')))
pdfmetrics.registerFont(TTFont('Montserrat-Bold', os.path.join(font_dir, 'Montserrat-Bold.ttf')))
pdfmetrics.registerFont(TTFont('Montserrat-Black', os.path.join(font_dir, 'Montserrat-Black.ttf')))
pdfmetrics.registerFont(TTFont('Metropolis-Black', os.path.join(font_dir, 'Metropolis-Black.ttf')))
pdfmetrics.registerFont(TTFont('Metropolis-Bold', os.path.join(font_dir, 'Metropolis-Bold.ttf')))

# -------------------------------------------
def draw_centrado(c, texto, y, font="Helvetica", size=12, return_center=False):
    c.setFont(font, size)
    page_width = c._pagesize[0]  # Ancho de la página, no altura
    text_width = c.stringWidth(texto, font, size)
    x = (page_width - text_width) / 2
    c.drawString(x, y, texto)
    if return_center:
        return x + text_width / 2

# -------------------------------------------
def draw_texto_centrado_multilinea(c, texto, y_inicial, font_name="Helvetica", font_size=12, max_width=700, line_spacing=5, x_centro=None):
    c.setFont(font_name, font_size)
    palabras = texto.strip().split()
    lineas = []
    linea_actual = ""

    for palabra in palabras:
        test_linea = f"{linea_actual} {palabra}".strip()
        if c.stringWidth(test_linea, font_name, font_size) <= max_width:
            linea_actual = test_linea
        else:
            lineas.append(linea_actual)
            linea_actual = palabra
    if linea_actual:
        lineas.append(linea_actual)

    y = y_inicial
    for linea in lineas:
        text_width = c.stringWidth(linea, font_name, font_size)
        x = (c._pagesize[0] - text_width) / 2 if not x_centro else x_centro - (text_width / 2)
        c.drawString(x, y, linea)
        y -= font_size + line_spacing

# -------------------------------------------
def generar_constancia(participante, qr_path=None):
    clave = participante['clave_participante']
    nombre_completo = f"{participante['nombre_participante']} {participante['apellidos_participante']}"
    nombre_curso = participante['nombre_curso']
    duracion_curso = participante['duracion_curso']
    nombre_tipo = participante['nombre_tipo'].strip().lower()
    nombre_ponente = participante['nombre_ponente']
    cedula = participante['cedula_ponente']
    tema = participante['nombre_tema']
    fecha = participante['fecha_curso']
    folio_constancia = participante['folio_constancia']

    output_path = f"static/constancias/{clave}.pdf"
    packet = io.BytesIO()

    # Orientación de página
    psz = portrait(letter) if nombre_tipo in ('especializacion', 'mini especializacion') else landscape(letter)
    c = canvas.Canvas(packet, pagesize=psz)

    # ----------------- ANVERSO -----------------
    if nombre_tipo in ('publico en general', 'empresarial', 'psicologia'):
        draw_texto_centrado_multilinea(c, nombre_completo, 330, "Helvetica-Bold", 18)
        draw_texto_centrado_multilinea(c, nombre_curso, 278, "Helvetica", 14)
        draw_texto_centrado_multilinea(c, f"Con una duración de {duracion_curso} horas", 248, "Helvetica", 14)
        draw_texto_centrado_multilinea(c, f"Ponente: {nombre_ponente}  Cédula: {cedula}", 220, "Helvetica", 12)
        draw_texto_centrado_multilinea(c, f"Tema: {tema}", 195, "Helvetica", 12)
        draw_texto_centrado_multilinea(c, f"Fecha: {fecha}", 170, "Helvetica", 12)

        if qr_path:
            img = ImageReader(qr_path)
            if nombre_tipo == 'psicologia':
                c.drawImage(img, x=50, y=25, width=150, height=150, mask='auto')
            else:
                c.drawImage(img, x=250, y=25, width=90, height=90, mask='auto')

    elif nombre_tipo == 'especializacion':
        draw_texto_centrado_multilinea(c, nombre_completo, 485, "Helvetica-Bold", 18)
        draw_texto_centrado_multilinea(c, nombre_curso, 460, "Helvetica", 14)
        draw_texto_centrado_multilinea(c, f"Duración: {duracion_curso} horas", 435, "Helvetica", 12)
        draw_texto_centrado_multilinea(c, f"Ponente: {nombre_ponente}  Cédula: {cedula}", 410, "Helvetica", 12)
        draw_texto_centrado_multilinea(c, f"Tema: {tema}", 385, "Helvetica", 12)
        draw_texto_centrado_multilinea(c, f"Fecha: {fecha}", 360, "Helvetica", 12)

        if qr_path:
            img = ImageReader(qr_path)
            c.drawImage(img, x=175, y=80, width=90, height=90, mask='auto')

    else:
        draw_texto_centrado_multilinea(c, f"TIPO DE CONSTANCIA DESCONOCIDO: {nombre_tipo}", 400, "Helvetica", 14)

    c.showPage()

    # ----------------- REVERSO -----------------
    c.setFont("Montserrat-Bold", 11)
    c.setFillColor(HexColor("#CF1111"))

    if nombre_tipo == 'especializacion':
        c.drawString(212, 715, f"{folio_constancia}")
        c.setFillColor(HexColor("#000000"))
        c.drawString(212, 695, nombre_completo)
    else:
        c.drawString(255, 543, f"{folio_constancia}")
        c.setFillColor(HexColor("#000000"))
        c.drawString(255, 523, nombre_completo)

    c.showPage()
    c.save()

    packet.seek(0)

    # Combinar con plantilla
    new_pdf = PdfReader(packet)

    if nombre_tipo == 'especializacion':
        plantilla_path = {
            'especializacion ing': "app/static/pdf/especializacion_ing.pdf",
            'especializacion lic': "app/static/pdf/especializacion_lic.pdf",
            'mini especializacion ing': "app/static/pdf/especializacion_ing.pdf",
        }.get(tema.lower(), "app/static/pdf/especializacion_lic.pdf")
    else:
        plantilla_path = {
            'psicologia': "app/static/pdf/psicologia.pdf",
            'empresarial': "app/static/pdf/empresarial.pdf",
        }.get(nombre_tipo, "app/static/pdf/publico.pdf")

    with open(plantilla_path, "rb") as f:
        existing_pdf = PdfReader(f)
        output = PdfWriter()

        max_pages = max(len(existing_pdf.pages), len(new_pdf.pages))

        for i in range(max_pages):
            if i < len(existing_pdf.pages):
                base_page = existing_pdf.pages[i]
                if i < len(new_pdf.pages):
                    overlay_page = new_pdf.pages[i]
                    base_page.merge_page(overlay_page)
                output.add_page(base_page)
            else:
                # Plantilla no tiene esta página, agregamos del PDF generado
                output.add_page(new_pdf.pages[i])


    output_stream = io.BytesIO()
    output.write(output_stream)
    output_stream.seek(0)

    # Determinar el nombre del archivo de salida
    nombre_archivo = f"{clave}-E.pdf" if nombre_tipo == "especializacion" else f"{clave}.pdf"

    return output_stream, nombre_archivo
