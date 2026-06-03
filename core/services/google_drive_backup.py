import gzip
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)

DRIVE_BACKUP_MIMETYPE = "application/gzip"
DEFAULT_BACKUP_FILENAME = "assemblytour-postgres-backup.sql.gz"
DEFAULT_SCOPES = ["https://www.googleapis.com/auth/drive"]


def _first_existing_client_secret_file():
    configured_path = os.getenv("GOOGLE_DRIVE_CLIENT_SECRET_FILE")
    if configured_path:
        return Path(configured_path)

    matches = sorted(Path(settings.BASE_DIR).glob("client_secret*.json"))
    if matches:
        return matches[0]

    fallback = Path(settings.BASE_DIR) / "credentials.json"
    return fallback


def _build_drive_service():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google.oauth2 import service_account
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    scopes = [
        scope.strip()
        for scope in os.getenv("GOOGLE_DRIVE_SCOPES", ",".join(DEFAULT_SCOPES)).split(",")
        if scope.strip()
    ]

    service_account_file = os.getenv("GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE")
    if service_account_file:
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=scopes,
        )
        return build("drive", "v3", credentials=credentials, cache_discovery=False)

    token_file = Path(os.getenv("GOOGLE_DRIVE_TOKEN_FILE", settings.BASE_DIR / "token.json"))
    credentials = None
    if token_file.exists():
        credentials = Credentials.from_authorized_user_file(token_file, scopes)

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        token_file.write_text(credentials.to_json())

    if not credentials or not credentials.valid:
        client_secret_file = _first_existing_client_secret_file()
        if not client_secret_file.exists():
            raise FileNotFoundError(
                "Google Drive client secret file was not found. Set "
                "GOOGLE_DRIVE_CLIENT_SECRET_FILE or place client_secret*.json in the project root."
            )

        flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_file), scopes)
        credentials = flow.run_local_server(port=0)
        token_file.write_text(credentials.to_json())

    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def _dump_postgres(output_dir):
    database = settings.DATABASES["default"]
    sql_path = Path(output_dir) / "postgres-backup.sql"
    gzip_path = Path(output_dir) / os.getenv("GOOGLE_DRIVE_BACKUP_FILENAME", DEFAULT_BACKUP_FILENAME)

    command = [
        "pg_dump",
        "--host",
        str(database["HOST"]),
        "--port",
        str(database.get("PORT") or 5432),
        "--username",
        str(database["USER"]),
        "--dbname",
        str(database["NAME"]),
        "--no-password",
        "--file",
        str(sql_path),
    ]

    env = os.environ.copy()
    env["PGPASSWORD"] = str(database["PASSWORD"])

    logger.info("Starting PostgreSQL dump for database %s", database["NAME"])
    subprocess.run(command, env=env, check=True, capture_output=True, text=True)

    logger.info("Compressing PostgreSQL dump to %s", gzip_path.name)
    with sql_path.open("rb") as source, gzip.open(gzip_path, "wb") as destination:
        shutil.copyfileobj(source, destination)

    return gzip_path


def _find_existing_drive_file(service, filename, folder_id=None):
    query_parts = [
        f"name = '{filename.replace(chr(39), chr(92) + chr(39))}'",
        "trashed = false",
    ]
    if folder_id:
        query_parts.append(f"'{folder_id}' in parents")

    response = service.files().list(
        q=" and ".join(query_parts),
        spaces="drive",
        fields="files(id, name)",
        pageSize=1,
    ).execute()
    files = response.get("files", [])
    return files[0] if files else None


def _upload_or_replace_backup(service, gzip_path):
    from googleapiclient.http import MediaFileUpload

    folder_id = os.getenv("GOOGLE_DRIVE_BACKUP_FOLDER_ID")
    metadata = {"name": gzip_path.name}
    if folder_id:
        metadata["parents"] = [folder_id]

    media = MediaFileUpload(str(gzip_path), mimetype=DRIVE_BACKUP_MIMETYPE, resumable=True)
    existing_file = _find_existing_drive_file(service, gzip_path.name, folder_id=folder_id)

    if existing_file:
        logger.info("Replacing existing Google Drive backup file %s", existing_file["id"])
        return service.files().update(
            fileId=existing_file["id"],
            media_body=media,
            body={"name": gzip_path.name},
            fields="id, name, modifiedTime, webViewLink",
        ).execute()

    logger.info("Uploading new Google Drive backup file %s", gzip_path.name)
    return service.files().create(
        body=metadata,
        media_body=media,
        fields="id, name, modifiedTime, webViewLink",
    ).execute()


def backup_postgres_to_google_drive():
    """Dump PostgreSQL, gzip the dump, then upload it to Google Drive."""
    with tempfile.TemporaryDirectory(prefix="assemblytour-db-backup-") as temp_dir:
        gzip_path = _dump_postgres(temp_dir)
        service = _build_drive_service()
        uploaded_file = _upload_or_replace_backup(service, gzip_path)
        logger.info("PostgreSQL backup uploaded to Google Drive: %s", uploaded_file)
        return uploaded_file
