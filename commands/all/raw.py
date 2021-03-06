from spiderpig import spiderpig
import numpy
import os.path
import pandas


@spiderpig()
def load_difficulty(data_dir='data'):
    if not os.path.exists('{}/difficulty.csv'.format(data_dir)):
        return None
    answers = load_answers()
    difficulty = pandas.read_csv('{}/difficulty.csv'.format(data_dir), index_col=None, dtype={'item_id': numpy.object})
    difficulty['probability'] = difficulty['value'].apply(lambda v: 1 / (1 + numpy.exp(v)))
    return difficulty[difficulty['item_id'].isin(answers['item_asked'].unique())]


@spiderpig(cached=False)
def load_misanswers():
    answers = load_answers()
    answers = answers[answers['item_asked'] != answers['item_answered']]
    return answers.groupby(['flashcard_id_asked', 'flashcard_id_answered']).apply(len).reset_index().rename(columns={0: 'misanswers'})


@spiderpig()
def load_flashcards(data_dir='data', language='en'):
    flashcards_flashcard = pandas.read_csv('{}/proso_flashcards_flashcard.csv'.format(data_dir), index_col=False, dtype={'item': numpy.object})
    flashcards_term = pandas.read_csv('{}/proso_flashcards_term.csv'.format(data_dir), index_col=False)
    flashcards_context = pandas.read_csv('{}/proso_flashcards_context.csv'.format(data_dir), index_col=False)
    flashcards_term = flashcards_term[flashcards_term['lang'] == language]
    flashcards_context = flashcards_context[flashcards_context['lang'] == language]
    flashcards_flashcard = flashcards_flashcard[flashcards_flashcard['term'].isin(flashcards_term['id'].unique())]
    flashcards_flashcard = flashcards_flashcard[flashcards_flashcard['context'].isin(flashcards_context['id'].unique())]

    flashcards_term.rename(columns={
        'id': 'term',
        'name': 'term_name',
        'identifier': 'term_id'
    }, inplace=True)
    flashcards_context.rename(columns={
        'id': 'context',
        'name': 'context_name',
        'identifier': 'context_id'
    }, inplace=True)
    flashcards_flashcard.rename(columns={
        'id': 'flashcard',
        'identifier': 'flashcard_id'
    }, inplace=True)
    flashcards_flashcard.drop(['active', 'description', 'lang'], axis=1, inplace=True)

    flashcards_flashcard = pandas.merge(flashcards_flashcard, flashcards_term[['term', 'term_name', 'term_id']], on='term', how='inner')
    flashcards_flashcard = pandas.merge(flashcards_flashcard, flashcards_context[['context', 'context_name', 'context_id']], on='context', how='inner')

    difficulty = load_difficulty()
    if difficulty is not None:
        difficulty.rename(columns={'value': 'difficulty', 'item_id': 'item', 'probability': 'difficulty_prob'}, inplace=True)
        flashcards_flashcard = pandas.merge(flashcards_flashcard, difficulty, on='item', how='inner')

    return flashcards_flashcard


@spiderpig()
def load_answers_with_seconds_ago():
    answers = load_answers().sort_values(by=['id'])
    seconds_ago = numpy.empty(len(answers))
    last_times = {}
    for i, (user, item, time) in enumerate(answers[['user', 'item_asked', 'time']].values):
        last_time = last_times.get((user, item))
        if last_time is not None:
            seconds_ago[i] = (time - last_time) / numpy.timedelta64(1, 's')
        else:
            seconds_ago[i] = None
        last_times[user, item] = time
    answers['seconds_ago'] = pandas.Series(seconds_ago, index=answers.index)
    return answers


@spiderpig()
def load_answers(contexts=None):
    answers = load_and_merge()
    if contexts:
        answers_filter = None
        for context in contexts:
            context_name, term_type = context.split(':')
            current_filter = ((answers['context_name_asked'] == context_name) & (answers['term_type_asked'] == term_type))
            if answers_filter is None:
                answers_filter = current_filter
            else:
                answers_filter |= current_filter
        answers = answers[answers_filter]
    return answers


@spiderpig()
def load_and_merge(data_dir='data', language='en', answer_limit=1, nrows=None, only_first=False):
    models_answer = pandas.read_csv(
        '{}/proso_models_answer.csv'.format(data_dir),
        index_col=False, parse_dates=['time'],
        dtype={'item_answered': numpy.object, 'item_asked': numpy.object},
        nrows=nrows
    )
    if only_first:
        models_answer.drop_duplicates(['user', 'item_asked'], inplace=True)
    flashcards_flashcard = pandas.read_csv('{}/proso_flashcards_flashcard.csv'.format(data_dir), index_col=False, dtype={'item': numpy.object})
    flashcards_term = pandas.read_csv('{}/proso_flashcards_term.csv'.format(data_dir), index_col=False)
    flashcards_context = pandas.read_csv('{}/proso_flashcards_context.csv'.format(data_dir), index_col=False)

    flashcards_term = flashcards_term[flashcards_term['lang'] == language]
    flashcards_context = flashcards_context[flashcards_context['lang'] == language]
    flashcards_flashcard = flashcards_flashcard[flashcards_flashcard['term'].isin(flashcards_term['id'].unique())]
    flashcards_flashcard = flashcards_flashcard[flashcards_flashcard['context'].isin(flashcards_context['id'].unique())]

    valid_users = [u for (u, n) in models_answer.groupby('user').apply(len).to_dict().items() if n >= int(answer_limit)]
    models_answer = models_answer[models_answer['user'].isin(valid_users)]

    flashcards_term.rename(columns={
        'id': 'term',
        'name': 'term_name',
        'type': 'term_type',
        'identifier': 'term_id',
    }, inplace=True)
    flashcards_context.rename(columns={
        'id': 'context',
        'name': 'context_name',
        'identifier': 'context_id',
    }, inplace=True)
    flashcards_flashcard.rename(columns={
        'id': 'flashcard',
        'identifier': 'flashcard_id',
    }, inplace=True)
    flashcards_flashcard.drop('additional_info', axis=1, inplace=True)
    models_answer.rename(columns={
        'context': 'practice_filter',
    }, inplace=True)
    models_answer.drop('item', axis=1, inplace=True)
    flashcards_flashcard.drop(['active', 'description', 'lang'], axis=1, inplace=True)

    if 'term_type' not in flashcards_term:
        flashcards_term['term_type'] = flashcards_term['term_name'].apply(lambda row: '')
    elif flashcards_term['term_type'].isnull().sum() == len(flashcards_term):
        flashcards_term['term_type'] = flashcards_term['term_type'].apply(lambda row: '')

    flashcards_flashcard = pandas.merge(flashcards_flashcard, flashcards_term[['term', 'term_name', 'term_type', 'term_id']], on='term', how='inner')
    flashcards_flashcard = pandas.merge(flashcards_flashcard, flashcards_context[['context', 'context_name', 'context_id']], on='context', how='inner')

    models_answer = pandas.merge(models_answer, flashcards_flashcard, left_on='item_asked', right_on='item')
    models_answer.drop('item', axis=1, inplace=True)
    models_answer.rename(columns={
        col: '{}_asked'.format(col) for col in flashcards_flashcard.columns
    }, inplace=True)

    models_answer = pandas.merge(models_answer, flashcards_flashcard, left_on='item_answered', right_on='item', how='left')
    models_answer.drop('item', axis=1, inplace=True)
    models_answer.rename(columns={
        col: '{}_answered'.format(col) for col in flashcards_flashcard.columns
    }, inplace=True)

    return models_answer
