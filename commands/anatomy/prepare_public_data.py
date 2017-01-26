from commands.all.raw import load_answers
from geoip import geolite2
from spiderpig import spiderpig
import json
import numpy
import os
import pandas


@spiderpig()
def load_practice_filter(data_dir='data'):
    return pandas.read_csv('{}/proso_models_practicecontext.csv'.format(data_dir), index_col=False)[['id', 'content']]


@spiderpig()
def load_answer_meta(data_dir='data'):
    return pandas.read_csv('{}/proso_models_answermeta.csv'.format(data_dir), index_col=False)[['id', 'content']]


@spiderpig()
def load_structure(data_dir='data', language='en'):
    data = pandas.read_csv('{}/custom_proso_models_relations.csv'.format(data_dir), index_col=False, dtype={'item_primary': numpy.object})
    data = data[data['key'] == 'parent']
    categories = pandas.read_csv('{}/proso_flashcards_category.csv'.format(data_dir), index_col=False)[['item', 'identifier', 'name', 'type', 'lang']]
    data = pandas.merge(data, categories.rename(columns={'item': 'item_secondary'}), on='item_secondary')
    data = data[data['lang'] == language]
    return data[['item_primary', 'type', 'name', 'identifier']].rename(columns={'item_primary': 'item'})


@spiderpig()
def load_sessions(data_dir):
    sessions = pandas.read_csv('{}/proso_user_session.csv'.format(data_dir), index_col=False)
    locations = pandas.read_csv('{}/proso_user_location.csv'.format(data_dir), index_col=False).rename(columns={'id': 'location'})
    data = pandas.merge(sessions, locations)[['id', 'ip_address']]
    data['ip_country'] = data['ip_address'].apply(get_country)
    ips = data['ip_address'].unique()
    ip_ids = dict(zip(ips, range(1, len(ips) + 1)))
    ip_ids[numpy.nan] = numpy.nan
    data['ip_id'] = data['ip_address'].apply(lambda i: ip_ids[i])
    return data


def get_country(ip):
    lookup = geolite2.lookup(ip)
    return numpy.nan if lookup is None else lookup.country


def canonical_practice_filter(pfilter):
    pfilter = json.loads(pfilter)
    if isinstance(pfilter, list):
        return json.dumps(sorted([sorted(fs) for fs in pfilter]))
    if len(pfilter['contexts']) == 0 and len(pfilter['types']) == 0:
        if len(pfilter['categories']) == 0:
            return '[]'
        if isinstance(pfilter['categories'][0], str):
            pfilter['categories'] = [pfilter['categories']]
        return json.dumps(sorted([sorted(['category/{}'.format(c) for c in cs]) for cs in pfilter['categories']]))
    if len(pfilter['types']) != 0:
        raise Exception("non empty filter 'types' is not allowed")
    if len(pfilter['contexts']) > 1:
        raise Exception('more than one context is not allowed')
    return json.dumps([['context/{}'.format(pfilter['contexts'][0])]])


@spiderpig()
def load_data():
    answers = load_answers()
    pfilter = load_practice_filter()
    pfilter['content'] = pfilter['content'].apply(canonical_practice_filter)
    answers = pandas.merge(answers, pfilter.rename(columns={'id': 'practice_filter', 'content': 'practice_filter_content'}), on='practice_filter')
    answers = answers[answers['term_secondary_asked'] == 'None']
    answers = answers[answers['term_secondary_answered'] == 'None']
    structure = load_structure()

    def _group(g):
        return json.dumps(sorted(g['name'].values))

    systems = structure[structure['type'] == 'system'].groupby('item').apply(_group).to_dict()
    locations = structure[structure['type'] == 'location'].groupby('item').apply(_group).to_dict()
    answers['systems_asked'] = answers['item_asked'].apply(lambda i: systems.get(i, 'unknown'))
    answers['locations_asked'] = answers['item_asked'].apply(lambda i: locations.get(i, 'uknown'))
    answers['systems_anwered'] = answers['item_answered'].apply(lambda i: systems.get(i, 'unknown') if i else None)
    answers['locations_answered'] = answers['item_answered'].apply(lambda i: locations.get(i, 'uknown') if i else None)
    answers['options'] = answers['guess'].apply(lambda g: 0 if g == 0 else int(round(1 / g)))
    answers = pandas.merge(answers, load_sessions().rename(columns={'id': 'session'})[['session', 'ip_country', 'ip_id']], on='session')
    answers.drop([
        'practice_filter', 'config', 'term_type_asked', 'term_type_answered',
        'term_answered', 'flashcard_answered', 'context_answered', 'guess',
        'session', 'context_id_answered', 'context_name_answered',
        'practice_set', 'context_asked', 'term_asked', 'term_secondary_asked',
        'context_id_asked', 'flashcard_id_asked', 'flashcard_id_answered',
        'metainfo', 'term_id_asked', 'term_id_answered', 'flashcard_asked',
        'term_secondary_answered',
    ], axis=1, inplace=True)
    LANGS = {'cs': 'la (cs)', 'cc': 'cs', 'en': 'en', 'la': 'la (en)', 'None': None}
    answers['lang'] = answers['lang'].apply(lambda l: LANGS[l] if l else None)
    answers.rename(columns={
        'context_name_asked': 'context_name',
        'practice_filter_content': 'practice_filter',
    }, inplace=True)
    return answers


def prepare_public_data(dest):
    if not os.path.exists(dest):
        os.makedirs(dest)
    answers = load_data()
    answers.to_csv('{}/answers.csv'.format(dest), index=False)
    with open(os.path.join(os.path.dirname(__file__), 'README.md'), 'r') as f:
        readme_content = f.read()
    with open(os.path.join(dest, 'README.md'), 'w') as f:
        f.write(readme_content.format(
            cz_percentage=int(round(100 * (answers['ip_country'] == 'CZ').mean())),
            sk_percentage=int(round(100 * (answers['ip_country'] == 'SK').mean())),
            total_learners=len(answers['user'].unique()),
            total_items=len(answers['item_asked'].unique()),
            total_answers=len(answers),
            collection_start=answers['time'].min().strftime('%d %B %Y'),
            collection_end=answers['time'].max().strftime('%d %B %Y')
        ))


def execute(dest):
    prepare_public_data(dest)
