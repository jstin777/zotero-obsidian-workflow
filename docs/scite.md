# Scite in Zotero and Obsidian

## Zotero plugin

1. Download the XPI from the [official Scite Zotero plugin releases](https://github.com/scitedotai/scite-zotero-plugin/releases).
2. In Zotero, open Tools → Plugins → gear → Install Plugin From File, select the XPI, and restart if requested.
3. Enable Supporting, Contrasting, Mentioning, Total Smart Citations and Total Distinct Citing Publications through the library column-header menu.
4. Select a paper with a DOI. Refresh its Scite data using the plugin's item menu, then open its Scite report through the plugin's report action. Check that the report identifies the same paper.

The [plugin's documentation](https://github.com/scitedotai/scite-zotero-plugin) says the plugin requires no account or API key and its v2 releases support Zotero 7+. Report pages or other Scite products can have different access requirements. Check actual access rather than assuming an institutional subscription. The template neither installs subscription credentials nor purchases access.

Plugin/API compatibility tested for this release is recorded in [Compatibility](compatibility.md). If columns do not appear, confirm the plugin is enabled and supports your Zotero version. A missing DOI, unavailable record, stale cache or network failure should not be interpreted as zero citations.

## Optional snapshots in Obsidian

After a successful sync:

```sh
.venv/bin/python tools/workflow.py scite YOUR_CITEKEY
```

This sends the paper DOI to Scite's tally service and stores a dated JSON snapshot under private `.workflow/scite/`. It does not alter Zotero or hand-edit an existing summary. Enable `scite.enabled` in `config.local.json` to include citation context when publishing a new summary or a reviewed refresh. It is disabled by default and there is no recurring bulk refresh.

Snapshots retain the matching DOI/report, checked and retrieved timestamps, six count fields, or an explicit unavailable/no-DOI reason. A failed later lookup preserves an earlier successful snapshot with its original date. Errors do not block publication. If the service changes its access requirements, the lookup reports unavailable; it does not bypass access controls.

Citation statements and distinct citing publications are different counts. Supporting/contrasting classifications do not establish independent replication or whole-paper validity. Read the report's passages and the citing papers before interpreting later evidence. Citation tallies are excluded from scientific keyword and semantic retrieval.
