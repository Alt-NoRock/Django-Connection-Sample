"""
全ての設定ファイル形式に対応した統合ランチャー
"""
import os
import sys
from dash_refactored import DashGraphApp
from dash_graphml_csv import GraphMLCSVDashApp


def scan_config_files():
    """設定ファイルをスキャンして種類別に分類"""
    config_dir = 'config'
    json_configs = []
    graphml_csv_configs = []
    
    if not os.path.exists(config_dir):
        return json_configs, graphml_csv_configs
    
    for file in os.listdir(config_dir):
        if file.endswith('.json'):
            config_path = os.path.join(config_dir, file)
            
            # 設定ファイルの内容を確認してタイプを判定
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    import json
                    config = json.load(f)
                    
                if 'data_sources' in config and 'graphml_file' in config['data_sources']:
                    # GraphML/CSV形式
                    graphml_csv_configs.append({
                        'file': file,
                        'path': config_path,
                        'type': 'GraphML/CSV'
                    })
                else:
                    # 従来のJSON形式
                    json_configs.append({
                        'file': file,
                        'path': config_path,
                        'type': 'JSON'
                    })
            except Exception as e:
                print(f"設定ファイル {file} の読み込みでエラー: {e}")
    
    return json_configs, graphml_csv_configs


def main():
    """メイン関数"""
    print("=== 統合 Dash Graph Application ランチャー ===")
    print()
    
    # 設定ファイルをスキャン
    json_configs, graphml_csv_configs = scan_config_files()
    
    if not json_configs and not graphml_csv_configs:
        print("設定ファイルが見つかりません。")
        return
    
    # 設定ファイルリストを表示
    all_configs = []
    option_num = 1
    
    if json_configs:
        print("📊 従来のJSON設定ファイル:")
        for config in json_configs:
            print(f"  {option_num}. {config['file']} ({config['type']})")
            all_configs.append(config)
            option_num += 1
    
    if graphml_csv_configs:
        print("\n🔗 GraphML/CSV設定ファイル:")
        for config in graphml_csv_configs:
            print(f"  {option_num}. {config['file']} ({config['type']})")
            all_configs.append(config)
            option_num += 1
    
    print(f"\n  0. 終了")
    
    # ユーザーに選択を求める
    try:
        choice = input(f"\n設定ファイルを選択してください (0-{len(all_configs)}): ")
        choice_idx = int(choice)
        
        if choice_idx == 0:
            print("アプリケーションを終了します。")
            return
        
        if 1 <= choice_idx <= len(all_configs):
            selected_config = all_configs[choice_idx - 1]
            print(f"\n選択された設定: {selected_config['file']} ({selected_config['type']})")
            
            # 設定タイプに応じてアプリケーションを起動
            if selected_config['type'] == 'GraphML/CSV':
                print("GraphML/CSV対応アプリケーションを起動中...")
                app = GraphMLCSVDashApp(selected_config['path'])
                app.run(debug=True)
            else:
                print("従来のJSONアプリケーションを起動中...")
                app = DashGraphApp(selected_config['path'])
                app.run(debug=True)
        else:
            print("無効な選択です。")
    
    except (ValueError, KeyboardInterrupt):
        print("\nアプリケーションを終了します。")
    except Exception as e:
        print(f"エラーが発生しました: {e}")


if __name__ == '__main__':
    main()