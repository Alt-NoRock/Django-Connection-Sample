"""
リファクタリング版 - 設定ファイルベースの Dash アプリケーション
"""
import dash
from dash import html, Input, Output, State, ctx
import dash_cytoscape as cyto
import dash_table
import dash.dcc as dcc
from utils.graph_loader import GraphConfigLoader, GraphStyleManager


class DashGraphApp:
    """設定ファイルベースのDashグラフアプリケーション"""
    
    def __init__(self, config_path: str):
        """
        Args:
            config_path: 設定ファイルのパス
        """
        self.config_loader = GraphConfigLoader(config_path)
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
        
        self.app.layout = html.Div([
            dcc.Store(id='last-selected', data={'type': None, 'value': None}),
            html.Button('グラフ再配置', id='relayout-btn', n_clicks=0),
            cyto.Cytoscape(
                id='cytoscape',
                elements=elements,
                style={
                    'width': layout_config['graph_size']['width'],
                    'height': layout_config['graph_size']['height']
                },
                layout={'name': layout_config['layout_algorithm']},
                stylesheet=stylesheet
            ),
            dash_table.DataTable(
                id='datatable',
                columns=table_config['columns'],
                data=table_data,
                row_selectable='single',
                style_cell=table_config['style']['cell'],
                style_header=table_config['style']['header']
            )
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
            if selected_rows:
                selected_row = table_data[selected_rows[0]]
                source_node = selected_row['source']
                target_node = selected_row['target']
                
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
            if not tapNodeData:
                return original_data
            
            clicked_node = tapNodeData['id']
            # クリックされたノードが送信元または送信先に含まれる行のみ表示
            filtered_data = [
                row for row in original_data 
                if row['source'] == clicked_node or row['target'] == clicked_node
            ]
            return filtered_data if filtered_data else original_data
        
        @self.app.callback(
            Output('cytoscape', 'layout'),
            [Input('relayout-btn', 'n_clicks')]
        )
        def relayout_graph(n_clicks):
            """グラフレイアウト再配置コールバック"""
            layout_config = self.config_loader.get_layout_config()
            if n_clicks:
                return {'name': layout_config['layout_algorithm'], 'animate': True}
            return {'name': layout_config['layout_algorithm']}
    
    def run(self, debug: bool = True, host: str = '127.0.0.1', port: int = 8050):
        """アプリケーションを実行"""
        self.app.run(debug=debug, host=host, port=port)


def main():
    """メイン関数"""
    # 設定ファイルのパスを指定
    config_path = 'config/graph_config.json'
    
    # アプリケーションを作成・実行
    app = DashGraphApp(config_path)
    app.run(debug=True)


if __name__ == '__main__':
    main()