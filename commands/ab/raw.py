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
def load_answers(data_dir='data', answer_limit=1, filter_invalid_tests=True, filter_invalid_response_time=True):
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

    return answers.sort_values(by=['user_id', 'id'])
