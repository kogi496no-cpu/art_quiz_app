# 美術検定クイズ (Art Quiz App)

## 概要

西洋美術と日本美術、二つのジャンルに対応したアートクイズWebアプリケーションです。

作品を登録・管理し、それらのデータに基づいて動的にクイズを出題します。間違えた問題だけを復習する機能も備えており、効率的な学習をサポートします。

## 主な特徴

- **2つのクイズモード**:
    - **通常モード**: 全ての作品からランダムにクイズを出題します。
    - **復習モード**: これまでに間違えた問題だけを抽出し、集中的に学習できます。
- **動的な選択肢生成**: 正解の作品と文脈的に関連性の高いダミー選択肢を、TF-IDFとコサイン類似度を用いて動的に生成します。
- **CRUD操作**: 作品データの登録、閲覧、更新、削除が可能な管理画面を備えています。
- **画像処理**: 作品画像のアップロードに対応し、サーバーサイドでサムネイルを自動生成します。
- **統計機能**: クイズの総合正解率や、分野（作者、タイトルなど）ごとの成績を記録・表示します。
- **ジャンル別データベース**: 西洋美術と日本美術でデータベースを分離し、それぞれのジャンルに特化したクイズ体験を提供します。

## 技術スタック

- **バックエンド**: Python, FastAPI
- **データベース**: SQLite
- **フロントエンド**: HTML, CSS, JavaScript (Vanilla)
- **主なPythonライブラリ**: Pydantic, scikit-learn, NumPy, Pillow, Uvicorn, Jinja2

## APIエンドポイント

### 作品管理 (`/api/{genre}/artworks`)

| メソッド | パス | 説明 |
| :--- | :--- | :--- |
| `GET` | `/` | 作品データを一覧取得 (検索クエリ `q` に対応) |
| `POST` | `/upload` | 新しい作品を登録 (画像ファイル含む) |
| `PUT` | `/{artwork_id}` | 指定したIDの作品情報を更新 |
| `DELETE` | `/{artwork_id}` | 指定したIDの作品を削除 (関連画像も削除) |

### クイズ機能 (`/api/{genre}/quiz`)

| メソッド | パス | 説明 |
| :--- | :--- | :--- |
| `GET` | `/multiple-choice` | 新しい4択クイズを1問生成して返す |
| `GET` | `/review` | 復習用のクイズを1問生成して返す |
| `POST` | `/submit` | クイズの回答結果をサーバーに記録する |
| `GET` | `/stats` | 総合的な統計情報 (正解率など) を返す |
| `POST` | `/reset` | 指定したジャンルのクイズ統計をリセットする |

## セットアップと実行

1.  **リポジトリをクローンします。**
    ```bash
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name
    ```

2.  **Pythonの仮想環境を作成し、有効化します。（推奨）**
    ```bash
    python3 -m venv venv
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
├── main.py           # FastAPIアプリのエントリポイント、画面遷移のルーティング
├── artworks.py       # 【API】作品のCRUD操作に関するルーター
├── quiz.py           # 【API】クイズ関連APIのエンドポイントを定義するルーター
├── quiz_builder.py   # 【ロジック】クイズの問題と選択肢を生成するビジネスロジック
├── database.py       # データベース接続の管理
├── requirements.txt  # 依存ライブラリ
│
├── static/           # CSS, JavaScriptなどの静的ファイル
└── templates/        # HTMLテンプレート
```