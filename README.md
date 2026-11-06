# Zotero → Obsidian Workflow

A Mac-first reading system that keeps your bibliography and annotations in Zotero and gives you searchable Markdown notes, reading queues, and a place to develop your ideas in Obsidian.

**Start here: [Setup guide](docs/setup.md) · [Reading colors and tags](docs/reading-system.md) · [First-paper tutorial](docs/first-paper.md)**

The core runs locally without an AI account, PDF conversion, or a paid sync service. It includes annotation-note sync, paper records, reading-history observations, exact Zotero links, and dashboards. Marker adds searchable full-paper text; QMD, Codex summaries, Scite snapshots, and scheduled processing are optional.

## What you get

- Eight annotation colors with consistent meanings; separate quotes, personal comments, child notes, and local review.
- Read, reading, explicit unread, unknown, and conflicting-status views—even for papers without annotations.
- Discovery origins, read-next, importance, and working-library selection kept separate.
- A bundled desktop Obsidian plugin that checks every five minutes and on vault opening after configuration.
- Protected local writing, conflict reporting, source hashes, recoverable writes, and private processing state.
- Setup instructions for **Zotero Connector for Chrome**, **Better BibTeX**, and **Scite for Zotero**.
- Optional Marker, keyword/semantic search, evidence-grounded Codex summaries, and a Mac scheduler.

## Quick start

1. Choose **Use this template → Create a new repository**, or download the release ZIP. A private repository is appropriate for your own customization. Open the folder as an Obsidian vault.
2. Install Zotero Desktop, Better BibTeX, Obsidian, Chrome's Zotero Connector, and Python 3.12 using [the setup guide](docs/setup.md).
3. In Terminal, change to this folder and run:

```sh
sh tools/setup.sh
.venv/bin/python tools/workflow.py init --list-collections
.venv/bin/python tools/workflow.py init --collection YOUR_COLLECTION_KEY --timezone America/Chicago
.venv/bin/python tools/workflow.py doctor
.venv/bin/python tools/workflow.py sync
```

4. Enable the bundled **Zotero Reading Sync** plugin in Obsidian. Open [the library](dashboards/Library.md) and [capture dashboard](dashboards/Captures.md).

For a no-account demonstration, use a **separate copy** of the template and replace the two `init` commands with `init --demo`. This reads synthetic fixtures without contacting Zotero. See [First paper](docs/first-paper.md).

## Documentation

| Guide | Purpose |
|---|---|
| [Setup](docs/setup.md) | Required applications, Chrome Connector, Better BibTeX, first sync |
| [Reading system](docs/reading-system.md) | Highlight colors, tags, provenance and note ownership |
| [First paper](docs/first-paper.md) | Synthetic demo and live reading walkthrough |
| [Scite](docs/scite.md) | Zotero plugin, reports and optional dated Obsidian snapshots |
| [Optional modules](docs/optional-modules.md) | Marker, QMD, Codex and scheduler |
| [Commands](docs/commands.md) | Configuration and CLI reference |
| [Backup and updates](docs/backup-and-updates.md) | Preserve notes and processing authority; safe upgrades |
| [Troubleshooting](docs/troubleshooting.md) | Diagnose access, identity, conflicts and failed jobs |
| [Compatibility](docs/compatibility.md) | What was tested and remaining limitations |
| [Dependencies](docs/dependencies.md) | Versions, installers, licenses and account boundaries |

## Where your data goes

| Location | Contents |
|---|---|
| `papers/` | Generated bibliography/status records and local review |
| `zotero-notes/` | Imported annotations/notes and protected local review |
| `notes/` | Optional AI summaries |
| `sources/markdown/` | Optional immutable Marker conversions and assets |
| `.workflow/` | Private history, ownership, source registrations, jobs, logs and indexes |
| `config.local.json` | Your collection keys, timezone and executable paths |
| `templates/`, `dashboards/`, `docs/` | Shareable workflow materials |
| `examples/` | Fictional fixtures and an original demonstration PDF |

Personal content, configuration, and runtime directories are ignored by Git. They still need private backup. Zotero owns the original PDFs. No cloud upload or Git push runs automatically. Optional Codex processing sends the selected source material to the configured AI service; Scite looks up DOIs; QMD and Marker may download model weights.

This is a starting template, not a claim that a successful extraction or AI summary establishes scientific accuracy. Review important claims against originals.

MIT license for original code, docs and examples. See [THIRD_PARTY.md](THIRD_PARTY.md) for dependency notices.
