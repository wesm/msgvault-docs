# Stage 1: Build msgvault binary
FROM golang:1.25 AS builder

RUN apt-get update && apt-get install -y --no-install-recommends git make gcc g++ && rm -rf /var/lib/apt/lists/*

COPY . /src
WORKDIR /src
RUN make build

# Stage 2: VHS recording runtime (Debian to match glibc builder)
FROM debian:trixie-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    ffmpeg \
    chromium \
    fontconfig \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install ttyd from GitHub (not in Debian repos)
ARG TARGETARCH
RUN case "${TARGETARCH}" in \
      arm64) TTYD_ARCH="aarch64" ;; \
      *)     TTYD_ARCH="x86_64" ;; \
    esac && \
    curl -fsSL -o /usr/local/bin/ttyd \
      "https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.${TTYD_ARCH}" && \
    chmod +x /usr/local/bin/ttyd

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

WORKDIR /tapes
ENTRYPOINT ["vhs"]
