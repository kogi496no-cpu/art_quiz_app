
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from gtda.homology import VietorisRipsPersistence
from gtda.plotting import plot_diagram
import matplotlib.pyplot as plt
import os

def analyze_artworks_tda(csv_files, output_dir):
    """CSVからアートワークデータを読み込み、TDA分析を実行してパーシステンス図を保存する"""
    
    print("TDA分析を開始します...")

    # 複数のCSVファイルを読み込んで結合
    try:
        dfs = [pd.read_csv(file) for file in csv_files if os.path.exists(file)]
        if not dfs:
            print("エラー: 対象のCSVファイルが見つかりません。")
            return
        df = pd.concat(dfs, ignore_index=True)
        print(f"合計 {len(df)} 件のデータを読み込みました。")
    except Exception as e:
        print(f"CSVファイルの読み込み中にエラーが発生しました: {e}")
        return

    # 'style' 列が存在するか確認
    if 'style' not in df.columns:
        print("エラー: 'style' 列がデータフレームに存在しません。")
        return

    # 'style' 列の欠損値を除外
    df = df.dropna(subset=['style'])
    if df.empty:
        print("エラー: 'style' 列に有効なデータがありません。")
        return

    # カテゴリデータを数値に変換
    print("'style' 列を数値データに変換しています...")
    label_encoder = LabelEncoder()
    # fit_transformは1次元配列を期待するため、df['style']を渡す
    style_encoded = label_encoder.fit_transform(df['style'])

    # TDAが扱えるように、(n_samples, n_features)の形式に変形
    # 今回はstyleという1つの特徴量のみなので、(n_samples, 1)とする
    data_for_tda = style_encoded.reshape(-1, 1)
    print(f"データ形式を {data_for_tda.shape} に変換しました。")

    # パーシステントホモロジーの計算
    print("パーシステントホモロジーを計算中... (Vietoris-Rips complex)")
    # homology_dimensions=[0, 1] は、連結成分(0次元)とループ(1次元)を計算対象とすることを意味する
    vr_persistence = VietorisRipsPersistence(homology_dimensions=[0, 1])
    diagrams = vr_persistence.fit_transform([data_for_tda]) # fit_transformはデータ点のリストを期待する

    # パーシステンス図のプロットと保存
    print("パーシステンス図を生成しています...")
    try:
        fig = plot_diagram(diagrams[0])
        output_path = os.path.join(output_dir, "persistence_diagram.png")
        fig.write_image(output_path)
        # matplotlibで表示・保存する場合
        # plt.figure()
        # plot_diagram(diagrams[0])
        # plt.savefig(output_path)
        # plt.close()
        print(f"パーシステンス図を {output_path} に保存しました。")
    except Exception as e:
        print(f"図の保存中にエラーが発生しました: {e}")
        print("plotlyのバックエンドで問題が発生した可能性があります。")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # CSVファイルのパス
    western_csv = os.path.join(base_dir, "western_artworks.csv")
    japanese_csv = os.path.join(base_dir, "japanese_artworks.csv")
    
    csv_files = [western_csv, japanese_csv]
    
    analyze_artworks_tda(csv_files, base_dir)

    print("\n分析が完了しました。")
