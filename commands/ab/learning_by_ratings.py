from .data import groupped_reference_series, fit_learning_curve
from .learning import plot_learning_curve
from .raw import load_answers, load_ratings_with_contexts
from pylab import rcParams
from spiderpig import spiderpig
from collections import defaultdict
import matplotlib.pyplot as plt
import output
import pandas
import numpy


MAPPING = {
    4: 2,
    5: 1,
    6: 0,
    7: -1,
    8: -2,
}


def get_ratings_group(ratings):
    ratings_sum = 0
    previous = 0
    for v in ratings:
        previous += v
        ratings_sum += previous
    ratings_mean = ratings_sum / len(ratings)
    if ratings_mean >= 1:
        return 'more difficult'
    elif ratings_mean > -1:
        return 'appropriate'
    else:
        return 'easier'


@spiderpig()
def reference_series(length, user_length, context_answer_limit):
    answers = load_answers()
    ratings = load_ratings_with_contexts()
    ratings['value'] = ratings['value'].apply(lambda x: MAPPING[int(x)])
    ratings = ratings.groupby(['user', 'context_name', 'term_type']).apply(lambda g: get_ratings_group(g['value'].values)).reset_index().rename(columns={0: 'ratings_group', 'user': 'user_id'})
    answers = pandas.merge(answers, ratings, on=['user_id', 'context_name', 'term_type'], how='left')
    answers['ratings_group'].fillna('unknown', inplace=True)
    return groupped_reference_series(answers, length=length, user_length=user_length, context_answer_limit=context_answer_limit, groupby=['experiment_setup_name', 'ratings_group'], limit_length=True)


@spiderpig()
def learning_curve(length, user_length, context_answer_limit, bootstrap_samples):
    group_series = defaultdict(dict)
    for (setup, group), data in reference_series(length=length, user_length=user_length, context_answer_limit=context_answer_limit).items():
        group_series[group][setup] = data
    group_series = dict(group_series)
    result = None
    for group, group_series in group_series.items():
        group_data = fit_learning_curve(group_series, length=length, balance=False, bootstrap_samples=bootstrap_samples)
        group_data['ratings_group'] = group_data['value'].apply(lambda x: group)
        if result is None:
            result = group_data
        else:
            result = result.append(group_data)
    return result


def plot_all_learning_curves(length, user_length, context_answer_limit, bootstrap_samples):
    data = learning_curve(length, user_length, context_answer_limit, bootstrap_samples)
    data.sort_values(by=['experiment_setup_name', 'ratings_group'], inplace=True)
    rcParams['figure.figsize'] = 14, 8
    for curve_type in ['fit', 'raw']:
        for i, (ratings_group, ratings_data) in enumerate(data[data['variable'] == curve_type].groupby('ratings_group')):
            plt.subplot(2, 2, i + 1)
            plt.title(ratings_group)
            plot_learning_curve(ratings_data, with_confidence=True)
            plt.ylim(0, 70)
        output.savefig('learning_by_ratings_{}'.format(curve_type))
    rcParams['figure.figsize'] = 7.5, 4
    for i, (setup_name, to_plot) in enumerate(data[data['variable'] == 'slope'].groupby('experiment_setup_name')):
        plt.title(ratings_group)
        plt.bar(
            numpy.arange(len(to_plot)) + 0.4 * i,
            to_plot['value'], 0.4,
            label=setup_name,
            color=output.palette()[i],
            yerr=[to_plot['value'] - to_plot['confidence_min'], to_plot['confidence_max'] - to_plot['value']],
            error_kw={'ecolor': 'black'},
        )
        plt.xticks(
            numpy.arange(len(to_plot)) + 0.4,
            to_plot['ratings_group']
        )
    plt.ylim(0.2, plt.ylim()[1])
    plt.yticks(
        numpy.linspace(min(plt.yticks()[0]), max(plt.yticks()[0]), 25),
        [plt.yticks()[0][0]] + [''] * 23 + [plt.yticks()[0][-1]]
    )
    plt.gca().yaxis.grid(True)
    plt.legend(loc=0, frameon=True, ncol=2, fontsize='x-small')
    plt.title('Learning rate')
    output.savefig('learning_by_ratings_slope')


def execute(length=10, user_length=None, context_answer_limit=100, with_confidence=False, bootstrap_samples=100):
    plot_all_learning_curves(length, user_length, context_answer_limit, bootstrap_samples)
