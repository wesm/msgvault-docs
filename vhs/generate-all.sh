#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
IMAGE_NAME="msgvault-vhs"
TAPES_DIR="$SCRIPT_DIR/tapes"
DEMO_DATA_DIR="$SCRIPT_DIR/demo-data"
OUTPUT_DIR="$SCRIPT_DIR/../public"

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Record msgvault TUI demos as .webm videos using VHS.

Options:
  --repo PATH     Path to msgvault source repo (default: ../msgvault sibling dir)
  --tape NAME     Record a single tape (without .tape extension)
  --list          List available tapes
  --skip-data     Skip demo data generation
  --skip-build    Skip Docker image build
  -h, --help      Show this help
EOF
}

list_tapes() {
    echo "Available tapes:"
    for f in "$TAPES_DIR"/*.tape; do
        echo "  $(basename "$f" .tape)"
    done
}

REPO="${MSGVAULT_REPO:-$SCRIPT_DIR/../../msgvault}"
SINGLE_TAPE=""
SKIP_DATA=false
SKIP_BUILD=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --repo)     REPO="$2"; shift 2 ;;
        --tape)     SINGLE_TAPE="$2"; shift 2 ;;
        --list)     list_tapes; exit 0 ;;
        --skip-data) SKIP_DATA=true; shift ;;
        --skip-build) SKIP_BUILD=true; shift ;;
        -h|--help)  usage; exit 0 ;;
        *)          echo "Unknown option: $1"; usage; exit 1 ;;
    esac
done

REPO="$(cd "$REPO" 2>/dev/null && pwd)" || {
    echo "Error: msgvault repo not found at $REPO"
    echo "Pass --repo PATH or set MSGVAULT_REPO."
    exit 1
}

# --- Step 1: Generate demo data ---
if [[ "$SKIP_DATA" == false ]]; then
    echo "==> Generating demo data..."
    (cd "$SCRIPT_DIR" && uv run generate_demo_data.py)
    echo ""
fi

# --- Step 2: Build Docker image ---
if [[ "$SKIP_BUILD" == false ]]; then
    echo "==> Building Docker image: $IMAGE_NAME"
    docker build -t "$IMAGE_NAME" -f "$SCRIPT_DIR/Dockerfile" "$REPO"
    echo ""
fi

# --- Step 3: Record tapes ---
mkdir -p "$OUTPUT_DIR"

record_tape() {
    local tape_name="$1"
    local tape_file="$TAPES_DIR/${tape_name}.tape"

    if [[ ! -f "$tape_file" ]]; then
        echo "Error: tape not found: $tape_file"
        return 1
    fi

    echo "==> Recording: $tape_name"
    docker run --rm \
        -v "$TAPES_DIR:/tapes" \
        -v "$DEMO_DATA_DIR:/root/.msgvault" \
        -e "MSGVAULT_HOME=/root/.msgvault" \
        "$IMAGE_NAME" \
        "/tapes/${tape_name}.tape"

    # Copy output
    local output_file="$TAPES_DIR/output/${tape_name}.webm"
    if [[ -f "$output_file" ]]; then
        cp "$output_file" "$OUTPUT_DIR/${tape_name}.webm"
        echo "  -> $OUTPUT_DIR/${tape_name}.webm"
    else
        echo "  Warning: expected output not found: $output_file"
    fi
}

if [[ -n "$SINGLE_TAPE" ]]; then
    record_tape "$SINGLE_TAPE"
else
    for tape_file in "$TAPES_DIR"/*.tape; do
        tape_name="$(basename "$tape_file" .tape)"
        record_tape "$tape_name"
    done
fi

echo ""
echo "Done! Videos are in $OUTPUT_DIR"
