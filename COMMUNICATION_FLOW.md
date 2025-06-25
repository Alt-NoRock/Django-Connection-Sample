```
クライアント（ブラウザ）
│
├─ HTTP通信
│  ├─ 初回ページ読み込み (GET /)
│  ├─ 投稿作成フォーム送信 (POST /create/)
│  ├─ 投稿削除 (POST /delete/{id}/)
│  ├─ 静的ファイル取得 (GET /static/*)
│  └─ API呼び出し (GET /api/posts/)
│
└─ WebSocket通信
   ├─ 接続確立 (ws://localhost/ws/posts/)
   ├─ リアルタイム投稿更新受信
   ├─ ランダムメッセージ受信
   └─ 接続状態管理

Django + Channels サーバー
│
├─ HTTP ハンドラー (Django Views)
│  ├─ index(), create_post(), delete_post()
│  ├─ 静的ファイル配信
│  └─ REST API エンドポイント
│
└─ WebSocket ハンドラー (Channels Consumer)
   ├─ PostConsumer - リアルタイム通信
   ├─ チャンネルレイヤー (Redis)
   └─ バックグラウンドタスク (ランダムメッセージ)
```
