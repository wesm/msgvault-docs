#!/usr/bin/env python3
"""Chart: distribution of email attachment types in a msgvault archive."""

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
    ggplot,
    labs,
    scale_fill_brewer,
    theme,
    theme_minimal,
)


def default_db_path() -> Path:
    return Path.home() / ".msgvault" / "msgvault.db"


# MIME types that represent email body parts rather than real attachments
BODY_MIME_TYPES = {"text/plain", "text/html", "text/x-watch-html", "text/watch-html"}


def load_attachments(db_path: Path) -> pd.DataFrame:
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found at {db_path}.")
    con = duckdb.connect()
    try:
        con.execute("LOAD sqlite;")
    except duckdb.IOException:
        con.execute("INSTALL sqlite; LOAD sqlite;")
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


def classify_attachment(row: pd.Series) -> str:
    """Classify an attachment using filename extension, falling back to MIME type."""
    filename = row["filename"]
    mime = row["mime_type"]

    # Try extension first if filename is present
    if pd.notna(filename) and filename:
        ext = Path(filename).suffix.lower().lstrip(".")
        if ext:
            ext_map = {
                "pdf": "PDF",
                "zip": "ZIP", "gz": "GZIP", "tar": "TAR", "7z": "7Z", "rar": "RAR",
                "docx": "DOCX", "doc": "DOC",
                "xlsx": "XLSX", "xls": "XLS", "csv": "CSV",
                "pptx": "PPTX", "ppt": "PPT",
                "json": "JSON", "xml": "XML",
                "html": "HTML", "htm": "HTML",
                "txt": "TXT", "log": "TXT", "md": "TXT", "rtf": "RTF",
                "eml": "EML",
                "ics": "Calendar", "vcf": "vCard",
                "png": "PNG", "jpg": "JPEG", "jpeg": "JPEG", "gif": "GIF",
                "svg": "SVG", "bmp": "BMP", "webp": "WebP",
                "tif": "TIFF", "tiff": "TIFF", "heic": "HEIC",
                "mp3": "Audio", "wav": "Audio", "m4a": "Audio", "ogg": "Audio",
                "mp4": "Video", "mov": "Video", "avi": "Video",
                "mkv": "Video", "webm": "Video",
                "p7s": "Signature", "sig": "Signature", "asc": "Signature",
                "pem": "Certificate", "cer": "Certificate", "crt": "Certificate",
            }
            if ext in ext_map:
                return ext_map[ext]
            return ext.upper()

    # Fall back to MIME type
    if pd.notna(mime) and mime:
        mime = mime.lower().split(";")[0].strip()
        mime_map = {
            "application/pdf": "PDF",
            "application/zip": "ZIP",
            "application/octet-stream": "Binary blob",
            "application/pgp-signature": "Signature",
            "message/rfc822": "EML",
            "text/calendar": "Calendar",
        }
        if mime in mime_map:
            return mime_map[mime]
        if mime.startswith("image/"):
            return mime.split("/")[1].upper()
        if mime.startswith("audio/"):
            return "Audio"
        if mime.startswith("video/"):
            return "Video"
        return mime.split("/")[-1][:20]

    return "Unknown"


def main():
    parser = argparse.ArgumentParser(description="Chart attachment types in msgvault")
    parser.add_argument(
        "--db",
        type=Path,
        default=default_db_path(),
        help="Path to msgvault SQLite database",
    )
    parser.add_argument(
        "--top", type=int, default=15, help="Number of top types to show"
    )
    parser.add_argument("--output", type=str, default=None, help="Save plot to file")
    args = parser.parse_args()

    df = load_attachments(args.db)

    if df.empty:
        print("No attachments found in database.")
        return

    df["type"] = df.apply(classify_attachment, axis=1)

    counts = (
        df.groupby("type")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )

    top = counts.head(args.top).copy()
    if len(counts) > args.top:
        other_count = counts.iloc[args.top :]["count"].sum()
        top = pd.concat(
            [top, pd.DataFrame([{"type": "Other", "count": other_count}])],
            ignore_index=True,
        )

    top["type"] = pd.Categorical(
        top["type"], categories=top.sort_values("count")["type"], ordered=True
    )

    p = (
        ggplot(top, aes(x="type", y="count", fill="type"))
        + geom_bar(stat="identity", show_legend=False)
        + coord_flip()
        + scale_fill_brewer(type="qual", palette="Set3")
        + labs(
            title="Email Attachment Types",
            x="",
            y="Number of attachments",
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
        print("No --output specified. Use --output <file> to save the chart.")
        p.save("attachment_types.png", dpi=150)
        print("Saved to attachment_types.png")


if __name__ == "__main__":
    main()
