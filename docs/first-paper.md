# Your first paper

## Try a synthetic demo first

Make a separate copy of the template. In that copy:

```sh
sh tools/setup.sh
.venv/bin/python tools/workflow.py init --demo
.venv/bin/python tools/workflow.py doctor
.venv/bin/python tools/workflow.py sync
.venv/bin/python tools/workflow.py sync
```

The second sync reports unchanged files. The fictional annotated paper appears under `papers/` and `zotero-notes/Example Topic/`; the unannotated paper still gets a library record. Open the two dashboards. Synthetic Zotero links illustrate link shape but do not point to your real library.

Write a sentence in an annotation file's **Local review and processing** section. Sync again and confirm it remains. `examples/demonstration.pdf` is an original, clearly fictional test document; it can be imported into a separate Zotero test library for manual practice. The JSON fixture's synthetic keys do not become the keys Zotero assigns on import.

The demo config never contacts Zotero. Do not switch a populated demo vault directly to the real library; begin with another clean template copy.

## Read a real paper

1. Select the configured collection in Zotero and save a paper using Chrome's Connector. Check the bibliography and downloaded attachment.
2. Add `reading/unread` if you know you have not read it. Apply its origin tag and add a discovery-provenance child note.
3. When starting, remove `reading/unread` and add `⏳`. Add a child note explaining why you are reading it.
4. Highlight a passage and add a comment. Add a sticky note in your own words. Use the [color key](reading-system.md).
5. Run the sync command or wait for the Obsidian plugin. Open the annotation note and follow its exact-annotation link back to Zotero.
6. Add your local review beneath the protected marker. Put a `#question/open` or `#idea/project` capture on its own line and find it in the dashboard.
7. When finished, remove `⏳` and add `✅`. The next successful sync updates the paper record and observes the status transition.
8. Enable Scite's columns/report action to inspect citation context. If you want whole-paper search, follow the optional Marker setup.

Selected collection membership controls what is mirrored. Reading status, working-library selection, and topic membership remain separate. Topic folders are not automatically created or rearranged in Zotero.
