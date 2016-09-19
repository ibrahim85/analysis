from .raw import load_context_difficulty, load_context_size
from pylab import rcParams
import matplotlib.pyplot as plt
import output
import pandas


def load_contexts():
    return pandas.merge(load_context_size(), load_context_difficulty(), on=['term_type', 'context_name'], how='inner')


def execute(ylim=False):
    rcParams['figure.figsize'] = 15, 10
    for context_name, term_type, difficulty, size in load_contexts()[['context_name', 'term_type', 'context_difficulty', 'context_size']].values:
        plt.plot(difficulty, size, marker='s', markersize=10, color='red')
        plt.text(difficulty, size, '{}, {}'.format(context_name, term_type), fontsize='small')
    plt.xlabel('Difficulty (error rate)')
    if ylim:
        plt.ylim(0, 60)
    plt.ylabel('Size')
    output.savefig('difficulty_vs_size')
