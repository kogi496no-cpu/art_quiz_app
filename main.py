import secrets
from starlette.middleware.sessions import SessionMiddleware

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# ルーターをインポート
from artworks import router as artworks_router
from quiz import quiz_router, stats_router

app = FastAPI()

# セッションミドルウェアの設定
# 本番環境では、このSECRET_KEYを環境変数などから取得するようにしてください
SECRET_KEY = secrets.token_hex(32)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# 静的ファイル配信の設定
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")

# ルーターを登録
app.include_router(stats_router)
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
    
    # ジャンルに応じたCSSファイルを決定
    css_file = f"{genre}.css"
    
    return templates.TemplateResponse("quiz.html", {"request": request, "genre": genre, "css_file": css_file})

@app.get("/artworks/{genre}", response_class=HTMLResponse)
async def read_artworks(request: Request, genre: str):
    """ジャンル別の作品管理ページ"""
    if genre not in ["western", "japanese"]:
        return RedirectResponse(url="/")
    
    # ジャンルに応じたCSSファイルを決定
    css_file = f"{genre}.css"
    
    return templates.TemplateResponse("artworks.html", {"request": request, "genre": genre, "css_file": css_file})
