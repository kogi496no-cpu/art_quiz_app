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

conn = sqlite3.connect("art.db", check_same_thread=False)
c = conn.cursor()

app = FastAPI()
app.include_router(artworks_router)
app.include_router(quiz_router)

# 静的ファイル配信の設定
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")


templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_quiz(request: Request):
    return templates.TemplateResponse("quiz.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def read_register(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# artworks-page エンドポイントはartworks.pyに移動しました