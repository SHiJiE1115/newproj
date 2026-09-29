FROM ubuntu:24.04@sha256:008173c23f95b170204355c12626cb5a965d779a7e1283b09e9cffbb1bf33ca3

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      python3 python3-numpy python3-pandas python3-scipy \
      python3-sklearn python3-sympy strace unzip \
 && rm -rf /var/lib/apt/lists/*

COPY author.zip wine.raw author_25.py entrypoint.sh /probe/
RUN mkdir -p /probe/src /probe/out \
 && unzip -q /probe/author.zip -d /probe/src \
 && install -D -m 0444 /probe/wine.raw \
      /probe/src/paper-decision-trees-as-partitioning-machines-0f354dac486a9845a9504419e31c84c7eb39507f/experiments/datasets/raw/wine.raw \
 && mkdir -p /probe/src/paper-decision-trees-as-partitioning-machines-0f354dac486a9845a9504419e31c84c7eb39507f/experiments/results/wine/ac25 \
 && chmod 0555 /probe/entrypoint.sh /probe/author_25.py \
 && chmod 0777 /probe/out /probe/src/paper-decision-trees-as-partitioning-machines-0f354dac486a9845a9504419e31c84c7eb39507f/experiments/results/wine/ac25

WORKDIR /probe
ENTRYPOINT ["/bin/bash", "/probe/entrypoint.sh"]
