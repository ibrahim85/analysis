from .raw import load_difficulty, load_answers
from math import exp
import matplotlib.pyplot as plt
import numpy as np
import output
import pandas as pd


def sigmoid(x):
    'Transform a real number to interval [0, 1]'
    return 1.0 / (1 + exp(-x))


def score_probability(target_probability, probability):
    'Compute a score when for the given probability when the target probability is given.'
    diff = target_probability - probability
    sign = 1 if diff > 0 else -1
    normed_diff = abs(diff) / max(0.001, abs(target_probability - 0.5 + sign * 0.5))
    return 1 - normed_diff ** 2


def plot_score_difficulty_examples(target_probability, n):
    answers = load_answers()
    difficulty = load_difficulty()
    difficulty['difficulty'] = difficulty['difficulty'].apply(lambda x: sigmoid(-x))
    terms = pd.merge(answers[['item_asked', 'term_name_asked']].drop_duplicates(), difficulty, left_on='item_asked', right_on='item_id', how='inner')[['term_name_asked', 'difficulty']]
    terms['score'] = terms['difficulty'].apply(lambda p: score_probability(target_probability, p))
    terms.sort_values(by=['score'], inplace=True, ascending=False)
    terms.reset_index(inplace=True)
    if n is not None:
        terms = terms.head(n=n)
    plt.plot(np.arange(len(terms)) + 0.5, terms['score'], linewidth=5, label='Score')
    plt.xticks(np.arange(len(terms)) + 0.5, terms['term_name_asked'], rotation=90)
    plt.bar(np.arange(len(terms)) + 0.1, terms['difficulty'], 0.8, color='#bbbbbb', label='Prediction', edgecolor='#bbbbbb')
    plt.xlim(0, len(terms))
    plt.legend(loc=2)
    output.savefig('score_difficulty_examples')


def plot_score_difficulty(target_probability):
    xs = np.linspace(0, 1, 100)
    difficulty = load_difficulty()
    plt.hist([sigmoid(-x) for x in difficulty['difficulty']], bins=10)
    plt.xlabel('Prediction\n(probability of correct answer on open question)')
    plt.ylabel('Number of items')
    plt.twinx()
    plt.plot(xs, [score_probability(target_probability, x) for x in xs], color='black', linewidth=5)
    plt.ylabel('Score')
    output.savefig('score_difficulty')


def execute(target_probability=0.7, n=None):
    plot_score_difficulty(target_probability)
    plot_score_difficulty_examples(target_probability, n)
