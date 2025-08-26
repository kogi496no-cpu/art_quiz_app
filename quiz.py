from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import random
import sqlite3
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

router = APIRouter()

# DB接続（main.pyと同じDBを利用）
conn = sqlite3.connect("art.db", check_same_thread=False)
c = conn.cursor()

templates = Jinja2Templates(directory="templates")

def get_similar_choices(all_artworks, correct_artwork, field, num_choices=3):
    """
    コサイン類似度に基づいて、類似した選択肢を取得する
    """
    # 'notes'フィールドをコーパスとして使用
    corpus = [artwork.get('notes', '') or '' for artwork in all_artworks]
    
    # TF-IDFベクトル化
    try:
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(corpus)
    except ValueError:
        # コーパスが空、またはすべてストップワードの場合
        return []

    # 正解の作品のインデックスを探す
    correct_index = -1
    for i, artwork in enumerate(all_artworks):
        if artwork['id'] == correct_artwork['id']:
            correct_index = i
            break
    
    if correct_index == -1:
        return []

    # コサイン類似度を計算
    cosine_sim = cosine_similarity(tfidf_matrix[correct_index], tfidf_matrix).flatten()
    
    # 類似度が高い順にインデックスをソート（自分自身は除く）
    # argsort()は昇順でインデックスを返すので、[::-1]で降順にする
    similar_indices = cosine_sim.argsort()[::-1]
    
    # 選択肢を収集
    choices = []
    correct_answer_value = correct_artwork[field]
    
    for idx in similar_indices:
        # 自分自身と、すでに選択肢にある値、正解と同じ値は除外
        if idx != correct_index:
            artwork = all_artworks[idx]
            choice_value = artwork[field]
            if choice_value and choice_value != correct_answer_value and choice_value not in choices:
                choices.append(choice_value)
        
        if len(choices) >= num_choices:
            break
            
    return choices

@router.post("/quiz/submit")
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

@router.get("/quiz/stats")
def get_quiz_stats():
    try:
        c.execute("SELECT COUNT(*) FROM quiz_results")
        total_attempts = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM quiz_results WHERE is_correct = 1")
        correct_attempts = c.fetchone()[0]
        c.execute("""
            SELECT question_field, COUNT(*) as total, SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct
            FROM quiz_results 
            GROUP BY question_field
        """)
        field_stats = c.fetchall()
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

@router.get("/quiz")
def get_quiz():
    c.execute("SELECT * FROM artworks ORDER BY RANDOM() LIMIT 1")
    row = c.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="データがありません")
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

@router.get("/quiz/multiple-choice")
def get_multiple_choice_quiz():
    c.execute("SELECT COUNT(*) FROM artworks WHERE image_filename IS NOT NULL")
    image_artwork_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM artworks")
    total_artwork_count = c.fetchone()[0]

    if total_artwork_count < 4:
        raise HTTPException(status_code=404, detail="4択クイズには最低4件のデータが必要です")

    possible_fields = ["author", "title", "style"]
    if image_artwork_count >= 4:
        possible_fields.append("image")
    
    question_field = random.choice(possible_fields)

    # 正解の作品を選ぶ
    if question_field == "image":
        c.execute("SELECT * FROM artworks WHERE image_filename IS NOT NULL ORDER BY RANDOM() LIMIT 1")
    else:
        c.execute("SELECT * FROM artworks ORDER BY RANDOM() LIMIT 1")
    
    correct_row_tuple = c.fetchone()
    if not correct_row_tuple:
        raise HTTPException(status_code=404, detail="適切なクイズデータが見つかりません。")

    columns = [d[0] for d in c.description]
    correct_row = dict(zip(columns, correct_row_tuple))

    quiz_artwork_data = correct_row.copy()
    choices = []
    correct_answer = None
    question_text = ""

    if question_field == "image":
        correct_answer = correct_row["image_filename"]
        c.execute("""
            SELECT image_filename FROM artworks 
            WHERE image_filename IS NOT NULL AND id != ? 
            ORDER BY RANDOM() LIMIT 3
        """, (correct_row["id"],))
        dummy_answers = [row[0] for row in c.fetchall()]
        
        if len(dummy_answers) < 3:
            raise HTTPException(status_code=500, detail="画像クイズの選択肢作成に失敗しました。画像付きの作品が4つ以上必要です。")

        choices = [correct_answer] + dummy_answers
        random.shuffle(choices)
        
        quiz_artwork_data["image_filename"] = "???"
        quiz_artwork_data["image_url"] = None
        question_text = "この作品の画像はどれ？"

    else: # author, title, style の場合
        correct_answer = correct_row[question_field]
        
        # --- コサイン類似度で選択肢を取得 ---
        c.execute("SELECT * FROM artworks")
        all_artworks_tuples = c.fetchall()
        all_artworks = [dict(zip(columns, row)) for row in all_artworks_tuples]
        
        dummy_answers = get_similar_choices(all_artworks, correct_row, question_field)

        # --- 類似選択肢が足りない場合のフォールバック ---
        if len(dummy_answers) < 3:
            # 既存のランダム選択ロジックをフォールバックとして使用
            fallback_query = f"""
            SELECT DISTINCT {question_field} FROM artworks 
            WHERE {question_field} != ? AND {question_field} IS NOT NULL AND {question_field} != ''
            ORDER BY RANDOM()
            """
            c.execute(fallback_query, (correct_answer,))
            
            fallback_candidates = [row[0] for row in c.fetchall()]
            for candidate in fallback_candidates:
                if candidate not in dummy_answers:
                    dummy_answers.append(candidate)
                if len(dummy_answers) >= 3:
                    break

        # --- それでも足りない場合の最終フォールバック ---
        if len(dummy_answers) < 3:
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
        
        # 最終手段
        i = 1
        while len(dummy_answers) < 3:
            dummy_answers.append(f"ダミー選択肢{i}")
            i += 1

        choices = [correct_answer] + dummy_answers[:3] # 必ず3つのダミー選択肢に
        random.shuffle(choices)
        
        quiz_artwork_data[question_field] = "???"
        field_names = {"author": "作者", "title": "作品名", "style": "美術様式"}
        question_text = f"この作品の{field_names[question_field]}は？"

    return {
        "artwork": quiz_artwork_data,
        "full_artwork_data": correct_row,
        "question": question_text,
        "question_field": question_field,
        "choices": choices,
        "correct_answer": correct_answer
    }

@router.post("/quiz/reset")
def reset_quiz_results():
    try:
        c.execute("DELETE FROM quiz_results")
        conn.commit()
        return {"message": "クイズ結果をリセットしました"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail="リセットに失敗しました")

@router.get("/quiz-page", response_class=HTMLResponse)
async def quiz_page(request: Request):
    return templates.TemplateResponse("quiz.html", {"request": request})
