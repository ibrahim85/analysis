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
def load_context_size():
    return load_answers().drop_duplicates(['item_asked_id']).groupby(['context_name', 'term_type']).apply(len).reset_index().rename(columns={0: 'context_size'})


@spiderpig()
def load_context_difficulty():
    return load_reference_answers().drop_duplicates(['item_asked_id', 'user_id']).groupby(['context_name', 'term_type']).apply(lambda g: (g['item_asked_id'] != g['item_answered_id']).mean()).reset_index().rename(columns={0: 'context_difficulty'})


@spiderpig()
def load_contexts():
    contexts = pandas.merge(load_context_size(), load_context_difficulty(), on=['context_name', 'term_type'], how='inner')
    contexts = contexts[contexts['context_size'] > 5]
    contexts['context_size_label'] = pandas.qcut(contexts['context_size'], [0, 0.25, 0.75, 1], labels=['small', 'medium', 'big'])
    contexts['context_difficulty_label'] = pandas.qcut(contexts['context_difficulty'], [0, 0.25, 0.75, 1], labels=['too easy', 'medium', 'difficult'])
    return contexts


@spiderpig()
def load_user_time(groupby=None):

    def _apply(data):
        return (data['response_time'][data['response_time'] != -1]).apply(lambda x: min(x / 1000.0, 30)).sum()

    if groupby is None:
        return load_answers().groupby('user_id').apply(_apply)
    else:
        return load_answers().groupby(list(set(groupby + ['user_id']))).apply(_apply)


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
def load_non_reference_answers():
    answers = load_answers()
    return answers[answers['metainfo_id'] != 1]


@spiderpig()
def load_options(data_dir='data', contexts=None):
    options = _load_options()
    flashcards = pandas.read_csv(os.path.join(data_dir, 'flashcards.csv'), index_col=False)
    if contexts:
        flashcard_filter = None
        for context in contexts:
            context_name, term_type = context.split(':')
            current_filter = ((flashcards['context_name'] == context_name) & (flashcards['term_type'] == term_type))
            if flashcard_filter is None:
                flashcard_filter = current_filter
            else:
                flashcard_filter |= current_filter
        flashcard_item_ids = flashcards[flashcard_filter]['item_id']
        options = options[options['item_asked_id'].isin(flashcard_item_ids)]
    return options


@spiderpig()
def _load_options(data_dir='data'):
    options = pandas.read_csv(os.path.join(data_dir, 'options.csv'), index_col=False)
    items = pandas.read_csv(os.path.join(data_dir, 'items.csv'), index_col=False).rename(columns={'fc_id': 'flashcard_id'})
    answers = load_answers()
    options = pandas.merge(options, answers[['id', 'item_asked_id', 'experiment_setup_id']].rename(columns={'id': 'flashcardanswer_id'}), on='flashcardanswer_id', how='inner')
    options = pandas.merge(options, items, on='flashcard_id', how='inner').rename(columns={'item_id': 'item_option_id', 'flashcardanswer_id': 'answer_id'})[['answer_id', 'item_asked_id', 'item_option_id', 'experiment_setup_id']]
    options = options[options['item_asked_id'] != options['item_option_id']]
    setups = load_setup_mapping()
    options['experiment_setup_name'] = options['experiment_setup_id'].apply(lambda i: setups[i])
    return options


@spiderpig()
def load_answers(contexts=None):
    answers = _load_answers()
    if contexts:
        answers_filter = None
        for context in contexts:
            context_name, term_type = context.split(':')
            if context_name not in answers['context_name'].unique():
                raise Exception('There is no context with name {}, available are {}'.format(context_name, answers['context_name'].unique()))
            current_filter = ((answers['context_name'] == context_name) & (answers['term_type'] == term_type))
            if answers_filter is None:
                answers_filter = current_filter
            else:
                answers_filter |= current_filter
        answers = answers[answers_filter]
    return answers


@spiderpig()
def _load_answers(data_dir='data', answer_limit=1, filter_invalid_tests=True, filter_invalid_response_time=True, setups=None, group_setups=None):
    answers = pandas.read_csv(os.path.join(data_dir, 'answers.csv'), index_col=False, parse_dates=['time'])
    flashcards = pandas.read_csv(os.path.join(data_dir, 'flashcards.csv'), index_col=False)
    all_setups = load_setup_mapping()

    answers['experiment_setup_name'] = answers['experiment_setup_id'].apply(lambda i: all_setups[i])
    if setups is not None and len(setups) > 0:
        setups = [int(s) if s.isdigit() else s for s in setups]
        answers = answers[answers['experiment_setup_name'].isin(setups)]

    valid_users = [u for (u, n) in answers.groupby('user_id').apply(len).to_dict().items() if n >= answer_limit]
    answers = answers[answers['user_id'].isin(valid_users)]

    if 'reference_computed' in answers.columns:
        answers['metainfo_id_old'] = answers['metainfo_id']
        answers['metainfo_id'] = answers['reference_computed'].apply(lambda x: 1 if x == 't' else None)
        invalid_users = set(answers[(answers['metainfo_id'] != 1) & (answers['metainfo_id_old'] == 1)]['user_id'].unique())
        invalid_users |= set(answers[(answers['metainfo_id'] == 1) & (answers['guess'] != 0)]['user_id'].unique())
        answers = answers[~answers['user_id'].isin(invalid_users)]
        filter_invalid_tests = False

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
def load_setup_mapping(data_dir='data', group_setups=None):
    all_setups = pandas.read_csv(os.path.join(data_dir, 'setups.csv'), index_col=False).set_index('experiment_setup_id')['experiment_setup_name'].to_dict()
    if group_setups is not None:
        all_setups = {i: name.split('-')[group_setups] for i, name in all_setups.items()}
    return all_setups


@spiderpig()
def load_ratings(data_dir='data'):
    ratings = pandas.read_csv(os.path.join(data_dir, 'ratings.csv'), index_col=False, parse_dates=['inserted'])
    labels = {
        1: 'easy',
        2: ' appropriate',
        3: 'difficult',
        4: 'much easier',
        5: 'bit easier',
        6: 'the same',
        7: 'bit harder',
        8: 'much harder',
    }
    ratings['label'] = ratings['value'].apply(lambda v: '{} - {}'.format(v, labels[v]))
    answers = load_answers()
    users = answers['user_id'].unique()
    return ratings[ratings['user_id'].isin(users) & (ratings['inserted'] <= answers['time'].max())]
