# Stage 1: Build msgvault binary
FROM golang:1.25-bookworm AS builder

RUN apt-get update && apt-get install -y --no-install-recommends git make gcc g++ && rm -rf /var/lib/apt/lists/*

COPY . /src
WORKDIR /src
RUN make build

# Stage 2: VHS recording runtime (Debian to match glibc builder)
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    ffmpeg \
    chromium \
    fontconfig \
    ca-certificates \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Build ttyd from source (not in Debian repos, prebuilt binaries need newer glibc)
RUN apt-get update && apt-get install -y --no-install-recommends \
    cmake make gcc g++ pkg-config libwebsockets-dev libjson-c-dev libssl-dev \
    && git clone --depth 1 --branch 1.7.7 https://github.com/tsl0922/ttyd.git /tmp/ttyd \
    && cd /tmp/ttyd && mkdir build && cd build \
    && cmake -DCMAKE_BUILD_TYPE=Release .. && make -j$(nproc) \
    && cp ttyd /usr/local/bin/ttyd \
    && rm -rf /tmp/ttyd \
    && apt-get purge -y cmake g++ pkg-config \
    && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# Install MesloLGS Nerd Font for consistent glyph rendering
RUN mkdir -p /usr/share/fonts/meslo && \
    curl -fsSL -o /usr/share/fonts/meslo/MesloLGS-NF-Regular.ttf \
      "https://github.com/romkatv/powerlevel10k-media/raw/master/MesloLGS%20NF%20Regular.ttf" && \
    curl -fsSL -o /usr/share/fonts/meslo/MesloLGS-NF-Bold.ttf \
      "https://github.com/romkatv/powerlevel10k-media/raw/master/MesloLGS%20NF%20Bold.ttf" && \
    fc-cache -f

# Install VHS (arch-aware)
RUN VHS_VERSION="0.8.0" && \
    case "${TARGETARCH}" in \
      arm64) VHS_ARCH="arm64" ;; \
      *)     VHS_ARCH="x86_64" ;; \
    esac && \
    curl -fsSL "https://github.com/charmbracelet/vhs/releases/download/v${VHS_VERSION}/vhs_${VHS_VERSION}_Linux_${VHS_ARCH}.tar.gz" \
      | tar -xz -C /tmp && \
    mv /tmp/vhs_*/vhs /usr/local/bin/vhs && \
    rm -rf /tmp/vhs_*

# Chromium no-sandbox wrapper (required in Docker)
RUN mv /usr/bin/chromium /usr/bin/chromium-real && \
    printf '#!/bin/sh\nexec /usr/bin/chromium-real --no-sandbox "$@"\n' > /usr/bin/chromium && \
    chmod +x /usr/bin/chromium

# Copy msgvault binary from builder
COPY --from=builder /src/msgvault /usr/local/bin/msgvault

# Verify binary runs
RUN msgvault version

WORKDIR /tapes
ENTRYPOINT ["vhs"]
