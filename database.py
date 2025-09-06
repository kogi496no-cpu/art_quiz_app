import sqlite3
from fastapi import HTTPException

UPLOAD_DIRS = {
    "western": "uploads/images",
    "japanese": "uploads/japanese_images"
}
THUMBNAIL_DIRS = {
    "western": "uploads/thumbnails",
    "japanese": "uploads/japanese_thumbnails"
}

def get_db_path(genre: str) -> str:
    if genre == "western":
        return "art.db"
    elif genre == "japanese":
        return "japanese_art.db"
    else:
        raise HTTPException(status_code=404, detail="Genre not found")

def get_upload_dir(genre: str) -> str:
    return UPLOAD_DIRS.get(genre)

def get_thumbnail_dir(genre: str) -> str:
    return THUMBNAIL_DIRS.get(genre)

def get_db_connection(genre: str):
    db_path = get_db_path(genre)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    # Row factory to get results as dictionaries
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()