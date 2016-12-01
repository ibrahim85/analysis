from .data import groupped_reference_series
from .raw import load_reference_answers
from pylab import rcParams
from spiderpig import spiderpig
import matplotlib.pyplot as plt
import numpy
import output
import pandas
import seaborn as sns


@spiderpig()
def reference_series():
    answers = load_reference_answers()
    return groupped_reference_series(answers, length=1000000, require_length=False)


def load_quit_score():
    result = []
    for condition, data in reference_series().items():
        for serie in data:
            result.append({
                'experiment_setup_name': condition,
                'score': 1 - serie[-1],
            })
    return pandas.DataFrame(result)


def plot_quit_score(ylim=None):
    if ylim is None:
        ylim = 0.5, 0.6
    data = load_quit_score().sort_values(by='experiment_setup_name')
    sns.barplot(y='Condition', x='score', data=data.rename(columns={'experiment_setup_name': 'Condition'}), color=output.palette()[0], orient='h')
    plt.gca().xaxis.grid(True)
    plt.xlim(*ylim)
    plt.xticks(numpy.linspace(ylim[0], ylim[1], 11), [ylim[0]] + [''] * 9 + [ylim[1]])
    plt.xlabel('Quit score')


def execute():
    rcParams['figure.figsize'] = 4, 6
    plot_quit_score()
    output.savefig('quit_score')
