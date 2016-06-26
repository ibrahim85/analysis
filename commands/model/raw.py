from commands.all.raw import load_answers_with_seconds_ago
from spiderpig import spiderpig
import random


@spiderpig()
def load_train_test_set(test_size=0.1, seed=42):
    random.seed(seed)
    answers = load_answers()
    all_users = set(answers['user'].unique())
    test_users = set(random.sample(all_users, int(len(all_users) * test_size)))
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
    return load_answers_with_seconds_ago()[['user', 'item_asked', 'item_answered', 'time', 'guess', 'seconds_ago']]
