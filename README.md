# 📘 SACAL – Sistema Administrador de Conecta Academy Latinoamerica

**SACAL** es una plataforma web diseñada para gestionar participantes, constancias, pagos, paquetes y sesiones académicas, con generación automática de documentos en PDF y filtros avanzados. Ideal para instituciones educativas o centros de capacitación.

---

## 🚀 Tecnologías utilizadas

- **Backend:** Python 3.10+, Flask
- **Frontend:** HTML, Bootstrap 5, JavaScript
- **Base de datos:** PostgreSQL
- **PDF:** ReportLab
- **Despliegue:** Gunicorn + Nginx (Linux)

---

## 📦 Estructura del proyecto

```
sacal/
│
├── app/
│   ├── routes/           # Blueprints por módulo
│   ├── models/           # Modelos con SQLAlchemy
│   ├── templates/        # Plantillas Jinja2
│   ├── static/           # CSS, JS, imágenes
│   └── utils/            # Funciones auxiliares (PDF, QR, etc.)
│
├── config.py             # Configuración Flask y DB
├── app.py                # Entrada principal de la app
├── requirements.txt      # Dependencias del proyecto
└── README.md             # Este archivo
```

---

## ⚙️ Instalación

1. Clona el repositorio:

```bash
git clone https://github.com/JoseMiguelVS/SACAL
cd sacal
```

2. Crea y activa un entorno virtual:

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instala dependencias:

```bash
pip install -r requirements.txt
```

4. Configura tu base de datos PostgreSQL y actualiza `.env`.

5. Ejecuta migraciones:

```bash
flask db init
flask db migrate
flask db upgrade
```

6. Corre el servidor local:

```bash
flask run
```

---

## 👤 Usuarios y Roles

- **Administrador:** Acceso completo a todos los módulos.
- **Promotor:** Registro y seguimiento de participantes.
- Inicio de sesión con correo electrónico y contraseña.

---

## 🔑 Módulos principales

| Módulo         | Funcionalidades clave                                                  |
|----------------|------------------------------------------------------------------------|
| Participantes  | Filtros avanzados, edición directa, registro con validaciones.         |
| Constancias    | Editor visual drag-and-drop, PDF con QR y datos personalizados.        |
| Pagos          | Registro de pagos, comprobantes, facturación con IVA dinámico.         |
| Paquetes       | Campos dinámicos, vinculación con sesiones y cursos.                   |
| Sesiones       | Agrupación de participantes por eventos, fechas, etc.                  |

---

## 🖨 Generación de PDF

Utiliza `ReportLab` para generar constancias personalizadas. Las coordenadas de los campos se configuran visualmente con una herramienta interna basada en HTML + JS.

También se integra generación de código QR en el PDF con información verificada.

---

## 🐞 Errores comunes

| Error | Posible causa | Solución |
|-------|----------------|----------|
| `NoneType * float` | Campo no numérico o vacío | Validar en formulario y backend |
| `column does not exist` | Migración pendiente | Revisa los modelos y corre `flask db upgrade` |
| `jinja2.exceptions.UndefinedError` | Variable faltante | Asegúrate de pasar todo el contexto a la plantilla |

---

## 🛠 Despliegue en producción

Usa `gunicorn` como servidor WSGI y `nginx` como proxy inverso.

```bash
gunicorn run:app -b localhost:8001 --reload
```

Asegúrate de tener configurado el servicio en `/etc/systemd/system/` para ejecución permanente.

---

## 🧾 Licencia

Este proyecto es de uso privado para fines educativos y administrativos.

---

## 👨‍💻 Autor

Desarrollado por: Jose Miguel Vazquez Sanchez  
Estudiante de Desarrollo de Software Multiplataforma  
Contacto: [josemiguelvazquezsanchez682@gmail.com]
