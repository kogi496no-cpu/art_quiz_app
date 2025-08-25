# Art Quiz App

美術作品に関するクイズを提供するウェブアプリケーションです。トップページでクイズに挑戦でき、作品の登録・管理も可能です。

## 機能

### 作品管理機能
- 作品の登録（画像アップロード対応）
- 登録済み作品の一覧表示、検索
- 作品情報の編集
- 作品の削除

### クイズ機能
- 穴埋めクイズ（作者名、作品名、様式、画像から1つを隠して出題）
- 4択クイズ（作者名、作品名、様式、画像から選択式で出題）
- クイズ結果の記録
- 統計情報の表示（正答率、分野別成績など）

## ページ構成

- **トップページ (`/`)**: メインのクイズページです。
- **作品登録ページ (`/register`)**: 新しい美術作品をデータベースに登録します。
- **作品管理ページ (`/artworks`)**: 登録済みの作品を一覧で確認、編集、削除できます。

## 技術スタック

- Backend: FastAPI (Python)
- Database: SQLite3
- Frontend: HTML, JavaScript, CSS
- 画像処理: Pillow (Python Imaging Library)

## プロジェクト構成

```
art_quiz_app/
│
├── main.py           # アプリケーションのエントリーポイント
├── artworks.py       # 作品関連の機能を管理
├── quiz.py          # クイズ関連の機能を管理
├── art.db           # SQLiteデータベース
│
├── static/          # 静的ファイル
│   ├── script.js    # フロントエンドのJavaScript
│   └── style.css    # スタイルシート
│
├── templates/       # HTMLテンプレート
│   ├── artworks.html  # 作品管理ページ
│   ├── index.html    # 作品登録ページ
│   └── quiz.html     # トップページ（クイズページ）
│
└── uploads/         # アップロードされたファイル
    ├── images/      # オリジナル画像
    └── thumbnails/  # サムネイル画像
```

## セットアップ

1. 必要なパッケージのインストール:
```bash
pip install -r requirements.txt
```

2. アプリケーションの起動:
```bash
python -m uvicorn main:app --reload
```

3. ブラウザでアクセス:
```
http://localhost:8000
```

## API エンドポイント

### 作品関連 (API)
- GET `/api/artworks` - 作品一覧の取得
- POST `/api/artworks/upload` - 新規作品の登録
- PUT `/api/artworks/{artwork_id}` - 作品情報の更新
- DELETE `/api/artworks/{artwork_id}` - 作品の削除

### クイズ関連 (API)
- GET `/quiz` - 穴埋めクイズの取得
- GET `/quiz/multiple-choice` - 4択クイズの取得
- POST `/quiz/submit` - クイズ結果の送信
- GET `/quiz/stats` - 統計情報の取得
- POST `/quiz/reset` - 統計情報のリセット

## データベース構造

### artworks テーブル
```sql
CREATE TABLE artworks (
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
```

### quiz_results テーブル
```sql
CREATE TABLE quiz_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_field TEXT,
    correct_answer TEXT,
    user_answer TEXT,
    is_correct BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

## 開発ガイドライン

### 新機能の追加
1. 作品関連の機能は `artworks.py` に追加
2. クイズ関連の機能は `quiz.py` に追加
3. 共通設定は `main.py` で管理

### コード規約
- PEP 8スタイルガイドに従う
- 各機能は適切なモジュールに分割
- エラーハンドリングを適切に実装

## ライセンス

This project is licensed under the MIT License - see the LICENSE file for details