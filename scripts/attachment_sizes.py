#!/usr/bin/env python3
"""Chart: total attachment size by type in a msgvault archive."""

# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "duckdb",
#     "pandas",
#     "plotnine",
# ]
# ///

import argparse
from pathlib import Path

import duckdb
import pandas as pd
from plotnine import (
    aes,
    coord_flip,
    element_text,
    geom_bar,
    geom_text,
    ggplot,
    labs,
    position_stack,
    scale_fill_brewer,
    scale_y_continuous,
    theme,
    theme_minimal,
)


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
    """Classify an attachment into a broad category using extension + MIME."""
    filename = row["filename"]
    mime = row["mime_type"]

    ext = ""
    if pd.notna(filename) and filename:
        ext = Path(filename).suffix.lower().lstrip(".")

    # Also parse MIME for fallback
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
        return "Documents (Word)"
    if ext in presentations or "presentation" in mime_lower or "powerpoint" in mime_lower:
        return "Presentations"
    if ext in text:
        return "Text files"
    if ext in calendar or mime_lower == "text/calendar":
        return "Calendar/Contacts"
    if ext in sigs or "pgp" in mime_lower or "pkcs" in mime_lower or "signature" in mime_lower:
        return "Signatures/Certs"
    if ext == "eml" or mime_lower == "message/rfc822":
        return "Email (EML)"
    return "Other"


def format_size(bytes_val: float) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if abs(bytes_val) < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} TB"


def main():
    parser = argparse.ArgumentParser(
        description="Chart total attachment size by type in msgvault"
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=default_db_path(),
        help="Path to msgvault SQLite database",
    )
    parser.add_argument("--output", type=str, default=None, help="Save plot to file")
    args = parser.parse_args()

    df = load_attachments(args.db)
    df["category"] = df.apply(classify_category, axis=1)

    summary = (
        df.groupby("category")
        .agg(total_bytes=("size", "sum"), count=("size", "count"))
        .reset_index()
        .sort_values("total_bytes", ascending=False)
    )

    summary["size_mb"] = summary["total_bytes"] / (1024 * 1024)
    summary["label"] = summary["total_bytes"].apply(format_size)

    summary["category"] = pd.Categorical(
        summary["category"],
        categories=summary.sort_values("total_bytes")["category"],
        ordered=True,
    )

    p = (
        ggplot(summary, aes(x="category", y="size_mb", fill="category"))
        + geom_bar(stat="identity", show_legend=False)
        + geom_text(
            aes(label="label"),
            position=position_stack(vjust=0.5),
            size=8,
            ha="center",
        )
        + coord_flip()
        + scale_fill_brewer(type="qual", palette="Paired")
        + scale_y_continuous(labels=lambda lst: [f"{v:.0f} MB" for v in lst])
        + labs(
            title="Total Attachment Size by Type",
            x="",
            y="Total size",
        )
        + theme_minimal()
        + theme(
            figure_size=(10, 6),
            plot_title=element_text(size=14, weight="bold"),
        )
    )

    if args.output:
        p.save(args.output, dpi=150)
        print(f"Saved to {args.output}")
    else:
        print(p)


if __name__ == "__main__":
    main()
