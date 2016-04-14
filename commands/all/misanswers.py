from .raw import load_answers
from spiderpig import spiderpig
import matplotlib.pyplot as plt
import numpy as np
import output


@spiderpig()
def load_confusing_factor(term_name):
    answers = load_answers()
    answers = answers[(answers['term_name_asked'] == term_name)]
    answers = answers[answers['term_name_answered'].notnull()]
    answers = answers[answers['item_asked'] != answers['item_answered']]
    count_all = len(answers)
    return answers.groupby('term_name_answered').apply(lambda g: np.round(100 * len(g) / count_all, 2))


def plot_misanswers(term_name, n):
    term_names, confusing_factor = list(zip(*sorted(load_confusing_factor(term_name).items(), reverse=True, key=lambda x: x[1])))
    if n is not None:
        term_names = term_names[:n]
        confusing_factor = confusing_factor[:n]
    plt.plot(confusing_factor, linewidth=2)
    plt.fill_between(list(range(len(confusing_factor))), [0] * len(confusing_factor), confusing_factor, alpha=0.2)
    plt.xlim(0, len(confusing_factor) - 1)
    plt.ylabel('Misanswers (%)')
    plt.title('{}'.format(term_name))
    plt.xticks(list(range(len(confusing_factor))), term_names, rotation=90)
    plt.tight_layout()
    output.savefig('misanswers')


def execute(term_name, n=None):
    plot_misanswers(term_name, n)
