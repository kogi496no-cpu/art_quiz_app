from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
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

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# アップロード設定
UPLOAD_DIR = "uploads/images"
THUMBNAIL_DIR = "uploads/thumbnails"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

# ディレクトリが存在しない場合は作成
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(THUMBNAIL_DIR, exist_ok=True)

# 画像処理のヘルパー関数
def validate_image_file(file: UploadFile) -> bool:
    """画像ファイルの検証"""
    # ファイル拡張子チェック
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False
    
    # MIMEタイプチェック
    if not file.content_type or not file.content_type.startswith('image/'):
        return False
    
    return True

def save_image_with_thumbnail(file: UploadFile) -> tuple[str, str, int]:
    """画像とサムネイルを保存して、ファイル名、サムネイル名、ファイルサイズを返す"""
    # 一意のファイル名生成
    ext = os.path.splitext(file.filename)[1].lower()
    unique_filename = f"{uuid.uuid4()}{ext}"
    thumbnail_filename = f"thumb_{unique_filename}"
    
    # オリジナル画像保存
    original_path = os.path.join(UPLOAD_DIR, unique_filename)
    thumbnail_path = os.path.join(THUMBNAIL_DIR, thumbnail_filename)
    
    # ファイルサイズ取得のためにファイルを読み込み
    content = file.file.read()
    file_size = len(content)
    
    # ファイルサイズチェック
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="ファイルサイズが大きすぎます（5MB以下）")
    
    # オリジナル画像保存
    with open(original_path, "wb") as buffer:
        buffer.write(content)
    
    # サムネイル作成
    try:
        with Image.open(original_path) as img:
            # RGBA画像の場合はRGBに変換
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # サムネイル作成（300x300に収まるようにリサイズ）
            img.thumbnail((300, 300), Image.Resampling.LANCZOS)
            img.save(thumbnail_path, optimize=True, quality=85)
    except Exception as e:
        # サムネイル作成に失敗した場合、オリジナルファイルを削除
        if os.path.exists(original_path):
            os.remove(original_path)
        raise HTTPException(status_code=400, detail="画像ファイルの処理に失敗しました")
    
    return unique_filename, thumbnail_filename, file_size

# DB接続（本来はmain.pyからimport推奨）
conn = sqlite3.connect("art.db", check_same_thread=False)
c = conn.cursor()

# 更新用モデル
class ArtworkUpdate(BaseModel):
    author: str
    title: str
    style: str
    notes: Optional[str] = None

    @validator('author', 'title', 'style')
    def sanitize_text_fields(cls, v):
        if not v:
            return v
        cleaned = re.sub(r'<[^>]*>', '', v)
        cleaned = html.escape(cleaned)
        if len(cleaned) > 200:
            raise ValueError('入力文字数が長すぎます（200文字以内）')
        return cleaned.strip()

    @validator('notes')
    def sanitize_notes(cls, v):
        if not v:
            return v
        cleaned = re.sub(r'<[^>]*>', '', v)
        cleaned = html.escape(cleaned)
        if len(cleaned) > 1000:
            raise ValueError('備考が長すぎます（1000文字以内）')
        return cleaned.strip()

@router.get("/artworks", response_class=HTMLResponse)
async def artworks_page(request: Request):
    return templates.TemplateResponse("artworks.html", {"request": request})

@router.get("/api/artworks")
def get_artworks(request: Request):
    try:
        search_query = request.query_params.get('q', None)
        
        base_query = "SELECT id, author, title, style, image_filename, image_size, image_type, notes FROM artworks"
        params = []
        
        if search_query:
            # 全文検索（複数キーワード対応）
            keywords = search_query.split()
            where_clauses = []
            for keyword in keywords:
                # 各キーワードで各カラムを検索
                keyword_param = f"%{keyword}%"
                where_clauses.append("(author LIKE ? OR title LIKE ? OR style LIKE ? OR notes LIKE ?)")
                params.extend([keyword_param] * 4)
            
            base_query += " WHERE " + " AND ".join(where_clauses)

        base_query += " ORDER BY id DESC"
        
        c.execute(base_query, params)
        
        rows = c.fetchall()
        columns = [description[0] for description in c.description]
        artworks = [dict(zip(columns, row)) for row in rows]
        
        return {"artworks": artworks}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"データの取得に失敗しました: {e}")

