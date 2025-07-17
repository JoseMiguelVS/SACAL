from datetime import datetime
import io
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape, portrait
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
    page_width = c._pagesize[0]  # Ancho, no altura

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
            x = (page_width - text_width) / 2
        c.drawString(x, y, linea)
        y -= font_size + line_spacing

# -------------------------------------------
def generar_constancia(participante, qr_path=None):
    packet = io.BytesIO()
    nombre_tipo = participante['nombre_tipo'].lower()

    # Selección de orientación: retrato para especialización
    if nombre_tipo in ('especializacion', 'mini especializacion'):
        psz = portrait(letter)
    else:
        psz = landscape(letter)

    c = canvas.Canvas(packet, pagesize=psz)


    nombre = participante['nombre_participante'].upper()
    apellidos = participante['apellidos_participante'].upper()
    curso = participante['nombre_curso']
    es_nacional = participante['es_nacional']
    fecha = participante['fecha']
    dia = fecha.day if isinstance(fecha, datetime) else int(str(fecha)[8:10])
    nombre_mes = participante['nombre_mes']
    duracion_curso = participante['duracion_curso']
    clave = participante['clave_participante']
    folio_constancia = participante['folio_constancia']
    tema = participante['nombre_tema'].lower()
    current_year = datetime.now().year

    nombre_completo = f'{nombre.upper()} {apellidos.upper()}'
    curso_com = f"\"{curso.upper()}\""

    match nombre_tipo.lower():
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

        case 'especializacion':
            # definir textos
            dur_txt = f"CON UNA DURACIÓN DE {duracion_curso} HORAS,"
            realz = "REALIZADO ONLINE EN VIVO,"
            fecha_txt = f"{nombre_mes.upper()} DE {current_year}."

            centro = draw_centrado(c, nombre_completo, 372, font="Montserrat-Bold", size=18, return_center=True)
            c.setFillColor(HexColor("#003366"))
            draw_texto_centrado_multilinea(c, curso_com, 280, "Metropolis-Black", 20, 500, x_centro=centro)
            c.setFillColor(HexColor("#000000"))
            draw_centrado(c, dur_txt,   235, "Montserrat-Bold", 10) 
            draw_centrado(c, realz,     225, "Montserrat-Bold", 10)
            draw_centrado(c, fecha_txt, 215, "Montserrat-Bold", 10)

            if qr_path:
                c.drawImage(qr_path, x=175, y=80, width=90, height=90)

    c.showPage()
        
    if nombre_tipo == 'especializacion':
            # Aquí editas la segunda página, puedes usar las mismas funciones o texto libre
        c.setFont("Montserrat-Bold", 11)
        c.setFillColor(HexColor("#CF1111"))
        c.drawString(212, 715, f"{folio_constancia}")  # Ajusta según el margen izquierdo deseado
        c.setFillColor(HexColor("#000000"))
        c.drawString(212, 695, nombre_completo)
        # c.drawString(205, 685, apellidos)
    
    else:
            # Aquí editas la segunda página, puedes usar las mismas funciones o texto libre
        c.setFont("Montserrat-Bold", 11)
        c.setFillColor(HexColor("#CF1111"))
        c.drawString(255, 643, f"{folio_constancia}")  # Ajusta según el margen izquierdo deseado
        c.setFillColor(HexColor("#000000"))
        c.drawString(255, 623, nombre_completo)

    c.showPage()  # <-- Mueve esto aquí para asegurar el cierre correcto de la página

    c.save()
    packet.seek(0)

    new_pdf = PdfReader(packet)
    if nombre_tipo == 'especializacion':
        plantilla_path = {
            'especializacion ing': "static/pdf/especializacion_ing.pdf",
            'especializacion lic': "static/pdf/especializacion_lic.pdf",
            'mini especializacion ing': "static/pdf/especializacion_ing.pdf",
        }.get(tema.lower(), "static/pdf/especializacion_lic.pdf")
        
    else:
        plantilla_path = {
            'psicologia': "static/pdf/psicologia.pdf",
            'empresarial': "static/pdf/empresarial.pdf"
        }.get(nombre_tipo, "static/pdf/publico.pdf")

    # Mejora: cerrar el archivo PDF al usarlo
    with open(plantilla_path, "rb") as f:
        existing_pdf = PdfReader(f)
        output = PdfWriter()

        for i in range(len(existing_pdf.pages)):
            base_page = existing_pdf.pages[i]
            if i < len(new_pdf.pages):
                overlay_page = new_pdf.pages[i]
                base_page.merge_page(overlay_page)
            output.add_page(base_page)

        constancia_path = f'static/constancias/{clave}-E.pdf' if nombre_tipo in ('especializacion', 'mini especializacion') else f'static/constancias/{clave}.pdf'

        with open(constancia_path, "wb") as outputStream:
            output.write(outputStream)

    return constancia_path