"""Configuration file for the Masterblog app."""
from pathlib import Path

DB_FILE_NAME = "database.json"
UID_FILE_NAME = "uid"

PROJECT_ROOT = Path(__file__).resolve().parent  # project root

UID_FILE_PATH = PROJECT_ROOT / Path("data/" + UID_FILE_NAME)
DB_FILE_PATH = PROJECT_ROOT / Path("data/" + DB_FILE_NAME)


ERR_NO_POST_UID = "No previous post_uid found, generate from posts."
ERR_SAVE_POST_UID = "Error saving uid file, abort."
ERR_DB_CORRUPT = "DB file corrupt, abort."
ERR_SAVE_DATA_FAILED = "Saving data failed, abort."
