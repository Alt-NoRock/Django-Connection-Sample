# GraphML/CSV対応版 - Django Connection Sample

## 🆕 新機能: GraphMLとCSVファイル対応

### 概要
従来のJSON設定に加えて、**GraphMLファイル**（グラフ構造）と**CSVファイル**（テーブルデータ）から直接データを読み込めるようになりました。

### 🎯 主な改善点

1. **GraphMLファイル対応**
   - NetworkXで標準的なGraphML形式をサポート
   - ノードとエッジの属性を自動読み込み
   - 外部ツールで作成したグラフデータを直接利用可能

2. **CSVファイル対応**
   - 任意のCSVファイルをテーブルデータとして読み込み
   - **カラムの動的対応**: CSVのカラム構成に自動的に適応
   - カラム名の日本語表示マッピング対応

3. **柔軟な設定システム**
   - ノードタイプ別のスタイル定義
   - フィルタリング対象カラムの指定
   - レイアウトアルゴリズムの選択

## 📁 ファイル構造

```
├── config/
│   ├── graphml_csv_config.json      # GraphML/CSV用設定
│   ├── graph_config.json           # 従来のJSON設定
│   └── web_architecture_config.json # Web構成例
├── data/
│   ├── sample_graph.graphml        # サンプルグラフデータ
│   └── sample_table.csv           # サンプルテーブルデータ
├── utils/
│   ├── graph_loader.py             # 従来のJSONローダー
│   └── graphml_csv_loader.py       # GraphML/CSVローダー
├── dash_graphml_csv.py             # GraphML/CSV対応アプリ
├── dash_refactored.py              # 従来のJSONアプリ
└── unified_launcher.py             # 統合ランチャー
```

## 🚀 使用方法

### 1. 統合ランチャーで起動
```bash
python unified_launcher.py
```
設定ファイルを自動検出し、形式に応じて適切なアプリを起動します。

### 2. 直接起動
```bash
# GraphML/CSV対応版
python dash_graphml_csv.py

# 従来のJSON版
python dash_refactored.py
```

## 📊 GraphML/CSV設定ファイル形式

```json
{
  "data_sources": {
    "graphml_file": "data/sample_graph.graphml",
    "csv_file": "data/sample_table.csv"
  },
  "node_type_styles": {
    "Interface": {
      "background_color": "#4CAF50",
      "width": 80,
      "height": 80,
      "icon": { "svg_base64": "...", "opacity": 0.7 }
    },
    "Device": {
      "background_color": "#FF9800",
      "width": 80,
      "height": 80
    }
  },
  "table": {
    "column_mapping": {
      "source": "送信元",
      "target": "送信先",
      "edge": "接続"
    },
    "filter_columns": ["source", "target"]
  }
}
```

## 📋 GraphMLファイル例

```xml
<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="label" for="node" attr.name="label" attr.type="string"/>
  <key id="type" for="node" attr.name="type" attr.type="string"/>
  
  <graph edgedefault="directed">
    <node id="WIFI">
      <data key="label">WIFI Interface</data>
      <data key="type">Interface</data>
    </node>
    
    <edge source="WIFI" target="CPU">
      <data key="label">無線通信</data>
    </edge>
  </graph>
</graphml>
```

## 📈 CSVファイル例

```csv
source,target,edge,type,description,bandwidth
WIFI,CPU,無線通信,Interface-Device,WiFi経由でのCPUへの通信,100Mbps
CPU,HDD,データ読み書き,Device-Device,ストレージへのデータアクセス,6Gbps
```

## 🎨 特徴

### 動的カラム対応
- CSVファイルのカラム構成に自動適応
- カラム名の日本語マッピング
- フィルタリング対象カラムの柔軟な指定

### ノードタイプ別スタイリング
- GraphMLのtype属性に基づく自動スタイリング
- SVGアイコンサポート
- カスタムカラーとサイズ設定

### インタラクション機能
- **ノードクリック**: 関連テーブル行をフィルタリング
- **テーブル行クリック**: 関連ノードとエッジをハイライト
- **ダブルクリック**: ハイライト解除
- **動的レイアウト**: グラフ再配置機能

## 🔧 カスタマイズ方法

### 1. 新しいGraphMLファイルを追加
```bash
# 1. GraphMLファイルを data/ に配置
# 2. 対応するCSVファイルを data/ に配置
# 3. config/ に設定ファイルを作成
# 4. unified_launcher.py で自動認識
```

### 2. ノードタイプのスタイル追加
```json
"node_type_styles": {
  "YourNewType": {
    "background_color": "#YOUR_COLOR",
    "width": 90,
    "height": 90,
    "icon": {
      "svg_base64": "YOUR_BASE64_SVG",
      "opacity": 0.8
    }
  }
}
```

### 3. CSVカラムマッピング
```json
"table": {
  "column_mapping": {
    "original_column": "表示名",
    "bandwidth": "帯域幅",
    "protocol": "プロトコル"
  }
}
```

## 📦 依存関係

```
pandas          # CSV読み込み
networkx        # GraphML読み込み
dash>=3.0.0     # Webアプリケーション
dash-cytoscape  # グラフ可視化
```

## 🎯 対応データ形式

| 形式 | グラフデータ | テーブルデータ | 設定方法 |
|------|-------------|---------------|----------|
| JSON | JSON内に定義 | JSON内に定義 | 全て設定ファイル内 |
| GraphML/CSV | GraphMLファイル | CSVファイル | 設定ファイル + データファイル |

## 🚧 今後の拡張予定

- [ ] Excel形式のサポート
- [ ] 複数CSVファイルの結合
- [ ] GraphMLの複雑な属性サポート
- [ ] リアルタイムデータ更新
- [ ] 設定ファイルのGUI編集機能