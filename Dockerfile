# syntax=docker/dockerfile:1.7
FROM pytorch/pytorch:2.8.0-cuda12.8-cudnn9-devel
USER root

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends openssh-client git && rm -rf /var/lib/apt/lists/*
RUN install -d -m 0700 /root/.ssh && ssh-keyscan github.com >> /root/.ssh/known_hosts && chmod 0644 /root/.ssh/known_hosts

COPY flash_attn-2.8.3+cu12torch2.8cxx11abiFALSE-cp311-cp311-linux_x86_64.whl /workspace/flash_attn-2.8.3+cu12torch2.8cxx11abiFALSE-cp311-cp311-linux_x86_64.whl
RUN pip install /workspace/flash_attn-2.8.3+cu12torch2.8cxx11abiFALSE-cp311-cp311-linux_x86_64.whl

# BuildKit forwards the SSH agent only for this instruction; no private key is copied
# into the build context or persisted in an image layer.
RUN --mount=type=ssh git clone -b wsl --recursive git@github.com:woforce/RewardHackingMRE.git rllm && \
    cd rllm && bash setup_env.sh && cd /workspace && \
    rm -rf /workspace/rllm

CMD ["/bin/bash"]

# Build with an SSH agent available to BuildKit:
# docker build --ssh default -t rllm .
# Docker Usage
# docker create --runtime=nvidia --gpus all --shm-size="10g" -v .:/workspace/rllm -v /tmp:/tmp --name rllm-container rllm sleep infinity
# docker start rllm-container
# docker exec -it rllm-container bash
