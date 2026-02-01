# Stage 1: Build msgvault binary
FROM golang:1.25-bookworm AS builder

RUN apt-get update && apt-get install -y --no-install-recommends git make gcc g++ && rm -rf /var/lib/apt/lists/*

COPY . /src
WORKDIR /src
RUN make build

# Stage 2: Screenshot runtime with freeze + tmux
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    tmux \
    fontconfig \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install MesloLGS Nerd Font for consistent glyph rendering
RUN mkdir -p /usr/share/fonts/meslo && \
    curl -fsSL -o /usr/share/fonts/meslo/MesloLGS-NF-Regular.ttf \
      "https://github.com/romkatv/powerlevel10k-media/raw/master/MesloLGS%20NF%20Regular.ttf" && \
    curl -fsSL -o /usr/share/fonts/meslo/MesloLGS-NF-Bold.ttf \
      "https://github.com/romkatv/powerlevel10k-media/raw/master/MesloLGS%20NF%20Bold.ttf" && \
    fc-cache -f

# Install freeze (arch-aware)
RUN FREEZE_VERSION="0.2.2" && \
    DPKG_ARCH="$(dpkg --print-architecture)" && \
    case "${DPKG_ARCH}" in \
      arm64) FREEZE_ARCH="arm64" ;; \
      *)     FREEZE_ARCH="x86_64" ;; \
    esac && \
    curl -fsSL "https://github.com/charmbracelet/freeze/releases/download/v${FREEZE_VERSION}/freeze_${FREEZE_VERSION}_Linux_${FREEZE_ARCH}.tar.gz" \
      | tar -xz -C /tmp && \
    mv /tmp/freeze_*/freeze /usr/local/bin/freeze && \
    rm -rf /tmp/freeze_* && \
    freeze --version

# Copy msgvault binary from builder
COPY --from=builder /src/msgvault /usr/local/bin/msgvault

# Verify binary runs
RUN msgvault version

WORKDIR /tapes
ENTRYPOINT ["bash"]
