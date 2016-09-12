from .raw import load_term_id_mapping
from fma.ontology import load_ontology, extract_relation_triples
from spiderpig import msg
import json
import pandas


def init_parser(parser):
    parser.add_argument(
        '--stats',
        dest='stats',
        action='store_true',
        default=False
    )
    parser.add_argument(
        '--filter',
        dest='filter_type',
        choices=['none', 'taid', 'app'],
        default='app'
    )
    parser.add_argument(
        '--format',
        dest='file_format',
        choices=['json', 'csv'],
        default='json'
    )
    parser.add_argument(
        '--relation',
        dest='relations',
        action='append',
        type=str,
        default=[],
    )
    parser.add_argument(
        '--dry',
        dest='dry',
        action='store_true',
        default=False
    )


def load_active_ontology():
    mapping = load_term_id_mapping()
    mapping = mapping[mapping['fma_id'].notnull()]
    fma_ids = mapping['fma_id'].apply(lambda i: 'http://purl.org/sig/ont/fma/fma{}'.format(i)).unique()
    ontology = load_ontology()
    to_remove = set(ontology['terms'].keys()) - set(fma_ids)
    ontology['terms'] = {t_id: t_data for t_id, t_data in ontology['terms'].items() if t_id not in to_remove}
    for t_data in ontology['terms'].values():
        for rel_type in ['info', 'relations']:
            for rel_name in t_data.get(rel_type, {}).keys():
                t_data[rel_type][rel_name] = list(set(t_data[rel_type][rel_name]) - to_remove)
            if rel_type in t_data:
                t_data[rel_type] = {rel_name: rel_data for rel_name, rel_data in t_data[rel_type].items() if len(rel_data) > 0}
    return {
        'terms': ontology['terms'],
        'relation-names': sorted({rel for data in ontology['terms'].values() for rel in data.get('relations', {}).keys()}),
        'info-names': sorted({rel for data in ontology['terms'].values() for rel in data['info'].keys()}),
    }


def execute(output_dir='output', stats=False, filter_type='app', relations=None, dry=False, file_format='json'):
    if filter_type == 'none':
        ontology = load_ontology(taids_only=False)
    elif filter_type == 'taid':
        ontology = load_ontology(taids_only=True)
    else:
        ontology = load_active_ontology()
    mapping = load_term_id_mapping()[['anatom_id', 'fma_id']].rename(columns={'anatom_id': 'anatomid', 'fma_id': 'fmaid'})
    extracted = extract_relation_triples(ontology)
    extracted = pandas.merge(extracted, mapping.rename(columns={'anatomid': 'anatomid_from', 'fmaid': 'fmaid_from'}), how='left', on='fmaid_from')
    extracted = pandas.merge(extracted, mapping.rename(columns={'anatomid': 'anatomid_to', 'fmaid': 'fmaid_to'}), how='left', on='fmaid_to')
    if stats:
        print('AVAILABLE RELATION TYPES SORTED BY USAGE')
        stats_data = extracted.groupby('relation').apply(len).sort_values(ascending=False)
        msg.info('{}/fma_ontology_stats.csv'.format(output_dir))
        stats_data.reset_index().rename(columns={0: 'instances'}).to_csv('{}/fma_ontology_stats.csv'.format(output_dir), index=False)
        print(stats_data.to_string())
        print()

    for relation in relations:
        print(relation)
        extracted_relation = extracted[extracted['relation'] == relation]
        for taid_from, taid_to, name_from, name_to in extracted_relation[['taid_from', 'taid_to', 'name_from', 'name_to']].values:
            print('    {} ({}) --> {} ({})'.format(name_from, 'X' if taid_from is None else taid_from, name_to, 'X' if taid_to is None else taid_to))
        if not dry:
            msg.info('{}/fma_ontology_{}.csv'.format(output_dir, relation))
            extracted_relation.to_csv('{}/fma_ontology_{}.csv'.format(output_dir, relation), index=False)
    if not dry:
        if file_format == 'json':
            msg.info('{}/fma_ontology.json'.format(output_dir))
            with open('{}/fma_ontology.json'.format(output_dir), 'w') as f:
                json.dump(ontology, f, sort_keys=True)
        else:
            msg.info('{}/fma_ontology.csv'.format(output_dir))
            extracted.to_csv('{}/fma_ontology.csv'.format(output_dir), index=False)