# 画像アップロード対応の作品登録エンドポイント
@router.post("/api/artworks/upload")
async def add_artwork_with_image(
    author: str = Form(...),
    title: str = Form(...),
    style: str = Form(...),
    notes: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None)
):
    try:
        # 画像ファイルの処理
        image_filename = None
        image_size = None
        image_type = None
        
        if image:
            if not validate_image_file(image):
                raise HTTPException(status_code=400, detail="無効な画像ファイルです")
            
            image_filename, thumbnail_filename, image_size = save_image_with_thumbnail(image)
            image_type = image.content_type
        
        # データベースに作品情報を登録
        c.execute("""
            INSERT INTO artworks (author, title, style, notes, image_filename, image_size, image_type) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            author,
            title,
            style,
            notes,
            image_filename,
            image_size,
            image_type
        ))
        
        artwork_id = c.lastrowid
        conn.commit()
        
        # 登録した作品情報を取得して返す
        c.execute("SELECT * FROM artworks WHERE id = ?", (artwork_id,))
        columns = [description[0] for description in c.description]
        artwork_data = dict(zip(columns, c.fetchone()))
        
        return {"message": "作品を登録しました", "artwork": artwork_data}
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        # 画像ファイルがある場合は削除
        if image_filename:
            try:
                original_path = os.path.join(UPLOAD_DIR, image_filename)
                thumbnail_path = os.path.join(THUMBNAIL_DIR, f"thumb_{image_filename}")
                if os.path.exists(original_path):
                    os.remove(original_path)
                if os.path.exists(thumbnail_path):
                    os.remove(thumbnail_path)
            except:
                pass  # エラーは無視（データベースロールバックが重要）
        
        raise HTTPException(status_code=500, detail="作品の登録に失敗しました")

# 作品更新エンドポイント
@router.put("/api/artworks/{artwork_id}")
def update_artwork(artwork_id: int, artwork: ArtworkUpdate):
    try:
        c.execute("""
            UPDATE artworks 
            SET author = ?, title = ?, style = ?, notes = ?
            WHERE id = ?
        """, (artwork.author, artwork.title, artwork.style, artwork.notes, artwork_id))
        
        if c.rowcount == 0:
            raise HTTPException(status_code=404, detail="作品が見つかりません")
        
        conn.commit()
        
        c.execute("SELECT * FROM artworks WHERE id = ?", (artwork_id,))
        columns = [description[0] for description in c.description]
        updated_artwork = dict(zip(columns, c.fetchone()))
        
        return {"message": "作品を更新しました", "artwork": updated_artwork}
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"更新に失敗しました: {e}")


# 作品削除エンドポイント
@router.delete("/api/artworks/{artwork_id}")
def delete_artwork(artwork_id: int):
    try:
        # まず削除対象の作品情報を取得（画像ファイル削除のため）
        c.execute("SELECT image_filename FROM artworks WHERE id = ?", (artwork_id,))
        row = c.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="作品が見つかりません")
        
        image_filename = row[0]
        
        # データベースから削除
        c.execute("DELETE FROM artworks WHERE id = ?", (artwork_id,))
        
        if c.rowcount == 0:
            raise HTTPException(status_code=404, detail="作品が見つかりません")
        
        conn.commit()
        
        # 関連する画像ファイルも削除
        if image_filename:
            try:
                original_path = os.path.join(UPLOAD_DIR, image_filename)
                thumbnail_path = os.path.join(THUMBNAIL_DIR, f"thumb_{image_filename}")
                
                if os.path.exists(original_path):
                    os.remove(original_path)
                if os.path.exists(thumbnail_path):
                    os.remove(thumbnail_path)
            except Exception as file_error:
                # ファイル削除エラーは警告レベル（データは削除済み）
                print(f"Warning: 画像ファイルの削除に失敗しました: {file_error}")
        
        return {"message": "作品を削除しました"}
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail="削除に失敗しました")
