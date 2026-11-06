# Troubleshooting

| Symptom | Check/action |
|---|---|
| Connection refused | Start Zotero Desktop. Confirm local communication is enabled and port 23119 is available. |
| HTTP 403 | Enable Zotero Settings → Advanced → local application communication. |
| Missing collection | Run `init --list-collections`; use collection keys, not names. Review config without deleting existing notes. |
| Missing citation key | Enable Better BibTeX, verify a citation key is exposed, or add a deliberate `citekey_overrides` entry. |
| Duplicate key | Resolve identity/key ambiguity in Zotero; the sync will not silently merge papers or overwrite a file. |
| Imported region edited | Preserve the file. Move intended local writing into Local review; restore imported bytes from a backup or reconcile against Zotero. Do not rewrite ownership hashes. |
| Routing destination exists | Preserve both files and compare local review before changing routes. |
| Reading conflict | Keep only the intended one of `reading/unread`, `⏳`, `✅`. |
| Wrong Chrome save location | Select the intended collection in Zotero and inspect the Connector save popup. Verify actual membership after saving. |
| Connector cannot reach Zotero | Check Connector options and Zotero's running state. Online-library saving is a separate path and may need cloud sync. |
| PDF absent | Download an accessible attachment in Zotero. Connector metadata saving does not guarantee full text. |
| Scite columns absent | Verify compatible plugin/version, enable columns, inspect DOI, refresh and open the matching report. |
| Scite unavailable | Preserve status as unavailable. Check network/report access; do not substitute zero. |
| Marker silent | Inspect `.workflow/logs/`; model download/OCR can be slow. Check its active process before retrying. |
| Marker lacks backend | Install llama.cpp and ensure `llama-server` is available to the actual runtime/scheduler. |
| Source changed | Restore registered bytes or explicitly convert a changed PDF and review a new summary proposal. Never edit source hashes. |
| Workflow busy | Another sync/conversion/worker owns the coordinator. Wait; do not remove locks or start overlapping conversions. |
| Previous worker may still run | Inspect `.workflow/child-process.json`; the PID/start identity may outlive the caller. Preserve the guard until termination is established. |
| Semantic search fails | Inspect `.workflow/qmd/last.log`, verify Node/pnpm/runtime versions and model access; keyword search remains available. |
| Codex fails | Check executable/authentication/account access and the job's `runner.log`. No approval bypass is installed. |
| Scheduler idle | Initial papers are deferred. Use `schedule queue --item KEY`; check Mac sleep/login/Zotero state. |
| Scheduler cannot access Documents | Inspect LaunchAgent logs and macOS permissions for its Python executable; consider a vault outside protected folders. |
| Retry exhausted | Review the failure and fix it, then `schedule retry --item KEY`. |

`doctor` does not inspect Chrome UI or claim end-to-end processing from executable availability. Manual verification steps and test coverage are listed in [Compatibility](compatibility.md).
