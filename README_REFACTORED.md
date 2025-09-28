# Django Connection Sample - リファクタリング版

このプロジェクトは、NetworkXとDash Cytoscapeを使用してインタラクティブな有向グラフとテーブルを表示するWebアプリケーションです。

## 🆕 リファクタリング後の特徴

### 1. 設定ファイルベースの設計
- **外部設定**: グラフの構造、スタイル、テーブル設定をJSONファイルで管理
- **柔軟性**: 設定ファイルを変更するだけで異なるグラフを表示可能
- **再利用性**: 同じコードで複数の異なるUIを作成可能

### 2. モジュール化されたアーキテクチャ
```
├── config/                    # 設定ファイル
│   ├── graph_config.json     # 元のハードウェア接続図
│   └── web_architecture_config.json  # Webアーキテクチャ図
├── utils/
│   └── graph_loader.py       # 設定読み込み・管理クラス
├── dash_refactored.py        # メインアプリケーション
└── app_launcher.py           # 設定選択ランチャー
```

### 3. 主要クラス

#### `GraphConfigLoader`
- JSON設定ファイルの読み込み
- NetworkXグラフの生成
- Cytoscapeスタイルシートの生成
- テーブルデータの生成

#### `GraphStyleManager`
- スタイルの動的管理
- ハイライト効果の適用
- ベーススタイルの管理

#### `DashGraphApp`
- Dashアプリケーションのカプセル化
- コールバック関数の管理
- レイアウトの自動生成

## 🚀 使用方法

### 1. 基本実行
```bash
# 元の設定でアプリを起動
python dash_refactored.py
```

### 2. 設定選択ランチャー
```bash
# 複数の設定から選択して起動
python app_launcher.py
```

### 3. カスタム設定での実行
```python
from dash_refactored import DashGraphApp

# カスタム設定ファイルを指定
app = DashGraphApp('path/to/your/config.json')
app.run()
```

## 📋 設定ファイル構造

```json
{
  "graph": {
    "nodes": [
      {
        "id": "NODE_ID",
        "label": "表示名",
        "type": "ノードタイプ",
        "icon": {
          "svg_base64": "Base64エンコードされたSVG",
          "opacity": 0.7
        },
        "style": {
          "background_color": "#4CAF50",
          "width": 80,
          "height": 80
        }
      }
    ],
    "edges": [
      {
        "source": "送信元ノードID",
        "target": "送信先ノードID",
        "label": "エッジラベル",
        "style": {
          "line_color": "#7FDBFF",
          "arrow_color": "#7FDBFF"
        }
      }
    ]
  },
  "table": {
    "columns": [...],
    "style": {...}
  },
  "layout": {...}
}
```

## 🎯 機能

### インタラクション機能
- **ノードクリック**: 関連するテーブル行をフィルタリング + ノードハイライト
- **テーブル行クリック**: 関連するノードとエッジをハイライト
- **ダブルクリック**: ハイライト解除
- **レイアウト再配置**: グラフの再配置ボタン

### スタイリング機能
- **SVGアイコン**: Base64エンコードされたSVGでノードアイコンを表示
- **カスタマイズ可能**: 色、サイズ、透明度などすべて設定ファイルで制御
- **レスポンシブ**: 異なる画面サイズに対応

## 🔧 拡張性

### 新しい設定ファイルの追加
1. `config/` ディレクトリに新しいJSONファイルを作成
2. 必要なnode、edge、table、layout情報を定義
3. `app_launcher.py` で自動的に選択肢に表示

### カスタムスタイルの追加
1. `GraphStyleManager` クラスを拡張
2. 新しいハイライト効果やアニメーションを追加
3. 設定ファイルに新しいスタイルオプションを追加

### 新機能の追加
1. `DashGraphApp` クラスにコールバック関数を追加
2. 必要に応じて設定ファイル構造を拡張
3. `GraphConfigLoader` に新しい設定読み込み機能を追加

## 🎨 利用可能な設定例

### 1. `graph_config.json`
- ハードウェア接続図（WIFI、JTAG、CPU、HDD）
- Interface/Device分類
- 技術系アイコン

### 2. `web_architecture_config.json`
- Webアーキテクチャ図（Client、API Gateway、Web Server、Database）
- サーバー系アイコン
- breadthfirstレイアウト

## 📝 今後の拡張予定

- [ ] 設定ファイルのバリデーション機能
- [ ] リアルタイムデータ連携
- [ ] エクスポート機能（PNG、PDF）
- [ ] アニメーション効果の追加
- [ ] 多言語対応
- [ ] テーマシステム

## 🛠️ 開発者向け情報

### 依存関係
```
dash>=3.0.0
dash-cytoscape
dash-table
networkx
```

### テスト実行
```bash
# 基本テスト
python -m pytest tests/

# 設定ファイルのバリデーションテスト
python utils/graph_loader.py
```