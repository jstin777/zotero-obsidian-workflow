# Commands and configuration

Run commands from the template directory with `.venv/bin/python tools/workflow.py`. For an external vault, put `--vault /absolute/vault/path` **before** the command. `--help` lists supported arguments. Output is JSON; exit 0 indicates success, 1 an execution/setup error, and 2 reported issues/failure.

| Command | Purpose |
|---|---|
| `init --list-collections` | Read personal-library collection keys |
| `init --collection KEY --timezone Region/City` | Create configuration once |
| `init --demo` | Configure synthetic fixtures in a separate template copy |
| `doctor` | Check base/API/identity and enabled executable readiness |
| `sync [--dry-run]` | Mirror selected metadata, reading marks, notes and annotations |
| `status` | Inspect sync, jobs and pending note transactions |
| `convert ITEM` | Convert all PDFs of one synced paper with Marker |
| `index [--semantic]` | Rebuild current evidence search |
| `search QUERY [--method keyword\|semantic\|hybrid] [--limit N]` | Search registered originals and current summaries |
| `summarize ITEM` | Prepare an evidence packet for a worker |
| `summarize ITEM --run` | Run configured Codex and publish a new summary |
| `summarize ITEM --refresh --reason TEXT [--run]` | Prepare/propose a replacement |
| `summarize --publish FILE --token TOKEN [--accept]` | Validate a payload; explicitly accept a reviewed replacement |
| `scite ITEM` | Retrieve/store a dated DOI citation snapshot |
| `schedule check\|run\|install\|status\|disable\|uninstall` | Manage the local scheduler |
| `schedule queue\|retry --item ITEM` | Deliberately enqueue/retry a paper |

ITEM is a unique citation key or Zotero parent item key. Attachment keys and collection keys are different identifiers. Use `doctor` to check missing or duplicate citation keys.

## Configuration

`config.example.json` contains defaults; `init` creates ignored `config.local.json`. Keep local config out of public repositories. Supported settings:

- `collection_keys`: one or more personal-library collection roots; `include_children` defaults true.
- `timezone`: IANA name, default UTC.
- `routes`: Zotero parent item key → relative annotation subfolder. Unsafe paths are rejected.
- `citekey_overrides`: explicit item key → stable unique citation key when local Zotero does not expose one.
- `main_attachments`: parent item key → attachment key when a paper has several PDFs.
- `colors`: display color name → meaning, used for both highlight and sticky-note headings.
- `marker`, `qmd`, `codex`, `scite`: independent `enabled` switches and runtime settings.
- `scheduler`: `enabled` is managed by install/disable; `mode` is `convert` or `summary`; interval defaults 3600 seconds.
- `fixture`: present only in demo/test configuration; prevents live Zotero access.

Base sync is read-only toward Zotero. Scope controls inclusion, not human reading status or permission to acquire new papers. Personal content is ignored by Git even when the repository is public; backups are separate.
