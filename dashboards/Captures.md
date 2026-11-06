# Capture dashboard

Searches annotation notes and paper local-review sections. Put completion tags on the same line as the original capture. Edit imported text in Zotero.

## Ideas

```query
(path:zotero-notes OR path:papers) line:((#idea/project OR #project/idea) -#promoted)
```

## Questions

```query
(path:zotero-notes OR path:papers) line:(#question/open -#resolved)
```

## Useful methods

```query
(path:zotero-notes OR path:papers) line:(#method/useful -#processed)
```

## Read next

```query
(path:zotero-notes OR path:papers) line:(#read/next -#processed -/^\s*[-*+]\s+\[[xX]\]/)
```

## Next actions

```query
(path:zotero-notes OR path:papers) line:(#action/next -#processed -/^\s*[-*+]\s+\[[xX]\]/)
```

## Knowledge

```query
(path:zotero-notes OR path:papers) line:(#Knowledge OR #knowledge)
```

## Card candidates

```query
(path:zotero-notes OR path:papers) line:(#card/candidate -#processed)
```

## Promoted

```query
(path:zotero-notes OR path:papers) line:(#promoted)
```

## Resolved

```query
(path:zotero-notes OR path:papers) line:(#resolved)
```

## Processed

```query
(path:zotero-notes OR path:papers) line:(#processed)
```

## Completed tasks

```query
(path:zotero-notes OR path:papers) task-done:(#read/next OR #action/next)
```
