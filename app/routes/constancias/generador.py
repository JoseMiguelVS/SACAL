from datetime import datetime
import io
import os
os.makedirs('static/constancias', exist_ok=True)
from reportlab.pdfbase import pdfmetrics

from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont('Montserrat-Regular', 'static/fonts/Montserrat-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Montserrat-Bold', 'static/fonts/Montserrat-Bold.ttf'))

#----------------------------------------------------------------------------------------------------------------------------------

def draw_texto_centrado_multilinea(c, texto, y_inicial, font_name="Helvetica", font_size=12, max_width=700, line_spacing=5):
    """
    Dibuja texto centrado horizontalmente en una hoja en orientación horizontal (landscape),
    usando height como base para el ancho visible.
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

    # Usar height como ancho en orientación horizontal
    page_width = c._pagesize[1]  # 🔄 height porque es landscape

    y = y_inicial
    for linea in lineas:
        text_width = c.stringWidth(linea, font_name, font_size)
        x = (page_width - text_width) / 2
        c.drawString(x, y, linea)
        y -= font_size + line_spacing


#---------------------------------------GENERADOR DE CONSTANCIAS------------------------------------------------

def generar_constancia(participante, qr_path):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from PyPDF2 import PdfWriter, PdfReader

    # Crear un canvas con tamaño LETTER (tamaño real del PDF)
    packet = io.BytesIO()
    width, height = letter  # 612 x 792 puntos
    c = canvas.Canvas(packet, pagesize=letter)

#--------------------------------------------VALORES DE LA CONSTANCIA--------------------------------
    nombre = participante['nombre_participante']
    apellidos = participante['apellidos_participante']
    curso = participante['nombre_curso']
    nombre_tipo = participante['nombre_tipo']
    categoria = participante['nombre_categoria']
    fecha = participante['fecha']
    dia = fecha.day if isinstance(fecha, datetime) else int(str(fecha)[8:10])
    nombre_mes = participante['nombre_mes']
    horario_inicio = participante['horario_inicio']
    horario_fin = participante['horario_fin']
    clave = participante['clave_participante']
    current_year = datetime.now().year

#--------------------------------------------- Calcular duración-----------------------------------------------------
    formato = "%H:%M:%S"
    try:
        inicio = datetime.strptime(str(horario_inicio), formato)
        fin = datetime.strptime(str(horario_fin), formato)
        duracion_horas = (fin - inicio).seconds // 3600
    except Exception:
        duracion_horas = 0

    texto_duracion = f"CON UNA DURACIÓN DE {duracion_horas} HORA(S),"
    realizado = "REALIZADO ONLINE EN VIVO,"
    texto_fecha = f"EL {dia} DE {nombre_mes.upper()} DE {current_year}."
    nombre_completo = f'{nombre.upper()} {apellidos.upper()}'
    curso_com = f"\"{curso.upper()}\""

    def draw_centrado(texto, y, font="Helvetica", size=12):
            c.setFont(font, size)
            text_width = c.stringWidth(texto, font, size)
            x = (height - text_width) / 2
            c.drawString(x, y, texto)

    # Impresión con centrado manual
    draw_centrado(nombre_completo, 290, font="Helvetica-Bold", size=18)
    curso_com = f"\"{curso.upper()}\""
    draw_texto_centrado_multilinea( c, texto=curso_com, y_inicial=220, font_name="Montserrat-Bold", font_size=25, max_width=700)# más permisivo
    draw_centrado(texto_duracion, 180, font="Montserrat-Bold", size=10)
    draw_centrado(realizado, 165, font="Montserrat-Bold", size=10)
    draw_centrado(texto_fecha, 150, font="Montserrat-Bold", size=10)

    # Insertar QR en parte inferior izquierda
    if qr_path:
        c.drawImage(qr_path, x=50, y=25, width=150, height=150)

    c.save()
    packet.seek(0)

    new_pdf = PdfReader(packet)
    if categoria == 'especializacion':
        plantilla_path = "static/pdf/espacializacion.pdf"
    elif nombre_tipo == 'psicologia':
        plantilla_path = "static/pdf/psicologia.pdf"
    elif nombre_tipo == 'empresarial':  
        plantilla_path = "static/pdf/empresarial.pdf"
    elif nombre_tipo == 'publico en general':
        plantilla_path = "static/pdf/publico.pdf"
    else:
        plantilla_path = "static/pdf/default.pdf"  # <- puedes poner un PDF genérico

    existing_pdf = PdfReader(open(plantilla_path, "rb"))

    page = existing_pdf.pages[0]
    page.merge_page(new_pdf.pages[0])

    output = PdfWriter()
    output.add_page(page)

    constancia_path = f'static/constancias/{clave}.pdf'
    with open(constancia_path, "wb") as outputStream:
        output.write(outputStream)

    return constancia_path
