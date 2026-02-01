# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "faker>=28.0",
#     "pyarrow>=17.0",
# ]
# ///
"""Generate a synthetic msgvault SQLite database and Parquet analytics cache for TUI demos."""

import datetime
import hashlib
import os
import random
import sqlite3
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

OUTPUT_DIR = Path(__file__).parent / "demo-data"
DB_PATH = OUTPUT_DIR / "msgvault.db"
ANALYTICS_DIR = OUTPUT_DIR / "analytics" / "messages"

# --- Configuration ---

ACCOUNTS = [
    {"email": "alex.chen@gmail.com", "name": "Alex Chen"},
    {"email": "jordan.miller@gmail.com", "name": "Jordan Miller"},
]

GMAIL_LABELS = [
    ("INBOX", "system"),
    ("SENT", "system"),
    ("STARRED", "system"),
    ("IMPORTANT", "system"),
    ("TRASH", "system"),
    ("DRAFT", "system"),
    ("SPAM", "system"),
    ("CATEGORY_PERSONAL", "system"),
    ("CATEGORY_SOCIAL", "system"),
    ("CATEGORY_PROMOTIONS", "system"),
    ("CATEGORY_UPDATES", "system"),
    ("CATEGORY_FORUMS", "system"),
    ("Projects", "user"),
    ("Receipts", "user"),
    ("Travel", "user"),
    ("Work", "user"),
]

DOMAINS = [
    "gmail.com", "yahoo.com", "outlook.com", "hey.com",
    "company.io", "university.edu", "nonprofit.org",
    "amazon.com", "github.com", "stripe.com", "slack.com",
    "notion.so", "linear.app", "vercel.com", "fly.io",
]

