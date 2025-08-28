from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import random
import sqlite3
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from pydantic import BaseModel
from typing import List

from database import get_db_connection

router = APIRouter()
templates = Jinja2Templates(directory="templates")

class QuizResult(BaseModel):
    question_field: str
    correct_answer: str
    user_answer: str
    is_correct: bool

def get_similar_choices(all_artworks: List[dict], correct_artwork: dict, field: str, num_choices=3) -> List[str]:
    corpus = [f"{artwork.get('author', '')} {artwork.get('title', '')} {artwork.get('style', '')}" for artwork in all_artworks]
    try:
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(corpus)
    except ValueError:
        return []

    correct_index = next((i for i, art in enumerate(all_artworks) if art['id'] == correct_artwork['id']), -1)
    if correct_index == -1:
        return []

    cosine_sim = cosine_similarity(tfidf_matrix[correct_index], tfidf_matrix).flatten()
    similar_indices = cosine_sim.argsort()[::-1]
    
    choices = []
    correct_answer_value = correct_artwork[field]
    
    for idx in similar_indices:
        if idx != correct_index:
            artwork = all_artworks[idx]
            choice_value = artwork[field]
            if choice_value and choice_value != correct_answer_value and choice_value not in choices:
                choices.append(choice_value)
        if len(choices) >= num_choices:
            break
            
    return choices

@router.post("/quiz/submit")
def submit_quiz_result(
    result: QuizResult,
    conn: sqlite3.Connection = Depends(get_db_connection)
):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO quiz_results (question_field, correct_answer, user_answer, is_correct) 
            VALUES (?, ?, ?, ?)
        """, (result.question_field, result.correct_answer, result.user_answer, result.is_correct))
        conn.commit()
        return {"message": "結果を記録しました"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"結果の記録に失敗しました: {e}")

@router.get("/quiz/stats")
def get_quiz_stats(conn: sqlite3.Connection = Depends(get_db_connection)):
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

@router.get("/quiz/multiple-choice")
def get_multiple_choice_quiz(genre: str, conn: sqlite3.Connection = Depends(get_db_connection)):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM artworks WHERE image_filename IS NOT NULL AND image_filename != ''")
    image_artwork_count = cursor.fetchone()['COUNT(*)']
    
    cursor.execute("SELECT COUNT(*) FROM artworks")
    total_artwork_count = cursor.fetchone()['COUNT(*)']

    if total_artwork_count < 4:
        raise HTTPException(status_code=404, detail="4択クイズには最低4件のデータが必要です")

    possible_fields = ["author", "title", "style"]
    if image_artwork_count >= 4:
        possible_fields.append("image")
    
    if not possible_fields:
        raise HTTPException(status_code=404, detail="クイズを作成できるフィールドがありません。")
        
    question_field = random.choice(possible_fields)

    if question_field == "image":
        cursor.execute("SELECT * FROM artworks WHERE image_filename IS NOT NULL AND image_filename != '' ORDER BY RANDOM() LIMIT 1")
    else:
        cursor.execute("SELECT * FROM artworks ORDER BY RANDOM() LIMIT 1")
    
    correct_row_tuple = cursor.fetchone()
    if not correct_row_tuple:
        raise HTTPException(status_code=404, detail="適切なクイズデータが見つかりません。")

    correct_row = dict(correct_row_tuple)
    quiz_artwork_data = correct_row.copy()
    choices = []
    correct_answer = ""
    question_text = ""

    if question_field == "image":
        correct_answer = correct_row["image_filename"]
        cursor.execute("""
            SELECT image_filename FROM artworks 
            WHERE image_filename IS NOT NULL AND image_filename != '' AND id != ? 
            ORDER BY RANDOM() LIMIT 3
        """, (correct_row["id"],))
        dummy_answers = [row['image_filename'] for row in cursor.fetchall()]
        
        if len(dummy_answers) < 3:
            raise HTTPException(status_code=500, detail="画像クイズの選択肢作成に失敗しました。画像付きの作品が4つ以上必要です。")

        choices = [correct_answer] + dummy_answers
        random.shuffle(choices)
        
        quiz_artwork_data["image_filename"] = "???"
        question_text = "この作品の画像はどれ？"

    else:
        correct_answer = correct_row[question_field]
        
        cursor.execute("SELECT * FROM artworks")
        all_artworks = [dict(row) for row in cursor.fetchall()]
        
        dummy_answers = get_similar_choices(all_artworks, correct_row, question_field)

        if len(dummy_answers) < 3:
            cursor.execute(f"""
                SELECT DISTINCT {question_field} FROM artworks 
                WHERE {question_field} != ? AND {question_field} IS NOT NULL AND {question_field} != ''
                ORDER BY RANDOM()
            """, (correct_answer,))
            
            fallback_candidates = [row[question_field] for row in cursor.fetchall()]
            for candidate in fallback_candidates:
                if candidate not in dummy_answers:
                    dummy_answers.append(candidate)
                if len(dummy_answers) >= 3:
                    break

        if len(dummy_answers) < 3:
            fallback_options = {
                "western": {
                    "author": ["レオナルド・ダ・ヴィンチ", "ミケランジェロ", "ラファエロ", "ピカソ", "モネ", "ゴッホ"],
                    "title": ["モナリザ", "最後の晩餐", "星月夜", "ひまわり", "叫び", "真珠の耳飾りの少女"],
                    "style": ["ルネサンス", "バロック", "印象派", "キュビスム", "シュルレアリスム", "抽象表現主義"]
                },
                "japanese": {
                    "author": ["葛飾北斎", "歌川広重", "伊藤若冲", "雪舟", "千利休", "横山大観"],
                    "title": ["冨嶽三十六景 神奈川沖浪裏", "東海道五十三次", "鳥獣人物戯画", "雪松図屏風", "風神雷神図屏風", "無我"],
                    "style": ["浮世絵", "琳派", "狩野派", "水墨画", "大和絵", "日本画"]
                }
            }
            all_fallbacks = [opt for opt in fallback_options[genre][question_field] if opt != correct_answer and opt not in dummy_answers]
            while len(dummy_answers) < 3 and all_fallbacks:
                chosen = random.choice(all_fallbacks)
                dummy_answers.append(chosen)
                all_fallbacks.remove(chosen)
        
        i = 1
        while len(dummy_answers) < 3:
            dummy_answers.append(f"ダミー選択肢{i}")
            i += 1

        choices = [correct_answer] + dummy_answers[:3]
        random.shuffle(choices)
        
        quiz_artwork_data[question_field] = "???"
        field_names = {"author": "作者", "title": "作品名", "style": "美術様式"}
        question_text = f"この作品の{field_names.get(question_field, '情報')}は？"

    return {
        "artwork": quiz_artwork_data,
        "full_artwork_data": correct_row,
        "question": question_text,
        "question_field": question_field,
        "choices": choices,
        "correct_answer": correct_answer
    }

@router.post("/quiz/reset")
def reset_quiz_results(conn: sqlite3.Connection = Depends(get_db_connection)):
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM quiz_results")
        conn.commit()
        return {"message": "クイズ結果をリセットしました"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"リセットに失敗しました")

@router.get("/quiz/recent-results")
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