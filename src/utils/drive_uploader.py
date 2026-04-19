"""
drive_uploader.py — Sube notebooks (.ipynb) a una carpeta compartida de Google Drive.

Uso:
    python src/utils/drive_uploader.py                          # Sube todos los .ipynb de notebooks/
    python src/utils/drive_uploader.py notebooks/MiNotebook.ipynb  # Sube uno específico

Requisitos previos:
    1. Tener habilitada la Google Drive API en tu proyecto de GCP.
    2. Haber descargado credentials.json en config/credentials.json
    3. pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
"""

import sys
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# ──────────────────────────────────────────────
# CONFIGURACIÓN — EDITA ESTOS VALORES
# ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CREDENTIALS_FILE = PROJECT_ROOT / "config" / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "config" / "token.json"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"

# ID de la carpeta compartida en Drive.
# Para obtenerlo: abre la carpeta en Drive en tu navegador,
# la URL será https://drive.google.com/drive/folders/XXXXXXXXXXXX
# Copia el XXXXXXXXXXXX y pégalo aquí:
DRIVE_FOLDER_ID = "101RXRn2OaZDz8JtovOEncgn77Lsiuxg4"

# Permisos necesarios (lectura/escritura de archivos)
SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def authenticate():
    """
    Autentica al usuario con OAuth2.
    La primera vez abrirá el navegador para autorizar.
    Las siguientes veces reutiliza el token guardado.
    """
    creds = None

    # Intentar cargar token existente
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    # Si no hay token válido, iniciar flujo OAuth
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refrescando token de acceso...")
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                print(f"❌ No se encontró {CREDENTIALS_FILE}")
                print("   Descarga credentials.json desde Google Cloud Console")
                print("   y colócalo en config/credentials.json")
                sys.exit(1)

            print("🌐 Abriendo navegador para autorización...")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Guardar token para futuras ejecuciones
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(creds.to_json())
        print("✅ Token guardado en", TOKEN_FILE)

    return creds


def upload_file(service, local_path: Path, folder_id: str) -> dict:
    """
    Sube un archivo a la carpeta especificada de Google Drive.
    Si ya existe un archivo con el mismo nombre, lo actualiza.

    Returns:
        Metadata del archivo subido (id, name, webViewLink).
    """
    file_name = local_path.name
    mime_type = "application/x-ipynb+json"

    # Buscar si ya existe un archivo con ese nombre en la carpeta
    query = f"name='{file_name}' and '{folder_id}' in parents and trashed=false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    existing_files = results.get("files", [])

    media = MediaFileUpload(str(local_path), mimetype=mime_type, resumable=True)

    if existing_files:
        # Actualizar archivo existente
        file_id = existing_files[0]["id"]
        print(f"   📝 Actualizando '{file_name}' (ya existía en Drive)...")
        updated = (
            service.files()
            .update(fileId=file_id, media_body=media, fields="id, name, webViewLink")
            .execute()
        )
        return updated
    else:
        # Crear archivo nuevo
        print(f"   📤 Subiendo '{file_name}' por primera vez...")
        file_metadata = {"name": file_name, "parents": [folder_id]}
        created = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id, name, webViewLink")
            .execute()
        )
        return created


def upload_notebooks(file_paths: list[Path] | None = None):
    """
    Sube uno o varios notebooks a la carpeta de Drive configurada.

    Args:
        file_paths: Lista de paths a subir. Si es None, sube todos
                    los .ipynb encontrados en notebooks/.
    """
    if DRIVE_FOLDER_ID == "TU_FOLDER_ID_AQUI":
        print("❌ Debes configurar DRIVE_FOLDER_ID en este archivo.")
        print("   Abre tu carpeta compartida en Drive y copia el ID de la URL.")
        sys.exit(1)

    # Determinar qué archivos subir
    if file_paths:
        notebooks = [Path(p).resolve() for p in file_paths]
    else:
        notebooks = sorted(NOTEBOOKS_DIR.glob("*.ipynb"))

    if not notebooks:
        print("⚠️  No se encontraron notebooks para subir.")
        return

    print(f"🚀 Subiendo {len(notebooks)} notebook(s) a Google Drive...")
    print(f"   Carpeta destino: https://drive.google.com/drive/folders/{DRIVE_FOLDER_ID}\n")

    # Autenticar y construir servicio
    creds = authenticate()
    service = build("drive", "v3", credentials=creds)

    # Subir cada notebook
    for nb_path in notebooks:
        if not nb_path.exists():
            print(f"   ⚠️  Archivo no encontrado: {nb_path}")
            continue

        result = upload_file(service, nb_path, DRIVE_FOLDER_ID)
        link = result.get("webViewLink", "N/A")
        print(f"   ✅ {result['name']} → {link}\n")

    print("🎉 Subida completada.")


if __name__ == "__main__":
    # Si se pasan argumentos, subir esos archivos específicos
    # Si no, subir todos los .ipynb de notebooks/
    if len(sys.argv) > 1:
        paths = [Path(p) for p in sys.argv[1:]]
        upload_notebooks(paths)
    else:
        upload_notebooks()
