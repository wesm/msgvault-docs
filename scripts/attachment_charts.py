#!/usr/bin/env python3
"""Combined chart: attachment counts and total size by type for a msgvault archive."""

# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "duckdb",
#     "matplotlib",
#     "pandas",
# ]
# ///

import argparse
from pathlib import Path

import duckdb
import matplotlib.pyplot as plt
import pandas as pd


def default_db_path() -> Path:
    return Path.home() / ".msgvault" / "msgvault.db"


def load_attachments(db_path: Path) -> pd.DataFrame:
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found at {db_path}.")
    con = duckdb.connect()
    df = con.sql(f"""
        SELECT filename, mime_type, size
        FROM sqlite_scan('{db_path}', 'attachments')
        WHERE NOT (
            (filename = '' OR filename IS NULL)
            AND mime_type IN ('text/plain', 'text/html', 'text/x-watch-html', 'text/watch-html')
        )
    """).df()
    con.close()
    return df


def classify_category(row: pd.Series) -> str:
    filename = row["filename"]
    mime = row["mime_type"]

    ext = ""
    if pd.notna(filename) and filename:
        ext = Path(filename).suffix.lower().lstrip(".")

    mime_lower = ""
    if pd.notna(mime) and mime:
        mime_lower = mime.lower().split(";")[0].strip()

    images = {"png", "jpg", "jpeg", "gif", "svg", "bmp", "webp", "tif", "tiff", "heic", "ico"}
    audio = {"mp3", "wav", "m4a", "ogg", "flac", "aac", "wma"}
    video = {"mp4", "mov", "avi", "mkv", "webm", "wmv", "flv"}
    archives = {"zip", "gz", "tar", "7z", "rar", "bz2", "xz"}
    spreadsheets = {"xlsx", "xls", "csv", "ods", "tsv"}
    documents = {"doc", "docx", "rtf", "odt", "pages"}
    presentations = {"ppt", "pptx", "odp", "key"}
    text = {"txt", "log", "md", "rst", "json", "xml", "html", "htm", "yaml", "yml"}
    calendar = {"ics", "vcf"}
    sigs = {"p7s", "sig", "asc", "pem", "cer", "crt", "pgp"}

    if ext == "pdf" or mime_lower == "application/pdf":
        return "PDF"
    if ext in images or mime_lower.startswith("image/"):
        return "Images"
    if ext in audio or mime_lower.startswith("audio/"):
        return "Audio"
    if ext in video or mime_lower.startswith("video/"):
        return "Video"
    if ext in archives:
        return "Archives"
    if ext in spreadsheets:
        return "Spreadsheets"
    if ext in documents or "wordprocessing" in mime_lower or "msword" in mime_lower:
        return "Documents"
    if ext in presentations or "presentation" in mime_lower or "powerpoint" in mime_lower:
        return "Presentations"
    if ext in text:
        return "Text files"
    if ext in calendar or mime_lower == "text/calendar":
        return "Calendar"
    if ext in sigs or "pgp" in mime_lower or "pkcs" in mime_lower or "signature" in mime_lower:
        return "Signatures"
    if ext == "eml" or mime_lower == "message/rfc822":
        return "Email (EML)"
    return "Other"


def format_count(x: float) -> str:
    if x >= 1000:
        return f"{x / 1000:.1f}k"
    return f"{int(x)}"


def format_size(bytes_val: float) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if abs(bytes_val) < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} TB"


# Curated palette with enough distinct colors
PALETTE = [
    "#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f",
    "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac",
    "#86bcb6", "#8cd17d", "#f1ce63", "#a0cbe8",
]


def main():
    parser = argparse.ArgumentParser(
        description="Combined attachment charts for a msgvault archive"
    )
    parser.add_argument(
        "--db", type=Path, default=default_db_path(),
        help="Path to msgvault SQLite database",
    )
    parser.add_argument(
        "--top", type=int, default=12, help="Number of categories to show"
    )
    parser.add_argument("--output", type=str, default=None, help="Save plot to file")
    args = parser.parse_args()

    df = load_attachments(args.db)
    df["category"] = df.apply(classify_category, axis=1)

    # Aggregate
    summary = (
        df.groupby("category")
        .agg(count=("size", "count"), total_bytes=("size", "sum"))
        .reset_index()
    )

    # Pick top N by count, roll up the rest into "Other"
    summary = summary.sort_values("count", ascending=False)
    # If "Other" already exists as a category, merge it into the rollup
    other_mask = summary["category"] == "Other"
    existing_other = summary[other_mask]
    non_other = summary[~other_mask]

    top = non_other.head(args.top).copy()
    remainder = non_other.iloc[args.top:]
    rollup_count = remainder["count"].sum() + existing_other["count"].sum()
    rollup_bytes = remainder["total_bytes"].sum() + existing_other["total_bytes"].sum()
    if rollup_count > 0:
        top = pd.concat([
            top,
            pd.DataFrame([{
                "category": "Other",
                "count": rollup_count,
                "total_bytes": rollup_bytes,
            }]),
        ], ignore_index=True)

    # Sort by count descending; this is the consistent y-axis order for both panels
    top = top.sort_values("count", ascending=True).reset_index(drop=True)
    categories = top["category"].tolist()

    top["count_label"] = top["count"].apply(format_count)
    top["size_label"] = top["total_bytes"].apply(format_size)
    top["size_mb"] = top["total_bytes"] / (1024 * 1024)

    colors = [PALETTE[i % len(PALETTE)] for i in range(len(categories))]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5), sharey=True)
    fig.suptitle("Email Attachments in Gmail Archive", fontsize=14, fontweight="bold", y=0.98)

    # Left panel: counts
    ax1.barh(categories, top["count"], color=colors)
    for i, (val, label) in enumerate(zip(top["count"], top["count_label"])):
        ax1.text(val + max(top["count"]) * 0.015, i, f" {label}", va="center", fontsize=8)
    ax1.set_title("Number of attachments", fontsize=11, fontweight="bold")
    ax1.set_xlim(0, max(top["count"]) * 1.18)
    ax1.xaxis.set_visible(False)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.spines["bottom"].set_visible(False)

    # Right panel: total size
    ax2.barh(categories, top["size_mb"], color=colors)
    for i, (val, label) in enumerate(zip(top["size_mb"], top["size_label"])):
        ax2.text(val + max(top["size_mb"]) * 0.015, i, f" {label}", va="center", fontsize=8)
    ax2.set_title("Total size", fontsize=11, fontweight="bold")
    ax2.set_xlim(0, max(top["size_mb"]) * 1.18)
    ax2.xaxis.set_visible(False)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.spines["bottom"].set_visible(False)

    fig.tight_layout()

    if args.output:
        fig.savefig(args.output, dpi=150, bbox_inches="tight")
        print(f"Saved to {args.output}")
    else:
        plt.show()


if __name__ == "__main__":
    main()
