# Commit And Review Guide

## Purpose

この文書は、`fake-openai-server` でのコミットとレビューを
一貫した粒度で行うための運用指針です。

## Commit Rules

- 1 つのコミットは 1 つの意図に絞る
- 機能変更と無関係なリファクタは分離する
- コミット前に最低限の品質ゲートを通す
- 実行できなかった検証はコミット後の説明や PR に残す

推奨フォーマット:

```text
type: concise summary

Why:
- reason 1
- reason 2
```

例:

```text
feat: add typed accelerator device settings

Why:
- allow cpu, mps, and cuda selection from .env
- keep local and compose runtime behavior aligned
```

## Recommended Check Order

変更前後で、次の順番を基本とします。

1. `uv run ruff check .`
2. `uv run ruff format --check .`
3. `uv run ty check`
4. `uv run pytest`
5. `docker compose config`

必要に応じて、README の手順や `.env` サンプルも同時に確認します。

## Review Checklist

- 変更意図がコミットメッセージから追える
- 型、schema、OpenAPI が実装と一致している
- `.env`、`compose.yaml`、README の変数名が一致している
- 重いモデルダウンロードを避けるテストになっている
- エラー時に内部詳細をレスポンスへ漏らしていない
- ログに秘密情報や巨大 payload を出していない
- Docker とローカル実行の起動手順が乖離していない

## Pull Request Notes

PR では次を簡潔に書きます。

- 何を変えたか
- なぜ必要か
- どの検証を実施したか
- 未実施の検証や既知のリスク
