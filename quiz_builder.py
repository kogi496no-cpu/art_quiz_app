import random
import sqlite3
from typing import List, Dict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from fastapi import HTTPException

def get_similar_choices(all_artworks: List[dict], correct_artwork: dict, field: str, num_choices=3) -> List[str]:
    """指定されたフィールドについて、似ている選択肢を返す"""
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
    correct_answer_value = correct_artwork[field].strip()
    added_choices_stripped = {correct_answer_value}

    for idx in similar_indices:
        if idx != correct_index:
            artwork = all_artworks[idx]
            choice_value = artwork.get(field)

            if not choice_value:
                continue

            choice_value_stripped = choice_value.strip()
            
            if choice_value_stripped and choice_value_stripped not in added_choices_stripped:
                choices.append(choice_value)
                added_choices_stripped.add(choice_value_stripped)

        if len(choices) >= num_choices:
            break
            
    return choices

def build_quiz_data(correct_row: Dict, conn: sqlite3.Connection, genre: str, question_field: str) -> Dict:
    """1件の作品データからクイズ一式を生成する"""
    cursor = conn.cursor()
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

    else: # author, title, style
        correct_answer = correct_row[question_field]
        
        cursor.execute("SELECT * FROM artworks")
        all_artworks = [dict(row) for row in cursor.fetchall()]
        
        dummy_answers = get_similar_choices(all_artworks, correct_row, question_field)

        added_choices_stripped = {correct_answer.strip()}
        for ans in dummy_answers:
            added_choices_stripped.add(ans.strip())

        if len(dummy_answers) < 3:
            cursor.execute(f"""
                SELECT DISTINCT {question_field} FROM artworks 
                WHERE {question_field} IS NOT NULL AND {question_field} != ''
                ORDER BY RANDOM()
            """, ())
            
            fallback_candidates = [row[question_field] for row in cursor.fetchall()]
            for candidate in fallback_candidates:
                if len(dummy_answers) >= 3:
                    break
                candidate_stripped = candidate.strip()
                if candidate_stripped and candidate_stripped not in added_choices_stripped:
                    dummy_answers.append(candidate)
                    added_choices_stripped.add(candidate_stripped)

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
            all_fallbacks = [opt for opt in fallback_options[genre][question_field] if opt.strip() not in added_choices_stripped]
            while len(dummy_answers) < 3 and all_fallbacks:
                chosen = random.choice(all_fallbacks)
                dummy_answers.append(chosen)
                all_fallbacks.remove(chosen)
                added_choices_stripped.add(chosen.strip())
        
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