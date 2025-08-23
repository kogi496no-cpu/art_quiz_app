

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from artworks import router as artworks_router
from pydantic import BaseModel, validator
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Optional
import random
import sqlite3
import re
import html
import os
import uuid
from PIL import Image
import shutil

app = FastAPI()
app.include_router(artworks_router)

# 静的ファイル配信の設定
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")

# アップロード設定
UPLOAD_DIR = "uploads/images"
THUMBNAIL_DIR = "uploads/thumbnails"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

# ディレクトリが存在しない場合は作成
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(THUMBNAIL_DIR, exist_ok=True)

# セキュリティヘッダーのミドルウェア
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src * data: https:; "  # 一時的に全て許可
        "connect-src 'self'"
    )
    return response

# SQLite 初期化
conn = sqlite3.connect("art.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS artworks (
    id INTEGER PRIMARY KEY,
    author TEXT,
    title TEXT,
    style TEXT,
    image_url TEXT,
    image_filename TEXT,
    image_size INTEGER,
    image_type TEXT,
    notes TEXT
)
""")

# クイズ結果記録テーブル
c.execute("""
CREATE TABLE IF NOT EXISTS quiz_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_field TEXT,
    correct_answer TEXT,
    user_answer TEXT,
    is_correct BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# 既存のテーブルに新しいカラムを追加（存在しない場合のみ）
def add_column_if_not_exists(table, column, col_type):
    try:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        conn.commit()
    except sqlite3.OperationalError as e:
        # カラムが既に存在する場合のエラーを無視
        if f"duplicate column name: {column}" not in str(e).lower():
            raise

add_column_if_not_exists('artworks', 'image_filename', 'TEXT')
add_column_if_not_exists('artworks', 'image_size', 'INTEGER')
add_column_if_not_exists('artworks', 'image_type', 'TEXT')
add_column_if_not_exists('artworks', 'notes', 'TEXT')


# Pydanticモデル
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

