"""
GraphMLとCSVファイルを読み込むための拡張ローダー.

このモジュールは、GraphMLファイルとCSVファイルを読み込み、
Dash Cytoscapeで使用可能な形式に変換する機能を提供する。
"""
import json
import os
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import networkx as nx
import pandas as pd


class GraphMLCSVConfigLoader:
    """
    GraphMLとCSVファイルを読み込み、設定を動的生成するクラス.
    
    このクラスは、設定ファイルに基づいてGraphMLファイルとCSVファイルを読み込み、
    Dash Cytoscapeで利用可能な形式に変換する機能を提供する。
    
    Attributes:
        config_path (str): 設定ファイルのパス
        config (Dict[str, Any]): 読み込まれた設定データ
        graph (Optional[nx.Graph]): NetworkXグラフオブジェクト
        table_df (Optional[pd.DataFrame]): CSVデータのDataFrame
    """
    
    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        ローダーを初期化し、設定とデータファイルを読み込む.

        Args:
            config_path (Optional[str]): 設定ファイルのパス（GraphMLとCSVのパスを含む）
                                       Noneの場合はデフォルト設定を使用
            
        Raises:
            FileNotFoundError: 設定ファイルが見つからない場合
            ValueError: ファイル読み込み時にエラーが発生した場合
        """
        self.config_path: Optional[str] = config_path
        self.config: Dict[str, Any] = {}
        self.graph: Optional[nx.Graph] = None
        self.table_df: Optional[pd.DataFrame] = None
        
        # 設定ファイルの読み込み
        self.config = self._load_config()
        
        # 設定ファイルが指定されている場合のみデータファイルを読み込み
        if self.config_path:
            self._load_data_files()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        設定ファイルを読み込む.
        
        JSONファイルから設定情報を読み込み、バリデーションを行う。
        設定ファイルが指定されていない場合はデフォルト設定を返す。
        
        Returns:
            Dict[str, Any]: 読み込まれた設定データ
            
        Raises:
            FileNotFoundError: 設定ファイルが見つからない場合
            ValueError: JSONファイルが無効な場合、または必須フィールドが不足している場合
        """
        if not self.config_path:
            # デフォルト設定を返す
            return {
                'data_sources': {},
                'graph': {},
                'table': {},
                'layout': {}
            }
            
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"設定ファイルが見つかりません: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                
                # 必須フィールドの存在確認
                self._validate_config(config_data)
                
                return config_data
                
        except json.JSONDecodeError as e:
            raise ValueError(f"設定ファイルのJSONが無効です: {e}")
        except Exception as e:
            raise ValueError(f"設定ファイルの読み込み中にエラーが発生しました: {e}")
    
    def _validate_config(self, config_data: Dict[str, Any]) -> None:
        """
        設定データの妥当性を検証する.
        
        Args:
            config_data (Dict[str, Any]): 検証する設定データ
            
        Raises:
            ValueError: 必須フィールドが不足している場合
        """
        # 設定ファイルが指定されていない場合は検証をスキップ
        if not self.config_path:
            return
            
        required_fields = ['data_sources']
        for field in required_fields:
            if field not in config_data:
                raise ValueError(f"必須フィールド '{field}' が設定ファイルに含まれていません")
        
        # data_sources内の必須フィールドも確認
        data_sources = config_data.get('data_sources', {})
        required_data_fields = ['graphml_file', 'csv_file']
        for field in required_data_fields:
            if field not in data_sources:
                raise ValueError(f"必須フィールド 'data_sources.{field}' が設定ファイルに含まれていません")
    
    def _load_data_files(self) -> None:
        """
        GraphMLとCSVファイルを読み込む.
        
        設定ファイルで指定されたGraphMLファイルとCSVファイルを読み込み、
        インスタンス変数に格納する。相対パスは絶対パスに変換される。
        
        Raises:
            ValueError: ファイル読み込み時にエラーが発生した場合
        """
        self._load_graphml_file()
        self._load_csv_file()
    
    def _load_graphml_file(self) -> None:
        """
        GraphMLファイルを読み込む.
        
        Raises:
            ValueError: GraphMLファイルの読み込みに失敗した場合
        """
        try:
            graphml_path = self._resolve_file_path('graphml_file')
            
            if not os.path.exists(graphml_path):
                raise FileNotFoundError(f"GraphMLファイルが見つかりません: {graphml_path}")
            
            self.graph = nx.read_graphml(graphml_path)
            
            # 読み込み結果の出力
            node_count = len(self.graph.nodes) if self.graph else 0
            edge_count = len(self.graph.edges) if self.graph else 0
            print(f"GraphMLファイルを読み込みました: {graphml_path}")
            print(f"ノード数: {node_count}, エッジ数: {edge_count}")
            
        except nx.NetworkXError as e:
            raise ValueError(f"GraphMLファイルの形式が無効です: {e}")
        except Exception as e:
            raise ValueError(f"GraphMLファイルの読み込みに失敗しました: {e}")
    
    def _load_csv_file(self) -> None:
        """
        CSVファイルを読み込む.
        
        Raises:
            ValueError: CSVファイルの読み込みに失敗した場合
        """
        try:
            csv_path = self._resolve_file_path('csv_file')
            
            if not os.path.exists(csv_path):
                raise FileNotFoundError(f"CSVファイルが見つかりません: {csv_path}")
            
            # 複数のエンコーディングを試行
            encodings = ['utf-8', 'utf-8-sig', 'cp932', 'shift_jis']
            
            for encoding in encodings:
                try:
                    self.table_df = pd.read_csv(csv_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError(f"CSVファイルのエンコーディングを判定できませんでした: {csv_path}")
            
            # 読み込み結果の出力
            row_count = len(self.table_df) if self.table_df is not None else 0
            col_count = len(self.table_df.columns) if self.table_df is not None else 0
            columns = list(self.table_df.columns) if self.table_df is not None else []
            
            print(f"CSVファイルを読み込みました: {csv_path}")
            print(f"行数: {row_count}, 列数: {col_count}")
            print(f"カラム: {columns}")
            
        except pd.errors.EmptyDataError:
            raise ValueError(f"CSVファイルが空です: {csv_path}")
        except pd.errors.ParserError as e:
            raise ValueError(f"CSVファイルの解析に失敗しました: {e}")
        except Exception as e:
            raise ValueError(f"CSVファイルの読み込みに失敗しました: {e}")
    
    def _resolve_file_path(self, file_key: str) -> str:
        """
        設定ファイル内のファイルパスを絶対パスに解決する.
        
        Args:
            file_key (str): 設定内のファイルキー名
            
        Returns:
            str: 解決された絶対パス
        """
        file_path = self.config['data_sources'][file_key]
        
        if os.path.isabs(file_path):
            return file_path
        else:
            # 相対パスの場合、設定ファイルの場所を基準に解決
            config_dir = os.path.dirname(os.path.abspath(self.config_path))
            return os.path.join(config_dir, file_path)
    
    def get_cytoscape_elements(self) -> List[Dict[str, Any]]:
        """
        GraphMLからCytoscape用のelementsリストを生成する.
        
        NetworkXグラフをDash Cytoscapeで表示可能な形式に変換する。
        初期状態では全てのエッジが無向グラフとして設定される。
        
        Returns:
            List[Dict[str, Any]]: Cytoscape用のノードとエッジの要素リスト
        """
        if self.graph is None:
            return []
        
        # ノード要素とエッジ要素を生成
        nodes = self._create_node_elements()
        edges = self._create_edge_elements()
        
        return nodes + edges
    
    def _create_node_elements(self) -> List[Dict[str, Any]]:
        """
        ノード要素を作成する.
        
        Returns:
            List[Dict[str, Any]]: Cytoscape用のノード要素リスト
        """
        if self.graph is None:
            return []
        
        nodes = []
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            
            # ノード属性の安全な取得
            label = self._get_node_label(node_data, node_id)
            node_type = self._get_node_type(node_data)
            
            node_element = {
                'data': {
                    'id': str(node_id),
                    'label': str(label),
                    'Type': str(node_type)
                },
                'classes': f'type-{str(node_type).lower()}'
            }
            
            # 追加属性があれば含める
            self._add_additional_node_attributes(node_element, node_data)
            
            nodes.append(node_element)
        
        return nodes
    
    def _get_node_label(self, node_data: Dict[str, Any], node_id: Any) -> str:
        """
        ノードのラベルを取得する.
        
        Args:
            node_data (Dict[str, Any]): ノードデータ
            node_id (Any): ノードID
            
        Returns:
            str: ノードラベル
        """
        # 優先順位に従ってラベルを取得
        label_candidates = ['label', 'name', 'title', 'id']
        
        for candidate in label_candidates:
            if candidate in node_data and node_data[candidate]:
                return str(node_data[candidate])
        
        return str(node_id)
    
    def _get_node_type(self, node_data: Dict[str, Any]) -> str:
        """
        ノードのタイプを取得する.
        
        Args:
            node_data (Dict[str, Any]): ノードデータ
            
        Returns:
            str: ノードタイプ
        """
        # 優先順位に従ってタイプを取得
        type_candidates = ['type', 'category', 'kind', 'class']
        
        for candidate in type_candidates:
            if candidate in node_data and node_data[candidate]:
                return str(node_data[candidate])
        
        return 'default'
    
    def _add_additional_node_attributes(
        self, 
        node_element: Dict[str, Any], 
        node_data: Dict[str, Any]
    ) -> None:
        """
        ノード要素に追加属性を設定する.
        
        Args:
            node_element (Dict[str, Any]): ノード要素（変更される）
            node_data (Dict[str, Any]): 元のノードデータ
        """
        # 特定の属性をCytoscapeのdata部分に追加
        additional_attrs = ['weight', 'size', 'color', 'description']
        
        for attr in additional_attrs:
            if attr in node_data:
                node_element['data'][attr] = node_data[attr]
    
    def _create_edge_elements(self) -> List[Dict[str, Any]]:
        """
        エッジ要素を作成する（初期状態は無向グラフ）.
        
        Returns:
            List[Dict[str, Any]]: Cytoscape用のエッジ要素リスト
        """
        if self.graph is None:
            return []
        
        edges = []
        for source, target in self.graph.edges():
            edge_data = self.graph[source][target]
            
            # エッジ属性の安全な取得
            edge_label = self._get_edge_label(edge_data, source, target)
            
            edge_element = {
                'data': {
                    'source': str(source),
                    'target': str(target),
                    'label': str(edge_label),
                    'directed': False  # 初期状態は無向
                },
                'classes': 'undirected'  # 無向エッジのクラス
            }
            
            # 追加属性があれば含める
            self._add_additional_edge_attributes(edge_element, edge_data)
            
            edges.append(edge_element)
        
        return edges
    
    def _get_edge_label(self, edge_data: Dict[str, Any], source: Any, target: Any) -> str:
        """
        エッジのラベルを取得する.
        
        Args:
            edge_data (Dict[str, Any]): エッジデータ
            source (Any): ソースノードID
            target (Any): ターゲットノードID
            
        Returns:
            str: エッジラベル
        """
        # 優先順位に従ってラベルを取得
        label_candidates = ['label', 'name', 'title', 'relation']
        
        for candidate in label_candidates:
            if candidate in edge_data and edge_data[candidate]:
                return str(edge_data[candidate])
        
        return f"{source}->{target}"
    
    def _add_additional_edge_attributes(
        self, 
        edge_element: Dict[str, Any], 
        edge_data: Dict[str, Any]
    ) -> None:
        """
        エッジ要素に追加属性を設定する.
        
        Args:
            edge_element (Dict[str, Any]): エッジ要素（変更される）
            edge_data (Dict[str, Any]): 元のエッジデータ
        """
        # 特定の属性をCytoscapeのdata部分に追加
        additional_attrs = ['weight', 'bandwidth', 'protocol', 'description']
        
        for attr in additional_attrs:
            if attr in edge_data:
                edge_element['data'][attr] = edge_data[attr]
    
    def get_directed_cytoscape_elements(
        self, 
        source_node: str, 
        target_node: str
    ) -> List[Dict[str, Any]]:
        """
        特定のエッジを有向に変更したCytoscape用のelementsリストを生成する.
        
        指定されたソースノードとターゲットノードの間のエッジのみを
        有向グラフとして表示し、その他は無向グラフのまま保持する。
        
        Args:
            source_node (str): ソースノードのID
            target_node (str): ターゲットノードのID
            
        Returns:
            List[Dict[str, Any]]: 更新されたCytoscape要素リスト
        """
        if self.graph is None:
            return []
        
        # ノード要素を作成（変更なし）
        nodes = self._create_node_elements()
        
        # エッジ要素を作成（指定されたエッジのみ有向）
        edges = self._create_directed_edge_elements(source_node, target_node)
        
        return nodes + edges
    
    def _create_directed_edge_elements(
        self, 
        target_source: str, 
        target_target: str
    ) -> List[Dict[str, Any]]:
        """
        指定されたエッジのみ有向に設定したエッジ要素を作成する.
        
        Args:
            target_source (str): 有向にするエッジのソースノード
            target_target (str): 有向にするエッジのターゲットノード
            
        Returns:
            List[Dict[str, Any]]: エッジ要素リスト
        """
        if self.graph is None:
            return []
        
        edges = []
        for edge_source, edge_target in self.graph.edges():
            edge_data = self.graph[edge_source][edge_target]
            edge_label = self._get_edge_label(edge_data, edge_source, edge_target)
            
            # 指定されたエッジの場合は有向に設定
            is_directed = (str(edge_source) == target_source and str(edge_target) == target_target)
            
            edge_element = {
                'data': {
                    'source': str(edge_source),
                    'target': str(edge_target),
                    'label': str(edge_label),
                    'directed': is_directed
                },
                'classes': 'directed' if is_directed else 'undirected'
            }
            
            # 追加属性があれば含める
            self._add_additional_edge_attributes(edge_element, edge_data)
            
            edges.append(edge_element)
        
        return edges
    
    def get_directed_cytoscape_elements_by_table_row(
        self, 
        selected_row: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        テーブル行選択に基づいて関連エッジを有向に変更したCytoscape用のelementsリストを生成する.
        
        選択されたテーブル行から接続情報を抽出し、対応するエッジを
        有向グラフとして表示するための要素リストを生成する。
        
        Args:
            selected_row (Dict[str, Any]): 選択されたテーブル行のデータ
            
        Returns:
            List[Dict[str, Any]]: 更新されたCytoscape要素リスト
        """
        if self.graph is None or not selected_row:
            return self.get_cytoscape_elements()
        
        # 選択行から接続情報を安全に取得
        connection_info = self._extract_connection_info(selected_row)
        
        if not connection_info:
            return self.get_cytoscape_elements()
        
        source_node, target_node = connection_info
        return self.get_directed_cytoscape_elements(source_node, target_node)
    
    def _extract_connection_info(self, selected_row: Dict[str, Any]) -> Optional[Tuple[str, str]]:
        """
        テーブル行から接続情報を抽出する.
        
        Args:
            selected_row (Dict[str, Any]): テーブル行データ
            
        Returns:
            Optional[Tuple[str, str]]: (source, target)のタプル、または None
        """
        # 設定から接続カラムを取得
        filter_columns = self.config.get('table', {}).get('filter_columns', [])
        
        if not filter_columns:
            # デフォルトの接続カラム候補
            potential_columns = ['source', 'target', 'from', 'to', 'node1', 'node2']
            filter_columns = [col for col in potential_columns if col in selected_row]
        
        if len(filter_columns) >= 2:
            source_node = str(selected_row.get(filter_columns[0], ''))
            target_node = str(selected_row.get(filter_columns[1], ''))
            
            if source_node and target_node:
                return source_node, target_node
        
        return None
    
    def get_node_types(self) -> List[str]:
        """
        グラフから全ノードタイプを取得する.
        
        Returns:
            List[str]: ソートされたノードタイプのリスト
        """
        if self.graph is None:
            return []
        
        types: Set[str] = set()
        
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            node_type = self._get_node_type(node_data)
            types.add(node_type)
        
        return sorted(list(types))
    
    def get_cytoscape_stylesheet(self) -> List[Dict[str, Any]]:
        """
        ノードタイプに基づいてスタイルシートを動的生成する.
        
        設定ファイルに基づいて、各ノードタイプとエッジタイプの
        スタイルを定義したCytoscapeスタイルシートを生成する。
        
        Returns:
            List[Dict[str, Any]]: Cytoscapeスタイルシートリスト
        """
        stylesheet = []
        
        # デフォルトスタイルの追加
        self._add_default_node_style(stylesheet)
        
        # ノードタイプ別スタイルの追加
        self._add_node_type_styles(stylesheet)
        
        # エッジスタイルの追加
        self._add_edge_styles(stylesheet)
        
        return stylesheet
    
    def _add_default_node_style(self, stylesheet: List[Dict[str, Any]]) -> None:
        """
        デフォルトノードスタイルを追加する.
        
        Args:
            stylesheet (List[Dict[str, Any]]): スタイルシートリスト（変更される）
        """
        default_style = self.config.get('layout', {}).get('default_node_style', {})
        
        base_node_style = {
            'selector': 'node',
            'style': {
                'label': 'data(label)',
                'background-color': default_style.get('background_color', '#666'),
                'shape': default_style.get('shape', 'ellipse'),
                'width': default_style.get('width', 60),
                'height': default_style.get('height', 60),
                'text-valign': 'center',
                'text-halign': 'center',
                'font-size': '10px',
                'color': '#333'
            }
        }
        
        stylesheet.append(base_node_style)
    
    def _add_node_type_styles(self, stylesheet: List[Dict[str, Any]]) -> None:
        """
        ノードタイプ別スタイルを追加する.
        
        Args:
            stylesheet (List[Dict[str, Any]]): スタイルシートリスト（変更される）
        """
        type_styles = self.config.get('node_type_styles', {})
        node_types = self.get_node_types()
        
        for node_type in node_types:
            if node_type in type_styles:
                style_config = type_styles[node_type]
                node_style = self._create_node_type_style(node_type, style_config)
                stylesheet.append(node_style)
    
    def _create_node_type_style(
        self, 
        node_type: str, 
        style_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        ノードタイプ別のスタイルを作成する.
        
        Args:
            node_type (str): ノードタイプ
            style_config (Dict[str, Any]): スタイル設定
            
        Returns:
            Dict[str, Any]: Cytoscapeスタイル定義
        """
        node_style = {
            'selector': f'node[Type = "{node_type}"]',
            'style': {
                'label': 'data(label)',
                'background-color': style_config.get('background_color', '#e0e0e0'),
                'shape': style_config.get('shape', 'ellipse'),
                'width': style_config.get('width', 60),
                'height': style_config.get('height', 60),
                'text-valign': 'center',
                'text-halign': 'center',
                'font-size': '10px',
                'color': '#333'
            }
        }
        
        # アイコン設定があれば追加
        if 'icon' in style_config:
            icon_config = style_config['icon']
            if 'svg_base64' in icon_config:
                node_style['style'].update({
                    'background-image': f'data:image/svg+xml;base64,{icon_config["svg_base64"]}',
                    'background-fit': 'contain',
                    'background-image-opacity': icon_config.get('opacity', 0.7),
                    'text-valign': 'bottom',
                    'text-margin-y': 5
                })
        
        return node_style
    
    def _add_edge_styles(self, stylesheet: List[Dict[str, Any]]) -> None:
        """
        エッジスタイルを追加する.
        
        Args:
            stylesheet (List[Dict[str, Any]]): スタイルシートリスト（変更される）
        """
        # デフォルトエッジスタイル
        default_edge_style = {
            'selector': 'edge',
            'style': {
                'curve-style': 'bezier',
                'width': 2,
                'line-color': '#999',
                'target-arrow-color': '#999',
                'label': 'data(label)',
                'font-size': '8px',
                'text-rotation': 'autorotate'
            }
        }
        stylesheet.append(default_edge_style)
        
        return stylesheet
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """
        新しい設定ファイルを読み込む.
        
        Args:
            config_path (str): 設定ファイルのパス
            
        Returns:
            Dict[str, Any]: 読み込まれた設定データ
        """
        self.config_path = config_path
        self.config = self._load_config()
        return self.config
    
    def load_graphml(self, graphml_path: str) -> nx.Graph:
        """
        GraphMLファイルを読み込む.
        
        Args:
            graphml_path (str): GraphMLファイルのパス
            
        Returns:
            nx.Graph: NetworkXグラフオブジェクト
        """
        if not os.path.exists(graphml_path):
            raise FileNotFoundError(f"GraphMLファイルが見つかりません: {graphml_path}")
        
        try:
            self.graph = nx.read_graphml(graphml_path)
            return self.graph
        except nx.NetworkXError as e:
            raise ValueError(f"GraphMLファイルの形式が無効です: {e}")
    
    def load_csv(self, csv_path: str) -> pd.DataFrame:
        """
        CSVファイルを読み込む.
        
        Args:
            csv_path (str): CSVファイルのパス
            
        Returns:
            pd.DataFrame: 読み込まれたDataFrame
        """
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSVファイルが見つかりません: {csv_path}")
        
        try:
            self.table_df = pd.read_csv(csv_path, encoding='utf-8')
            return self.table_df
        except Exception as e:
            raise ValueError(f"CSVファイルの読み込みに失敗しました: {e}")
    
    def validate_files(self, graphml_path: str = None, csv_path: str = None) -> bool:
        """
        ファイルの存在と形式を検証する.
        
        Args:
            graphml_path (str, optional): GraphMLファイルのパス
            csv_path (str, optional): CSVファイルのパス
            
        Returns:
            bool: すべてのファイルが有効な場合True
        """
        try:
            if graphml_path:
                if not os.path.exists(graphml_path):
                    return False
            
            if csv_path:
                if not os.path.exists(csv_path):
                    return False
            
            return True
        except Exception:
            return False
    
    def generate_cytoscape_data(self) -> Dict[str, Any]:
        """
        Cytoscape用のデータを生成する.
        
        Returns:
            Dict[str, Any]: Cytoscapeデータ（nodes, edges, stylesheet）
        """
        if self.graph is None:
            return {'nodes': [], 'edges': [], 'stylesheet': []}
        
        nodes = self._convert_nodes_to_cytoscapes()
        edges = self._convert_edges_to_cytoscape()
        stylesheet = self._generate_stylesheet()
        
        return {
            'nodes': nodes,
            'edges': edges,
            'stylesheet': stylesheet
        }
    
    def get_table_data(self) -> List[Dict[str, Any]]:
        """CSVからテーブル用のデータを生成"""
        if self.table_df is None:
            return []
        
        # DataFrameを辞書のリストに変換
        return self.table_df.to_dict('records')
    
    def get_table_columns(self) -> List[Dict[str, str]]:
        """CSVのカラム情報からテーブルカラムを動的生成"""
        if self.table_df is None:
            return []
        
        columns = []
        for col in self.table_df.columns:
            # カラム表示名の設定（設定ファイルにマッピングがあれば使用）
            column_mapping = self.config.get('table', {}).get('column_mapping', {})
            display_name = column_mapping.get(col, col)
            
            columns.append({
                'name': display_name,
                'id': col
            })
        
        return columns
    
    def get_table_config(self) -> Dict[str, Any]:
        """テーブルの設定を取得"""
        base_config = self.config.get('table', {})
        
        # 動的にカラム情報を追加
        return {
            'columns': self.get_table_columns(),
            'style': base_config.get('style', {
                'cell': {'textAlign': 'center'},
                'header': {'fontWeight': 'bold'}
            })
        }
    
    def get_layout_config(self) -> Dict[str, Any]:
        """レイアウト設定を取得"""
        return self.config.get('layout', {})
    
    def filter_table_by_node(self, node_id: str, original_data: List[Dict]) -> List[Dict]:
        """ノードIDに基づいてテーブルをフィルタリング"""
        if not original_data:
            return []
        
        # 設定からフィルタリング対象のカラムを取得
        filter_columns = self.config.get('table', {}).get('filter_columns', [])
        
        if not filter_columns:
            # デフォルトで 'source', 'target' カラムを探す
            first_row = original_data[0]
            potential_columns = ['source', 'target', 'from', 'to', 'sender', 'receiver']
            filter_columns = [col for col in potential_columns if col in first_row]
        
        if not filter_columns:
            return original_data
        
        # フィルタリング実行
        filtered_data = []
        for row in original_data:
            for col in filter_columns:
                if col in row and str(row[col]) == str(node_id):
                    filtered_data.append(row)
                    break
        
        return filtered_data if filtered_data else original_data
    
    def get_grouped_layout_config(self) -> Dict[str, Any]:
        """ノードタイプ別グループ化レイアウト設定を生成（Interface/Processer/Storage）"""
        if self.graph is None:
            return {'name': 'cose'}
        
        # ノードをタイプ別に分類
        interface_nodes = []
        processer_nodes = []
        storage_nodes = []
        other_nodes = []
        
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            node_type = node_data.get('type', node_data.get('category', 'default'))
            
            if node_type.lower() == 'interface':
                interface_nodes.append(str(node_id))
            elif node_type.lower() == 'processer':
                processer_nodes.append(str(node_id))
            elif node_type.lower() == 'storage':
                storage_nodes.append(str(node_id))
            else:
                other_nodes.append(str(node_id))
        
        # プリセット位置を計算
        preset_positions = {}
        
        # Interfaceノード（左側に整列配置）
        interface_count = len(interface_nodes)
        if interface_count > 0:
            interface_spacing = min(150, 600 / max(1, interface_count - 1)) if interface_count > 1 else 150
            start_y = -(interface_count - 1) * interface_spacing / 2
            
            for i, node_id in enumerate(interface_nodes):
                y_pos = start_y + i * interface_spacing
                preset_positions[node_id] = {'x': -300, 'y': y_pos}
        
        # Processerノード（中央に配置）
        processer_count = len(processer_nodes)
        if processer_count > 0:
            processer_spacing = min(150, 600 / max(1, processer_count - 1)) if processer_count > 1 else 150
            start_y = -(processer_count - 1) * processer_spacing / 2
            
            for i, node_id in enumerate(processer_nodes):
                y_pos = start_y + i * processer_spacing
                preset_positions[node_id] = {'x': 0, 'y': y_pos}
        
        # Storageノード（右側に整列配置）
        storage_count = len(storage_nodes)
        if storage_count > 0:
            storage_spacing = min(150, 600 / max(1, storage_count - 1)) if storage_count > 1 else 150
            start_y = -(storage_count - 1) * storage_spacing / 2
            
            for i, node_id in enumerate(storage_nodes):
                y_pos = start_y + i * storage_spacing
                preset_positions[node_id] = {'x': 300, 'y': y_pos}
        
        # その他のノード（上部に配置）
        other_count = len(other_nodes)
        if other_count > 0:
            other_spacing = min(120, 400 / max(1, other_count - 1)) if other_count > 1 else 120
            start_x = -(other_count - 1) * other_spacing / 2
            
            for i, node_id in enumerate(other_nodes):
                x_pos = start_x + i * other_spacing
                preset_positions[node_id] = {'x': x_pos, 'y': -200}
        
        # プリセットレイアウト設定
        layout_config = {
            'name': 'preset',
            'positions': preset_positions,
            'fit': True,
            'padding': 100,
            'animate': True,
            'animationDuration': 1500,
            'animationEasing': 'ease-in-out'
        }
        
        print(f"📋 3層グループ化レイアウト:")
        print(f"  Interface={len(interface_nodes)} (左側)")
        print(f"  Processer={len(processer_nodes)} (中央)")
        print(f"  Storage={len(storage_nodes)} (右側)")
        print(f"  Other={len(other_nodes)} (上部)")
        
        for node_type, nodes in [('Interface', interface_nodes), ('Processer', processer_nodes), ('Storage', storage_nodes), ('Other', other_nodes)]:
            if nodes:
                print(f"    {node_type}: {', '.join(nodes)}")
        
        return layout_config


class GraphStyleManager:
    """グラフのスタイル管理クラス（拡張版）"""
    
    def __init__(self, base_stylesheet: List[Dict[str, Any]]):
        self.base_stylesheet = base_stylesheet
    
    def get_base_stylesheet(self) -> List[Dict[str, Any]]:
        """ベーススタイルシートを取得"""
        return self.base_stylesheet.copy()
    
    def add_node_highlight(self, node_id: str, color: str = 'red', width: int = 4) -> List[Dict[str, Any]]:
        """ノードハイライトスタイルを追加"""
        highlight_style = {
            'selector': f'node[id = "{node_id}"]',
            'style': {'border-width': width, 'border-color': color}
        }
        return self.base_stylesheet + [highlight_style]
    
    def add_edge_highlight(self, source: str, target: str, color: str = 'orange') -> List[Dict[str, Any]]:
        """エッジハイライトスタイルを追加"""
        highlight_styles = [
            {'selector': f'node[id = "{source}"]', 'style': {'border-width': 4, 'border-color': color}},
            {'selector': f'node[id = "{target}"]', 'style': {'border-width': 4, 'border-color': color}},
            {'selector': f'edge[source = "{source}"][target = "{target}"]', 
             'style': {'line-color': color, 'target-arrow-color': color}}
        ]
        return self.base_stylesheet + highlight_styles
    
    def get_directed_stylesheet(self) -> List[Dict[str, Any]]:
        """有向・無向エッジのスタイルシートを取得"""
        directed_styles = [
            # 無向エッジのスタイル（矢印なし）
            {
                'selector': 'edge.undirected',
                'style': {
                    'target-arrow-shape': 'none',
                    'source-arrow-shape': 'none',
                    'line-style': 'solid',
                    'line-color': '#666',
                    'width': 2
                }
            },
            # 有向エッジのスタイル（矢印あり）
            {
                'selector': 'edge.directed',
                'style': {
                    'target-arrow-shape': 'triangle',
                    'target-arrow-color': '#e74c3c',
                    'line-color': '#e74c3c',
                    'width': 3,
                    'line-style': 'solid'
                }
            }
        ]
        return self.base_stylesheet + directed_styles