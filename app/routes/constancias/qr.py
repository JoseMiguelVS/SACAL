from datetime import datetime
import qrcode
import os
from io import BytesIO

def generar_qr_memoria(participante):
    nombre_curso = participante['nombre_curso']
    fecha = participante['fecha']
    nombre_mes = participante['nombre_mes']
    nombre_ponente = participante['nombre_ponente']
    curp_ponente = participante['curp_ponente']
    cedula_ponente = participante['cedula_ponente']
    certificaciones = participante['certificaciones']
    horario_inicio = participante['horario_inicio']
    horario_fin = participante['horario_fin']
    clave = participante['clave_participante']
    nombre_participante = participante['nombre_participante']
    folio_constancia = participante['folio_constancia']
    current_year = datetime.now().year

    # Extraer día
    dia = fecha.day if isinstance(fecha, datetime) else int(str(fecha)[8:10])

    # Asegurar que los horarios sean strings
    horario_inicio = str(horario_inicio)
    horario_fin = str(horario_fin)

    # Calcular duración
    formato = "%H:%M:%S"
    try:
        inicio = datetime.strptime(horario_inicio, formato)
        fin = datetime.strptime(horario_fin, formato)
        duracion_horas = (fin - inicio).seconds // 3600
    except Exception:
        duracion_horas = 0

    # Contenido QR con formato del reverso
    contenido_qr = f"""
INFORMACION DE CONSTANCIA:
    Folio: {folio_constancia}
INFORMACION DE PARTICIPANTE:
    FOLIO: {clave}
    NOMBRE DEL PARTICIPANTE: {nombre_participante.upper()}
    CURSO: {nombre_curso.upper()}
    CON UNA DURACIÓN DE {duracion_horas} HORAS,
    EL {dia} DE {nombre_mes.upper()} DE {current_year}.
    REALIZADO ONLINE EN VIVO,

INFORMACIÓN DE PONENTE:
    NOMBRE:{nombre_ponente.upper()}
    CURP:{curp_ponente}
    CEDULA:{cedula_ponente}
    CERTIFICACIONES:{certificaciones}

DIRECCIÓN DE OFICINAS:
    HIDALGO 303, EDIFICIO TORRE APIZACO, QUINTO PISO,
    INTERIOR PH5, CIUDAD DE APIZACO, TLAXCALA, MÉXICO.

INFORMACION DE CONTACTO
    TELÉFONO DE OFICINAS: +52 241 41 8 02 50
    WHATSAPP: +52 241 407 30 17
    QUEJAS AL: +52 241 198 22 36
    PÁGINA WEB: https://www.grupodipaam.com
    CORREO ELECTRÓNICO: diag.medicoypsicologico@hotmail.com
    FACEBOOK: https://www.facebook.com/conecta.academylatam

PARA VERIFICAR LA VALIDEZ DE ESTA CONSTANCIA 
PUEDE COMUNICARSE AL TELÉFONO DE OFICINAS ARRIBA INDICADO PROPORCIONANDO 
EL NÚMERO DE FOLIO Y NOMBRE DEL PARTICIPANTE QUE TOMÓ EL CURSO.    
    """

    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(contenido_qr)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    return buffer