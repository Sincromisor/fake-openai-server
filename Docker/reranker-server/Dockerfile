FROM fake-openai-server/base-server:latest

COPY --chown=fos:fos \
    ./src \
    /opt/fos/src

USER fos
CMD ["uv", "run", "fake-openai-reranker"]
