from fastapi import FastAPI, HTTPException
from artworks import router as artworks_router
from quiz import router as quiz_router
from pydantic import BaseModel, validator
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Optional
import random
import sqlite3
import re
import html

conn = sqlite3.connect("art.db", check_same_thread=False)
c = conn.cursor()

class ArtworkBase(BaseModel):
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

class ArtworkUpdate(ArtworkBase):
    pass

app = FastAPI()
app.include_router(artworks_router)
app.include_router(quiz_router)

# 静的ファイル配信の設定
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")

# 作品一覧取得エンドポイント
@app.get("/artworks")
def get_artworks():
    try:
        c.execute("SELECT id, author, title, style, image_url, image_filename, image_size, image_type, notes FROM artworks ORDER BY id DESC")
        rows = c.fetchall()
        columns = [description[0] for description in c.description]
        artworks = [dict(zip(columns, row)) for row in rows]
        return {"artworks": artworks}
    except Exception as e:
        raise HTTPException(status_code=500, detail="データの取得に失敗しました")

# 作品更新エンドポイント
@app.put("/artworks/{artwork_id}")
def update_artwork(artwork_id: int, artwork_update: ArtworkUpdate):
    try:
        # データベースを更新
        c.execute("""
            UPDATE artworks 
            SET author = ?, title = ?, style = ?, notes = ?
            WHERE id = ?
        """, (
            artwork_update.author,
            artwork_update.title,
            artwork_update.style,
            artwork_update.notes,
            artwork_id
        ))
        
        if c.rowcount == 0:
            raise HTTPException(status_code=404, detail="作品が見つかりません")
            
        conn.commit()
        
        # 更新された作品情報を取得して返す
        c.execute("SELECT id, author, title, style, image_url, image_filename, image_size, image_type, notes FROM artworks WHERE id = ?", (artwork_id,))
        updated_artwork = dict(zip([d[0] for d in c.description], c.fetchone()))

        return {"message": "更新しました", "artwork": updated_artwork}

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"更新に失敗しました: {e}")



templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# artworks-page エンドポイントはartworks.pyに移動しました