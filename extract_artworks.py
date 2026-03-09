
import sqlite3
import pandas as pd
import os

def extract_data_to_csv(db_path, genre, output_dir):
    """データベースからアートワークデータを抽出し、CSVファイルに保存する"""
    if not os.path.exists(db_path):
        print(f"エラー: データベースファイルが見つかりません: {db_path}")
        return

    print(f"{db_path} からデータを抽出中...")
    try:
        conn = sqlite3.connect(db_path)
        # pandasのread_sql_queryを使ってテーブル全体をDataFrameに読み込む
        df = pd.read_sql_query("SELECT * FROM artworks", conn)
        conn.close()

        # ジャンル列を追加
        df['genre'] = genre

        # 出力ファイルパスを構築
        output_filename = f"{genre}_artworks.csv"
        output_path = os.path.join(output_dir, output_filename)

        # CSVとして保存
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"データを {output_path} に保存しました。")
        print(f"合計 {len(df)} 件のレコードを抽出しました。")

    except Exception as e:
        print(f"{db_path} の処理中にエラーが発生しました: {e}")

if __name__ == "__main__":
    # このスクリプトが置かれているディレクトリを基準にする
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # データベースのパス
    western_db = os.path.join(base_dir, "art.db")
    japanese_db = os.path.join(base_dir, "japanese_art.db")

    # データを抽出
    extract_data_to_csv(western_db, "western", base_dir)
    extract_data_to_csv(japanese_db, "japanese", base_dir)

    print("\n処理が完了しました。")
