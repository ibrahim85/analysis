from data import iterdicts
from spiderpig import spiderpig
import os
import pandas


@spiderpig()
def load_user_answers(groupby=None):
    if groupby is None:
        return load_answers().groupby('user_id').apply(len)
    else:
        return load_answers().groupby(list(set(groupby + ['user_id']))).apply(len)


@spiderpig()
def load_success(first=None, round_base=None, reference=True):
    answers = load_answers()
    if first is not None:
        answers.groupby('user_id').head(first)
    if not reference:
        answers = answers[answers['metainfo_id'] != 1]

    def _round(x):
        if round_base is None:
            return x
        return int(round_base * round(float(x * 100) / round_base)) / 100.0
    return answers.groupby('user_id').head(n=30).groupby('user_id').apply(
        lambda g: _round((g['item_asked_id'] == g['item_answered_id']).mean())
    )


@spiderpig()
def load_school_usage(data_dir='data', school_threshold=10):
    answers = load_answers()
    sessions = pandas.read_csv(os.path.join(data_dir, 'ip_address.csv'), index_col=False)
    user_ips = pandas.merge(answers, sessions, on=['session_id', 'user_id']).drop_duplicates('user_id').set_index('user_id')['ip_address']
    ip_counts = user_ips.reset_index().groupby('ip_address').apply(len)
    school_ips = ip_counts[ip_counts > school_threshold].reset_index()['ip_address']
    return user_ips.isin(school_ips)


@spiderpig()
def load_reference_answers():
    answers = load_answers()
    return answers[answers['metainfo_id'] == 1]


@spiderpig()
def load_answers(contexts=None):
    answers = _load_answers()
    if contexts:
        answers_filter = None
        for context in contexts:
            context_name, term_type = context.split(':')
            current_filter = ((answers['context_name'] == context_name) & (answers['term_type'] == term_type))
            if answers_filter is None:
                answers_filter = current_filter
            else:
                answers_filter |= current_filter
        answers = answers[answers_filter]
    return answers


@spiderpig()
def _load_answers(data_dir='data', answer_limit=1, filter_invalid_tests=True, filter_invalid_response_time=True):
    answers = pandas.read_csv(os.path.join(data_dir, 'answers.csv'), index_col=False, parse_dates=['time'])
    flashcards = pandas.read_csv(os.path.join(data_dir, 'flashcards.csv'), index_col=False)
    setups = pandas.read_csv(os.path.join(data_dir, 'setups.csv'), index_col=False).set_index('experiment_setup_id')['experiment_setup_name'].to_dict()

    answers['experiment_setup_name'] = answers['experiment_setup_id'].apply(lambda i: setups[i])

    valid_users = [u for (u, n) in answers.groupby('user_id').apply(len).to_dict().items() if n >= answer_limit]
    answers = answers[answers['user_id'].isin(valid_users)]

    if filter_invalid_response_time:
        invalid_users = answers[answers['response_time'] < 0]['user_id'].unique()
        answers = answers[~answers['user_id'].isin(invalid_users)]

    answers = pandas.merge(answers, flashcards, on='item_id', how='inner')

    if filter_invalid_tests:
        invalid_users = answers[answers['context_id'] == 17]['user_id'].unique()
        answers = answers[~answers['user_id'].isin(invalid_users)]

        invalid_users = set()
        last_user = None
        last_context = None
        counter = None
        for row in iterdicts(answers.sort_values(by=['user_id', 'context_name', 'term_type', 'id'])):
            if last_user != row['user_id'] or last_context != (row['context_name'], row['term_type']):
                last_user = row['user_id']
                last_context = (row['context_name'], row['term_type'])
                counter = 0
            if row['metainfo_id'] == 1 and counter % 10 != 0:
                invalid_users.add(row['user_id'])
            counter += 1
        answers = answers[~answers['user_id'].isin(invalid_users)]

    return answers.sort_values(by=['id'])


@spiderpig()
def load_ratings(data_dir='data'):
    ratings = pandas.read_csv(os.path.join(data_dir, 'ratings.csv'), index_col=False, parse_dates=['inserted'])
    users = load_answers()['user_id'].unique()
    return ratings[ratings['user_id'].isin(users)]
