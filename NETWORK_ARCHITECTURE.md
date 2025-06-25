# Django WebSocket アプリケーション ネットワークアーキテクチャ図

## 🏗️ 全体アーキテクチャ図

```
                    ┌─────────────────────────────────────────────────────────────┐
                    │                    Internet                                 │
                    └─────────────────────────────────────────────────────────────┘
                                                │
                                          HTTPS/WSS
                                        (Port 443/80)
                                                │
                    ┌─────────────────────────────────────────────────────────────┐
                    │                AWS Application Load Balancer (ALB)          │
                    │                                                             │
                    │  ┌─────────────────┐    ┌──────────────────────────────┐   │
                    │  │  SSL Termination │    │    リスナールール              │   │
                    │  │  - HTTPS → HTTP │    │  - WebSocket: /ws/*         │   │
                    │  │  - WSS → WS     │    │  - Health: /health/*        │   │
                    │  └─────────────────┘    │  - Default: /*              │   │
                    │                         └──────────────────────────────┘   │
                    └─────────────────────────────────────────────────────────────┘
                                                │
                                        HTTP/WebSocket
                                          (Port 80)
                                                │
                    ┌─────────────────────────────────────────────────────────────┐
                    │                   EC2 Instance                              │
                    │                                                             │
                    │  ┌─────────────────────────────────────────────────────┐   │
                    │  │               Docker Environment                    │   │
                    │  │                                                     │   │
                    │  │  ┌─────────┐   ┌────────────────┐   ┌───────────┐  │   │
                    │  │  │  Nginx  │   │  Django+Daphne │   │   Redis   │  │   │
                    │  │  │Port: 80 │───│   Port: 8000   │───│Port: 6379 │  │   │
                    │  │  │         │   │                │   │           │  │   │
                    │  │  │ Proxy   │   │  ASGI Server   │   │ Channel   │  │   │
                    │  │  │ Static  │   │  WebSocket     │   │ Layer     │  │   │
                    │  │  └─────────┘   │  HTTP          │   └───────────┘  │   │
                    │  │                │                │                  │   │
                    │  │                └────────────────┘                  │   │
                    │  │                        │                           │   │
                    │  │                ┌───────────────┐                   │   │
                    │  │                │  PostgreSQL   │                   │   │
                    │  │                │  Port: 5432   │                   │   │
                    │  │                │               │                   │   │
                    │  │                │   Database    │                   │   │
                    │  │                └───────────────┘                   │   │
                    │  └─────────────────────────────────────────────────────┘   │
                    └─────────────────────────────────────────────────────────────┘
```

## 🔗 通信フロー詳細

### 1. HTTP リクエストフロー

```
Client Browser
      │
      │ 1. HTTPS Request
      ▼
Application Load Balancer
      │
      │ 2. HTTP Request (SSL終端)
      ▼
EC2 Instance → Nginx (Port 80)
      │
      │ 3. Proxy Pass
      ▼
Django + Daphne (Port 8000)
      │
      │ 4. Database Query
      ▼
PostgreSQL (Port 5432)
```

### 2. WebSocket 接続フロー

```
Client Browser
      │
      │ 1. WSS Connection
      ▼
Application Load Balancer
      │ Sticky Session 有効
      │ 2. WebSocket Upgrade
      ▼
EC2 Instance → Nginx (Port 80)
      │
      │ 3. WebSocket Proxy
      ▼
Django + Daphne (Port 8000)
      │
      │ 4. Channel Layer
      ▼
Redis (Port 6379)
```

## 🌐 ポート構成

| コンポーネント | 内部ポート | 外部公開 | 用途 |
|------------|----------|---------|------|
| ALB | - | 80, 443 | エントリーポイント |
| Nginx | 80 | × | リバースプロキシ |
| Django+Daphne | 8000 | × | アプリケーションサーバー |
| PostgreSQL | 5432 | × | データベース |
| Redis | 6379 | × | WebSocketチャンネル |

