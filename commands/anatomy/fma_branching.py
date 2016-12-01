from .fma_ontology import load_ontology_as_dataframe
from itertools import chain
from spiderpig import spiderpig
from spiderpig.msg import info
import yaml
import json


OPPOSITES = {
    'branch_of': 'branch',
    'tributary_of': 'tributary',
    'constitutional_part_of': 'constitutional_part',
    'venous_drainage_of': 'venous_drainage',
    'arterial_supply_of': 'arterial_supply',
    'nerve_supply_of': 'nerve_supply',
    'lymphatic_drainage_of': 'lymphatic_drainage',
}
RELATIONS = {
    'arterial_supply',
    'branch',
    'constitutional_part',
    'continuous_distally_with',
    'continuous_proximally_with',
    'continuous_with',
    'lymphatic_drainage',
    'nerve_supply',
    'nerve_supply',
    'receives_input_from',
    'regional_part',
    'tributary',
    'venous_drainage',
}


def init_parser(parser):
    parser.add_argument(
        '--filter',
        dest='filter_type',
        choices=['none', 'taid', 'app'],
        default='app'
    )
    parser.add_argument(
        '--format',
        dest='format',
        choices=['json', 'yaml'],
        default='json'
    )
    parser.add_argument(
        '--fmaid',
        dest='fmaid'
    )
    parser.add_argument(
        '--drop-sides',
        dest='drop_sides',
        action='store_true',
        default=False
    )
    parser.add_argument(
        '--relation',
        dest='relations',
        action='append',
        default=[]
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


def count_relations(record, relation_key, top=True, collected=None):
    if collected is None:
        collected = set()
    if top:
        for r in record.values():
            count_relations(r, relation_key, False, collected)
        return len(collected)
    if relation_key not in record:
        return
    for r in record[relation_key]:
        collected.add((record['fmaid'], relation_key, r['fmaid']))
        count_relations(r, relation_key, False, collected)


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


def extract_relation(record, relation):
    new_record = {}
    for key in ['fmaid', 'taid', 'name']:
        if key not in record:
            continue
        new_record[key] = record[key]
    if relation in record:
        new_record[relation] = [extract_relation(r, relation) for r in record[relation]]
    return new_record


@spiderpig(cached=False)
def save_branching(branching, output_dir='output', filename='branching', format='json'):
    if format == 'yaml':
        with open('{}/{}.yaml'.format(output_dir, filename), 'w') as outfile:
            yaml.dump(branching, outfile)
            info('{}/{}.yaml'.format(output_dir, filename))
    else:
        with open('{}/{}.json'.format(output_dir, filename), 'w') as outfile:
            json.dump(branching, outfile)
            info('{}/{}.json'.format(output_dir, filename))


def execute(filter_type='app', fmaid=None, drop_sides=False, relations=None):
    if len(relations) == 0:
        relations = RELATIONS
    relations = set(relations)
    filter_fmaid = fmaid
    ontology = load_ontology_as_dataframe(filter_type='none')
    result = {}
    filtered = ontology[ontology['relation'].isin(relations | {k for k, v in OPPOSITES.items() if v in relations})]
    for fmaid_from, fmaid_to, name_from, name_to, relation, taid_from, taid_to, anatomid_from, anatomid_to in filtered[['fmaid_from', 'fmaid_to', 'name_from', 'name_to', 'relation', 'taid_from', 'taid_to', 'anatomid_from', 'anatomid_to']].values:
        if OPPOSITES.get(relation) in relations:
            relation = OPPOSITES[relation]
            fmaid_from, fmaid_to = fmaid_to, fmaid_from
            taid_from, taid_to = taid_to, taid_from
            name_from, name_to = name_to, name_from
            anatomid_from, anatomid_to = anatomid_to, anatomid_from
        record = result.get(fmaid_from, {})
        record['fmaid'] = fmaid_from
        record['name'] = name_from
        if isinstance(anatomid_from, str):
            record['anatomid'] = anatomid_from
        if taid_from:
            record['taid'] = taid_from
        if relation in relations:
            prev = record.get(relation, [])
            if fmaid_to not in prev:
                prev.append(fmaid_to)
                record[relation] = prev

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

    def _collect_transitive_relation(fmaid, relation, collected):
        if fmaid in collected:
            return collected[fmaid]
        if relation not in result[fmaid]:
            collected[fmaid] = set()
        else:
            collected[fmaid] = set()
            collected[fmaid] = set(chain(*[set(result[i].get(relation, [])) | _collect_transitive_relation(i, relation, collected) for i in result[fmaid][relation]]))
        return collected[fmaid]

    for relation in relations:
        transitive = dict()
        for fmaid in result:
            _collect_transitive_relation(fmaid, relation, transitive)
        for record in result.values():
            if relation in record:
                record[relation] = [result[i] for i in record[relation] if i not in transitive[record['fmaid']]]

    if drop_sides:

        def _is_not_side(r):
            name = r['name'].lower()
            if name.startswith('left') or name.startswith('right'):
                return False
            if ' of left ' in name or ' of right ' in name:
                return False
            return True
        for relation in relations:
            for record in result.values():
                remove_by_predicate(record, _is_not_side, relation)
        result = {fmaid: record for fmaid, record in result.items() if _is_not_side(record)}

    if filter_type != 'none':
        key = 'anatomid' if filter_type == 'app' else 'taid'
        for relation in relations:
            for record in result.values():
                remove_by_predicate(record, lambda r: key in r, relation)
        result = {fmaid: record for fmaid, record in result.items() if len(set(record) & relations) > 0 and key in record}

    result = remove_recursion(result)
    if filter_fmaid is not None:
        save_branching({str(filter_fmaid): result[str(filter_fmaid)]}, filename='branching_{}'.format(filter_fmaid))
    result = {i: r for i, r in result.items() if len(relations & set(r.keys())) > 0}
    for relation in relations:
        print(relation, count_relations(result, relation))
    filename = 'branching' if filter_type == 'none' else 'branching_{}'.format(filter_type)
    if drop_sides:
        filename += '_drop_sides'
    for relation in relations:
        r_result = {i: extract_relation(r, relation) for i, r in result.items() if relation in r}
        save_branching(r_result, filename='{}_{}'.format(filename, relation))
