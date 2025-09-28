"""
GraphMLとCSVファイル対応版 - Dash アプリケーション
"""
import dash
from dash import html, Input, Output, State, ctx
import dash_cytoscape as cyto
from dash import dash_table
import dash.dcc as dcc
from utils.graphml_csv_loader import GraphMLCSVConfigLoader, GraphStyleManager


class GraphMLCSVDashApp:
    """GraphMLとCSVファイルベースのDashアプリケーション"""
    
    def __init__(self, config_path: str):
        """
        Args:
            config_path: 設定ファイルのパス（GraphMLとCSVのパスを含む）
        """
        self.config_loader = GraphMLCSVConfigLoader(config_path)
        self.app = dash.Dash(__name__)
        self.setup_layout()
        self.setup_callbacks()
    
    def setup_layout(self):
        """レイアウトを設定"""
        # 設定から各種データを取得
        elements = self.config_loader.get_cytoscape_elements()
        stylesheet = self.config_loader.get_cytoscape_stylesheet()
        table_data = self.config_loader.get_table_data()
        table_config = self.config_loader.get_table_config()
        layout_config = self.config_loader.get_layout_config()
        
        # スタイルマネージャーを初期化
        self.style_manager = GraphStyleManager(stylesheet)
        
        # 情報表示用のコンポーネント
        info_div = html.Div([
            html.H3("データ情報"),
            html.P(f"ノード数: {len([e for e in elements if 'source' not in e['data']])}"),
            html.P(f"エッジ数: {len([e for e in elements if 'source' in e['data']])}"),
            html.P(f"テーブル行数: {len(table_data)}"),
            html.P(f"テーブル列数: {len(table_config['columns'])}"),
            html.Hr()
        ], style={'margin': '20px', 'padding': '10px', 'border': '1px solid #ddd'})
        
        self.app.layout = html.Div([
            info_div,
            dcc.Store(id='last-selected', data={'type': None, 'value': None}),
            html.Button('グラフ再配置', id='relayout-btn', n_clicks=0, 
                       style={'margin': '10px', 'padding': '10px 20px'}),
            
            html.Div([
                cyto.Cytoscape(
                    id='cytoscape',
                    elements=elements,
                    style={
                        'width': layout_config.get('graph_size', {}).get('width', '700px'),
                        'height': layout_config.get('graph_size', {}).get('height', '600px'),
                        'border': '1px solid #ddd'
                    },
                    layout={'name': layout_config.get('layout_algorithm', 'cose')},
                    stylesheet=stylesheet
                )
            ], style={'display': 'inline-block', 'vertical-align': 'top', 'margin': '10px'}),
            
            html.Div([
                html.H3("データテーブル（動的生成）"),
                dash_table.DataTable(
                    id='datatable',
                    columns=table_config['columns'],
                    data=table_data,
                    row_selectable='single',
                    style_cell=table_config['style']['cell'],
                    style_header=table_config['style']['header'],
                    style_table={'overflowX': 'auto'},
                    page_size=10  # ページング機能を追加
                )
            ], style={'margin': '20px'})
        ])
    
    def setup_callbacks(self):
        """コールバック関数を設定"""
        
        @self.app.callback(
            [Output('cytoscape', 'stylesheet'), Output('last-selected', 'data')],
            [Input('datatable', 'selected_rows'), Input('cytoscape', 'tapNodeData')],
            [State('last-selected', 'data'), State('datatable', 'data')]
        )
        def update_styles(selected_rows, tapNodeData, last_selected, table_data):
            """スタイル更新コールバック"""
            base_stylesheet = self.style_manager.get_base_stylesheet()
            
            # ダブルクリック判定と処理（前回と同じ場合はクリア）
            if tapNodeData:
                current_selection = {'type': 'node', 'value': tapNodeData['id']}
                if last_selected == current_selection:
                    # ダブルクリック: 選択解除
                    return base_stylesheet, {'type': None, 'value': None}
                else:
                    # 新規選択: ノードクリック処理
                    clicked_node = tapNodeData['id']
                    highlighted_stylesheet = self.style_manager.add_node_highlight(clicked_node)
                    return highlighted_stylesheet, current_selection
            
            # テーブル行選択処理
            if selected_rows and table_data:
                selected_row = table_data[selected_rows[0]]
                
                # フィルタリング対象のカラムを動的に特定
                filter_columns = self.config_loader.config.get('table', {}).get('filter_columns', [])
                if not filter_columns:
                    # デフォルトで 'source', 'target' を探す
                    potential_columns = ['source', 'target', 'from', 'to']
                    filter_columns = [col for col in potential_columns if col in selected_row]
                
                if len(filter_columns) >= 2:
                    source_node = str(selected_row[filter_columns[0]])
                    target_node = str(selected_row[filter_columns[1]])
                    
                    current_selection = {'type': 'table', 'value': selected_rows[0]}
                    if last_selected == current_selection:
                        # ダブルクリック: 選択解除
                        return base_stylesheet, {'type': None, 'value': None}
                    
                    # 関連ノードとエッジのハイライト
                    highlighted_stylesheet = self.style_manager.add_edge_highlight(source_node, target_node)
                    return highlighted_stylesheet, current_selection
            
            return base_stylesheet, {'type': None, 'value': None}
        
        @self.app.callback(
            Output('datatable', 'data'),
            [Input('cytoscape', 'tapNodeData')],
            [State('datatable', 'data')]
        )
        def filter_table(tapNodeData, original_data):
            """テーブルフィルタリングコールバック"""
            if not tapNodeData or not original_data:
                return original_data
            
            clicked_node = tapNodeData['id']
            # 設定ベースのフィルタリング
            filtered_data = self.config_loader.filter_table_by_node(clicked_node, original_data)
            return filtered_data
        
        @self.app.callback(
            Output('cytoscape', 'layout'),
            [Input('relayout-btn', 'n_clicks')]
        )
        def relayout_graph(n_clicks):
            """グラフレイアウト再配置コールバック"""
            layout_config = self.config_loader.get_layout_config()
            if n_clicks:
                return {'name': layout_config.get('layout_algorithm', 'cose'), 'animate': True}
            return {'name': layout_config.get('layout_algorithm', 'cose')}
    
    def run(self, debug: bool = True, host: str = '127.0.0.1', port: int = 8051):
        """アプリケーションを実行（ポート番号を変更）"""
        print(f"GraphML/CSV対応アプリケーションを起動中...")
        print(f"URL: http://{host}:{port}")
        self.app.run(debug=debug, host=host, port=port)


def main():
    """メイン関数"""
    # 設定ファイルのパスを指定
    config_path = 'config/graphml_csv_config.json'
    
    # アプリケーションを作成・実行
    try:
        app = GraphMLCSVDashApp(config_path)
        app.run(debug=True)
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        print("設定ファイルとデータファイルが正しく配置されているか確認してください。")


if __name__ == '__main__':
    main()