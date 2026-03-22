FROM nvidia/cuda:12.9.1-cudnn-runtime-ubuntu24.04 AS builder

ARG FOS_USER_ID=fos
ARG FOS_USER_DIR=/opt/fos

ENV PATH=${FOS_USER_DIR}/.cargo/bin:${FOS_USER_DIR}/.local/bin:${PATH}

# curl: uvのインストール
# その他: sentencepieceのビルド
RUN --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    --mount=type=cache,target=/var/cache/apt/archives,sharing=locked \
    apt-get update \
    && apt-get install -y \
    curl \
    build-essential \
    cmake pkg-config \
    libprotobuf-dev \
    libsentencepiece-dev

RUN useradd -u 1001 -s /bin/bash -d ${FOS_USER_DIR} ${FOS_USER_ID} && \
    mkdir -p ${FOS_USER_DIR} && \
    chown -R ${FOS_USER_ID}:${FOS_USER_ID} ${FOS_USER_DIR}

WORKDIR ${FOS_USER_DIR}
USER ${FOS_USER_ID}
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && id && pwd && echo ${FOS_USER_ID}

COPY --chown=${FOS_USER_ID}:${FOS_USER_ID} \
    ./pyproject.toml \
    ./uv.lock \
    ./.python-version \
    ./src \
    ./README.md \
    ${FOS_USER_DIR}/

RUN --mount=type=cache,target=${FOS_USER_DIR}/.cache,uid=1001,gid=1001 \
    uv sync


#-----------
# Runner
#-----------
FROM nvidia/cuda:12.9.1-cudnn-runtime-ubuntu24.04 AS runner

ARG FOS_USER_ID=fos
ARG FOS_USER_DIR=/opt/fos

ENV PATH=${FOS_USER_DIR}/.cargo/bin:${FOS_USER_DIR}/.local/bin:${PATH}

# sentencepieceの利用に必要なものをインストール
RUN --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    --mount=type=cache,target=/var/cache/apt/archives,sharing=locked \
    apt-get update \
    && apt-get install -y libsentencepiece0 libprotobuf-c1


RUN useradd -u 1001 -s /bin/bash -d ${FOS_USER_DIR} ${FOS_USER_ID} && \
    mkdir -p ${FOS_USER_DIR} && \
    chown -R ${FOS_USER_ID}:${FOS_USER_ID} ${FOS_USER_DIR}

WORKDIR ${FOS_USER_DIR}
USER ${FOS_USER_ID}

COPY --from=builder --chown=${FOS_USER_ID}:${FOS_USER_ID} \
    ${FOS_USER_DIR}/.local \
    ${FOS_USER_DIR}/.local

COPY --from=builder --chown=${FOS_USER_ID}:${FOS_USER_ID} \
    ${FOS_USER_DIR}/.venv \
    ${FOS_USER_DIR}/.venv

COPY --from=builder --chown=${FOS_USER_ID}:${FOS_USER_ID} \
    ${FOS_USER_DIR}/.config \
    ${FOS_USER_DIR}/.config

COPY --from=builder --chown=${FOS_USER_ID}:${FOS_USER_ID} \
    ${FOS_USER_DIR}/pyproject.toml \
    ${FOS_USER_DIR}/uv.lock \
    ${FOS_USER_DIR}/.python-version \
    ${FOS_USER_DIR}/src \
    ${FOS_USER_DIR}/

COPY --chmod=755 ./Docker/base-server/setup.sh /opt/setup.sh

RUN mkdir -p ${FOS_USER_DIR}/.cache

USER root
CMD ["/opt/setup.sh"]
