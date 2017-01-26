from .data import groupped_reference_series, fit_learning_curve
from .learning import plot_learning_curve
from .raw import load_reference_answers
from spiderpig import spiderpig
import matplotlib.pyplot as plt
from pylab import rcParams
from collections import defaultdict
import output
import numpy
import math


@spiderpig()
def reference_series(length, user_length, context_answer_limit):
    answers = load_reference_answers()
    answers['context'] = answers.apply(lambda g: '{}, {}'.format(g['context_name'].replace('Czech Rep.', 'CZ').replace('United States', 'US'), g['term_type'].replace('region_cz', 'region')), axis=1)
    return groupped_reference_series(answers, length=length, user_length=user_length, context_answer_limit=context_answer_limit, groupby=['experiment_setup_name', 'context'])


@spiderpig()
def learning_curve(length, user_length, context_answer_limit, bootstrap_samples):
    group_series = defaultdict(dict)
    for (setup, context), data in reference_series(length=length, user_length=user_length, context_answer_limit=context_answer_limit).items():
        group_series[context][setup] = data
    group_series = dict(group_series)
    result = None
    for context, context_series in group_series.items():
        context_data = fit_learning_curve(context_series, length=length, balance=False, bootstrap_samples=bootstrap_samples)
        context_data['context'] = context_data['value'].apply(lambda x: context)
        if result is None:
            result = context_data
        else:
            result = result.append(context_data)
    return result


def plot_all_learning(length, user_length, context_answer_limit, bootstrap_samples):
    data = learning_curve(length, user_length, context_answer_limit, bootstrap_samples)
    data = data[data['variable'] == 'slope']
    data.sort_values(by='experiment_setup_name', inplace=True)
    rows = int(math.ceil(len(data['context'].unique()) / 4))
    rcParams['figure.figsize'] = 20, 4 * rows
    for i, (context, to_plot) in enumerate(data.groupby('context')):
        plt.subplot(rows, 4, i + 1)
        plt.title(context)
        plt.bar(
            numpy.arange(len(to_plot)) + 0.4,
            to_plot['value'], 0.8,
            color=output.palette()[0],
            yerr=[to_plot['value'] - to_plot['confidence_min'], to_plot['confidence_max'] - to_plot['value']],
            error_kw={'ecolor': 'black'},
        )
        plt.xticks(
            numpy.arange(len(to_plot)) + 0.8,
            to_plot['experiment_setup_name']
        )
        ylim = plt.ylim()
        plt.yticks(numpy.linspace(ylim[0], ylim[1], 11), [ylim[0]] + [''] * 9 + [ylim[1]])
        plt.yticks(
            plt.yticks()[0],
            [plt.yticks()[0][0]] + [''] * (len(plt.yticks()[0]) - 2) + [plt.yticks()[0][-1]]
        )
        plt.gca().yaxis.grid(True)
    output.savefig('learning_by_context')


def execute(length=10, user_length=None, context_answer_limit=100, with_confidence=False, bootstrap_samples=100, balance=False, vertical=False):
    plot_all_learning(length, user_length, context_answer_limit, bootstrap_samples)
