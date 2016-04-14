import numpy
import pandas
from spiderpig import spiderpig


@spiderpig()
def load_difficulty(data_dir='data'):
    answers = load_answers()
    difficulty = pandas.read_csv('{}/difficulty.csv'.format(data_dir), index_col=None, dtype={'item_id': numpy.object})
    return difficulty[difficulty['item_id'].isin(answers['item_asked'].unique())]


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
def load_and_merge(data_dir='data', language='en', answer_limit=1):
    models_answer = pandas.read_csv('{}/proso_models_answer.csv'.format(data_dir), index_col=False, parse_dates=['time'], dtype={'item_answered': numpy.object, 'item_asked': numpy.object})
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
    }, inplace=True)
    flashcards_context.rename(columns={
        'id': 'context',
        'name': 'context_name',
    }, inplace=True)
    flashcards_flashcard.rename(columns={
        'id': 'flashcard',
    }, inplace=True)
    models_answer.rename(columns={
        'context': 'practice_filter',
    }, inplace=True)
    models_answer.drop('item', axis=1, inplace=True)
    flashcards_flashcard.drop(['active', 'description', 'identifier', 'lang'], axis=1, inplace=True)

    if flashcards_term['term_type'].isnull().sum() == len(flashcards_term):
        flashcards_term['term_type'] = flashcards_term['term_type'].apply(lambda row: '')

    flashcards_flashcard = pandas.merge(flashcards_flashcard, flashcards_term[['term', 'term_name', 'term_type']], on='term', how='inner')
    flashcards_flashcard = pandas.merge(flashcards_flashcard, flashcards_context[['context', 'context_name']], on='context', how='inner')

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
