# Optional modules

Enable modules in `config.local.json` only after their checks succeed. The core reading workflow requires none of them.

## Marker: strongly recommended for full-paper search

Obsidian can immediately search imported metadata, annotations and personal review. Marker adds the rest of each PDF as Markdown, with images and page boundaries. It does not guarantee correct table, equation or OCR extraction.

Install the pinned converter separately:

```sh
brew install llama.cpp
python3.12 -m venv .marker-venv
.marker-venv/bin/python -m pip install -r tools/requirements-marker.txt
```

Marker 2's CPU/Apple Silicon backend requires `llama-server`; its model weights download on first use. See [upstream installation](https://github.com/datalab-to/marker#installation) and its model-weight license. No cloud-assisted conversion is enabled. Expect larger downloads and more memory than the base workflow. Check free disk space before converting a large library.

Set `marker.enabled` to `true`, retaining `.marker-venv/bin/marker_single` as the executable, then:

```sh
.venv/bin/python tools/workflow.py doctor
.venv/bin/python tools/workflow.py convert YOUR_CITEKEY
.venv/bin/python tools/workflow.py index
.venv/bin/python tools/workflow.py search 'a phrase from the paper'
```

All PDF attachments are converted. Missing downloads produce an actionable error. Existing PDFs remain in Zotero; immutable Markdown and assets go to `sources/markdown/`. Every version records PDF/output hashes, converter version/settings and physical-page coverage. Changing a PDF creates a new conversion version on explicit conversion. Altered registered Markdown is rejected; restore its original bytes rather than editing hashes. An orphaned output directory from a failed registration is preserved for inspection.

With several PDFs, set `main_attachments` to an item-key → main-attachment-key map before summarizing; other attachments are labelled supplements. Inspect that classification yourself.

## QMD semantic/hybrid search

Keyword evidence search uses Python's SQLite FTS5 and needs no extra search package. QMD is optional and downloads local models. Install **Node 24.22.1** and **pnpm 11.25.0** using their official distributions/version manager. Those are the release's test versions. Then:

```sh
.venv/bin/python tools/install_qmd.py --node /absolute/path/to/node --pnpm /absolute/path/to/pnpm
.venv/bin/python tools/workflow.py index --semantic
.venv/bin/python tools/workflow.py search 'the concept I remember' --method semantic
.venv/bin/python tools/workflow.py search 'the concept I remember' --method hybrid
```

The installer uses QMD 2.8.3 at a checksum-verified commit and the included frozen pnpm lock. It builds a private runtime, not a global installation. Source/summary hashes are checked before each query. Human annotations remain available through Obsidian search and are not ranked as scientific evidence. Scite counts are excluded from evidence search. Index failures do not invalidate a successful summary publication; repair/rebuild the index separately.

## Codex summaries

Install [Codex CLI](https://developers.openai.com/codex/cli/) and authenticate using the CLI's supported login. Set `codex.enabled` to `true`; set `codex.executable` to its absolute executable path for scheduling. `codex.model` can be an explicit model available to your account; `null` uses the CLI's configured default. Account limits and service costs follow your account.

After conversion:

```sh
.venv/bin/python tools/workflow.py summarize YOUR_CITEKEY --run
```

Each run gets a fresh packet containing original text, PDF copies, metadata, and source versions. The worker runs with a read-only sandbox and returns schema-constrained JSON. Publication validates section completeness, source versions, physical pages, exact quotations, and intervening note edits. These checks do not prove scientific support. Review the resulting summary against originals.

To use a compatible agent manually, run `summarize YOUR_CITEKEY` to prepare a packet, follow its instructions, then publish its JSON:

```sh
.venv/bin/python tools/workflow.py summarize --publish /path/to/payload.json --token TOKEN
```

Replacing an existing summary requires a deliberate proposal:

```sh
.venv/bin/python tools/workflow.py summarize YOUR_CITEKEY --run --refresh --reason 'Explain why revision is needed'
# Inspect proposed.md and comparison.diff in the returned job directory.
.venv/bin/python tools/workflow.py summarize --publish /path/to/job/payload.json --token TOKEN --accept
```

Packets expire after 24 hours. Intervening edits or changed sources require preparation again. Source Markdown, copied PDFs and the summary request are provided to the configured AI service. Review your data-sharing obligations before enabling it. No paper acquisition, Zotero editing, card creation or Git commit happens in the worker.

## Optional Mac scheduler

Default: disabled, hourly interval, conversion-only mode, at most one eligible paper per tick. Initial library records are deferred. New arrivals after the first successful sync are eligible; queue an older paper explicitly.

Configure and test Marker first. For AI summaries, also configure Codex and set `scheduler.mode` to `summary`. Set `scheduler.notifications` to `false` to disable notifications.

```sh
.venv/bin/python tools/workflow.py schedule check
.venv/bin/python tools/workflow.py schedule queue --item YOUR_CITEKEY
.venv/bin/python tools/workflow.py schedule run
.venv/bin/python tools/workflow.py schedule install
.venv/bin/python tools/workflow.py schedule status
```

`check` refreshes metadata and reports the next eligible job without conversion or AI. `run` is an explicit immediate tick even when the LaunchAgent is disabled. Installation loads a per-vault LaunchAgent without starting an AI job at installation. It runs while you are logged in and the Mac is awake; Zotero must be open. Sleep delays work. macOS Documents/Desktop access restrictions may require permission for the actual scheduled executable; try a vault outside those protected folders before broadening permissions.

Idle checks use no model. Failures wait six hours and stop after three attempts. Other eligible jobs can progress. `schedule retry --item KEY` resets that item's retry budget deliberately. Existing summaries are never automatically replaced; use reviewed refresh. Locks and persistent child-process identities prevent overlapping workers after interruptions.

```sh
.venv/bin/python tools/workflow.py schedule disable
# Equivalent removal command; preserves notes, logs, history and queue:
.venv/bin/python tools/workflow.py schedule uninstall
```

Reinstall after moving the vault or changing Python/CLI paths. Notification delivery depends on macOS permissions/Focus; saved status and logs remain authoritative. Check source freshness before interpreting a completed job. Topic sorting and Git operations are not scheduler steps.
