
# Art Quiz App (西洋美術 & 日本美術)

西洋美術と日本美術、二つのジャンルに対応したアートクイズを提供するウェブアプリケーションです。
トップページから挑戦したいジャンルを選択し、クイズを楽しんだり、作品データを管理したりすることができます。

## 主な機能

- **ジャンル選択**: トップページで「西洋美術」「日本美術」のどちらかを選択。
- **クイズ機能**: 作品の画像や情報に関する4択クイズ。
- **作品管理**: 作品データの登録、一覧表示、検索、編集、削除。
- **画像アップロード**: 作品画像の登録に対応。
- **データ分離**: ジャンルごとにデータベースと画像フォルダを分離して管理。

## 技術スタック

- **Backend**: FastAPI (Python)
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript (Vanilla JS)
- **Image Processing**: Pillow

## プロジェクト構成

```
art_quiz_app/
│
├── main.py           # FastAPIアプリケーションのエントリーポイント
├── artworks.py       # 作品管理APIのルーター
├── quiz.py           # クイズAPIのルーター
├── database.py       # DB接続の管理
│
├── art.db            # 西洋美術のデータベース
├── japanese_art.db   # 日本美術のデータベース
│
├── static/           # 静的ファイル
│   ├── script.js     # フロントエンドのJavaScript
│   └── style.css     # スタイルシート
│
├── templates/        # HTMLテンプレート
│   ├── index.html    # トップページ（ジャンル選択）
│   ├── artworks.html # 作品管理ページ
│   └── quiz.html     # クイズページ
│
└── uploads/          # アップロードされた画像
    ├── images/       # 西洋美術のオリジナル画像
    ├── thumbnails/   # 西洋美術のサムネイル
    ├── japanese_images/      # 日本美術のオリジナル画像
    └── japanese_thumbnails/  # 日本美術のサムネイル
```

## セットアップと実行

1.  **必要なライブラリをインストールします。**
    ```bash
    pip install -r requirements.txt
    ```

2.  **FastAPIアプリケーションを起動します。**
    ```bash
    uvicorn main:app --reload
    ```

3.  **ブラウザでアクセスします。**
    [http://localhost:8000](http://localhost:8000)

## 使い方

1.  **トップページ**にアクセスすると、ジャンル選択画面が表示されます。
2.  「クイズに挑戦」ボタンをクリックすると、各ジャンルの**クイズページ** (`/quiz/{genre}`) に移動します。
3.  「作品を管理」ボタンをクリックすると、各ジャンルの**作品管理ページ** (`/artworks/{genre}`) に移動し、作品の登録や編集ができます。

## APIエンドポイント

APIはジャンル指定のプレフィックス (`/api/{genre}`) を持ちます。
`{genre}` には `western` または `japanese` が入ります。

### 作品関連 (Artworks)
- `GET /api/{genre}/artworks`: 作品一覧の取得
- `POST /api/{genre}/artworks/upload`: 新規作品の登録
- `PUT /api/{genre}/artworks/{artwork_id}`: 作品情報の更新
- `DELETE /api/{genre}/artworks/{artwork_id}`: 作品の削除

### クイズ関連 (Quiz)
- `GET /api/{genre}/quiz/multiple-choice`: 4択クイズの取得
- `POST /api/{genre}/quiz/submit`: クイズ結果の送信
- `GET /api/{genre}/quiz/stats`: 統計情報の取得
- `POST /api/{genre}/quiz/reset`: 統計情報のリセット

## データベース構造

`art.db` と `japanese_art.db` は同じテーブル構造を持っています。

### `artworks` テーブル
```sql
CREATE TABLE "artworks" (
    "id" INTEGER,
    "author" TEXT,
    "title" TEXT,
    "style" TEXT,
    "image_url" TEXT,
    "image_filename" TEXT,
    "image_size" INTEGER,
    "image_type" TEXT,
    "notes" TEXT,
    PRIMARY KEY ("id")
)
```

### `quiz_results` テーブル
```sql
CREATE TABLE "quiz_results" (
    "id" INTEGER,
    "question_field" TEXT,
    "correct_answer" TEXT,
    "user_answer" TEXT,
    "is_correct" BOOLEAN,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id" AUTOINCREMENT)
)
```
