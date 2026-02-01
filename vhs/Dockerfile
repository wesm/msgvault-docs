# Stage 1: Build msgvault binary
FROM golang:1.25-alpine AS builder

RUN apk add --no-cache git make gcc musl-dev

COPY . /src
WORKDIR /src
RUN make build

# Stage 2: VHS recording runtime
FROM alpine:3.19

RUN apk add --no-cache \
    bash \
    ffmpeg \
    chromium \
    fontconfig \
    ttyd \
    ca-certificates \
    curl

# Install MesloLGS Nerd Font for consistent glyph rendering
RUN mkdir -p /usr/share/fonts/meslo && \
    curl -fsSL -o /usr/share/fonts/meslo/MesloLGS-NF-Regular.ttf \
      "https://github.com/romkatv/powerlevel10k-media/raw/master/MesloLGS%20NF%20Regular.ttf" && \
    curl -fsSL -o /usr/share/fonts/meslo/MesloLGS-NF-Bold.ttf \
      "https://github.com/romkatv/powerlevel10k-media/raw/master/MesloLGS%20NF%20Bold.ttf" && \
    fc-cache -f

# Install VHS (arch-aware)
ARG TARGETARCH
RUN VHS_VERSION="0.8.0" && \
    case "${TARGETARCH}" in \
      arm64) VHS_ARCH="arm64" ;; \
      *)     VHS_ARCH="x86_64" ;; \
    esac && \
    curl -fsSL "https://github.com/charmbracelet/vhs/releases/download/v${VHS_VERSION}/vhs_${VHS_VERSION}_Linux_${VHS_ARCH}.tar.gz" \
      | tar -xz -C /usr/local/bin vhs

# Chromium no-sandbox wrapper (required in Docker)
RUN mv /usr/bin/chromium-browser /usr/bin/chromium-browser-real && \
    printf '#!/bin/sh\nexec /usr/bin/chromium-browser-real --no-sandbox "$@"\n' > /usr/bin/chromium-browser && \
    chmod +x /usr/bin/chromium-browser

# Copy msgvault binary from builder
COPY --from=builder /src/msgvault /usr/local/bin/msgvault

WORKDIR /tapes
ENTRYPOINT ["vhs"]
