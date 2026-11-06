# Reading colors, tags and ownership

## Color key

| Color | Meaning | Typical comment |
|---|---|---|
| Gray | Context | Why this passage matters here |
| Yellow | Claims, results, supporting evidence | Restate the finding |
| Blue | Definitions, theory, models, background | Explain the concept |
| Green | Methods, operational definitions, analysis | What could I reuse? |
| Red | Limitations, contradictions, uncertainty, questions | What does this fail to establish? |
| Purple | Personal ideas, connections, interpretations | Connect to a project |
| Orange | Follow-up actions and reading | A concrete next step |
| Magenta | Recall and possible flashcards | Something worth remembering |

Use the same meanings for highlights and sticky notes. Prefix a sticky note with Introduction, Methods, Results or Discussion when section context matters. A color describes the role of a capture; it never authorizes an automatic action. Color meanings can be customized in `config.local.json` under `colors`.

## Paper tags and shortcuts

In Zotero's tag selector, assign a color to a tag and place it in the shortcut position shown below. Verify the resulting number shortcut in your Zotero version. These are paper-level labels, separate from PDF annotation colors and note-capture tags. Existing shortcuts are not modified by the template.

| Key | Exact tag | Meaning |
|---|---|---|
| 1 | `⏳` | Currently reading |
| 2 | `✅` | Read |
| 3 | `⭐️` | Important |
| 4 | `👎` | Not useful |
| 5 | `📌 reading/next` | Chosen for next reading |
| 6 | `📥 status/selected` | Selected for the working library |
| 7 | `🌱 origin/personal` | Found in personal browsing/reading |
| 8 | `👤 origin/recommended` | Recommended or sent by someone |
| 9 | `🔎 origin/literature-search` | Found through a literature search |

Also use uncolored `reading/unread` for confirmed unread and `status/candidate` for awaiting selection. Remove the previous reading-status tag when changing status: the independent toggles do not do this automatically. Two or three of `reading/unread`, `⏳`, and `✅` produce a visible conflict. No reading tag means unknown. Important, not useful, selected, and read-next do not determine reading status.

Initial read/reading marks have unknown historical dates. Later changes get observation timestamps and calendar dates in the configured timezone. These describe what a successful sync observed, not the exact time you read. A mark toggled between checks can be missed. Re-adding read does not prove rereading.

## Capture tags

| Tag | Use | Completion |
|---|---|---|
| `#idea/project` | Project idea or connection | Add `#promoted` and a destination link |
| `#question/open` | Question | Add `#resolved` and the answer/link |
| `#method/useful` | Reusable method | Add `#processed` and a destination |
| `#read/next` | Reading action | Complete its checkbox or add `#processed` |
| `#action/next` | Action | Complete its checkbox or add `#processed` |
| `#Knowledge` | Knowledge to retain | Preserve context and link durable notes |
| `#card/candidate` | Possible flashcard | Review deliberately; cards are not generated |
| `#promoted` | Idea developed elsewhere | Preserve the destination |
| `#resolved` | Question answered | Preserve the answer |
| `#processed` | Capture handled | Preserve the outcome |

Legacy `#knowledge` and `#project/idea` are recognized by the dashboard. Tags can appear in annotation comments, annotation tags, child notes, or local review. Complete an imported capture in Zotero. Completion tags belong on the same line as the capture; a separate linked local task does not suppress an unchanged source line.

## Discovery provenance

Origin tags answer **how did this paper enter my reading workflow?** They do not describe its journal or publisher. Attach a paper-level child note using [the provenance template](../templates/discovery-provenance.md). Record the recommender, URL/search query, date when known, and context. Preserve unknowns and distinguish explicit information from inference. Subsequent searches do not erase the original discovery history. The sync does not infer an origin from a PDF upload.

## Which text can I edit?

Zotero owns imported quotations, comments, sticky notes and child notes. Obsidian owns the section after `<!-- zotero-local-review -->`. Both paper records and annotation files have this local section. Imported-region edits trigger a conflict and are preserved, not overwritten. Never remove the marker.

Paper-level child notes appear at the top. Sticky notes and highlights are separate and grouped by color; attachment notes appear last. PDF links use one-based physical pages, which can differ from printed page labels. Image/ink annotations link to Zotero; embedded child-note media depend on their original links.

One annotation file belongs to one Zotero item. Collection descendants route into matching folders; unrelated memberships use `_unfiled` unless `routes` supplies an item-key override. Safe moves preserve local review and leave a redirect. Citation-key changes preserve existing filenames. Standalone notes and group libraries are outside v0.1 scope.
