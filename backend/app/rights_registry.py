"""Scope-aware source permission registry for export-time rights checks.

This records operator-supplied permission evidence metadata; it does not
authenticate the grantor or determine whether permission is legally sufficient.
"""
from __future__ import annotations

import ipaddress
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

ALLOWED_USES = frozenset({"analyze", "edit", "publish"})


def _ends_in_ipv4_number(label: str) -> bool:
    """Match URL-host numeric suffix forms that browsers may parse as IPv4."""
    lowered = label.lower()
    if lowered.startswith("0x"):
        digits = lowered[2:]
        if not digits or all(character in "0123456789abcdef" for character in digits):
            return True
    # WHATWG-style URL parsers classify a final label ending in an
    # ASCII digit as an IPv4 candidate, even when numeric parsing later
    # fails (for example, "label1", "0xg1", or "0a9"). Require the
    # complete hostname to be canonical IPv4 in those cases.
    return lowered.isascii() and lowered[-1:].isdigit()


def _valid_hostname(hostname: str) -> bool:
    """Accept DNS/IDNA names and IP literals without ambiguous forms."""
    # Scoped IPv6 literals are deliberately unsupported at this registry
    # boundary. Different URL consumers handle encoded/raw zone identifiers
    # inconsistently, so reject percent signs before invoking the IP parser.
    if "%" in hostname:
        return False
    if ":" in hostname:
        try:
            ipaddress.IPv6Address(hostname)
            return True
        except ValueError:
            return False
    try:
        ascii_hostname = hostname.encode("idna").decode("ascii")
    except UnicodeError:
        return False
    # A single terminal dot is the conventional fully-qualified DNS form.
    if ascii_hostname.endswith("."):
        ascii_hostname = ascii_hostname[:-1]
    if not ascii_hostname or len(ascii_hostname) > 253:
        return False

    # URL consumers can interpret shorthand, octal, hexadecimal, or invalid
    # dotted-decimal numeric hosts differently. Accept only canonical IPv4
    # literals when the final label has a URL-parser numeric form.
    if _ends_in_ipv4_number(ascii_hostname.rsplit(".", 1)[-1]):
        try:
            ipaddress.IPv4Address(ascii_hostname)
            return True
        except ValueError:
            return False

    labels = ascii_hostname.split(".")
    return all(
        label
        and len(label) <= 63
        and label[0].isalnum()
        and label[-1].isalnum()
        and all(character.isalnum() or character == "-" for character in label)
        for label in labels
    )


def _time(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str) and value.strip():
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    else:
        raise ValueError("timestamp must be ISO text or a datetime")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamps must include a timezone")
    return parsed


