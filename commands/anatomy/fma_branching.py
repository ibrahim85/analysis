from .fma_ontology import load_ontology_as_dataframe
from itertools import chain
from spiderpig import spiderpig
from spiderpig.msg import info
import yaml

def init_parser(parser):
    parser.add_argument(
        '--filter',
        dest='filter_type',
        choices=['none', 'taid', 'app'],
        default='app'
    )
    parser.add_argument(
        '--fmaid',
        dest='fmaid'
    )


def remove_recursion(value):
    if isinstance(value, list):
        return [remove_recursion(v) for v in value]
    if isinstance(value, dict):
        return {k: remove_recursion(v) for k, v in value.items()}
    return value


def holds_predicate(record, predicate, follow_key, cache=None):
    if cache is None:
        cache = {}
    if record['fmaid'] in cache:
        return cache[record['fmaid']]
    result = predicate(record) and all([
        holds_predicate(r, predicate, follow_key, cache=cache)
        for r in record.get(follow_key, [])
    ])
    cache[record['fmaid']] = result
    return result


def count_relations(record, relation_key):
    if relation_key not in record:
        return 0
    return len(record[relation_key]) + sum([count_relations(r, relation_key) for r in record[relation_key]])


def remove_by_predicate(record, predicate, follow_key):
    if record is None:
        return None
    if not predicate(record):
        return None
    if follow_key not in record:
        return record
    processed = [remove_by_predicate(r, predicate, follow_key) for r in record[follow_key]]
    record[follow_key] = [r for r in processed if r is not None]
    if len(record[follow_key]) == 0:
        del record[follow_key]
    return record


@spiderpig(cached=False)
def save_branching(branching, output_dir='output', filename='branching'):
    with open('{}/{}.yaml'.format(output_dir, filename), 'w') as outfile:
        yaml.dump(branching, outfile, default_flow_style=False)
        info('{}/{}.yaml'.format(output_dir, filename))


def execute(filter_type='app', fmaid=None):
    filter_fmaid = fmaid
    ontology = load_ontology_as_dataframe(filter_type='none')
    result = {}
    filtered = ontology[ontology['relation'].isin(['branch', 'tributary'])]
    for fmaid_from, fmaid_to, name_from, name_to, relation, taid_from, taid_to, anatomid_from, anatomid_to in filtered[['fmaid_from', 'fmaid_to', 'name_from', 'name_to', 'relation', 'taid_from', 'taid_to', 'anatomid_from', 'anatomid_to']].values:
        record = result.get(fmaid_from, {})
        record['fmaid'] = fmaid_from
        record['name'] = name_from
        if isinstance(anatomid_from, str):
            record['anatomid'] = anatomid_from
        if taid_from:
            record['taid'] = taid_from
        if relation == 'branch':
            branch = record.get('branch', [])
            branch.append(fmaid_to)
            record['branch'] = branch
        elif relation == 'tributary':
            trib_of = record.get('tributary', [])
            trib_of.append(fmaid_to)
            record['tributary'] = trib_of
        result[fmaid_from] = record
        if fmaid_to not in result:
            record = {
                'fmaid': fmaid_to,
                'name': name_to,
            }
            if taid_to:
                record['taid'] = taid_to
            if isinstance(anatomid_to, str):
                record['anatomid'] = anatomid_to
            result[fmaid_to] = record

    transitive = dict()

    def _collect_transitive_tributary(fmaid):
        if fmaid in transitive:
            return transitive[fmaid]
        if 'tributary' not in result[fmaid]:
            transitive[fmaid] = set()
        else:
            transitive[fmaid] = set(chain(*[set(result[i].get('tributary', [])) | _collect_transitive_tributary(i) for i in result[fmaid]['tributary']]))
        return transitive[fmaid]

    for fmaid in result:
        _collect_transitive_tributary(fmaid)

    for record in result.values():
        if 'tributary' in record:
            record['tributary'] = [result[i] for i in record['tributary'] if i not in transitive[record['fmaid']]]
        if 'branch' in record:
            record['branch'] = [result[i] for i in record['branch']]
    result = remove_recursion(result)
    if filter_type != 'none':
        key = 'anatomid' if filter_type == 'app' else 'taid'
        result = {
            fmaid: remove_by_predicate(record, lambda r: key in r, 'branch')
            for fmaid, record in result.items()
        }
        result = {
            fmaid: remove_by_predicate(record, lambda r: key in r, 'tributary')
            for fmaid, record in result.items()
        }
        result = {fmaid: record for fmaid, record in result.items() if record is not None}
    print('BRANCH', (sum([count_relations(r, 'branch') for r in result.values()])))
    print('TRIBUTARY', sum([count_relations(r, 'tributary') for r in result.values()]))
    save_branching({i: r for i, r in result.items() if 'branch' in r or 'tributary' in r})
    if filter_fmaid is not None:
        save_branching(result[str(filter_fmaid)], filename='branching_{}'.format(filter_fmaid))
