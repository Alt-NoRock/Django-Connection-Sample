"""
高度な初期化機能付きの GraphML/CSV Dash アプリケーション
"""
import dash
from dash import html, Input, Output, State, ctx, no_update
import dash_cytoscape as cyto
from dash import dash_table
import dash.dcc as dcc
from typing import List, Dict, Any, Optional, Tuple
from utils.graphml_csv_loader import GraphMLCSVConfigLoader, GraphStyleManager


# 定数定義
class AppConstants:
    """アプリケーション定数"""
    DEFAULT_HOST = '127.0.0.1'
    DEFAULT_PORT = 8053
    DEFAULT_LAYOUT = 'cose'
    PAGE_SIZE = 10
    
    # スタイル定数
    INFO_CARD_STYLE = {
        'margin-right': '20px', 
        'padding': '5px 10px', 
        'border-radius': '4px'
    }
    
    NODE_INFO_COLOR = '#e3f2fd'
    EDGE_INFO_COLOR = '#e8f5e8'
    TABLE_INFO_COLOR = '#fff3e0'
    COLUMN_INFO_COLOR = '#f3e5f5'
    
    BUTTON_BASE_STYLE = {
        'margin': '5px', 
        'padding': '8px 16px', 
        'border': 'none', 
        'border-radius': '6px', 
        'font-size': '13px', 
        'cursor': 'pointer',
        'font-weight': 'bold'
    }


class StyleHelper:
    """スタイル関連のヘルパークラス"""
    
    @staticmethod
    def get_info_span_style(bg_color: str) -> Dict[str, str]:
        """
        情報表示用スパンのスタイルを生成する.

        Args:
            bg_color (str): 背景色のカラーコード

        Returns:
            Dict[str, str]: 生成されたスタイル辞書
        """
        return {**AppConstants.INFO_CARD_STYLE, 'background-color': bg_color}
    
    @staticmethod
    def get_button_style(bg_color: str, text_color: str = 'white') -> Dict[str, str]:
        """
        ボタンスタイルを生成する.

        Args:
            bg_color (str): 背景色のカラーコード
            text_color (str, optional): テキスト色. Defaults to 'white'.

        Returns:
            Dict[str, str]: 生成されたボタンスタイル辞書
        """
        return {
            **AppConstants.BUTTON_BASE_STYLE,
            'background-color': bg_color,
            'color': text_color
        }


