# Local media authorization gate

Before a future renderer can access a recording, call
validate_authorized_media_asset with the local path, matching source ID,
permission record, and timezone-aware approval timestamp.

The permission record must include the process_media scope and must be
within its grant, expiry, and revocation window. The validator rejects source
mismatches, missing paths, directories, and symbolic links. It returns a
resolved local file path only after those checks pass.

This is a narrow preflight gate, not a rights determination or a renderer. It does
not download, decode, edit, or publish media. Keep third-party music/game rights
and platform restrictions in the human review process. Publishing remains disabled.
