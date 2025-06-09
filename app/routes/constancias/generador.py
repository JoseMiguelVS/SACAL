from datetime import datetime
import io
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfWriter, PdfReader
os.makedirs('static/constancias', exist_ok=True)

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

# Registro de fuentes
pdfmetrics.registerFont(TTFont('Montserrat-Regular', 'static/fonts/Montserrat-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Montserrat-Bold', 'static/fonts/Montserrat-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Montserrat-Black', 'static/fonts/Montserrat-Black.ttf'))
pdfmetrics.registerFont(TTFont('Metropolis-Black', 'static/fonts/Metropolis-Black.ttf'))
pdfmetrics.registerFont(TTFont('Metropolis-Bold', 'static/fonts/Metropolis-Bold.ttf'))

# -------------------------------------------
def draw_centrado(c, texto, y, font="Helvetica", size=12, return_center=False):
    c.setFont(font, size)
    page_height = c._pagesize[1]
    text_width = c.stringWidth(texto, font, size)
    x = (page_height - text_width) / 2
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
def generar_constancia(participante, qr_path):
    packet = io.BytesIO()
    width, height = letter
    c = canvas.Canvas(packet, pagesize=letter)

    nombre = participante['nombre_participante']
    apellidos = participante['apellidos_participante']
    curso = participante['nombre_curso']
    nombre_tipo = participante['nombre_tipo']
    es_nacional = participante['es_nacional']
    fecha = participante['fecha']
    dia = fecha.day if isinstance(fecha, datetime) else int(str(fecha)[8:10])
    nombre_mes = participante['nombre_mes']
    duracion_curso = participante['duracion_curso']
    clave = participante['clave_participante']
    current_year = datetime.now().year

    nombre_completo = f'{nombre.upper()} {apellidos.upper()}'
    curso_com = f"\"{curso.upper()}\""

    match nombre_tipo.lower():
        case 'especializacion':
            texto_duracion = f"CON UNA DURACIÓN DE {duracion_curso} HORAS,"
            realizado = "REALIZADO ONLINE EN VIVO,"
            texto_fecha = f"{nombre_mes.upper()} DE {current_year}."
            espe = "ESPECIALIZACIÓN:"

            centro_nombre = draw_centrado(c, nombre_completo, 300, font="Montserrat-Bold", size=18, return_center=True)
            c.setFillColor(HexColor("#003366"))
            draw_texto_centrado_multilinea(c, espe, 230, "Metropolis-Black", 25, 500, x_centro=centro_nombre)
            draw_texto_centrado_multilinea(c, curso_com, 210, "Metropolis-Black", 20, 500, x_centro=centro_nombre)
            c.setFillColorRGB(0, 0, 0)

            draw_centrado(c, texto_duracion, 165, "Montserrat-Bold", 10)
            draw_centrado(c, realizado, 150, "Montserrat-Bold", 10)
            draw_centrado(c, texto_fecha, 135, "Montserrat-Bold", 10)

            if qr_path:
                c.drawImage(qr_path, x=50, y=25, width=90, height=90)

        case 'mini especializacion':
            texto_duracion = f"CON UNA DURACIÓN DE {duracion_curso} HORAS,"
            realizado = "REALIZADO ONLINE EN VIVO,"
            texto_fecha = f"{nombre_mes.upper()} DE {current_year}."
            espe = "MINI ESPECIALIZACIÓN:"

            centro_nombre = draw_centrado(c, nombre_completo, 300, font="Montserrat-Bold", size=18, return_center=True)
            c.setFillColor(HexColor("#003366"))
            draw_texto_centrado_multilinea(c, espe, 230, "Metropolis-Black", 25, 500, x_centro=centro_nombre)
            draw_texto_centrado_multilinea(c, curso_com, 210, "Metropolis-Black", 20, 500, x_centro=centro_nombre)
            c.setFillColorRGB(0, 0, 0)

            draw_centrado(c, texto_duracion, 165, "Montserrat-Bold", 10)
            draw_centrado(c, realizado, 150, "Montserrat-Bold", 10)
            draw_centrado(c, texto_fecha, 135, "Montserrat-Bold", 10)

            if qr_path:
                c.drawImage(qr_path, x=50, y=25, width=90, height=90)

        case 'publico en general':

            if duracion_curso == '8':
                participacion = "POR SU PARTICIPACIÓN EN EL CURSO-TALLER NACIONAL" if es_nacional else "POR SU PARTICIPACIÓN EN EL CURSO-TALLER INTERNACIONAL"
            else:
                participacion = "POR SU PARTICIPACIÓN EN EL CURSO NACIONAL" if es_nacional else "POR SU PARTICIPACIÓN EN EL CURSO INTERNACIONAL"

            texto_duracion = f"CON UNA DURACIÓN DE {duracion_curso} HORAS,"
            realizado = "REALIZADO ONLINE EN VIVO,"
            texto_fecha = f"EL {dia} DE {nombre_mes.upper()} DE {current_year}."

            centro_nombre = draw_centrado(c, nombre_completo, 270, font="Montserrat-Bold", size=18, return_center=True)
            draw_centrado(c, participacion, 230, "Montserrat-Bold", 14)
            draw_texto_centrado_multilinea(c, curso_com, 200, "Metropolis-Black", 25, 500, x_centro=centro_nombre)

            draw_centrado(c, texto_duracion, 150, "Montserrat-Bold", 10)
            draw_centrado(c, realizado, 135, "Montserrat-Bold", 10)
            draw_centrado(c, texto_fecha, 120, "Montserrat-Bold", 10)   

            if qr_path:
                c.drawImage(qr_path, x=250, y=25, width=90, height=90)

        case 'empresarial':
            texto_duracion = f"CON UNA DURACIÓN DE {duracion_curso} HORAS,"
            realizado = "REALIZADO ONLINE EN VIVO,"
            texto_fecha = f"EL {dia} DE {nombre_mes.upper()} DE {current_year}."

            if duracion_curso == '8':
                participacion = "POR SU PARTICIPACIÓN EN EL CURSO-TALLER NACIONAL" if es_nacional else "POR SU PARTICIPACIÓN EN EL CURSO-TALLER INTERNACIONAL"
            else:
                participacion = "POR SU PARTICIPACIÓN EN EL CURSO NACIONAL" if es_nacional else "POR SU PARTICIPACIÓN EN EL CURSO INTERNACIONAL"

            centro_nombre = draw_centrado(c, nombre_completo, 300, font="Montserrat-Bold", size=18, return_center=True)
            draw_centrado(c, participacion, 260, "Montserrat-Bold", 14)
            draw_texto_centrado_multilinea(c, curso_com, 230, "Metropolis-Black", 25, 500, x_centro=centro_nombre)

            draw_centrado(c, texto_duracion, 180, "Montserrat-Bold", 10)
            draw_centrado(c, realizado, 165, "Montserrat-Bold", 10)
            draw_centrado(c, texto_fecha, 150, "Montserrat-Bold", 10)

            if qr_path:
                c.drawImage(qr_path, x=250, y=25, width=90, height=90)

        case 'psicologia':

            if duracion_curso == '8':
                participacion = "POR SU PARTICIPACIÓN EN EL CURSO-TALLER NACIONAL" if es_nacional else "POR SU PARTICIPACIÓN EN EL CURSO-TALLER INTERNACIONAL"
            else:
                participacion = "POR SU PARTICIPACIÓN EN EL CURSO NACIONAL" if es_nacional else "POR SU PARTICIPACIÓN EN EL CURSO INTERNACIONAL"

            texto_duracion = f"CON UNA DURACIÓN DE {duracion_curso} HORAS,"
            realizado = "REALIZADO ONLINE EN VIVO,"
            texto_fecha = f"EL {dia} DE {nombre_mes.upper()} DE {current_year}."

            centro_nombre = draw_centrado(c, nombre_completo, 270, font="Montserrat-Bold", size=18, return_center=True)
            draw_centrado(c, participacion, 230, "Montserrat-Bold", 14)
            draw_texto_centrado_multilinea(c, curso_com, 200, "Metropolis-Black", 25, 500, x_centro=centro_nombre)

            draw_centrado(c, texto_duracion, 150, "Montserrat-Bold", 10)
            draw_centrado(c, realizado, 135, "Montserrat-Bold", 10)
            draw_centrado(c, texto_fecha, 120, "Montserrat-Bold", 10)

            if qr_path:
                c.drawImage(qr_path, x=50, y=25, width=150, height=150)

    c.save()
    packet.seek(0)

    new_pdf = PdfReader(packet)
    plantilla_path = {
        'especializacion': "static/pdf/especializacion.pdf",
        'mini especializacion': "static/pdf/especializacion.pdf",
        'psicologia': "static/pdf/psicologia.pdf",
        'empresarial': "static/pdf/empresarial.pdf"
    }.get(nombre_tipo.lower(), "static/pdf/publico.pdf")

    existing_pdf = PdfReader(open(plantilla_path, "rb"))
    page = existing_pdf.pages[0]
    page.merge_page(new_pdf.pages[0])

    output = PdfWriter()
    output.add_page(page)

    if nombre_tipo.lower() in ('especializacion', 'mini especializacion'):
        constancia_path = f'static/constancias/{clave}-E.pdf'
    else:
        constancia_path = f'static/constancias/{clave}.pdf'

    with open(constancia_path, "wb") as outputStream:
        output.write(outputStream)

    return constancia_path