class AdvancedGraphMLCSVDashApp:
    """
    高度な初期化機能付きGraphML/CSVベースのDashアプリケーション.
    
    GraphMLファイルとCSVファイルを読み込み、インタラクティブな
    グラフ可視化とテーブル表示を提供するDashアプリケーション。
    """
    
    def __init__(self, config_path: str) -> None:
        """
        アプリケーションを初期化する.

        Args:
            config_path (str): 設定ファイルのパス（GraphMLとCSVのパスを含む）
            
        Raises:
            FileNotFoundError: 設定ファイルが見つからない場合
            ValueError: 設定ファイルの形式が無効な場合
        """
        self.config_loader: GraphMLCSVConfigLoader = GraphMLCSVConfigLoader(config_path)
        self.app: dash.Dash = dash.Dash(__name__)
        self.style_manager: Optional[GraphStyleManager] = None
        self.setup_layout()
        self.setup_callbacks()
    
    def _merge_stylesheets(
        self, 
        base_styles: List[Dict[str, Any]], 
        additional_styles: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        スタイルシートをマージし、重複セレクタを除去する.

        Args:
            base_styles (List[Dict[str, Any]]): ベースとなるスタイルのリスト
            additional_styles (List[Dict[str, Any]]): 追加するスタイルのリスト

        Returns:
            List[Dict[str, Any]]: マージされたスタイルシートのリスト
        """
        if not base_styles:
            return additional_styles.copy() if additional_styles else []
        
        merged = base_styles.copy()
        existing_selectors = {
            style.get('selector', '') for style in merged if 'selector' in style
        }
        
        for style in additional_styles or []:
            selector = style.get('selector', '')
            if selector and selector not in existing_selectors:
                merged.append(style)
                existing_selectors.add(selector)
        
        return merged
    
    def _handle_node_selection(
        self, 
        clicked_node: str, 
        last_selected: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        ノード選択処理を行う.
        
        同じノードが連続してクリックされた場合は選択を解除し、
        新しいノードがクリックされた場合はハイライト表示する。

        Args:
            clicked_node (str): クリックされたノードのID
            last_selected (Dict[str, Any]): 前回選択された項目の情報

        Returns:
            Tuple[List[Dict[str, Any]], Dict[str, Any]]: 
                (更新されたスタイルシート, 新しい選択状態)
        """
        if not clicked_node:
            return self.style_manager.get_directed_stylesheet(), {'type': None, 'value': None}
            
        # ダブルクリック判定（同じノードの連続クリック）
        if (last_selected.get('type') == 'node' 
            and last_selected.get('value') == clicked_node):
            # 選択解除
            return self.style_manager.get_directed_stylesheet(), {'type': None, 'value': None}
        
        # 新しいノードのハイライト
        try:
            highlighted_stylesheet = self.style_manager.add_node_highlight(clicked_node)
            return highlighted_stylesheet, {'type': 'node', 'value': clicked_node}
        except Exception:
            # ハイライト処理が失敗した場合はデフォルトスタイルを返す
            return self.style_manager.get_directed_stylesheet(), {'type': None, 'value': None}
    
    def _handle_table_row_selection(
        self, 
        selected_rows: Optional[List[int]], 
        table_data: Optional[List[Dict[str, Any]]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        テーブル行選択時のエッジ向き制御を処理する.
        
        選択された行の情報に基づいて、対応するエッジを有向グラフに変更し、
        関連するノードとエッジをハイライト表示する。

        Args:
            selected_rows (Optional[List[int]]): 選択されたテーブル行のインデックス
            table_data (Optional[List[Dict[str, Any]]]): テーブルデータ

        Returns:
            Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]: 
                (更新されたグラフ要素, 更新されたスタイルシート)
        """
        # バリデーション
        if not selected_rows or not table_data or not self.config_loader:
            # 選択がない場合は無向グラフに戻す
            elements = self.config_loader.get_cytoscape_elements()
            stylesheet = self.style_manager.get_directed_stylesheet()
            return elements, stylesheet
        
        # 選択された行を処理
        selected_row = table_data[selected_rows[0]]
        source_node = selected_row.get('source', '')
        target_node = selected_row.get('target', '')
        
        if source_node and target_node:
            # 関連エッジを有向に変更し、ハイライト
            directed_elements = self.config_loader.get_directed_cytoscape_elements_by_table_row(selected_row)
            directed_stylesheet = self.style_manager.get_directed_stylesheet()
            highlight_stylesheet = self.style_manager.add_edge_highlight(source_node, target_node)
            combined_stylesheet = self._merge_stylesheets(directed_stylesheet, highlight_stylesheet)
            
            return directed_elements, combined_stylesheet
        
        # デフォルトは無向グラフ
        elements = self.config_loader.get_cytoscape_elements()
        stylesheet = self.style_manager.get_directed_stylesheet()
        return elements, stylesheet
    
    def _create_info_section(
        self, 
        elements: List[Dict[str, Any]], 
        table_data: List[Dict[str, Any]], 
        table_config: Dict[str, Any]
    ) -> html.Div:
        """
        データ情報セクションを作成する.
        
        グラフの統計情報（ノード数、エッジ数）とテーブル情報を
        視覚的に表示するセクションを生成する。

        Args:
            elements (List[Dict[str, Any]]): Cytoscapeのグラフ要素
            table_data (List[Dict[str, Any]]): テーブルデータ
            table_config (Dict[str, Any]): テーブル設定

        Returns:
            html.Div: 情報表示セクションのDivコンポーネント
        """
        # データの安全な取得
        node_count = len([e for e in (elements or []) if 'source' not in e.get('data', {})])
        edge_count = len([e for e in (elements or []) if 'source' in e.get('data', {})])
        table_row_count = len(table_data or [])
        table_col_count = len(table_config.get('columns', []) if table_config else [])
        
        info_spans = [
            html.Span(
                f"ノード数: {node_count}", 
                style=StyleHelper.get_info_span_style(AppConstants.NODE_INFO_COLOR)
            ),
            html.Span(
                f"エッジ数: {edge_count}", 
                style=StyleHelper.get_info_span_style(AppConstants.EDGE_INFO_COLOR)
            ),
            html.Span(
                f"テーブル行数: {table_row_count}", 
                style=StyleHelper.get_info_span_style(AppConstants.TABLE_INFO_COLOR)
            ),
            html.Span(
                f"テーブル列数: {table_col_count}", 
                style=StyleHelper.get_info_span_style(AppConstants.COLUMN_INFO_COLOR)
            )
        ]
        
        return html.Div([
            html.H3("📊 データ情報", style={'margin': '0 0 10px 0'}),
            html.Div(
                info_spans, 
                style={'display': 'flex', 'flex-wrap': 'wrap', 'gap': '10px'}
            ),
            html.Hr(style={'margin': '15px 0'})
        ], style={
            'margin': '20px', 
            'padding': '15px', 
            'border': '1px solid #ddd', 
            'border-radius': '8px', 
            'background-color': '#fafafa'
        })
    
    def _create_control_panel(self) -> html.Div:
        """
        アプリケーションのコントロールパネルを作成する.
        
        グラフレイアウトの制御、リセット機能などの
        ユーザーインターフェース要素を含むパネルを生成する。

        Returns:
            html.Div: コントロールパネルのDivコンポーネント
        """
        # 主要操作ボタンの定義
        primary_buttons = [
            html.Button(
                '🔄 グラフ再配置', 
                id='relayout-btn', 
                n_clicks=0,
                style=StyleHelper.get_button_style('#4CAF50')
            ),
            html.Button(
                '📋 グループ配置', 
                id='group-layout-btn', 
                n_clicks=0,
                style=StyleHelper.get_button_style('#2196F3')
            ),
            html.Button(
                '🧹 状態初期化', 
                id='reset-btn', 
                n_clicks=0,
                style=StyleHelper.get_button_style('#f44336')
            ),
        ]
        
        # 二次操作ボタンの定義
        secondary_buttons = [
            html.Button(
                '🎯 選択解除のみ', 
                id='clear-selection-btn', 
                n_clicks=0,
                style=StyleHelper.get_button_style('#FF9800')
            ),
            html.Button(
                '📋 テーブルリセット', 
                id='reset-table-btn', 
                n_clicks=0,
                style=StyleHelper.get_button_style('#9C27B0')
            ),
            html.Button(
                '🎨 スタイルリセット', 
                id='reset-style-btn', 
                n_clicks=0,
                style=StyleHelper.get_button_style('#607D8B')
            ),
        ]
        
        return html.Div([
            html.H4(
                "🎛️ コントロールパネル", 
                style={'margin': '0 0 15px 0', 'color': '#333'}
            ),
            html.Div([
                # 基本操作ボタン
                html.Div(
                    primary_buttons, 
                    style={
                        'display': 'flex', 
                        'gap': '10px', 
                        'margin-bottom': '10px', 
                        'flex-wrap': 'wrap'
                    }
                ),
                # 部分初期化ボタン
                html.Div(
                    secondary_buttons, 
                    style={'display': 'flex', 'gap': '5px', 'flex-wrap': 'wrap'}
                ),
            ], style={'display': 'flex', 'flex-direction': 'column', 'align-items': 'center'}),
            # ステータス表示
            html.Div(
                id='reset-status', 
                style={
                    'margin': '15px 0', 
                    'text-align': 'center', 
                    'color': '#666', 
                    'font-weight': 'bold', 
                    'min-height': '20px'
                }
            )
        ], style={
            'margin': '20px', 
            'padding': '20px', 
            'border': '1px solid #ddd', 
            'border-radius': '8px', 
            'background-color': '#f9f9f9'
        })
    
    def _create_table_section(
        self, 
        table_data: List[Dict[str, Any]], 
        table_config: Dict[str, Any]
    ) -> html.Div:
        """
        データテーブルセクションを作成する.
        
        CSVデータに基づく動的なテーブル表示を生成し、
        行選択機能とページング機能を提供する。

        Args:
            table_data (List[Dict[str, Any]]): 表示するテーブルデータ
            table_config (Dict[str, Any]): テーブルの設定情報

        Returns:
            html.Div: テーブルセクションのDivコンポーネント
        """
        # データの安全な取得
        safe_table_data = table_data or []
        safe_table_config = table_config or {}
        
        # 列設定の安全な取得
        columns = safe_table_config.get('columns', [])
        style_config = safe_table_config.get('style', {})
        
        return html.Div([
            html.H3(
                "📋 データテーブル（動的生成）", 
                style={'color': '#333', 'margin-bottom': '15px'}
            ),
            dash_table.DataTable(
                id='datatable',
                columns=columns,
                data=safe_table_data,
                row_selectable='single',
                style_cell=style_config.get('cell', {}),
                style_header=style_config.get('header', {}),
                style_table={'overflowX': 'auto'},
                page_size=AppConstants.PAGE_SIZE,
                # 柔軟なデータ構造への対応
                fill_width=True,
                sort_action='native' if safe_table_data else 'none',
                filter_action='native' if safe_table_data else 'none'
            )
        ], style={
            'margin': '20px', 
            'padding': '20px', 
            'border': '1px solid #ddd', 
            'border-radius': '8px', 
            'background-color': '#fafafa'
        })
    
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
        
        # エッジの向きスタイルを初期設定に追加
        stylesheet = self.style_manager.get_directed_stylesheet()
        
        # 情報表示用のコンポーネント
        info_div = self._create_info_section(elements, table_data, table_config)
        
        self.app.layout = html.Div([
            info_div,
            dcc.Store(id='last-selected', data={'type': None, 'value': None}),
            dcc.Store(id='original-table-data', data=table_data),  # 元のテーブルデータを保存
            
            # コントロールパネル
            self._create_control_panel(),
            
            html.Div([
                cyto.Cytoscape(
                    id='cytoscape',
                    elements=elements,
                    style={
                        'width': layout_config.get('graph_size', {}).get('width', '700px'),
                        'height': layout_config.get('graph_size', {}).get('height', '600px'),
                        'border': '2px solid #ddd',
                        'border-radius': '8px'
                    },
                    layout={'name': layout_config.get('layout_algorithm', 'cose')},
                    stylesheet=stylesheet
                )
            ], style={'display': 'inline-block', 'vertical-align': 'top', 'margin': '10px'}),
            
            self._create_table_section(table_data, table_config)
        ])
    

    
    def setup_callbacks(self) -> None:
        """
        アプリケーションのすべてのコールバック関数を設定する.
        
        各機能別にコールバックを分離して設定し、
        保守性と可読性を向上させる。
        
        Raises:
            Exception: コールバック設定中にエラーが発生した場合
        """
        try:
            self._setup_style_callback()
            self._setup_table_filter_callback()
            self._setup_edge_direction_callback()
            self._setup_layout_callbacks()
            self._setup_reset_callbacks()
            self._setup_status_clear_callback()
        except Exception as e:
            print(f"コールバック設定中にエラーが発生しました: {e}")
            raise
    
    def _setup_style_callback(self):
        """スタイル更新コールバックを設定"""
        @self.app.callback(
            [Output('cytoscape', 'stylesheet'),
             Output('last-selected', 'data')],
            [Input('cytoscape', 'tapNodeData'),
             Input('datatable', 'selected_rows')],
            [State('last-selected', 'data'),
             State('datatable', 'data')]
        )
        def update_styles(tapNodeData, selected_rows, last_selected, table_data):
            """スタイル更新コールバック"""
            base_stylesheet = self.style_manager.get_base_stylesheet()
            
            # ノードクリック処理
            if tapNodeData:
                return self._handle_node_selection(tapNodeData['id'], last_selected)
            
            # テーブル行選択処理
            if selected_rows and table_data:
                return self._handle_table_style_selection(selected_rows, table_data, last_selected)
            
            return base_stylesheet, {'type': None, 'value': None}
    
    def _handle_table_style_selection(self, selected_rows: List[int], table_data: List[Dict], last_selected: Dict) -> Tuple[List[Dict], Dict]:
        """テーブル選択時のスタイル処理"""
        selected_row = table_data[selected_rows[0]]
        filter_columns = self.config_loader.config.get('table', {}).get('filter_columns', [])
        if not filter_columns:
            potential_columns = ['source', 'target', 'from', 'to']
            filter_columns = [col for col in potential_columns if col in selected_row]
        
        if len(filter_columns) >= 2:
            source_node = str(selected_row[filter_columns[0]])
            target_node = str(selected_row[filter_columns[1]])
            
            current_selection = {'type': 'table', 'value': selected_rows[0]}
            if last_selected == current_selection:
                return self.style_manager.get_base_stylesheet(), {'type': None, 'value': None}
            
            highlighted_stylesheet = self.style_manager.add_edge_highlight(source_node, target_node)
            return highlighted_stylesheet, current_selection
        
        return self.style_manager.get_base_stylesheet(), {'type': None, 'value': None}
    
    def _setup_table_filter_callback(self):
        """テーブルフィルタリングコールバックを設定"""
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
            filtered_data = self.config_loader.filter_table_by_node(clicked_node, original_data)
            return filtered_data
    
    def _setup_edge_direction_callback(self):
        """エッジの向き制御コールバックを設定"""
        @self.app.callback(
            [Output('cytoscape', 'elements', allow_duplicate=True),
             Output('cytoscape', 'stylesheet', allow_duplicate=True)],
            [Input('datatable', 'selected_rows')],
            [State('datatable', 'data')],
            prevent_initial_call=True
        )
        def update_edge_direction_and_highlight(selected_rows, table_data):
            """テーブル行選択時にエッジの向きを変更し、同時にハイライト"""
            if not selected_rows or not table_data:
                # 選択がない場合は無向グラフに戻す
                elements = self.config_loader.get_cytoscape_elements()
                stylesheet = self.style_manager.get_directed_stylesheet()
                return elements, stylesheet
            
            # 選択された行からsourceとtargetを取得
            selected_row = table_data[selected_rows[0]]
            source_node = selected_row.get('source', '')
            target_node = selected_row.get('target', '')
            
            if source_node and target_node:
                # テーブル行に関連するエッジを有向に変更（ハイライト対象エッジと同じ）
                directed_elements = self.config_loader.get_directed_cytoscape_elements_by_table_row(selected_row)
                
                # エッジハイライトスタイルと有向エッジスタイルを統合
                directed_stylesheet = self.style_manager.get_directed_stylesheet()
                highlight_stylesheet = self.style_manager.add_edge_highlight(source_node, target_node)
                
                # スタイルをマージ（重複除去）
                combined_stylesheet = self._merge_stylesheets(directed_stylesheet, highlight_stylesheet)
                
                return directed_elements, combined_stylesheet
            
            # デフォルトは無向グラフ
            elements = self.config_loader.get_cytoscape_elements()
            stylesheet = self.style_manager.get_directed_stylesheet()
            return elements, stylesheet
    
    def _setup_layout_callbacks(self):
        """レイアウト関連コールバックを設定"""
        pass  # 統合リセットコールバックに含まれているため、後で分離
    
    def _setup_reset_callbacks(self) -> None:
        """
        リセット関連コールバックを設定する.
        
        複数のリセット機能を個別のコールバックに分離し、
        保守性と理解しやすさを向上させる。
        """
        self._setup_full_reset_callback()
        self._setup_partial_reset_callbacks()
        self._setup_layout_callbacks_impl()
    
    def _setup_full_reset_callback(self) -> None:
        """完全リセット用のコールバックを設定"""
        @self.app.callback(
            [Output('cytoscape', 'stylesheet', allow_duplicate=True), 
             Output('cytoscape', 'elements', allow_duplicate=True),
             Output('last-selected', 'data', allow_duplicate=True),
             Output('datatable', 'data', allow_duplicate=True),
             Output('datatable', 'selected_rows', allow_duplicate=True),
             Output('cytoscape', 'layout', allow_duplicate=True),
             Output('reset-status', 'children', allow_duplicate=True)],
            [Input('reset-btn', 'n_clicks')],
            [State('original-table-data', 'data')],
            prevent_initial_call=True
        )
        def handle_full_reset(reset_clicks: Optional[int], original_data: List[Dict[str, Any]]):
            """
            完全リセット処理を実行する.
            
            Args:
                reset_clicks (Optional[int]): リセットボタンのクリック回数
                original_data (List[Dict[str, Any]]): 元のテーブルデータ
            
            Returns:
                Tuple: (stylesheet, elements, selection, table_data, selected_rows, layout, status)
            """
            if not reset_clicks:
                return tuple([no_update] * 7)
            
            # 初期状態に完全リセット
            reset_result = self._create_full_reset_state(original_data)
            status_message = f"✅ ダッシュボードが完全に初期化されました（無向グラフ状態） (リセット回数: {reset_clicks})"
            
            return (*reset_result, status_message)
    
    def _create_full_reset_state(self, original_data: List[Dict[str, Any]]) -> Tuple:
        """完全リセット状態を作成する"""
        try:
            reset_stylesheet = self.style_manager.get_directed_stylesheet()
            reset_elements = self.config_loader.get_cytoscape_elements()
            layout_config = self.config_loader.get_layout_config()
            
            return (
                reset_stylesheet,
                reset_elements,
                {'type': None, 'value': None},
                original_data or [],
                [],
                {'name': layout_config.get('layout_algorithm', 'cose'), 'animate': True}
            )
        except Exception:
            # エラー時はno_updateを返す
            return tuple([no_update] * 6)
    
    def _setup_partial_reset_callbacks(self) -> None:
        """部分的リセット機能のコールバックを設定"""
        @self.app.callback(
            [Output('cytoscape', 'stylesheet', allow_duplicate=True),
             Output('last-selected', 'data', allow_duplicate=True),
             Output('datatable', 'selected_rows', allow_duplicate=True),
             Output('reset-status', 'children', allow_duplicate=True)],
            [Input('clear-selection-btn', 'n_clicks')],
            prevent_initial_call=True
        )
        def handle_selection_clear(clear_clicks: Optional[int]):
            """選択状態のみクリアする"""
            if not clear_clicks:
                return tuple([no_update] * 4)
            
            reset_stylesheet = self.style_manager.get_directed_stylesheet()
            status_message = "🎯 選択状態をクリアしました"
            
            return reset_stylesheet, {'type': None, 'value': None}, [], status_message
        
        @self.app.callback(
            [Output('datatable', 'data', allow_duplicate=True),
             Output('datatable', 'selected_rows', allow_duplicate=True),
             Output('reset-status', 'children', allow_duplicate=True)],
            [Input('reset-table-btn', 'n_clicks')],
            [State('original-table-data', 'data')],
            prevent_initial_call=True
        )
        def handle_table_reset(table_clicks: Optional[int], original_data: List[Dict[str, Any]]):
            """テーブルデータのみリセットする"""
            if not table_clicks:
                return tuple([no_update] * 3)
            
            status_message = "📋 テーブルデータをリセットしました"
            return original_data or [], [], status_message
        
        @self.app.callback(
            [Output('cytoscape', 'stylesheet', allow_duplicate=True),
             Output('cytoscape', 'elements', allow_duplicate=True),
             Output('last-selected', 'data', allow_duplicate=True),
             Output('reset-status', 'children', allow_duplicate=True)],
            [Input('reset-style-btn', 'n_clicks')],
            prevent_initial_call=True
        )
        def handle_style_reset(style_clicks: Optional[int]):
            """スタイルのみリセットする"""
            if not style_clicks:
                return tuple([no_update] * 4)
            
            reset_stylesheet = self.style_manager.get_directed_stylesheet()
            reset_elements = self.config_loader.get_cytoscape_elements()
            status_message = "🎨 グラフスタイルをリセットしました"
            
            return reset_stylesheet, reset_elements, {'type': None, 'value': None}, status_message
    
    def _setup_layout_callbacks_impl(self) -> None:
        """レイアウト制御のコールバックを設定"""
        @self.app.callback(
            [Output('cytoscape', 'layout', allow_duplicate=True),
             Output('reset-status', 'children', allow_duplicate=True)],
            [Input('relayout-btn', 'n_clicks'),
             Input('group-layout-btn', 'n_clicks')],
            prevent_initial_call=True
        )
        def handle_layout_change(relayout_clicks: Optional[int], group_clicks: Optional[int]):
            """レイアウト変更を処理する"""
            if not ctx.triggered:
                return no_update, no_update
            
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            layout_config = self.config_loader.get_layout_config()
            
            if button_id == 'relayout-btn' and relayout_clicks:
                layout = {'name': layout_config.get('layout_algorithm', 'cose'), 'animate': True}
                status_message = f"🔄 グラフレイアウトを再配置しました (再配置回数: {relayout_clicks})"
                return layout, status_message
            
            elif button_id == 'group-layout-btn' and group_clicks:
                grouped_layout = self.config_loader.get_grouped_layout_config()
                status_message = "📋 ノードをタイプ別にグループ化しました (Interface/Processer/Storage分離)"
                return grouped_layout, status_message
            
            return no_update, no_update
    
    def _setup_status_clear_callback(self) -> None:
        """ステータスメッセージの自動クリア機能を設定"""
        @self.app.callback(
            Output('reset-status', 'children', allow_duplicate=True),
            [Input('cytoscape', 'tapNodeData'), Input('datatable', 'selected_rows')],
            prevent_initial_call=True
        )
        def clear_reset_status(
            tap_data: Optional[Dict[str, Any]], 
            selected_rows: Optional[List[int]]
        ) -> str:
            """
            ユーザーが何かを選択したらリセットステータスをクリアする.
            
            Args:
                tap_data (Optional[Dict[str, Any]]): タップされたノードのデータ
                selected_rows (Optional[List[int]]): 選択されたテーブル行
            
            Returns:
                str: 空文字列（ステータスクリア）またはno_update
            """
            if tap_data or selected_rows:
                return ""
            return no_update
    
    def run(
        self, 
        debug: bool = True, 
        host: str = AppConstants.DEFAULT_HOST, 
        port: int = AppConstants.DEFAULT_PORT
    ) -> None:
        """
        Dashアプリケーションを起動する.
        
        Args:
            debug (bool, optional): デバッグモードの有効/無効. Defaults to True.
            host (str, optional): ホストアドレス. Defaults to AppConstants.DEFAULT_HOST.
            port (int, optional): ポート番号. Defaults to AppConstants.DEFAULT_PORT.
            
        Raises:
            Exception: アプリケーション起動時にエラーが発生した場合
        """
        try:
            print(f"高度な初期化機能付きGraphML/CSVアプリケーションを起動中...")
            print(f"URL: http://{host}:{port}")
            self.app.run(debug=debug, host=host, port=port)
        except Exception as e:
            print(f"アプリケーション起動中にエラーが発生しました: {e}")
            raise


# グローバルスコープでアプリケーションインスタンスを作成
config_path = 'config/graphml_csv_config.json'
app = None

try:
    # アプリケーションインスタンスを作成
    dash_app_instance = AdvancedGraphMLCSVDashApp(config_path)
    app = dash_app_instance.app  # Dashアプリオブジェクトを取得
except Exception as e:
    print(f"アプリケーション初期化エラー: {e}")
    print("設定ファイルとデータファイルが正しく配置されているか確認してください。")


def main() -> None:
    """
    アプリケーションのメインエントリーポイント.
    
    設定ファイルを読み込み、Dashアプリケーションを起動する。
    エラーが発生した場合は適切なメッセージを表示する。
    
    Raises:
        SystemExit: アプリケーション初期化または起動時にエラーが発生した場合
    """
    global app, dash_app_instance
    
    try:
        if dash_app_instance:
            dash_app_instance.run(debug=True)
        else:
            print("アプリケーションが初期化されていません。")
    except Exception as e:
        print(f"アプリケーション起動エラー: {e}")
        print("設定ファイルとデータファイルが正しく配置されているか確認してください。")


if __name__ == '__main__':
    main()