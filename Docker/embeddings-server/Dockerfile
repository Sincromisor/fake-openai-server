FROM fake-openai-server/base-server:latest

COPY --chown=fos:fos \
    ./src \
    /opt/fos/src


USER fos
CMD ["sh", "-c", "uv run uvicorn fake_openai_server.main.embeddings:app --host ${EMBEDDINGS_HOST:-0.0.0.0} --port ${EMBEDDINGS_PORT:-8081}"]
