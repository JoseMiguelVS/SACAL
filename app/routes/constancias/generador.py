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
    """
    Dibuja texto centrado horizontalmente. Si se pasa x_centro, alinea usando ese centro en lugar del centro de la hoja.
    """
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

    page_height = c._pagesize[1]
    y = y_inicial
    for linea in lineas:
        text_width = c.stringWidth(linea, font_name, font_size)
        if x_centro:
            x = x_centro - (text_width / 2)
        else:
            x = (page_height - text_width) / 2
        c.drawString(x, y, linea)
        y -= font_size + line_spacing

# -------------------------------------------
def generar_constancia(participante, qr_path=None):
    packet = io.BytesIO()
    nombre_tipo = participante['nombre_tipo'].lower()

    # Selección de orientación
    psz = portrait(letter) if nombre_tipo in ('especializacion', 'mini especializacion') else landscape(letter)

    c = canvas.Canvas(packet, pagesize=psz)

    nombre = participante['nombre_participante'].upper()
    apellidos = participante['apellidos_participante'].upper()
    curso = participante['nombre_curso']
    es_nacional = participante['es_nacional']
    fecha = participante['fecha_curso']
    dia = fecha.day if isinstance(fecha, datetime) else int(str(fecha)[8:10])
    nombre_mes = participante['nombre_mes']
    duracion_curso = participante['duracion_curso']
    clave = participante['clave_participante']
    folio_constancia = participante['folio_constancia']
    tema = participante['nombre_tema'].lower()
    current_year = datetime.now().year

    nombre_completo = f'{nombre} {apellidos}'
    curso_com = f"\"{curso.upper()}\""

    match nombre_tipo:
        case 'publico en general' | 'empresarial' | 'psicologia':
            if duracion_curso == '8':
                participacion = f"POR SU PARTICIPACIÓN EN EL CURSO-TALLER {'NACIONAL' if es_nacional else 'INTERNACIONAL'}"
            else:
                participacion = f"POR SU PARTICIPACIÓN EN EL CURSO {'NACIONAL' if es_nacional else 'INTERNACIONAL'}"

            texto_duracion = f"CON UNA DURACIÓN DE {duracion_curso} HORAS,"
            realizado = "REALIZADO ONLINE EN VIVO,"
            texto_fecha = f"EL {dia} DE {nombre_mes.upper()} DE {current_year}."

            y_base = 270 if nombre_tipo != 'empresarial' else 300
            centro_nombre = draw_centrado(c, nombre_completo, y_base, font="Montserrat-Bold", size=18, return_center=True)

            draw_centrado(c, participacion, y_base - 40, "Montserrat-Bold", 14)

            # Ajustar fuente del curso si es largo
            curso_lineas = curso_com.count(" ") // 5 + 1
            font_size = 25 if curso_lineas <= 2 else 18
            draw_texto_centrado_multilinea(c, curso_com, y_base - 70, "Metropolis-Black", font_size, 500, x_centro=centro_nombre)

            draw_centrado(c, texto_duracion, y_base - 120, "Montserrat-Bold", 10)
            draw_centrado(c, realizado, y_base - 135, "Montserrat-Bold", 10)
            draw_centrado(c, texto_fecha, y_base - 150, "Montserrat-Bold", 10)

            if qr_path:
                img = ImageReader(qr_path)
                c.drawImage(img, x=250 if nombre_tipo != 'psicologia' else 50, y=25, width=90 if nombre_tipo != 'psicologia' else 150, height=90 if nombre_tipo != 'psicologia' else 150, mask='auto')

        case 'especializacion':
            dur_txt = f"CON UNA DURACIÓN DE {duracion_curso} HORAS,"
            realz = "REALIZADO ONLINE EN VIVO,"
            fecha_txt = f"{nombre_mes.upper()} DE {current_year}."

            centro = draw_centrado(c, nombre_completo, 372, font="Montserrat-Bold", size=18, return_center=True)
            c.setFillColor(HexColor("#003366"))
            curso_lineas = curso_com.count(" ") // 5 + 1
            font_size = 20 if curso_lineas <= 2 else 16
            draw_texto_centrado_multilinea(c, curso_com, 280, "Metropolis-Black", font_size, 500, x_centro=centro)
            c.setFillColor(HexColor("#000000"))
            draw_centrado(c, dur_txt,   235, "Montserrat-Bold", 10) 
            draw_centrado(c, realz,     225, "Montserrat-Bold", 10)
            draw_centrado(c, fecha_txt, 215, "Montserrat-Bold", 10)

            if qr_path:
                img = ImageReader(qr_path)
                c.drawImage(img, x=175, y=80, width=90, height=90, mask='auto')

    c.showPage()  # ← Cierra la primera página

    # Generar reverso como segunda página
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

    c.showPage()  # ← Cierra segunda página correctamente

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
