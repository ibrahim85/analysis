from commands.all.raw import load_and_merge
from spiderpig import spiderpig
from random import sample


@spiderpig()
def load_train_test_set(test_size=0.1, seed=42):
    answers = load_answers()
    all_users = set(answers['user'].unique())
    test_users = set(sample(all_users, int(len(all_users) * test_size)))
    answers['test'] = answers['user'].isin(test_users)
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
    return load_and_merge()[['user', 'item_asked', 'item_answered', 'time', 'guess']]
