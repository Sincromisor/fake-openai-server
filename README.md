# fake-openai-server

OpenAI API 互換の embeddings サーバーと rerank サーバーを、
ローカル環境で提供する FastAPI ベースのプロジェクトです。

既定では次のモデルを利用します。

- Embeddings: [cl-nagoya/ruri-v3-310m](https://huggingface.co/cl-nagoya/ruri-v3-310m)
- Rerank: [cl-nagoya/ruri-v3-reranker-310m](https://huggingface.co/cl-nagoya/ruri-v3-reranker-310m)

このリポジトリは stateless です。
データベースは使わず、`docker compose` を正規の起動経路として扱います。

## 構成

主要なコードは `src/fake_openai_server/` 配下にあります。

- `src/fake_openai_server/app.py`
  - FastAPI アプリケーションファクトリ
- `src/fake_openai_server/asgi.py`
  - ASGI factory と CLI エントリポイント
- `src/fake_openai_server/config.py`
  - `pydantic-settings` ベースの型付き設定
- `src/fake_openai_server/api/routers/`
  - embeddings / rerank / health の各ルータ
- `src/fake_openai_server/services/`
  - モデル初期化と推論ロジック
- `src/fake_openai_server/schemas/`
  - request / response / error の pydantic スキーマ

## 必要なもの

- NVIDIA GPU を利用できる環境
- [uv](https://docs.astral.sh/uv/)
- `docker compose`

ローカル直接実行では、`sentencepiece` などのビルド依存が必要です。

```sh
sudo apt install \
  build-essential \
  cmake \
  pkg-config \
  libprotobuf-dev \
  libsentencepiece-dev
```

## 設定

`.env.example` をコピーして使います。

```sh
cp .env.example .env
```

利用する主な環境変数は次のとおりです。

```dotenv
EMBEDDINGS_MODEL_NAME=cl-nagoya/ruri-v3-310m
EMBEDDINGS_HOST=0.0.0.0
EMBEDDINGS_PORT=8081
EMBEDDINGS_LOG_LEVEL=INFO
EMBEDDINGS_LOG_JSON=true

RERANKER_MODEL_NAME=cl-nagoya/ruri-v3-reranker-310m
RERANKER_HOST=0.0.0.0
RERANKER_PORT=8082
RERANKER_LOG_LEVEL=INFO
RERANKER_LOG_JSON=true
```

設定値が不足または不正な場合、起動時に明示的に失敗します。

## Docker Compose で起動する

```sh
cp .env.example .env
docker compose build
docker compose up -d
```

Hugging Face のモデルキャッシュは `./volumes/hf-cache` に保持されます。

構成確認だけを行いたい場合は次を利用できます。

```sh
docker compose config
```

## ローカルで起動する

依存関係を同期します。

```sh
uv sync --group dev
```

embeddings サーバー:

```sh
uv run fake-openai-embeddings
```

reranker サーバー:

```sh
uv run fake-openai-reranker
```

## ヘルスチェック

両サービスとも次のエンドポイントを持ちます。

- `/health/live`
  - プロセスが応答可能かを返します
- `/health/ready`
  - モデル初期化が完了しているかを返します

## API

### Embeddings

エンドポイント:

```text
POST /v1/embeddings
```

サンプル:

```sh
curl -s http://127.0.0.1:8081/v1/embeddings \
  -H 'Content-Type: application/json' \
  --data-raw '{
    "model": "cl-nagoya/ruri-v3-310m",
    "input": [
      "文章: てきとうなテキストだよ。",
      "文章: てきとうなテキストです。"
    ]
  }'
```

### Rerank

エンドポイント:

```text
POST /v1/rerank
```

サンプル:

```sh
curl -s http://127.0.0.1:8082/v1/rerank \
  -H 'Content-Type: application/json' \
  --data-raw '{
    "model": "cl-nagoya/ruri-v3-reranker-310m",
    "query": "山形県の蔵王温泉にある「泉質」はなに？",
    "documents": [
      "蔵王温泉はどのような特徴を持つ温泉ですか？",
      "山形市の蔵王温泉はどのような温泉ですか？",
      "蔵王温泉の特徴は何ですか？"
    ]
  }'
```

### OpenAPI

FastAPI の OpenAPI は各サービスで利用できます。

- embeddings: `http://127.0.0.1:8081/openapi.json`
- reranker: `http://127.0.0.1:8082/openapi.json`

## 検証コマンド

このリポジトリでは `uv` を通じてコマンドを実行します。

```sh
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pytest
docker compose config
```

## Dify での利用例

Embeddings:

- Model Type: Text Embedding
- Model Name: `cl-nagoya/ruri-v3-310m`
- API Key: なし
- API endpoint URL: `http://<host>:8081/v1`

Rerank:

- Model Type: Rerank
- Model Name: `cl-nagoya/ruri-v3-reranker-310m`
- API Key: なし
- API endpoint URL: `http://<host>:8082/v1`
