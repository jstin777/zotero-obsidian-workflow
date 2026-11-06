# Compatibility and validation

Release validation date: **2026-11-06**. This is an initial preview release, not a claim of broad app/OS compatibility.

## Verified so far

| Component | Environment / evidence |
|---|---|
| Base install | Fresh Python 3.12.13 virtual environments on macOS 26.6.2, Apple Silicon arm64; clean tracked-file export installed with base dependencies only |
| Deterministic workflow | Synthetic two-paper library: one annotated, one unannotated; repeated sync unchanged |
| Offline tests | 33 passing tests for sync, ownership, history, routing, recovery, source validation, publication, Scite failure handling and scheduler behavior |
| Marker | Real conversion of the original one-page demo with installed Marker 2.0.0, Surya 0.22.1, torch 2.13.0, PyMuPDF 1.28.0; existing converter environment reused |
| QMD | Fresh checksum-verified QMD 2.8.3 runtime built with Node 24.22.1 and pnpm 11.25.0; real semantic and hybrid queries returned the demo source |
| Scite tally service | Successful live DOI lookup, matching DOI and all six count fields; no API credential supplied |
| Zotero local API / Better BibTeX | Read-only API probe on Zotero 11.0/API v3; 100 sampled parent records exposed citationKey; Better BibTeX 9.0.77 active |
| Scite Zotero plugin | Version 2.0.5 reported active by Zotero profile metadata; columns/report UI not verified |
| Codex | Real CLI invocation returned structured JSON for the synthetic paper and passed guarded publication; CLI account defaults used |
| Native scheduler | Isolated synthetic vault: actual LaunchAgent install, idle/no-AI execution, explicit queued conversion, and removal tested |
| Demo PDF | Rendered and visually inspected; all text fits and is clearly marked synthetic |
| Bundled Obsidian plugin | JavaScript syntax plus mocked settings/setup/concurrency/success behavior checked; UI opening attempted in Obsidian 1.14.4 but folder picker remained disabled, followed by computer-use capture failure |

## Remaining live checks

- A fresh isolated Zotero profile with the Chrome Connector saving and Scite's Zotero UI columns/report action has not yet been exercised. Installed application presence or a successful local API probe does not verify these UI flows.
- Better BibTeX citation-key exposure was checked read-only on the current library; destination libraries must still pass `doctor`.
- Fresh installation of the entire Marker ML stack and first-time model downloads has not been exercised; only the installed runtime conversion was tested.
- Intel Macs, older macOS/Zotero versions, Windows, Linux desktop integration and group libraries are unverified. Offline Linux CI does not establish desktop support.
- Scientific accuracy on real research papers is not certified by the demonstration or quote-validation tests.

No personal library records, source papers or private processing history were used as distributed test fixtures. The real Zotero library was not modified for these tests. Synthetic keys are intentionally nonfunctional outside the fixture adapter.
