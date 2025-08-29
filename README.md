# 美術検定クイズAPI (Art Quiz API)

## 概要

西洋美術と日本美術、二つのジャンルに対応したアートクイズ機能を提供するFastAPIアプリケーションです。

作品データの管理機能と、関連性の高い選択肢を動的に生成するクイズAPIを備えています。

## 主な特徴

- **RESTful API**: FastAPIを利用した、作品データとクイズ機能のためのRESTful API。
- **動的なクイズ生成**: TF-IDFとコサイン類似度 (`scikit-learn`を利用) を使用し、正解の作品と文脈的に関連性の高いダミー選択肢を動的に生成します。
- **作品管理 (CRUD)**: 作品データの登録、取得、更新、削除機能。
- **画像処理**: 作品画像のアップロードに対応し、サーバーサイドでサムネイルを自動生成 (`Pillow`を利用)。
- **統計機能**: クイズの正解率や分野別の成績など、詳細な統計情報をトラッキング・提供します。
- **ジャンル別データ**: パスパラメータ (`/api/{genre}/...`) により、西洋美術 (`western`) と日本美術 (`japanese`) のデータ空間を明確に分離。

## 技術スタック

- **バックエンド**: Python, FastAPI
- **データ操作**: Pydantic
- **データベース**: SQLite (標準ライブラリ)
- **機械学習 / 計算**: scikit-learn, NumPy
- **画像処理**: Pillow
- **その他**: Uvicorn (ASGIサーバー), python-multipart (フォームデータ処理), Jinja2 (テンプレートエンジン)

## APIエンドポイント

### 作品管理 (`/api/{genre}/artworks`)

| メソッド | パス                  | 説明                                       |
| :------- | :-------------------- | :----------------------------------------- |
| `GET`    | `/`                   | 作品データを一覧取得 (検索クエリ `q` に対応) |
| `POST`   | `/upload`             | 新しい作品を登録 (画像ファイル含む)        |
| `PUT`    | `/{artwork_id}`       | 指定したIDの作品情報を更新                 |
| `DELETE` | `/{artwork_id}`       | 指定したIDの作品を削除 (関連画像も削除)    |

### クイズ機能 (`/api/{genre}/quiz`)

| メソッド | パス                  | 説明                                     |
| :------- | :-------------------- | :--------------------------------------- |
| `GET`    | `/multiple-choice`    | 新しい4択クイズを1問生成して返す         |
| `POST`   | `/submit`             | クイズの回答結果をサーバーに記録する     |
| `GET`    | `/stats`              | 総合的な統計情報 (正解率など) を返す     |
| `POST`   | `/reset`              | 指定したジャンルのクイズ統計をリセットする |
| `GET`    | `/recent-results`     | 最近のクイズ結果10件を返す               |

## セットアップと実行

1.  **リポジトリをクローンします。**
    ```bash
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name
    ```

2.  **Pythonの仮想環境を作成し、有効化します。（推奨）**
    ```bash
    python -m venv venv
    source venv/bin/activate  # macOS/Linux
    # venv\Scripts\activate    # Windows
    ```

3.  **必要なライブラリをインストールします。**
    ```bash
    pip install -r requirements.txt
    ```

4.  **FastAPIアプリケーションを起動します。**
    ```bash
    uvicorn main:app --reload
    ```
    サーバーが `http://127.0.0.1:8000` で起動します。

## プロジェクト構成

```
/
│
├── main.py           # FastAPIアプリケーションのエントリーポイント
├── artworks.py       # 作品管理APIのルーター
├── quiz.py           # クイズAPIのルーター
├── database.py       # DB接続の管理
├── requirements.txt  # 依存ライブラリ
│
├── static/           # CSS, JavaScriptなどの静的ファイル
│   ├── western.css
│   ├── japanese.css
│   └── ...
│
├── templates/        # HTMLテンプレート
│   ├── index.html
│   ├── artworks.html
│   └── quiz.html
│
└── uploads/          # アップロードされた画像
    ├── images/
    └── thumbnails/
```
