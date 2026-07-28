import os
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse
import dropbox
from dropbox.files import WriteMode
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_API_HOST = os.getenv("DROPBOX_API_HOST", "api.dropbox.com")
DATABASE_URL = os.getenv("DATABASE_URL")

LOCAL_BACKUP_PATH = os.getenv("LOCAL_BACKUP_PATH", "/tmp/postgres_latest.sql.gz")
DROPBOX_DEST_PATH = os.getenv("DROPBOX_DEST_PATH", "/backups/postgres_latest.sql.gz")


def validate_env():
    required = ["DATABASE_URL", "DROPBOX_APP_KEY", "DROPBOX_APP_SECRET", "DROPBOX_REFRESH_TOKEN"]
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")


def parse_database_url(db_url):
    parsed = urlparse(db_url)
    if parsed.scheme != "postgres":
        raise ValueError("DATABASE_URL must start with postgres://")

    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "user": parsed.username or "postgres",
        "password": parsed.password or "",
        "dbname": parsed.path.lstrip("/") or "postgres",
    }


def dump_database():
    db = parse_database_url(DATABASE_URL)
    print(f"Dumping database '{db['dbname']}' at {db['host']}:{db['port']}...")

    env = os.environ.copy()
    if db["password"]:
        env["PGPASSWORD"] = db["password"]

    cmd = (
        f"pg_dump -U {db['user']} -h {db['host']} -p {db['port']} -d {db['dbname']} | "
        f"gzip > {LOCAL_BACKUP_PATH}"
    )

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        raise Exception(f"pg_dump failed: {result.stderr}")
    print("Database dumped and compressed successfully.")


def upload_to_dropbox():
    print("Connecting to Dropbox using refresh token...")
    dbx = dropbox.Dropbox(
        app_key=DROPBOX_APP_KEY,
        app_secret=DROPBOX_APP_SECRET,
        oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
    )

    if DROPBOX_API_HOST and DROPBOX_API_HOST != "api.dropboxapi.com":
        dbx._host_map = {
            "api": DROPBOX_API_HOST,
            "content": "api-content.dropbox.com" if DROPBOX_API_HOST == "api.dropbox.com" else DROPBOX_API_HOST,
            "notify": DROPBOX_API_HOST,
        }

    dest_path = Path(DROPBOX_DEST_PATH)
    parent = str(dest_path.parent)
    if parent and parent != ".":
        try:
            from dropbox.files import CreateFolderError
            dbx.files_create_folder_v2(parent, autorename=False)
            print(f"Created Dropbox folder: {parent}")
        except Exception as e:
            if "conflict" not in str(e).lower():
                raise
            print(f"Dropbox folder already exists: {parent}")

    with open(LOCAL_BACKUP_PATH, "rb") as f:
        print(f"Uploading to Dropbox at {DROPBOX_DEST_PATH} (Overwriting if exists)...")
        dbx.files_upload(
            f.read(),
            DROPBOX_DEST_PATH,
            mode=WriteMode.overwrite,
        )
    print("Dropbox upload and overwrite completed successfully!")


def main():
    try:
        validate_env()
        dump_database()
        upload_to_dropbox()
    except Exception as e:
        print(f"[ERROR] Backup process failed: {e}")
        raise
    finally:
        if os.path.exists(LOCAL_BACKUP_PATH):
            os.remove(LOCAL_BACKUP_PATH)
            print("Local temporary backup file cleaned up.")


if __name__ == "__main__":
    main()
