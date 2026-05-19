FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        build-essential \
        ca-certificates \
        curl \
        git \
        nano \
        nodejs \
        npm \
        python3 \
        python3-pip \
        sudo \
        vim \
    && useradd -m -s /bin/bash coder \
    && echo "coder ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/coder \
    && chmod 0440 /etc/sudoers.d/coder \
    && mkdir -p /workspace \
    && chown coder:coder /workspace \
    && rm -rf /var/lib/apt/lists/*

USER coder
WORKDIR /workspace
CMD ["bash", "-l"]
