from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sqlite3

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# DB接続（本来はmain.pyからimport推奨）
conn = sqlite3.connect("art.db", check_same_thread=False)
c = conn.cursor()

@router.get("/artworks-page", response_class=HTMLResponse)
async def artworks_page(request: Request):
    return templates.TemplateResponse("artworks.html", {"request": request})

@router.get("/artworks")
def get_artworks():
    try:
        c.execute("SELECT id, author, title, style, image_url, image_filename, image_size, image_type, notes FROM artworks ORDER BY id DESC")
        rows = c.fetchall()
        columns = [description[0] for description in c.description]
        artworks = [dict(zip(columns, row)) for row in rows]
        return {"artworks": artworks}
    except Exception as e:
        raise HTTPException(status_code=500, detail="データの取得に失敗しました")
