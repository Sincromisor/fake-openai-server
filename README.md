# fake-open-ai-server

OpenAI API互換のText embeddingsサーバーと、
Rerankサーバーをローカルで提供します。

[Dify](https://dify.ai/)で日本語の処理をおこないたい際に、
OpenAI-API-compatibleモデルプロバイダーでこれを指定します。

デフォルトでは次のモデルを利用します。

- Text embedding: [cl-nagoya/ruri-v3-310m](https://huggingface.co/cl-nagoya/ruri-v3-310m)
- Rerank: [cl-nagoya/ruri-v3-reranker-310m](https://huggingface.co/cl-nagoya/ruri-v3-reranker-310m)

`.env` で利用モデルを切り替えられます。`docker compose` とローカル直接実行のどちらでも同じ設定を使えます。

```sh
$ cp .env.example .env
```

```dotenv
EMBEDDINGS_MODEL_NAME=cl-nagoya/ruri-v3-310m
RERANKER_MODEL_NAME=cl-nagoya/ruri-v3-reranker-310m
```

## 必要なもの

- [sentence-transformers](https://sbert.net/)が利用できる環境
  - Text embeddings: GPU VRAM1.5GB程度
  - Rerank: GPU VRAM1.5GB程度


## Docker Composeで実行する場合

buildしてupするだけです。

```sh
$ cp .env.example .env
$ docker compose build
$ docker compose up -d
```
モデルのキャッシュはホストの`volumes`ディレクトリに保持されます。


## Dockerなしで実行したい場合
### パッケージのインストール

```sh
$ sudo apt install \
       build-essential \
       cmake pkg-config \
       libprotobuf-dev \
       libsentencepiece-dev
```


### Pythonライブラリのインストール
ライブラリの管理は[uv](https://github.com/astral-sh/uv)を用います。

```sh
$ uv sync
```


## つかいかた(Text embeddings)

### Text embeddingサーバーの起動

```sh
$ cp .env.example .env
$ uv run uvicorn embeddings-api-server:app --host 0.0.0.0 --port 8081
```

Docker Composeの場合は不要です。


### Text embeddingサーバーの動作テスト

```sh
$ curl -v http://127.0.0.1:8081/v1/embeddings -H 'Content-Type: application/json' --data-raw '
{
    "model": "cl-nagoya/ruri-v3-310m",
    "input": [
        "文章: てきとうなテキストだよ。",
        "文章: てきとうなテキストです。"
    ]
}'
```

```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "embedding": [
        0.8186585903167725,
        -0.47749972343444824,
        -0.34532251954078674,
        ...
        0.15132111310958862,
        -0.34593141078948975,
        -0.6007830500602722
      ],
      "index": 0
    },
    {
      "object": "embedding",
      "embedding": [
        0.958991289138794,
        -0.322582870721817,
        -0.35985010862350464,
        ...
        0.21222521364688873,
        -0.33821913599967957,
        -0.6487450003623962
      ],
      "index": 1
    }
  ],
  "model": "cl-nagoya/ruri-v3-310m",
  "usage": {
    "prompt_tokens": 0,
    "total_tokens": 0
  }
}
```


### Difyでの設定

- Model Type: Text Embedding
- Model Name: cl-nagoya/ruri-v3-310m
- API Key: なし
- API endpoint URL: http://サーバーのホスト名・IPアドレス:8081/v1
- Model context size: 512


## つかいかた(Rerank)

### Rerankサーバーの起動

```sh
$ cp .env.example .env
$ uv run uvicorn reranker-api-server:app --host 0.0.0.0 --port 8082
```

Docker Composeの場合は不要です。


### Rerankサーバーの動作テスト

```sh
$ curl -v http://127.0.0.1:8082/v1/rerank -H 'Content-Type: application/json' --data-raw '
{
    "model": "cl-nagoya/ruri-v3-reranker-310m",
    "query": "山形県の蔵王温泉にある「泉質」はなに？",
    "documents": [
        "蔵王温泉はどのような特徴を 持つ温泉ですか？",
        "山形市の蔵王温泉はどのような温泉ですか？",
        "蔵王温泉の特徴は何ですか？"
    ]
}'
```

```json
{
  "results": [
    {
      "document": {
        "text": "蔵王温泉はどのような特徴を 持つ温泉ですか？"
      },
      "relevance_score": 0.029905224218964577,
      "index": 0
    },
    {
      "document": {
        "text": "山形市の蔵王温泉はどのような温泉ですか？"
      },
      "relevance_score": 0.013406982645392418,
      "index": 1
    },
    {
      "document": {
        "text": "蔵王温泉の特徴は何ですか？"
      },
      "relevance_score": 0.012443745508790016,
      "index": 2
    }
  ],
  "model": "cl-nagoya/ruri-v3-reranker-310m",
  "usage": {
    "total_tokens": 0
  }
}
```


### Difyでの設定

- Model Type: Rerank
- Model Name: cl-nagoya/ruri-v3-reranker-310m
- API Key: なし
- API endpoint URL: http://サーバーのホスト名・IPアドレス:8082/v1
- Model context size: 512
