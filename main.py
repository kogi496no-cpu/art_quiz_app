
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# ルーターをインポート
from artworks import router as artworks_router
from quiz import router as quiz_router

app = FastAPI()

# 静的ファイル配信の設定
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")

# ルーターをジャンルごとのプレフィックスで登録
app.include_router(artworks_router, prefix="/api/{genre}")
app.include_router(quiz_router, prefix="/api/{genre}")

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """トップページ。西洋美術か日本美術かを選択する画面。"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/quiz/{genre}", response_class=HTMLResponse)
async def read_quiz(request: Request, genre: str):
    """ジャンル別のクイズページ"""
    if genre not in ["western", "japanese"]:
        return RedirectResponse(url="/")
    return templates.TemplateResponse("quiz.html", {"request": request, "genre": genre})

@app.get("/artworks/{genre}", response_class=HTMLResponse)
async def read_artworks(request: Request, genre: str):
    """ジャンル別の作品管理ページ"""
    if genre not in ["western", "japanese"]:
        return RedirectResponse(url="/")
    return templates.TemplateResponse("artworks.html", {"request": request, "genre": genre})
