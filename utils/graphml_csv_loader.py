"""
GraphMLとCSVファイルを読み込むための拡張ローダー
"""
import json
import pandas as pd
import networkx as nx
from typing import Dict, List, Any, Optional
import os


class GraphMLCSVConfigLoader:
    """GraphMLとCSVファイルを読み込み、設定を動的生成するクラス"""
    
    def __init__(self, config_path: str):
        """
        Args:
            config_path: 設定ファイルのパス（GraphMLとCSVのパスを含む）
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.graph = None
        self.table_df = None
        self._load_data_files()
    
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"設定ファイルが見つかりません: {self.config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"設定ファイルのJSONが無効です: {e}")
    
    def _load_data_files(self):
        """GraphMLとCSVファイルを読み込み"""
        # GraphMLファイルの読み込み
        graphml_path = self.config['data_sources']['graphml_file']
        if not os.path.isabs(graphml_path):
            # 相対パスの場合、カレントディレクトリからの相対パスとして解釈
            graphml_path = os.path.abspath(graphml_path)
        
        try:
            self.graph = nx.read_graphml(graphml_path)
            print(f"GraphMLファイルを読み込みました: {graphml_path}")
            print(f"ノード数: {len(self.graph.nodes)}, エッジ数: {len(self.graph.edges)}")
        except Exception as e:
            raise ValueError(f"GraphMLファイルの読み込みに失敗しました: {e}")
        
        # CSVファイルの読み込み
        csv_path = self.config['data_sources']['csv_file']
        if not os.path.isabs(csv_path):
            csv_path = os.path.abspath(csv_path)
        
        try:
            self.table_df = pd.read_csv(csv_path, encoding='utf-8')
            print(f"CSVファイルを読み込みました: {csv_path}")
            print(f"行数: {len(self.table_df)}, 列数: {len(self.table_df.columns)}")
            print(f"カラム: {list(self.table_df.columns)}")
        except Exception as e:
            raise ValueError(f"CSVファイルの読み込みに失敗しました: {e}")
    
    def get_cytoscape_elements(self) -> List[Dict[str, Any]]:
        """GraphMLからCytoscape用のelementsリストを生成"""
        if self.graph is None:
            return []
        
        # ノード要素を作成
        nodes = []
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            
            # ノードのlabelを取得（複数の候補から選択）
            label = node_data.get('label', node_data.get('name', str(node_id)))
            
            # ノードのtypeを取得（デフォルト値を設定）
            node_type = node_data.get('type', node_data.get('category', 'default'))
            
            nodes.append({
                'data': {
                    'id': str(node_id),
                    'label': str(label),
                    'Type': str(node_type)
                },
                'classes': f'type-{str(node_type).lower()}'
            })
        
        # エッジ要素を作成
        edges = []
        for source, target in self.graph.edges():
            edge_data = self.graph[source][target]
            
            # エッジのlabelを取得
            edge_label = edge_data.get('label', edge_data.get('name', f"{source}->{target}"))
            
            edges.append({
                'data': {
                    'source': str(source),
                    'target': str(target),
                    'label': str(edge_label)
                }
            })
        
        return nodes + edges
    
    def get_node_types(self) -> List[str]:
        """グラフから全ノードタイプを取得"""
        if self.graph is None:
            return []
        
        types = set()
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            node_type = node_data.get('type', node_data.get('category', 'default'))
            types.add(str(node_type))
        
        return sorted(list(types))
    
    def get_cytoscape_stylesheet(self) -> List[Dict[str, Any]]:
        """ノードタイプに基づいてスタイルシートを動的生成"""
        stylesheet = []
        
        # デフォルトノードスタイル
        default_style = self.config['layout']['default_node_style']
        stylesheet.append({
            'selector': 'node',
            'style': {
                'label': 'data(label)',
                'background-color': default_style['background_color'],
                'shape': default_style['shape'],
                'width': default_style['width'],
                'height': default_style['height'],
                'text-valign': 'center',
                'text-halign': 'center',
                'font-size': '10px',
                'color': '#333'
            }
        })
        
        # タイプ別スタイル定義
        type_styles = self.config.get('node_type_styles', {})
        node_types = self.get_node_types()
        
        for node_type in node_types:
            if node_type in type_styles:
                style_config = type_styles[node_type]
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
                
                stylesheet.append(node_style)
        
        # デフォルトエッジスタイル
        stylesheet.append({
            'selector': 'edge',
            'style': {
                'line-color': '#7FDBFF',
                'target-arrow-color': '#7FDBFF',
                'target-arrow-shape': 'triangle',
                'arrow-scale': 1.5,
                'curve-style': 'bezier',
                'label': 'data(label)',
                'font-size': '8px'
            }
        })
        
        return stylesheet
    
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