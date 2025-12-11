import os

POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", 5432)
POSTGRES_DB = os.environ.get("POSTGRES_DB", "blatnye")
POSTGRES_USER = os.environ.get("POSTGRES_USER", "blatnyeuser")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "bratunyipass")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"