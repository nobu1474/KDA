import sys
import pickle
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from visualization.jones_interactive import launch_interactive_jones_direction_explorer

# 保存したデータのパス
DATA_FILE = PROJECT_ROOT / "outputs" / "saved_jones_explorer_data.pkl"

if __name__ == "__main__":
    if not DATA_FILE.exists():
        print(f"エラー: データファイルが見つかりません: {DATA_FILE}")
        print("先に view_jones_direction_explorer.py を実行してデータを生成してください。")
        sys.exit(1)

    print(f"データ ({DATA_FILE}) を読み込んでいます...")
    with open(DATA_FILE, "rb") as f:
        data = pickle.load(f)

    curves = data["curves"]
    poly_map = data["poly_map"]

    print(f"球面点数: {len(poly_map)}")
    print("サーバーを起動しています（ http://127.0.0.1:8050 にアクセスしてください）...")

    launch_interactive_jones_direction_explorer(
        curves,
        poly_map,
        title="Interactive Jones polynomial explorer (Saved Data)",
        host="127.0.0.1",
        port=8050,
        debug=False,
        run_server=True,
    )
