"""
設定切り替え可能なサンプルアプリケーション
"""
import os
from dash_refactored import DashGraphApp


def main():
    """メイン関数 - 設定ファイルを選択してアプリを起動"""
    print("=== Dash Graph Application ===")
    print("利用可能な設定ファイル:")
    
    config_dir = 'config'
    config_files = []
    
    # 設定ファイルをスキャン
    if os.path.exists(config_dir):
        for file in os.listdir(config_dir):
            if file.endswith('.json'):
                config_files.append(file)
                print(f"{len(config_files)}. {file}")
    
    if not config_files:
        print("設定ファイルが見つかりません。")
        return
    
    # ユーザーに選択を求める
    try:
        choice = input(f"\n設定ファイルを選択してください (1-{len(config_files)}): ")
        choice_idx = int(choice) - 1
        
        if 0 <= choice_idx < len(config_files):
            selected_config = config_files[choice_idx]
            config_path = os.path.join(config_dir, selected_config)
            print(f"選択された設定: {selected_config}")
            
            # アプリケーションを起動
            app = DashGraphApp(config_path)
            print(f"アプリケーションを起動中... http://127.0.0.1:8050")
            app.run(debug=True)
        else:
            print("無効な選択です。")
    except (ValueError, KeyboardInterrupt):
        print("アプリケーションを終了します。")


if __name__ == '__main__':
    main()