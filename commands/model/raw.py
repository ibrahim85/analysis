from commands.all.raw import load_and_merge
from spiderpig import spiderpig
from random import sample


@spiderpig()
def load_train_test_set(test_size=0.1, seed=42):
    answers = load_answers()
    all_users = answers['user_id'].unique()
    test_users = set(sample(all_users, int(len(all_users) * test_size)))
    answers['test'] = answers['user_id'].isin(test_users)
    return answers


@spiderpig()
def load_train_set():
    data = load_train_test_set()
    return data[~data['test']]


@spiderpig()
def load_test_set():
    data = load_train_test_set()
    return data[data['test']]


@spiderpig()
def load_answers():
    return load_and_merge()[['user_id', 'item_asked_id', 'item_answered_id', 'time']]
