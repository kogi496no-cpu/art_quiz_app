from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import random
import sqlite3
from pydantic import BaseModel
from typing import List

from database import get_db_connection
from quiz_builder import build_quiz_data

quiz_router = APIRouter()
stats_router = APIRouter()
templates = Jinja2Templates(directory="templates")

class QuizResult(BaseModel):
    artwork_id: int
    question_field: str
    correct_answer: str
    user_answer: str
    is_correct: bool


@quiz_router.post("/quiz/submit")
def submit_quiz_result(
    result: QuizResult,
    conn: sqlite3.Connection = Depends(get_db_connection)
):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO quiz_results (artwork_id, question_field, correct_answer, user_answer, is_correct) 
            VALUES (?, ?, ?, ?, ?)
        """, (result.artwork_id, result.question_field, result.correct_answer, result.user_answer, result.is_correct))
        conn.commit()
        return {"message": "結果を記録しました"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"結果の記録に失敗しました: {e}")

@stats_router.get("/quiz/stats/{genre}")
def get_quiz_stats(genre: str, conn: sqlite3.Connection = Depends(get_db_connection)):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM quiz_results")
        total_attempts = cursor.fetchone()['COUNT(*)']
        cursor.execute("SELECT COUNT(*) FROM quiz_results WHERE is_correct = 1")
        correct_attempts = cursor.fetchone()['COUNT(*)']
        cursor.execute("""
            SELECT question_field, COUNT(*) as total, SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct
            FROM quiz_results 
            GROUP BY question_field
        """)
        field_stats_rows = cursor.fetchall()
        field_stats = [
            {
                "field": row["question_field"],
                "total": row["total"],
                "correct": row["correct"],
                "accuracy": round((row["correct"] / row["total"] * 100), 1) if row["total"] > 0 else 0
            }
            for row in field_stats_rows
        ]

        cursor.execute("""
            SELECT question_field, correct_answer, user_answer, is_correct, created_at
            FROM quiz_results 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        recent_results_rows = cursor.fetchall()
        recent_results = [dict(row) for row in recent_results_rows]

        overall_accuracy = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0
        return {
            "total_attempts": total_attempts,
            "correct_attempts": correct_attempts,
            "overall_accuracy": round(overall_accuracy, 1),
            "field_stats": field_stats,
            "recent_results": recent_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"統計情報の取得に失敗しました: {e}")


@stats_router.get("/quiz/stats_view/{genre}", response_class=HTMLResponse)
async def get_quiz_stats_view(request: Request, genre: str):
    return templates.TemplateResponse("quiz_stats.html", {"request": request, "genre": genre})


@quiz_router.get("/quiz/multiple-choice")
def get_multiple_choice_quiz(genre: str, request: Request, conn: sqlite3.Connection = Depends(get_db_connection)):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM artworks")
    total_artwork_count = cursor.fetchone()['COUNT(*)']
    if total_artwork_count < 4:
        raise HTTPException(status_code=404, detail="4択クイズには最低4件のデータが必要です")

    HISTORY_LENGTH = 5
    quiz_history = request.session.get("quiz_history", [])
    artwork_ids_to_exclude = tuple(quiz_history)
    
    exclude_sql = ""
    if artwork_ids_to_exclude:
        exclude_sql = f" AND id NOT IN {artwork_ids_to_exclude}"
        if len(artwork_ids_to_exclude) == 1:
            exclude_sql = f" AND id != {artwork_ids_to_exclude[0]}"

    cursor.execute("SELECT COUNT(*) FROM artworks WHERE 1=1" + exclude_sql)
    remaining_artwork_count = cursor.fetchone()['COUNT(*)']

    if remaining_artwork_count == 0 and artwork_ids_to_exclude:
        quiz_history = []
        request.session["quiz_history"] = []
        exclude_sql = ""

    query = f"SELECT * FROM artworks WHERE 1=1{exclude_sql} ORDER BY RANDOM() LIMIT 1"
    cursor.execute(query)
    correct_row_tuple = cursor.fetchone()

    if not correct_row_tuple:
        # 履歴をクリアして再試行
        request.session["quiz_history"] = []
        query = f"SELECT * FROM artworks ORDER BY RANDOM() LIMIT 1"
        cursor.execute(query)
        correct_row_tuple = cursor.fetchone()
        if not correct_row_tuple:
            raise HTTPException(status_code=404, detail="適切なクイズデータが見つかりません。")

    correct_row = dict(correct_row_tuple)
    
    quiz_history.append(correct_row['id'])
    if len(quiz_history) > HISTORY_LENGTH:
        quiz_history.pop(0)
    request.session["quiz_history"] = quiz_history

    cursor.execute("SELECT COUNT(*) FROM artworks WHERE image_filename IS NOT NULL AND image_filename != ''")
    image_artwork_count = cursor.fetchone()['COUNT(*)']

    possible_fields = ["author", "title", "style"]
    if image_artwork_count >= 4:
        possible_fields.append("image")
    question_field = random.choice(possible_fields)

    return build_quiz_data(correct_row, conn, genre, question_field)

@quiz_router.post("/quiz/reset")
def reset_quiz_results(genre: str, conn: sqlite3.Connection = Depends(get_db_connection)):
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM quiz_results")
        conn.commit()
        return {"message": "クイズ結果をリセットしました"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"リセットに失敗しました")

@quiz_router.get("/quiz/recent-results")
def get_recent_results(genre: str, conn: sqlite3.Connection = Depends(get_db_connection)):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT question_field, correct_answer, user_answer, is_correct, created_at
            FROM quiz_results
            ORDER BY created_at DESC
            LIMIT 10
        """)
        results = cursor.fetchall()
        return [dict(row) for row in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"最近の結果の取得に失敗しました: {e}")


@quiz_router.get("/quiz/review")
def get_review_quiz(genre: str, request: Request, conn: sqlite3.Connection = Depends(get_db_connection)):
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT artwork_id FROM quiz_results WHERE is_correct = 0")
    incorrect_artwork_ids = [row['artwork_id'] for row in cursor.fetchall()]

    if not incorrect_artwork_ids:
        raise HTTPException(status_code=404, detail="復習する問題がありません。")

    artwork_id_to_review = random.choice(incorrect_artwork_ids)

    cursor.execute("SELECT * FROM artworks WHERE id = ?", (artwork_id_to_review,))
    correct_row_tuple = cursor.fetchone()

    if not correct_row_tuple:
        raise HTTPException(status_code=404, detail="クイズ対象の作品データが見つかりません。")

    correct_row = dict(correct_row_tuple)

    possible_fields = ["author", "title", "style"]
    if correct_row.get("image_filename"):
        possible_fields.append("image")
    question_field = random.choice(possible_fields)

    return build_quiz_data(correct_row, conn, genre, question_field)