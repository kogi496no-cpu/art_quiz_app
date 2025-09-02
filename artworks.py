from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from pydantic import BaseModel, validator
import sqlite3
import os
import uuid
from PIL import Image
import re
import html

from database import get_db_connection, get_upload_dir, get_thumbnail_dir

router = APIRouter()
templates = Jinja2Templates(directory="templates")

MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

def validate_image_file(file: UploadFile) -> bool:
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False
    if not file.content_type or not file.content_type.startswith('image/'):
        return False
    return True

def save_image_with_thumbnail(content: bytes, filename: str, genre: str) -> tuple[str, str, int]:
    upload_dir = get_upload_dir(genre)
    thumbnail_dir = get_thumbnail_dir(genre)
    
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(thumbnail_dir, exist_ok=True)

    ext = os.path.splitext(filename)[1].lower()
    unique_filename = f"{uuid.uuid4()}{ext}"
    
    original_path = os.path.join(upload_dir, unique_filename)
    thumbnail_path = os.path.join(thumbnail_dir, f"thumb_{unique_filename}")
    
    file_size = len(content)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="ファイルサイズが大きすぎます（5MB以下）")
    
    with open(original_path, "wb") as buffer:
        buffer.write(content)
    
    try:
        with Image.open(original_path) as img:
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            img.thumbnail((300, 300), Image.Resampling.LANCZOS)
            img.save(thumbnail_path, optimize=True, quality=85)
    except Exception as e:
        if os.path.exists(original_path):
            os.remove(original_path)
        raise HTTPException(status_code=400, detail=f"画像ファイルの処理に失敗しました: {e}")
    
    return unique_filename, f"thumb_{unique_filename}", file_size

class ArtworkUpdate(BaseModel):
    author: str
    title: str
    style: str
    notes: Optional[str] = None

    @validator('author', 'title', 'style')
    def sanitize_text_fields(cls, v):
        if not v: return v
        cleaned = re.sub(r'<[^>]*>', '', v)
        cleaned = html.escape(cleaned)
        if len(cleaned) > 200: raise ValueError('入力文字数が長すぎます（200文字以内）')
        return cleaned.strip()

    @validator('notes')
    def sanitize_notes(cls, v):
        if not v: return v
        cleaned = re.sub(r'<[^>]*>', '', v)
        cleaned = html.escape(cleaned)
        if len(cleaned) > 1000: raise ValueError('備考が長すぎます（1000文字以内）')
        return cleaned.strip()

@router.get("/artworks")
def get_artworks(
    request: Request,
    genre: str,
    conn: sqlite3.Connection = Depends(get_db_connection)
):
    try:
        cursor = conn.cursor()
        search_query = request.query_params.get('q', None)
        
        base_query = "SELECT id, author, title, style, image_filename, image_size, image_type, notes FROM artworks"
        params = []
        
        if search_query:
            keywords = search_query.split()
            where_clauses = []
            for keyword in keywords:
                keyword_param = f"%{keyword}%"
                where_clauses.append("(author LIKE ? OR title LIKE ? OR style LIKE ? OR notes LIKE ?)")
                params.extend([keyword_param] * 4)
            base_query += " WHERE " + " AND ".join(where_clauses)

        base_query += " ORDER BY id DESC"
        
        cursor.execute(base_query, params)
        artworks = [dict(row) for row in cursor.fetchall()]
        
        return {"artworks": artworks}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"データの取得に失敗しました: {e}")

@router.post("/artworks/upload")
async def add_artwork_with_image(
    genre: str,
    author: str = Form(...),
    title: str = Form(...),
    style: str = Form(...),
    notes: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    conn: sqlite3.Connection = Depends(get_db_connection)
):
    # サニタイズ
    author = author.strip()
    title = title.strip()
    style = style.strip()
    if notes:
        notes = notes.strip()

    image_filename = None
    try:
        cursor = conn.cursor()
        image_size = None
        image_type = None
        
        if image:
            if not validate_image_file(image):
                raise HTTPException(status_code=400, detail="無効な画像ファイルです")
            
            content = await image.read()
            image_filename, _, image_size = save_image_with_thumbnail(content, image.filename, genre)
            image_type = image.content_type
        
        cursor.execute("""
            INSERT INTO artworks (author, title, style, notes, image_filename, image_size, image_type) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (author, title, style, notes, image_filename, image_size, image_type))
        
        artwork_id = cursor.lastrowid
        conn.commit()
        
        cursor.execute("SELECT * FROM artworks WHERE id = ?", (artwork_id,))
        artwork_data = dict(cursor.fetchone())
        
        return {"message": "作品を登録しました", "artwork": artwork_data}
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        if image_filename:
            try:
                upload_dir = get_upload_dir(genre)
                thumbnail_dir = get_thumbnail_dir(genre)
                original_path = os.path.join(upload_dir, image_filename)
                thumbnail_path = os.path.join(thumbnail_dir, f"thumb_{image_filename}")
                if os.path.exists(original_path): os.remove(original_path)
                if os.path.exists(thumbnail_path): os.remove(thumbnail_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"作品の登録に失敗しました: {e}")

@router.put("/artworks/{artwork_id}")
def update_artwork(
    genre: str,
    artwork_id: int,
    artwork: ArtworkUpdate,
    conn: sqlite3.Connection = Depends(get_db_connection)
):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE artworks 
            SET author = ?, title = ?, style = ?, notes = ?
            WHERE id = ?
        """, (artwork.author, artwork.title, artwork.style, artwork.notes, artwork_id))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="作品が見つかりません")
        
        conn.commit()
        
        cursor.execute("SELECT * FROM artworks WHERE id = ?", (artwork_id,))
        updated_artwork = dict(cursor.fetchone())
        
        return {"message": "作品を更新しました", "artwork": updated_artwork}
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"更新に失敗しました: {e}")

@router.delete("/artworks/{artwork_id}")
def delete_artwork(
    genre: str,
    artwork_id: int,
    conn: sqlite3.Connection = Depends(get_db_connection)
):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT image_filename FROM artworks WHERE id = ?", (artwork_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="作品が見つかりません")
        
        image_filename = row["image_filename"]
        
        cursor.execute("DELETE FROM artworks WHERE id = ?", (artwork_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="作品が見つかりません")
        
        conn.commit()
        
        if image_filename:
            try:
                upload_dir = get_upload_dir(genre)
                thumbnail_dir = get_thumbnail_dir(genre)
                original_path = os.path.join(upload_dir, image_filename)
                thumbnail_path = os.path.join(thumbnail_dir, f"thumb_{image_filename}")
                
                if os.path.exists(original_path): os.remove(original_path)
                if os.path.exists(thumbnail_path): os.remove(thumbnail_path)
            except Exception as file_error:
                print(f"Warning: 画像ファイルの削除に失敗しました: {file_error}")
        
        return {"message": "作品を削除しました"}
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"削除に失敗しました: {e}")