## 🔒 セキュリティグループ設定

### ALB セキュリティグループ
```
Inbound Rules:
- HTTP (80) ← 0.0.0.0/0
- HTTPS (443) ← 0.0.0.0/0

Outbound Rules:
- HTTP (80) → EC2 Security Group
```

### EC2 セキュリティグループ
```
Inbound Rules:
- HTTP (80) ← ALB Security Group
- SSH (22) ← 管理者IP/32 (必要時のみ)

Outbound Rules:
- ALL → 0.0.0.0/0 (外部API、パッケージダウンロード用)
```

## 📡 ALB リスナールール

### Priority 100: WebSocket トラフィック
```yaml
条件:
  - Path: /ws/*
  - Header: Connection=upgrade
アクション:
  - Target Group: django-websocket-main-tg
  - Sticky Session: 有効 (24時間)
```

### Priority 200: ヘルスチェック
```yaml
条件:
  - Path: /health/*
アクション:
  - Target Group: django-websocket-health-tg
  - Port: 8000 (直接Daphne)
```

### Priority 300: デフォルト (HTTP)
```yaml
条件:
  - Default
アクション:
  - Target Group: django-websocket-main-tg
  - Port: 80 (Nginx経由)
```

## 🔄 データフロー

### 投稿作成時のリアルタイム更新

```
User A (Browser)
      │
      │ 1. POST /create/
      ▼
ALB → Nginx → Django
      │
      │ 2. DB Insert
      ▼
PostgreSQL
      │
      │ 3. Channel Send
      ▼
Redis Channel Layer
      │
      │ 4. WebSocket Broadcast
      ▼
All Connected Clients
(User A, User B, User C...)
```

### ランダムメッセージ配信

```
Background Task (Django)
      │
      │ 1. Generate Random Message
      │    (5-20秒間隔)
      ▼
Redis Channel Layer
      │
      │ 2. Channel Send
      ▼
WebSocket Consumers
      │
      │ 3. Broadcast to Clients
      ▼
All Connected Browsers
```

## 🚀 スケーリング構成 (Auto Scaling)

```
                         Internet
                             │
                    ┌────────────────┐
                    │      ALB       │
                    └────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
         ┌─────────┐   ┌─────────┐   ┌─────────┐
         │  EC2-1  │   │  EC2-2  │   │  EC2-3  │
         │         │   │         │   │         │
         │ Django  │   │ Django  │   │ Django  │
         │ Redis   │   │ Redis   │   │ Redis   │
         └─────────┘   └─────────┘   └─────────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
                    ┌────────────────┐
                    │   RDS (共有)   │
                    │   PostgreSQL   │
                    └────────────────┘
```

**注意**: Redis は各EC2で個別実行。本格的なスケーリングには Redis Cluster または ElastiCache が必要。

## 📊 監視ポイント

### ヘルスチェック
- **ALB → EC2**: `/health/` エンドポイント
- **間隔**: 30秒
- **タイムアウト**: 5秒
- **正常判定**: 2回連続成功
- **異常判定**: 2回連続失敗

### メトリクス監視
- **EC2**: CPU使用率、メモリ使用率
- **ALB**: レスポンス時間、エラー率
- **WebSocket**: 接続数、メッセージ配信数
- **Redis**: メモリ使用率、接続数

## 🔧 設定ファイル対応

| ファイル | 役割 |
|---------|------|
| `nginx.conf` | ALB → Nginx プロキシ設定 |
| `docker-compose.yml` | ローカル開発環境 |
| `docker-compose.aws.yml` | AWS本番環境 |
| `alb-target-group.tf` | Terraform ALB設定 |
| `settings.py` | Django ASGI/Channel設定 |

この構成により、HTTP/HTTPS の通常リクエストと WebSocket 通信の両方を効率的に処理し、ALB のロードバランシングとスティッキーセッションによって高可用性を実現しています。