ATTACHMENT_TYPES = [
    ("report.pdf", "application/pdf"),
    ("photo.jpg", "image/jpeg"),
    ("screenshot.png", "image/png"),
    ("spreadsheet.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ("document.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ("archive.zip", "application/zip"),
    ("data.csv", "text/csv"),
    ("slides.pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
    ("invoice.pdf", "application/pdf"),
    ("image.heic", "image/heic"),
]

DATE_START = datetime.datetime(2022, 1, 1, tzinfo=datetime.timezone.utc)
DATE_END = datetime.datetime(2024, 12, 31, tzinfo=datetime.timezone.utc)
TARGET_MESSAGES = 500


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_type TEXT NOT NULL DEFAULT 'gmail',
            identifier TEXT NOT NULL,
            display_name TEXT,
            sync_cursor TEXT,
            last_sync_at DATETIME
        );

        CREATE TABLE conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER NOT NULL REFERENCES sources(id),
            source_conversation_id TEXT NOT NULL,
            conversation_type TEXT NOT NULL DEFAULT 'email_thread',
            message_count INTEGER DEFAULT 0,
            last_message_at DATETIME
        );

        CREATE TABLE participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_address TEXT NOT NULL,
            display_name TEXT,
            domain TEXT
        );
        CREATE UNIQUE INDEX idx_participants_email ON participants(email_address);

        CREATE TABLE messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL REFERENCES conversations(id),
            source_id INTEGER NOT NULL REFERENCES sources(id),
            source_message_id TEXT NOT NULL,
            message_type TEXT NOT NULL DEFAULT 'email',
            sent_at DATETIME NOT NULL,
            sender_id INTEGER REFERENCES participants(id),
            subject TEXT,
            body_text TEXT,
            snippet TEXT,
            size_estimate INTEGER,
            has_attachments BOOLEAN DEFAULT 0,
            deleted_at DATETIME
        );

        CREATE TABLE message_recipients (
            message_id INTEGER NOT NULL REFERENCES messages(id),
            participant_id INTEGER NOT NULL REFERENCES participants(id),
            recipient_type TEXT NOT NULL
        );

        CREATE TABLE labels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER NOT NULL REFERENCES sources(id),
            source_label_id TEXT NOT NULL,
            name TEXT NOT NULL,
            label_type TEXT NOT NULL DEFAULT 'system'
        );

        CREATE TABLE message_labels (
            message_id INTEGER NOT NULL REFERENCES messages(id),
            label_id INTEGER NOT NULL REFERENCES labels(id)
        );

        CREATE TABLE attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER NOT NULL REFERENCES messages(id),
            filename TEXT,
            mime_type TEXT,
            size INTEGER,
            content_hash TEXT,
            storage_path TEXT
        );

        CREATE VIRTUAL TABLE messages_fts USING fts5(
            subject,
            body_text,
            content='messages',
            content_rowid='id'
        );
    """)


def random_date() -> datetime.datetime:
    delta = DATE_END - DATE_START
    offset = random.randint(0, int(delta.total_seconds()))
    dt = DATE_START + datetime.timedelta(seconds=offset)
    # Bias toward business hours
    return dt.replace(hour=random.choices(range(24), weights=[1]*6 + [3]*12 + [2]*6)[0],
                      minute=random.randint(0, 59))


def get_or_create_participant(conn: sqlite3.Connection, email: str, name: str | None = None) -> int:
    row = conn.execute("SELECT id FROM participants WHERE email_address = ?", (email,)).fetchone()
    if row:
        return row[0]
    domain = email.split("@")[1] if "@" in email else ""
    conn.execute(
        "INSERT INTO participants (email_address, display_name, domain) VALUES (?, ?, ?)",
        (email, name or fake.name(), domain),
    )
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def generate_contacts(conn: sqlite3.Connection, count: int = 80) -> list[int]:
    """Pre-generate a pool of external contacts."""
    ids = []
    for _ in range(count):
        domain = random.choice(DOMAINS)
        email = f"{fake.user_name()}@{domain}"
        pid = get_or_create_participant(conn, email)
        ids.append(pid)
    return ids


def populate(conn: sqlite3.Connection) -> None:
    # Create sources
    source_ids = []
    account_participant_ids = []
    for acct in ACCOUNTS:
        conn.execute(
            "INSERT INTO sources (source_type, identifier, display_name, sync_cursor, last_sync_at) "
            "VALUES ('gmail', ?, ?, '12345', datetime('now'))",
            (acct["email"], acct["name"]),
        )
        sid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        source_ids.append(sid)
        pid = get_or_create_participant(conn, acct["email"], acct["name"])
        account_participant_ids.append(pid)

    # Create labels for each source
    label_map: dict[tuple[int, str], int] = {}
    for sid in source_ids:
        for label_name, label_type in GMAIL_LABELS:
            conn.execute(
                "INSERT INTO labels (source_id, source_label_id, name, label_type) VALUES (?, ?, ?, ?)",
                (sid, label_name, label_name, label_type),
            )
            lid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            label_map[(sid, label_name)] = lid

    # Generate contacts
    contact_ids = generate_contacts(conn)

    # Generate messages
    conv_counter = 0
    for i in range(TARGET_MESSAGES):
        source_idx = random.randint(0, len(ACCOUNTS) - 1)
        sid = source_ids[source_idx]
        account_pid = account_participant_ids[source_idx]

        sent_at = random_date()
        is_sent = random.random() < 0.25

        # Conversation (some messages share threads)
        if random.random() < 0.7 or conv_counter == 0:
            conv_counter += 1
            conn.execute(
                "INSERT INTO conversations (source_id, source_conversation_id, conversation_type, message_count, last_message_at) "
                "VALUES (?, ?, 'email_thread', 1, ?)",
                (sid, f"thread_{conv_counter:05d}", sent_at.isoformat()),
            )
            conv_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        else:
            # Add to existing conversation
            conn.execute(
                "UPDATE conversations SET message_count = message_count + 1, last_message_at = ? WHERE id = ?",
                (sent_at.isoformat(), conv_id),
            )

        if is_sent:
            sender_id = account_pid
            recipient_id = random.choice(contact_ids)
        else:
            sender_id = random.choice(contact_ids)
            recipient_id = account_pid

        subject = fake.sentence(nb_words=random.randint(3, 10)).rstrip(".")
        body = "\n\n".join(fake.paragraphs(nb=random.randint(1, 4)))
        snippet = body[:100]
        has_attach = random.random() < 0.2
        size = random.randint(1000, 500000) if not has_attach else random.randint(50000, 5000000)

        conn.execute(
            "INSERT INTO messages (conversation_id, source_id, source_message_id, message_type, "
            "sent_at, sender_id, subject, body_text, snippet, size_estimate, has_attachments) "
            "VALUES (?, ?, ?, 'email', ?, ?, ?, ?, ?, ?, ?)",
            (conv_id, sid, f"msg_{i:06d}", sent_at.isoformat(), sender_id,
             subject, body, snippet, size, int(has_attach)),
        )
        msg_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Recipients
        conn.execute(
            "INSERT INTO message_recipients (message_id, participant_id, recipient_type) VALUES (?, ?, 'to')",
            (msg_id, recipient_id),
        )
        # Occasional CC
        if random.random() < 0.15:
            cc_id = random.choice(contact_ids)
            conn.execute(
                "INSERT INTO message_recipients (message_id, participant_id, recipient_type) VALUES (?, ?, 'cc')",
                (msg_id, cc_id),
            )

        # Labels
        applied_labels = []
        if is_sent:
            applied_labels.append("SENT")
        else:
            applied_labels.append("INBOX")
            if random.random() < 0.15:
                applied_labels.append("STARRED")
            if random.random() < 0.3:
                applied_labels.append("IMPORTANT")
            # Category labels
            cat = random.choices(
                ["CATEGORY_PERSONAL", "CATEGORY_SOCIAL", "CATEGORY_PROMOTIONS",
                 "CATEGORY_UPDATES", "CATEGORY_FORUMS"],
                weights=[40, 15, 20, 15, 10],
            )[0]
            applied_labels.append(cat)
            # User labels
            if random.random() < 0.2:
                applied_labels.append(random.choice(["Projects", "Receipts", "Travel", "Work"]))

        for label_name in applied_labels:
            lid = label_map.get((sid, label_name))
            if lid:
                conn.execute(
                    "INSERT INTO message_labels (message_id, label_id) VALUES (?, ?)",
                    (msg_id, lid),
                )

        # Attachments
        if has_attach:
            num_attach = random.randint(1, 3)
            for _ in range(num_attach):
                fname, mtype = random.choice(ATTACHMENT_TYPES)
                asize = random.randint(10000, 2000000)
                chash = hashlib.sha256(f"{msg_id}_{fname}_{random.random()}".encode()).hexdigest()
                spath = f"{chash[:2]}/{chash}"
                conn.execute(
                    "INSERT INTO attachments (message_id, filename, mime_type, size, content_hash, storage_path) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (msg_id, fname, mtype, asize, chash, spath),
                )

    # Populate FTS
    conn.execute("INSERT INTO messages_fts(messages_fts) VALUES('rebuild')")


def generate_parquet(conn: sqlite3.Connection) -> None:
    """Generate Parquet analytics cache that the TUI reads."""
    ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)

    rows = conn.execute("""
        SELECT
            m.id,
            m.source_id,
            s.identifier AS account,
            m.conversation_id,
            m.sent_at,
            p.email_address AS sender_email,
            p.display_name AS sender_name,
            p.domain AS sender_domain,
            m.subject,
            m.snippet,
            m.size_estimate,
            m.has_attachments
        FROM messages m
        JOIN participants p ON m.sender_id = p.id
        JOIN sources s ON m.source_id = s.id
        WHERE m.deleted_at IS NULL
        ORDER BY m.sent_at
    """).fetchall()

    columns = {
        "message_id": pa.array([r[0] for r in rows], type=pa.int64()),
        "source_id": pa.array([r[1] for r in rows], type=pa.int64()),
        "account": pa.array([r[2] for r in rows], type=pa.string()),
        "conversation_id": pa.array([r[3] for r in rows], type=pa.int64()),
        "sent_at": pa.array([r[4] for r in rows], type=pa.string()),
        "sender_email": pa.array([r[5] for r in rows], type=pa.string()),
        "sender_name": pa.array([r[6] for r in rows], type=pa.string()),
        "sender_domain": pa.array([r[7] for r in rows], type=pa.string()),
        "subject": pa.array([r[8] for r in rows], type=pa.string()),
        "snippet": pa.array([r[9] for r in rows], type=pa.string()),
        "size_estimate": pa.array([r[10] for r in rows], type=pa.int64()),
        "has_attachments": pa.array([bool(r[11]) for r in rows], type=pa.bool_()),
    }

    table = pa.table(columns)

    # Add year column for partitioning
    years = [r[4][:4] if r[4] else "2023" for r in rows]
    table = table.append_column("year", pa.array(years, type=pa.string()))

    # Also join labels and recipients for the Parquet cache
    label_rows = conn.execute("""
        SELECT ml.message_id, l.name
        FROM message_labels ml
        JOIN labels l ON ml.label_id = l.id
    """).fetchall()
    labels_by_msg: dict[int, list[str]] = {}
    for mid, lname in label_rows:
        labels_by_msg.setdefault(mid, []).append(lname)

    recipient_rows = conn.execute("""
        SELECT mr.message_id, p.email_address, mr.recipient_type
        FROM message_recipients mr
        JOIN participants p ON mr.participant_id = p.id
    """).fetchall()
    recipients_by_msg: dict[int, list[str]] = {}
    for mid, email, rtype in recipient_rows:
        recipients_by_msg.setdefault(mid, []).append(email)

    label_col = pa.array(
        [",".join(labels_by_msg.get(r[0], [])) for r in rows],
        type=pa.string(),
    )
    recipient_col = pa.array(
        [",".join(recipients_by_msg.get(r[0], [])) for r in rows],
        type=pa.string(),
    )
    table = table.append_column("labels", label_col)
    table = table.append_column("recipients", recipient_col)

    pq.write_to_dataset(
        table,
        root_path=str(ANALYTICS_DIR),
        partition_cols=["year"],
    )
    print(f"  Parquet analytics written to {ANALYTICS_DIR}")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"Removed existing {DB_PATH}")

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")

    print("Creating schema...")
    create_schema(conn)

    print(f"Generating {TARGET_MESSAGES} messages across {len(ACCOUNTS)} accounts...")
    populate(conn)
    conn.commit()

    # Stats
    msg_count = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    part_count = conn.execute("SELECT COUNT(*) FROM participants").fetchone()[0]
    conv_count = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
    attach_count = conn.execute("SELECT COUNT(*) FROM attachments").fetchone()[0]
    print(f"  {msg_count} messages, {conv_count} conversations, {part_count} participants, {attach_count} attachments")

    print("Generating Parquet analytics cache...")
    generate_parquet(conn)

    conn.close()
    print(f"Done! Database: {DB_PATH}")


if __name__ == "__main__":
    main()
