"""
グラフ設定を読み込むためのユーティリティクラス
"""
import json
import networkx as nx
from typing import Dict, List, Any, Tuple


class GraphConfigLoader:
    """グラフ設定を外部ファイルから読み込むクラス"""
    
    def __init__(self, config_path: str):
        """
        Args:
            config_path: 設定ファイルのパス
        """
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"設定ファイルが見つかりません: {self.config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"設定ファイルのJSONが無効です: {e}")
    
    def create_networkx_graph(self) -> nx.DiGraph:
        """NetworkXのDiGraphを作成"""
        G = nx.DiGraph()
        
        # ノードを追加
        for node_config in self.config['graph']['nodes']:
            G.add_node(
                node_config['id'],
                Type=node_config['type'],
                label=node_config['label'],
                icon=node_config.get('icon', {}),
                style=node_config.get('style', {})
            )
        
        # エッジを追加
        for edge_config in self.config['graph']['edges']:
            G.add_edge(
                edge_config['source'],
                edge_config['target'],
                edge_name=edge_config['label'],
                style=edge_config.get('style', {})
            )
        
        return G
    
    def get_cytoscape_elements(self) -> List[Dict[str, Any]]:
        """Cytoscape用のelementsリストを生成"""
        G = self.create_networkx_graph()
        
        # ノード要素を作成
        nodes = [
            {
                'data': {
                    'id': node,
                    'label': G.nodes[node]['label'],
                    'Type': G.nodes[node]['Type']
                },
                'classes': f'type-{G.nodes[node]["Type"].lower()}'
            } for node in G.nodes()
        ]
        
        # エッジ要素を作成
        edges = [
            {
                'data': {
                    'source': u,
                    'target': v,
                    'label': G[u][v]['edge_name']
                }
            } for u, v in G.edges()
        ]
        
        return nodes + edges
    
    def get_cytoscape_stylesheet(self) -> List[Dict[str, Any]]:
        """Cytoscape用のスタイルシートを生成"""
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
                'text-valign': 'bottom',
                'text-margin-y': -5
            }
        })
        
        # 個別ノードスタイル
        for node_config in self.config['graph']['nodes']:
            node_style = {
                'selector': f'node[id = "{node_config["id"]}"]',
                'style': {
                    'label': 'data(label)',
                    'background-color': node_config['style']['background_color'],
                    'shape': 'ellipse',
                    'width': node_config['style']['width'],
                    'height': node_config['style']['height'],
                    'text-valign': 'bottom',
                    'text-margin-y': 5,
                    'color': '#333',
                    'font-size': '12px'
                }
            }
            
            # アイコン設定があれば追加
            if 'icon' in node_config and 'svg_base64' in node_config['icon']:
                node_style['style'].update({
                    'background-image': f'data:image/svg+xml;base64,{node_config["icon"]["svg_base64"]}',
                    'background-fit': 'contain',
                    'background-image-opacity': node_config['icon']['opacity']
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
                'label': 'data(label)'
            }
        })
        
        return stylesheet
    
    def get_table_data(self) -> List[Dict[str, str]]:
        """テーブル用のデータを生成"""
        G = self.create_networkx_graph()
        return [
            {
                'source': u,
                'target': v,
                'edge': G[u][v]['edge_name']
            } for u, v in G.edges()
        ]
    
    def get_table_config(self) -> Dict[str, Any]:
        """テーブルの設定を取得"""
        return self.config['table']
    
    def get_layout_config(self) -> Dict[str, Any]:
        """レイアウト設定を取得"""
        return self.config['layout']


class GraphStyleManager:
    """グラフのスタイル管理クラス"""
    
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