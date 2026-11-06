# Install on a Mac

## 1. Get a clean vault

Use the GitHub template button or extract the release ZIP. Put the folder somewhere you own, such as `~/Research/zotero-obsidian-workflow`. Open Obsidian → Open folder as vault. Avoid using an existing populated vault for your first setup.

The template contains no personal library. The synthetic demo uses a separate copy so its identity/history cannot be mistaken for your real Zotero library.

## 2. Applications

- Install [Zotero Desktop](https://www.zotero.org/download/). This release targets the local API of current Zotero; see the tested versions in [Compatibility](compatibility.md).
- Install [Obsidian](https://obsidian.md/download). Use a desktop release with Bases enabled for the library table. The capture dashboard uses core Search.
- Install [Better BibTeX for Zotero](https://retorque.re/zotero-better-bibtex/installation/) from its official release XPI using Zotero → Tools → Plugins → gear → Install Plugin From File. Restart if requested. Preserve existing citation keys; do not regenerate your library's keys to try this template. Pin keys you use in writing. The workflow reads `citationKey` from the local API; `doctor` reports absent keys. Explicit `citekey_overrides` are available if necessary.
- Install [Python 3.12](https://www.python.org/downloads/) or use [Homebrew](https://brew.sh): `brew install python@3.12`. The Mac system Python may be too old.

## 3. Zotero Connector for Chrome

Install the **official [Zotero Connector](https://www.zotero.org/download/connectors)** in Chrome. Pin its toolbar button using Chrome's Extensions menu. In the Connector's options, verify that Zotero Desktop is available.

Create or choose a collection such as **Reading Library**, optionally with an **Inbox** subcollection. Select the intended collection in Zotero, visit an article's publisher/record page in Chrome, and click Save to Zotero. Check title, authors, year, DOI, collection membership, and any attachment. A publisher page often supplies better metadata than a bare PDF URL.

Connector saving does not guarantee PDF access. Download an accessible PDF and attach it to the correct parent item when needed. Keep Zotero open for this local workflow; cloud-library saving is a separate Connector feature. See the [official guide](https://www.zotero.org/support/connector).

Add discovery and reading tags yourself. Saving through Chrome alone does not reveal whether a paper was recommended, personally discovered, read, or unread.

## 4. Enable local communication and choose scope

In Zotero Settings → Advanced, enable **Allow other applications on this computer to communicate with Zotero**. Keep Zotero running. Ordinary workflow sync uses the unauthenticated loopback [local API](https://www.zotero.org/support/dev/web_api/v3/local_api) and does not write Zotero records. Do not expose port 23119 externally.

In Terminal, type `cd `, drag the template folder into Terminal, and press Return. Then:

```sh
sh tools/setup.sh
.venv/bin/python tools/workflow.py init --list-collections
```

Find your collection's key in the output; a collection key is different from its name, a paper key, and a citation key. Initialize once:

```sh
.venv/bin/python tools/workflow.py init --collection YOUR_COLLECTION_KEY --timezone America/Chicago
.venv/bin/python tools/workflow.py doctor
.venv/bin/python tools/workflow.py sync --dry-run
.venv/bin/python tools/workflow.py sync
```

Use your own IANA timezone. Omitting it selects UTC. Descendant collections are included by default. Repeat `--collection` to include additional roots in the same personal library. Group libraries are not supported in v0.1.

Initialization refuses to overwrite existing configuration. Edit `config.local.json` deliberately to change scope; removed papers are preserved and become inactive in private processing state. Collection scope changes do not delete notes.

## 5. Enable Obsidian sync

Open Settings → Community plugins, allow community plugins after reviewing the bundled source, and enable **Zotero Reading Sync**. Its source is included at `.obsidian/plugins/zotero-reading-sync/main.js`; there is no third-party community-directory download for this template plugin.

After configuration, it runs on opening the vault and every five minutes. Command palette → **Zotero Reading Sync: Sync Zotero reading notes now** runs immediately. Assign a hotkey in Obsidian's Hotkeys settings if desired. Disable automatic sync in the plugin's settings when troubleshooting.

The plugin uses this vault's `.venv/bin/python`; moving the vault requires rebuilding the environment. Both Zotero and this Obsidian vault must be open for automatic annotation sync. Scheduled conversion is configured separately.

## 6. Configure reading tags and Scite

Follow [Reading system](reading-system.md) for colored-tag shortcut positions and meanings. The template does not silently replace existing Zotero shortcuts. Follow [Scite](scite.md) to install the citation-context plugin and verify its columns/report links.

Then complete [First paper](first-paper.md). Marker is optional but strongly recommended when you want full-paper search in Obsidian.
