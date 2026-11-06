#!/usr/bin/env python3
"""Read-only Scite tally snapshots for guarded paper-summary publication."""
import argparse
import datetime as dt
import json
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request


COUNTS = ('supporting', 'contradicting', 'mentioning', 'unclassified', 'total', 'citingPublications')
HEADING = 'Scite citation context'


def normalize_doi(value):
    return re.sub(r'^(?:doi:\s*|https?://(?:dx\.)?doi\.org/)', '', value.strip(), flags=re.I).lower()


def report_url(doi):
    return 'https://scite.ai/reports/' + urllib.parse.quote(doi, safe='/') if doi else None


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError('Scite timestamp must be an ISO datetime with timezone')
    parsed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Scite timestamp must include timezone')
    return parsed


def validate(snapshot, expected_doi):
    if not isinstance(snapshot, dict) or type(snapshot.get('schema_version')) is not int or snapshot['schema_version'] != 1:
        raise ValueError('Scite snapshot must have schema_version 1')
    doi = normalize_doi(expected_doi or '')
    if snapshot.get('doi') != doi or snapshot.get('report_url') != report_url(doi):
        raise ValueError('Scite snapshot DOI/report must match the focus paper')
    timestamp(snapshot.get('checked_at'))
    state = snapshot.get('status')
    if state == 'retrieved':
        if not re.fullmatch(r'10\.\d{4,9}/\S+', doi):
            raise ValueError('Retrieved Scite snapshot needs a full DOI')
        if timestamp(snapshot.get('retrieved_at')) != timestamp(snapshot['checked_at']):
            raise ValueError('Scite retrieval time must match successful check time')
        counts = snapshot.get('counts')
        if not isinstance(counts, dict) or set(counts) != set(COUNTS) or any(
                type(counts[k]) is not int or counts[k] < 0 for k in COUNTS):
            raise ValueError('Scite counts must be complete nonnegative integers; unavailable is not zero')
    elif state in ('unavailable', 'no-doi'):
        if snapshot.get('counts') is not None or snapshot.get('retrieved_at') is not None:
            raise ValueError('Failed Scite checks cannot claim counts or a retrieval date')
        if not isinstance(snapshot.get('reason'), str) or not snapshot['reason'].strip():
            raise ValueError('Unavailable Scite snapshot needs a reason')
        if (state == 'no-doi') != (not doi):
            raise ValueError('Scite no-doi status must match paper identity')
    else:
        raise ValueError('Unknown Scite snapshot status')
    if 'last_attempt' in snapshot:
        attempt = snapshot['last_attempt']
        if state != 'retrieved' or not isinstance(attempt, dict) or not isinstance(attempt.get('reason'), str):
            raise ValueError('Only a retained successful Scite snapshot can carry a failed later attempt')
        if timestamp(attempt.get('checked_at')) < timestamp(snapshot['retrieved_at']):
            raise ValueError('Failed later Scite attempt predates the retained snapshot')
    return snapshot


def retrieve(doi, opener=None, checked_at=None):
    opener = opener or urllib.request.urlopen
    doi = normalize_doi(doi or '')
    now = checked_at or dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    result = dict(schema_version=1, doi=doi, report_url=report_url(doi), status='unavailable',
        checked_at=now, retrieved_at=None, counts=None, reason=None)
    if not doi:
        result.update(status='no-doi', reason='No DOI in the verified paper metadata.')
    elif not re.fullmatch(r'10\.\d{4,9}/\S+', doi):
        result['reason'] = 'Missing or invalid full DOI; resolve the paper DOI before retrying.'
    else:
        endpoint = 'https://api.scite.ai/tallies/' + urllib.parse.quote(doi, safe='')
        try:
            with opener(urllib.request.Request(endpoint, headers={'Accept': 'application/json'}), timeout=20) as response:
                data = json.load(response)
            if not isinstance(data, dict) or normalize_doi(data.get('doi', '') or '') != doi:
                raise ValueError('Scite returned no matching DOI.')
            if any(type(data.get(k)) is not int or data[k] < 0 for k in COUNTS):
                raise ValueError('Scite returned incomplete or invalid counts.')
            # Timestamp successful response receipt, not the start of a network request.
            received = checked_at or dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
            result.update(status='retrieved', checked_at=received, retrieved_at=received,
                counts={k:data[k] for k in COUNTS}, reason=None)
        except urllib.error.HTTPError as error:
            result['reason'] = 'Scite tally service returned HTTP ' + str(error.code) + '.'
        except (OSError, ValueError, TypeError, AttributeError) as error:
            result['reason'] = 'Scite lookup unavailable: ' + str(error)[:300]
    return validate(result, doi)


def merge(previous, fresh, doi):
    """Retain a genuine dated snapshot if a later request fails."""
    if previous is not None:
        validate(previous, doi)
    if fresh is None:
        return previous
    validate(fresh, doi)
    if previous and previous['status'] == 'retrieved' and fresh['status'] == 'unavailable':
        result = dict(previous, last_attempt={'checked_at':fresh['checked_at'], 'reason':fresh['reason']})
        return validate(result, doi)
    return fresh


def plain(value):
    # Service/error text cannot introduce Markdown headings or HTML comments.
    return ' '.join(str(value).split()).replace('<', '&lt;').replace('>', '&gt;')


def render(snapshot):
    validate(snapshot, snapshot['doi'])
    lines = ['## ' + HEADING, '']
    if snapshot['report_url']:
        lines += ['[Scite report](' + snapshot['report_url'] + ')', '']
    if snapshot['status'] == 'retrieved':
        counts = snapshot['counts']
        lines += ['**Retrieved:** ' + snapshot['retrieved_at'], '',
            '| Scite metric | Count |', '|---|---:|']
        for key, label in (('supporting','Supporting citation statements'),
                ('contradicting','Contrasting citation statements'), ('mentioning','Mentioning citation statements'),
                ('unclassified','Unclassified citation statements'), ('total','Total Smart Citations'),
                ('citingPublications','Distinct citing publications')):
            lines.append('| ' + label + ' | ' + str(counts[key]) + ' |')
        lines += ['', '**Context review:** Counts only; this snapshot does not include review of citing passages or papers.']
        if snapshot.get('last_attempt'):
            attempt = snapshot['last_attempt']
            lines += ['', '**Later check unavailable:** ' + attempt['checked_at'] + ' — ' + plain(attempt['reason'])
                + ' The successful snapshot above retains its original retrieval date.']
    else:
        lines += ['**Check attempted:** ' + snapshot['checked_at'], '',
            '**Status:** ' + snapshot['status'] + ' — ' + plain(snapshot['reason']), '',
            'No verified counts were retrieved; unavailable data is not zero.']
    lines += ['', '_Counts describe automatically classified citation statements within Scite’s coverage. '
        'One paper can contribute multiple statements, and statements may concern different claims or methods. '
        'Supporting/contrasting labels do not establish independent replication or whole-paper validity. '
        'Coverage and classification can be incomplete or mistaken; the retrieval date does not establish '
        'complete literature coverage through that date. Inspect the report and original citing papers '
        'before interpreting later evidence. This snapshot is excluded from ranked scientific retrieval._']
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--doi', default='', help='Verified paper DOI; omit if absent')
    parser.add_argument('--output', required=True, type=Path, help='New JSON snapshot path in .literature/')
    args = parser.parse_args()
    snapshot = retrieve(args.doi)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Historical capture files are immutable; choose a fresh path on each retrieval.
    with args.output.open('x') as stream:
        json.dump(snapshot, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(snapshot, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