# 画像アップロード対応の作品登録エンドポイント
@app.post("/artworks/upload")
async def add_artwork_with_image(
    author: str = Form(...),
    title: str = Form(...),
    style: str = Form(...),
    notes: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None)
):
    try:
        # バリデーション
        artwork_data = ArtworkBase(author=author, title=title, style=style, notes=notes)

        # 画像ファイルの処理
        image_filename, image_size, image_type = None, None, None
        if image and image.filename:
            if not validate_image_file(image):
                raise HTTPException(status_code=400, detail="サポートされていない画像形式です")
            image_filename, _, image_size = save_image_with_thumbnail(image)
            image_type = image.content_type

        # データベースに保存
        c.execute("""
            INSERT INTO artworks (author, title, style, notes, image_url, image_filename, image_size, image_type) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            artwork_data.author, artwork_data.title, artwork_data.style, artwork_data.notes,
            None, image_filename, image_size, image_type
        ))
        conn.commit()
        
        return {"message": "保存しました", "image_uploaded": image_filename is not None}
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"データの保存に失敗しました: {e}")

# 作品一覧取得エンドポイント
@app.get("/artworks")
def get_artworks():
    try:
        c.execute("SELECT id, author, title, style, image_url, image_filename, image_size, image_type, notes FROM artworks ORDER BY id DESC")
        rows = c.fetchall()
        
        # カラム名を取得
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

# 作品削除エンドポイント
@app.delete("/artworks/{artwork_id}")
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

# クイズ結果記録エンドポイント
@app.post("/quiz/submit")
def submit_quiz_result(result: dict):
    try:
        c.execute("""
            INSERT INTO quiz_results (question_field, correct_answer, user_answer, is_correct) 
            VALUES (?, ?, ?, ?)
        """, (
            result.get("question_field"),
            result.get("correct_answer"),
            result.get("user_answer"),
            result.get("is_correct")
        ))
        conn.commit()
        return {"message": "結果を記録しました"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail="結果の記録に失敗しました")

# 統計情報取得エンドポイント
@app.get("/quiz/stats")
def get_quiz_stats():
    try:
        # 全体統計
        c.execute("SELECT COUNT(*) FROM quiz_results")
        total_attempts = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM quiz_results WHERE is_correct = 1")
        correct_attempts = c.fetchone()[0]
        
        # 分野別統計
        c.execute("""
            SELECT question_field, 
                   COUNT(*) as total,
                   SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct
            FROM quiz_results 
            GROUP BY question_field
        """)
        field_stats = c.fetchall()
        
        # 最近の結果（直近10件）
        c.execute("""
            SELECT question_field, correct_answer, user_answer, is_correct, created_at
            FROM quiz_results 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        recent_results = c.fetchall()
        
        overall_accuracy = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0
        
        return {
            "total_attempts": total_attempts,
            "correct_attempts": correct_attempts,
            "overall_accuracy": round(overall_accuracy, 1),
            "field_stats": [
                {
                    "field": row[0],
                    "total": row[1],
                    "correct": row[2],
                    "accuracy": round((row[2] / row[1] * 100), 1) if row[1] > 0 else 0
                }
                for row in field_stats
            ],
            "recent_results": [
                {
                    "field": row[0],
                    "correct_answer": row[1],
                    "user_answer": row[2],
                    "is_correct": bool(row[3]),
                    "date": row[4]
                }
                for row in recent_results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="統計情報の取得に失敗しました")

# クイズ用エンドポイント（従来版）
@app.get("/quiz")
def get_quiz():
    c.execute("SELECT * FROM artworks ORDER BY RANDOM() LIMIT 1")
    row = c.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="データがありません")

    # カラム名から辞書を作成
    columns = [description[0] for description in c.description]
    artwork_data = dict(zip(columns, row))

    fields = ["author", "title", "style", "image"]
    hide_field = random.choice(fields)

    quiz = artwork_data.copy()
    answer = None

    if hide_field == 'image':
        quiz['image_filename'] = None
        quiz['image_url'] = None
        answer = "画像"
    else:
        answer = quiz[hide_field]
        quiz[hide_field] = "???"

    return {
        "quiz": quiz,
        "answer_field": hide_field,
        "answer": answer,
        "notes": artwork_data.get("notes")
    }

# 4択クイズ用エンドポイント
@app.get("/quiz/multiple-choice")
def get_multiple_choice_quiz():
    # 最低4件のデータが必要
    c.execute("SELECT COUNT(*) FROM artworks")
    count = c.fetchone()[0]
    if count < 4:
        raise HTTPException(status_code=404, detail="4択クイズには最低4件のデータが必要です")

    # 正解の作品を選択
    c.execute("SELECT * FROM artworks ORDER BY RANDOM() LIMIT 1")
    correct_row_tuple = c.fetchone()
    columns = [d[0] for d in c.description]
    correct_row = dict(zip(columns, correct_row_tuple))
    
    # 問題として出す項目を選択（作者、作品名、様式のいずれか）
    question_field = random.choice(["author", "title", "style"])
    correct_answer = correct_row[question_field]
    
    # ダミー選択肢を3つ生成
    dummy_query = f"""
    SELECT DISTINCT {question_field} FROM artworks 
    WHERE {question_field} != ? AND {question_field} IS NOT NULL AND {question_field} != ''
    ORDER BY RANDOM() LIMIT 3
    """
    c.execute(dummy_query, (correct_answer,))
    dummy_answers = [row[0] for row in c.fetchall()]
    
    # ダミーが足りない場合は一般的な選択肢で補完
    fallback_options = {
        "author": ["レオナルド・ダ・ヴィンチ", "ミケランジェロ", "ラファエロ", "ピカソ", "モネ", "ゴッホ"],
        "title": ["モナリザ", "最後の晩餐", "星月夜", "ひまわり", "叫び", "真珠の耳飾りの少女"],
        "style": ["ルネサンス", "バロック", "印象派", "キュビスム", "シュルレアリスム", "抽象表現主義"]
    }
    
    all_fallbacks = [opt for opt in fallback_options[question_field] if opt != correct_answer and opt not in dummy_answers]
    while len(dummy_answers) < 3 and all_fallbacks:
        chosen = random.choice(all_fallbacks)
        dummy_answers.append(chosen)
        all_fallbacks.remove(chosen)

    # それでも足りない場合の最終手段
    i = 1
    while len(dummy_answers) < 3:
        dummy_answers.append(f"ダミー選択肢{i}")
        i += 1

    # 選択肢をシャッフル
    choices = [correct_answer] + dummy_answers
    random.shuffle(choices)
    
    # 作品情報を整理（問題にするフィールドは隠す）
    quiz_artwork_data = correct_row.copy()
    quiz_artwork_data[question_field] = "???"
    
    # 問題文の生成
    field_names = {"author": "作者", "title": "作品名", "style": "美術様式"}
    question_text = f"この作品の{field_names[question_field]}は？"
    
    return {
        "artwork": quiz_artwork_data,
        "full_artwork_data": correct_row, # 正解表示用に完全なデータを保持
        "question": question_text,
        "question_field": question_field,
        "choices": choices,
        "correct_answer": correct_answer
    }

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/quiz/reset")
def reset_quiz_results():
    try:
        c.execute("DELETE FROM quiz_results")
        conn.commit()
        return {"message": "クイズ結果をリセットしました"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail="リセットに失敗しました")
    
@app.get("/artworks-page", response_class=HTMLResponse)
async def artworks_page(request: Request):
    return templates.TemplateResponse("artworks.html", {"request": request})

@app.get("/quiz-page", response_class=HTMLResponse)
async def quiz_page(request: Request):
    return templates.TemplateResponse("quiz.html", {"request": request})