class SourceRightsRegistry:
    """Persist source grants and fail closed when scope/platform is missing."""

    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path).expanduser()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connect(self):
        db = sqlite3.connect(self.database_path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS source_rights (
                    source_id TEXT PRIMARY KEY,
                    source_url TEXT NOT NULL,
                    grantor TEXT NOT NULL,
                    evidence_ref TEXT NOT NULL,
                    allowed_uses_json TEXT NOT NULL,
                    platforms_json TEXT NOT NULL,
                    attribution TEXT NOT NULL,
                    disclosure TEXT NOT NULL,
                    valid_from TEXT NOT NULL,
                    expires_at TEXT,
                    revoked_at TEXT
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS source_rights_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    details_json TEXT NOT NULL
                )
            """)

    def register(self, record: dict[str, Any], *, actor: str = "operator") -> None:
        if not isinstance(record, dict):
            raise ValueError("rights record must be an object")
        required = ("source_id", "source_url", "grantor", "evidence_ref",
                    "allowed_uses", "platforms", "valid_from")
        missing = [key for key in required if record.get(key) is None or record.get(key) == ""]
        if missing:
            raise ValueError("missing required rights fields: " + ", ".join(missing))
        text_fields = ("source_id", "source_url", "grantor", "evidence_ref")
        for field in text_fields:
            value = record[field]
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} must be a non-empty string")
        for field in ("attribution", "disclosure"):
            if field in record and not isinstance(record[field], str):
                raise ValueError(f"{field} must be a string")
        if not isinstance(actor, str) or not actor.strip():
            raise ValueError("actor is required")
        actor = actor.strip()
        raw_uses = record["allowed_uses"]
        raw_platforms = record["platforms"]
        if not isinstance(raw_uses, (list, tuple, set, frozenset)):
            raise ValueError("allowed_uses must be a collection of scope strings")
        if not isinstance(raw_platforms, (list, tuple, set, frozenset)):
            raise ValueError("platforms must be a collection of platform strings")
        if any(not isinstance(item, str) or not item.strip() for item in raw_uses):
            raise ValueError("allowed_uses must contain non-empty strings")
        if any(not isinstance(item, str) or not item.strip() for item in raw_platforms):
            raise ValueError("platforms must contain non-empty strings")
        uses = frozenset(item.strip().lower() for item in raw_uses)
        if not uses or not uses.issubset(ALLOWED_USES):
            raise ValueError("allowed_uses must contain only analyze, edit, publish")
        platforms = sorted({item.strip().lower() for item in raw_platforms})
        if not platforms:
            raise ValueError("at least one permitted platform is required")
        raw_source_url = record["source_url"]
        if any(
            character.isspace() or ord(character) < 0x20
            or ord(character) == 0x7F or character == chr(92)
            for character in raw_source_url
        ):
            raise ValueError("source_url must not contain whitespace, control characters, or backslashes")
        source_url = raw_source_url.strip()
        try:
            parsed_source_url = urlsplit(source_url)
            # Accessing .port validates its numeric syntax and range.
            parsed_source_url.port
            if parsed_source_url.netloc.endswith(":"):
                raise ValueError("source_url must not have an empty port")
        except ValueError as exc:
            raise ValueError("source_url must be a valid http(s) URL") from exc
        hostname = parsed_source_url.hostname
        if (
            parsed_source_url.scheme.lower() not in ("http", "https")
            or not parsed_source_url.netloc
            or not hostname
            or not _valid_hostname(hostname)
            or parsed_source_url.username is not None
            or parsed_source_url.password is not None
        ):
            raise ValueError("source_url must be a valid http(s) URL without embedded credentials")
        values = (
            record["source_id"].strip(), source_url, record["grantor"].strip(),
            record["evidence_ref"].strip(), json.dumps(sorted(uses)),
            json.dumps(platforms), record.get("attribution", "").strip(),
            record.get("disclosure", "").strip(), _time(record["valid_from"]).isoformat(),
            _time(record["expires_at"]).isoformat()
            if record.get("expires_at") is not None else None,
            None,
        )
        if not all(values[:4]):
            raise ValueError("source_id, grantor, and evidence_ref must be non-empty")
        if values[9] and _time(values[9]) <= _time(values[8]):
            raise ValueError("expires_at must be later than valid_from")
        with self._connect() as db:
            try:
                # A source ID is an immutable grant identity. Updating an
                # existing row could broaden scope or clear a revocation.
                db.execute("""
                    INSERT INTO source_rights VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, values)
            except sqlite3.IntegrityError as exc:
                # Translate only a primary/unique-key collision. Other
                # integrity failures indicate a different database problem
                # and must retain their original exception for diagnosis.
                duplicate_codes = {
                    sqlite3.SQLITE_CONSTRAINT_PRIMARYKEY,
                    sqlite3.SQLITE_CONSTRAINT_UNIQUE,
                }
                if getattr(exc, "sqlite_errorcode", None) not in duplicate_codes:
                    raise
                raise PermissionError(
                    f"rights already exist for source {values[0]}; register a new source ID for a new grant"
                ) from exc
            db.execute("""
                INSERT INTO source_rights_audit(source_id, action, actor, occurred_at, details_json)
                VALUES (?, 'registered', ?, ?, ?)
            """, (values[0], actor, datetime.now(timezone.utc).isoformat(),
                  json.dumps({"uses": sorted(uses), "platforms": platforms})))

    def authorize(self, source_id: str, use: str, platform: str,
                  *, at: datetime | None = None) -> dict[str, Any]:
        """Return the grant metadata or raise PermissionError; unknown is blocked."""
        if any(not isinstance(value, str) or not value.strip()
               for value in (source_id, use, platform)):
            raise ValueError("source_id, use, and platform must be non-empty strings")
        source_id = source_id.strip()
        use = use.strip().lower()
        platform = platform.strip().lower()
        if use not in ALLOWED_USES:
            raise ValueError(f"unsupported use: {use}")
        with self._connect() as db:
            row = db.execute("SELECT * FROM source_rights WHERE source_id=?",
                             (source_id,)).fetchone()
        now = _time(at) if at is not None else datetime.now(timezone.utc)
        if row is None:
            raise PermissionError(f"no recorded rights for source {source_id}")
        if row["revoked_at"] and now >= _time(row["revoked_at"]):
            raise PermissionError(f"rights revoked for source {source_id}")
        if now < _time(row["valid_from"]):
            raise PermissionError(f"rights not yet valid for source {source_id}")
        if row["expires_at"] and now >= _time(row["expires_at"]):
            raise PermissionError(f"rights expired for source {source_id}")
        if use not in json.loads(row["allowed_uses_json"]):
            raise PermissionError(f"{use} is outside the recorded permission scope")
        if platform.lower() not in json.loads(row["platforms_json"]):
            raise PermissionError(f"{platform} is outside the permitted platforms")
        return {
            "source_id": row["source_id"], "source_url": row["source_url"],
            "grantor": row["grantor"], "evidence_ref": row["evidence_ref"],
            "attribution": row["attribution"], "disclosure": row["disclosure"],
        }

    def revoke(self, source_id: str, *, actor: str,
               at: datetime | None = None) -> bool:
        if any(not isinstance(value, str) or not value.strip()
               for value in (source_id, actor)):
            raise ValueError("source_id and actor must be non-empty strings")
        source_id = source_id.strip()
        actor = actor.strip()
        when = (_time(at) if at is not None else datetime.now(timezone.utc)).isoformat()
        with self._connect() as db:
            cur = db.execute("UPDATE source_rights SET revoked_at=? "
                             "WHERE source_id=? AND revoked_at IS NULL",
                             (when, source_id))
            if cur.rowcount:
                db.execute("""
                    INSERT INTO source_rights_audit(source_id, action, actor, occurred_at, details_json)
                    VALUES (?, 'revoked', ?, ?, '{}')
                """, (source_id, actor, when))
            return cur.rowcount == 1

    def audit_events(self, source_id: str) -> list[dict[str, str]]:
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError("source_id must be a non-empty string")
        source_id = source_id.strip()
        with self._connect() as db:
            rows = db.execute("""
                SELECT action, actor, occurred_at, details_json
                FROM source_rights_audit WHERE source_id=? ORDER BY id
            """, (source_id,)).fetchall()
        return [dict(row) for row in rows]
