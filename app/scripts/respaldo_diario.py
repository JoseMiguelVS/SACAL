import os
import datetime
import subprocess
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Crear respaldo de PostgreSQL
def backup_postgres():
    fecha = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    backup_filename = f"{os.environ.get('db_name')}_backup_{fecha}.sql"
    backup_dir = os.path.join(os.getcwd(), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    backup_path = os.path.join(backup_dir, backup_filename)

    os.environ['PGPASSWORD'] = os.environ.get('db_password')

    try:
        subprocess.run([
            "pg_dump",
            "-h", os.environ.get('db_host'),
            "-U", os.environ.get('db_username'),
            "-F", "c",  # formato personalizado
            "-f", backup_path,
            os.environ.get('db_name')
        ], check=True)
        print(f"✅ Respaldo creado: {backup_path}")
        return backup_path
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al crear respaldo: {e}")
        return None

# Subir archivo a Google Drive
def upload_to_drive(file_path):
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("mycreds.txt")

    if gauth.credentials is None:
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()

    gauth.SaveCredentialsFile("mycreds.txt")
    drive = GoogleDrive(gauth)

    file = drive.CreateFile({'title': os.path.basename(file_path)})
    file.SetContentFile(file_path)
    file.Upload()
    print(f"📤 Archivo subido a Drive: {file['title']}")

# Ejecución principal
def main():
    backup_path = backup_postgres()
    if backup_path:
        upload_to_drive(backup_path)

if __name__ == "__main__":
    main()
