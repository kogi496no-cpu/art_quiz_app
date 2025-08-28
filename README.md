# 美術検定クイズアプリ

西洋美術と日本美術、二つのジャンルに対応したアートクイズを提供するウェブアプリケーションです。
挑戦したいジャンルを選ぶと、それぞれの世界観に合わせた最適なUIでクイズを楽しめます。

## ✨ 特徴

- **2つの美術ジャンル**: 西洋美術と日本美術、それぞれの奥深い世界を探求できます。
- **テーマ別UI**: アプリの体験を豊かにするため、3つの異なるデザインテーマを実装しています。
    - **トップページ**: これから始まるアート体験への期待感を高める、モダンで洗練されたデザイン。
    - **西洋美術モード**: クラシックなネイビーと金色を基調とし、格調高いセリフ体フォントを使用した、西洋の美術館を彷彿とさせるデザイン。
    - **日本美術モード**: 蘇芳色(赤)と金色を基調とし、流麗な明朝体フォントを使用した、豪華で趣のある和風デザイン。
- **インタラクティブなクイズ**: 作品の画像や情報に関する4択クイズが出題され、正解率などの統計も確認できます。
- **作品管理機能**: クイズの元となる作品データを、簡単な操作で登録、一覧表示、編集、削除できます。

## 🛠️ 使用技術

- **バックエンド**: FastAPI (Python)
- **フロントエンド**: HTML, CSS, JavaScript
- **データベース**: SQLite
- **フォント**: Google Fonts (Playfair Display, Lora, Shippori Mincho)
- **画像処理**: Pillow

## 🚀 セットアップと実行方法

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

5.  **ブラウザでアクセスします。**
    [http://127.0.0.1:8000](http://127.0.0.1:8000)

## 📂 ディレクトリ構成

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
│   ├── western.css   # 西洋美術モードのスタイル
│   ├── japanese.css  # 日本美術モードのスタイル
│   └── style.css     # トップページのスタイル
│
├── templates/        # HTMLテンプレート
│   ├── index.html    # トップページ（ジャンル選択）
│   ├── artworks.html # 作品管理ページ
│   └── quiz.html     # クイズページ
│
└── uploads/          # アップロードされた画像
```