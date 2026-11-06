# Backup, recovery and updates

## Back up both Zotero and the vault

Use Zotero's [backup guidance](https://www.zotero.org/support/zotero_data). Zotero cloud synchronization is not a substitute for an independent backup. Keep PDFs, the library database, notes, and plugin configuration together according to Zotero's instructions.

Privately back up the entire workflow vault, including ignored content:

- `papers/`, `zotero-notes/` and any local review writing.
- `notes/` and `sources/markdown/` with their assets.
- `config.local.json`.
- **`.workflow/`**: ownership hashes, reading history, source registrations, summary publication authority, recovery journals, queue and logs.

The Git template contains code/docs and examples, not these private backups. `git clone` alone does not restore your reading or publication history. Runtime environments can be recreated. Search indexes (`search.sqlite`, search-manifest, QMD index/projections) can be rebuilt; ownership, reading history, sources.json and summaries.json cannot safely be reconstructed by trusting arbitrary current note bytes.

## Restore

Stop the Obsidian sync plugin and disable the LaunchAgent. Wait for live workers to end; do not delete process guards to force progress. Restore the matching Zotero library and vault snapshot. Restore private state with its corresponding files, then recreate `.venv` using `tools/setup.sh`. Reinstall optional runtimes and update absolute paths if needed.

Run `doctor`, `sync --dry-run`, and `status`. Resolve differences before regular sync. A different Zotero server/database identity requires a separate vault or its matching state. Do not edit the stored server ID or source hashes to force acceptance. Rebuild search with `index`, then `index --semantic` if enabled. Reinstall the scheduler only after manual operation succeeds.

## Interrupted work

Pending note writes recover on the next real sync. Publication journals recover when a summary command or scheduler runs. Recovery verifies the expected before/after bytes; edits on either side remain conflicts. Preserve logs/journals until you understand the failure. A process identity guard can remain after interruption: inspect its PID/start identity and wait for the child to end; the workflow checks it before launching another child.

## Update

Read release notes first. Back up privately and stop sync/scheduling. In a temporary clean directory, download the new release and run its demo/tests. Compare configuration examples and release migration notes. Apply code, docs, templates, and bundled-plugin updates to your customized copy with a reviewed Git merge or selective file copy; never replace personal directories or `config.local.json` wholesale.

Re-run the base installer, `doctor`, and a dry-run sync. Template changes can intentionally update generated regions; local review remains preserved. Reinstall the LaunchAgent when paths/runtime versions change. Retain the prior release and backup until your own paper workflow passes. There is no automatic self-updater.
