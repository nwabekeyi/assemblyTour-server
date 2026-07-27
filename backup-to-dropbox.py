import os
import subprocess
from pathlib import Path
import dropbox
from dropbox.files import WriteMode
from dotenv import load_dotenv

# Load environment variables from .env file located in the same directory
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

# Retrieve variables from environment
DB_CONTAINER_NAME = os.getenv("DB_CONTAINER_NAME")
DB_USER = os.getenv("DB_USER", "postgres")
DB_NAME = os.getenv("DB_NAME")

DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

LOCAL_BACKUP_PATH = os.getenv("LOCAL_BACKUP_PATH", "/tmp/postgres_latest.sql.gz")
DROPBOX_DEST_PATH = os.getenv("DROPBOX_DEST_PATH", "/backups/postgres_latest.sql.gz")

def validate_env():
    """Ensure all required environment variables are set before running."""
    required_vars = [
        "DB_CONTAINER_NAME", "DB_NAME", 
        "DROPBOX_APP_KEY", "DROPBOX_APP_SECRET", "DROPBOX_REFRESH_TOKEN"
    ]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

def dump_database():
    print(f"Dumping database '{DB_NAME}' from container '{DB_CONTAINER_NAME}'...")
    cmd = f"docker exec {DB_CONTAINER_NAME} pg_dump -U {DB_USER} -d {DB_NAME} | gzip > {LOCAL_BACKUP_PATH}"
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"pg_dump failed: {result.stderr}")
    print("Database dumped and compressed successfully.")

def upload_to_dropbox():
    print("Connecting to Dropbox using refresh token...")
    dbx = dropbox.Dropbox(
        app_key=DROPBOX_APP_KEY,
        app_secret=DROPBOX_APP_SECRET,
        oauth2_refresh_token=DROPBOX_REFRESH_TOKEN
    )

    with open(LOCAL_BACKUP_PATH, "rb") as f:
        print(f"Uploading to Dropbox at {DROPBOX_DEST_PATH} (Overwriting if exists)...")
        dbx.files_upload(
            f.read(),
            DROPBOX_DEST_PATH,
            mode=WriteMode.overwrite
        )
    print("Dropbox upload and overwrite completed successfully!")

def main():
    try:
        validate_env()
        dump_database()
        upload_to_dropbox()
    except Exception as e:
        print(f"[ERROR] Backup process failed: {e}")
    finally:
        if os.path.exists(LOCAL_BACKUP_PATH):
            os.remove(LOCAL_BACKUP_PATH)
            print("Local temporary backup file cleaned up.")

if __name__ == "__main__":
    main()