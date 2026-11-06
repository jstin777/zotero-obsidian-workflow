# Dependencies and accounts

| Layer | Required software | Pinned/tested package inputs |
|---|---|---|
| Base reading | Python 3.12+, Zotero Desktop with local API, Better BibTeX, Obsidian desktop | `requirements.txt`: PyYAML 6.0.3, markdownify 1.2.3 and pinned transitive dependencies |
| Browser saving | Chrome and Zotero Connector | Install current official application/extension; record tested versions in compatibility report |
| Scite in Zotero | Official Scite XPI | Plugin installed separately; no Scite code or credentials bundled |
| Scite snapshots | Base Python + network | Standard-library DOI tally request; unavailable results handled explicitly |
| PDF conversion | Python 3.12 environment, llama.cpp backend | Marker 2.0.0, Surya 0.22.1, PyTorch 2.13.0, PyMuPDF 1.28.0 in `tools/requirements-marker.txt` |
| Semantic search | Node 24.22.1, pnpm 11.25.0, Xcode Command Line Tools for native builds | QMD 2.8.3 commit `93d211f9ef4a869a9aed0d075ca767dda552627f`; SHA-256 verified source and frozen `tools/qmd-pnpm-lock.yaml` |
| AI summaries | Marker module, Codex CLI and an authenticated account | Local CLI capability checks; configurable model; no model/access promise |
| Scheduling | macOS launchd, configured optional modules | Per-vault LaunchAgent; no system service/root requirement |
| Development | Base plus ReportLab/pypdf | `tools/requirements-dev.txt`; not needed to use already-generated examples |

Base dependencies and the QMD tree are pinned. Marker pins the main conversion packages; its transitive package graph and downloaded weights are upstream-managed, so this is not a fully hermetic ML runtime. Record `pip freeze` privately after installation when reproducibility matters. See [Compatibility](compatibility.md) for the environment actually exercised.

On a new Mac, `xcode-select --install` provides the compiler tools needed by some optional Node/Python dependencies. Follow Apple's installer. Do not install Marker or QMD for annotation sync alone.

No subscription is required for base local sync. Zotero cloud storage and Obsidian Sync are separate optional services. Codex account availability/usage limits vary. Scite plugin installation and report/product access are separate concerns. Downloading a PDF remains subject to your existing access rights. Third-party license links are in [THIRD_PARTY.md](../THIRD_PARTY.md).
