[日本語](README.ja.md) | [English](README.md)

# Matrix Webhook アプリケーションサービス

このリポジトリには、Matrix ルームにメッセージを送信するための Webhook 機能を提供する Matrix アプリケーションサービスが含まれています。外部サービスから簡単な HTTP POST リクエストを使用して Matrix ルームにメッセージを送信することができます。

---

## 目次

1. [前提条件](#前提条件)
2. [初期設定](#初期設定)
3. [設定](#設定)
4. [サービスの実行](#サービスの実行)
5. [使用例](#使用例)

---

## 前提条件

- Docker & Docker Compose (v3.8+)
- 稼働中の Matrix ホームサーバー（Synapse）
- Python 3.8+（Docker を使用しない場合）

---

## 初期設定

1. このリポジトリをクローンします
2. アプリケーションサービスの設定ファイル `webhook_as.yaml` は matrix-server ディレクトリにあります。以下のように設定します：

   ```yaml
   # 設定例
   hs_token: "random_secret_token" # ホームサーバーがASを認証するためのトークン
   as_token: "another_random_token" # ASがホームサーバーを認証するためのトークン
   url: "http://localhost:9000" # このサービスが実行されるURL
   sender_localpart: "webhook" # ASボットのユーザーIDローカルパート
   namespaces:
     users: []
     aliases: []
     rooms: []
   ```

---

## 設定

サービスは環境変数または `docker-compose.yml` ファイルで直接設定できます：

```yaml
environment:
  - MATRIX_HOMESERVER_URL=http://synapse:8008
  - MATRIX_USER_ID=@webhook:example.com
  - AS_TOKEN=another_random_token
  - HS_TOKEN=random_secret_token
  - PORT=9000
```

---

## サービスの実行

### Docker Compose を使用（推奨）

デタッチドモードでサービスを起動します：

```bash
docker-compose up -d
```

### Docker を使用しない場合

1. 依存関係をインストールします：

   ```bash
   pip install -r requirements.txt
   ```

2. サービスを実行します：
   ```bash
   python main.py
   ```

サービスはデフォルトでポート 9000 でリッスンします。

---

## 使用例

### メッセージの送信

curl を使用してルームにメッセージを送信します：

```bash
curl -XPOST http://localhost:9000/webhook \
     -H 'Content-Type: application/json' \
     -d '{"text":"Webhook via AS works test!","channel":"#test:localhost"}'
```

成功時のレスポンス：

```json
{
  "ok": true,
  "event_id": "$VLnAIICMyUu8m39dA6lftWHz11B-WJzsRUtNuYg5mjQ"
}
```

### メッセージフォーマットオプション

異なるフォーマットでメッセージを送信できます：

```bash
# HTMLフォーマットのメッセージ
curl -XPOST http://localhost:9000/webhook \
     -H 'Content-Type: application/json' \
     -d '{
           "text": "<b>太字のテキスト</b>と<i>斜体のテキスト</i>",
           "channel": "#test:localhost",
           "format": "html"
         }'

# メンション付きのプレーンテキスト
curl -XPOST http://localhost:9000/webhook \
     -H 'Content-Type: application/json' \
     -d '{
           "text": "こんにちは @user:example.com、これを確認してください！",
           "channel": "#test:localhost"
         }'
```

---

## エラーハンドリング

サービスは適切な HTTP ステータスコードと JSON レスポンスを返します：

- 200: メッセージ送信成功
- 400: リクエストフォーマットが無効
- 401: 認証失敗
- 404: ルームが見つからない
- 500: 内部サーバーエラー

エラーレスポンスの例：

```json
{
  "ok": false,
  "error": "ルームが見つかりません"
}
```
