from geoip import geolite2
from .raw import load_answers, load_ratings
import numpy
import pandas
import os
from spiderpig import spiderpig


META = {
    'slepemapy-ab-random-random': {
        'please_cite': r'''@inproceedings{papousek2016evaluation,
 author = {Papou\v{s}ek, Jan and Stanislav, V\'{\i}t and Pel\'{a}nek, Radek},
 title = {Evaluation of an Adaptive Practice System for Learning Geography Facts},
 booktitle = {Proceedings of the Sixth International Conference on Learning Analytics \& Knowledge},
 year = {2016},
 isbn = {978-1-4503-4190-5},
 location = {Edinburgh, United Kingdom},
 pages = {134--142},
 numpages = {9},
 doi = {10.1145/2883851.2883884},
 publisher = {ACM}
}''',
        'experiment_citation': 'Papoušek, J., Pelánek, R. & Stanislav, V. [Evaluation of an Adaptive Practice System for Learning Geography Facts](http://www.fi.muni.cz/~xpelanek/publications/lak16-evaluation.pdf). Learning Analytics & Knowledge, 2016.',
    },
    'slepemapy-ab-target-difficulty': {
        'please_cite': r'''@inproceedings{papousek2016impact,
 author="Papou{\v{s}}ek, Jan and Stanislav, V{\'i}t and Pel{\'a}nek, Radek",
 editor="Micarelli, Alessandro and Stamper, John and Panourgia, Kitty",
 title="Impact of Question Difficulty on Engagement and Learning",
 bookTitle="Intelligent Tutoring Systems: 13th International Conference",
 year="2016",
 publisher="Springer International Publishing",
 pages="267--272",
 isbn="978-3-319-39583-8",
 doi="10.1007/978-3-319-39583-8_28",
 url="http://dx.doi.org/10.1007/978-3-319-39583-8_28"
}''',
        'experiment_citation': 'Papoušek, J., Pelánek, R. & Stanislav, V. [Impact of Question Difficulty on Engagement and Learning](http://www.fi.muni.cz/~xpelanek/publications/its-target-difficulty.pdf). Intelligent Tutoring Systems, 2016.',
    }
}


@spiderpig()
def load_sessions(data_dir):
    return pandas.read_csv(os.path.join(data_dir, 'ip_address.csv'), index_col=False)


@spiderpig()
def load_flashcards(data_dir):
    return pandas.read_csv(os.path.join(data_dir, 'flashcards.csv'), index_col=False)


def get_country(ip):
    lookup = geolite2.lookup(ip)
    return numpy.nan if lookup is None else lookup.country


def get_meta():
    key = get_name()
    return META.get(key, {
        'please_cite': 'TODO',
        'experiment_citation': 'TODO',
    })


@spiderpig(cached=False)
def get_name(data_dir):
    return data_dir.strip('/').split('/')[-1]


def prepare_public_data(dest):
    if not os.path.exists(dest):
        os.makedirs(dest)
    answers = load_answers()[[
        'id', 'time', 'response_time', 'item_answered_id', 'item_asked_id', 'user_id',
        'guess', 'metainfo_id', 'direction', 'experiment_setup_name', 'context_name', 'session_id'
    ]]
    flashcards = load_flashcards()
    feedback = load_ratings()
    session_ip = load_sessions()[['session_id', 'ip_address']]

    session_ip['session_id'] = session_ip['session_id']
    session_ip = session_ip[['session_id', 'ip_address']]
    session_ip['ip_country'] = session_ip['ip_address'].apply(get_country)
    ips = session_ip['ip_address'].unique()
    ip_ids = dict(zip(ips, range(1, len(ips) + 1)))
    ip_ids[numpy.nan] = numpy.nan
    session_ip['ip_id'] = session_ip['ip_address'].apply(lambda i: ip_ids[i])
    session_ip = session_ip[['session_id', 'ip_country', 'ip_id']]
    answers = pandas.merge(answers, session_ip, on='session_id', how='inner')

    answers['options'] = answers['guess'].apply(lambda g: 0 if g == 0 else int(round(1 / g)))
    answers['reference'] = answers['metainfo_id'] == 1
    answers['condition'] = answers['experiment_setup_name']
    answers = pandas.merge(answers, flashcards[['item_id', 'term_name']], left_on='item_asked_id', right_on='item_id', how='inner')
    answers['term_asked_name'] = answers['term_name']
    del answers['term_name']
    answers = pandas.merge(answers, flashcards[['item_id', 'term_name']], left_on='item_answered_id', right_on='item_id', how='inner')
    answers['term_answered_name'] = answers['term_name']
    del answers['term_name']

    term_type_trans = {
        'region_cz': 'region',
        'bundesland': 'region',
        'region_it': 'region',
        'autonomous_Comunity': 'region',
        'province': 'region'
    }

    term_type_dict = flashcards.set_index('item_id')['term_type'].to_dict()
    us_state_items = flashcards[(flashcards['context_name'] == 'United States') & (flashcards['term_type'] == 'state')]['item_id'].unique()
    flashcards['term_type'] = flashcards['item_id'].apply(
        lambda i: term_type_trans.get(term_type_dict[i], term_type_dict[i]) if i not in us_state_items else 'region'
    )
    answers = pandas.merge(answers, flashcards[['item_id', 'term_type']], left_on='item_asked_id', right_on='item_id', how='inner')

    answers = answers[[
        'id', 'time', 'response_time', 'item_answered_id', 'item_asked_id', 'user_id',
        'options', 'reference', 'direction', 'condition', 'context_name',
        'term_type', 'term_asked_name', 'term_answered_name', 'ip_country', 'ip_id'
        ]]
    answers.sort_values(by='id', inplace=True)
    answers.to_csv('{}/answers.csv'.format(dest), index=False)

    feedback = feedback[feedback['user_id'].isin(answers['user_id'].unique())]
    feedback.to_csv('{}/feedback.csv'.format(dest), index=False)
    with open(os.path.join(os.path.dirname(__file__), 'README.md'), 'r') as f:
        readme_content = f.read()
    with open(os.path.join(dest, 'README.md'), 'w') as f:
        f.write(readme_content.format(
            cz_percentage=int(round(100 * (answers['ip_country'] == 'CZ').mean())),
            sk_percentage=int(round(100 * (answers['ip_country'] == 'SK').mean())),
            total_students=len(answers['user_id'].unique()),
            total_items=len(answers['item_asked_id'].unique()),
            total_answers=len(answers),
            experiment_start=answers['time'].min().strftime('%d %B %Y'),
            experiment_end=answers['time'].max().strftime('%d %B %Y'),
            **get_meta()
        ))


def execute(dest):
    prepare_public_data(dest)
