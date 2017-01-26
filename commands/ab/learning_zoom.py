from .data import groupped_reference_series, fit_learning_curve
from .raw import load_contexts, load_reference_answers
from pylab import rcParams
from spiderpig import spiderpig
import matplotlib.pyplot as plt
import output
import pandas
import numpy


@spiderpig()
def reference_series(length, zoom_column, user_length=None, context_answer_limit=1):
    answers = load_reference_answers()
    answers = pandas.merge(answers, load_contexts(), on=['term_type', 'context_name'], how='inner')
    result = {}
    for zoom_column_key, context_data in answers.groupby(zoom_column):
        result[zoom_column_key] = groupped_reference_series(context_data, length=length, user_length=user_length, context_answer_limit=context_answer_limit)
    return result


@spiderpig()
def global_learning_curve(length, zoom_column, bootstrap_samples, user_length=None, context_answer_limit=1):
    result = None
    for zoom_column_key, context_data in reference_series(length=length, zoom_column=zoom_column, user_length=user_length, context_answer_limit=context_answer_limit).items():
        not_balanced = fit_learning_curve(context_data, length=length, balance=False, bootstrap_samples=bootstrap_samples)
        not_balanced[zoom_column] = not_balanced['value'].apply(lambda v: zoom_column_key)
        if result is None:
            result = not_balanced
        else:
            result = result.append(not_balanced)
    return result


def plot_learning_curve(data, legend=True, with_confidence=False):
    MARKERS = "dos^" * 10
    for i, (setup, setup_data) in enumerate(data.groupby('experiment_setup_name')):
        plt.plot(setup_data['attempt'] + 1, setup_data['value'].apply(lambda x: x * 100 if x < 1 else x), label=setup, color=output.palette()[i], marker=MARKERS[i], markersize=10)
        if with_confidence:
            plt.fill_between(
                setup_data['attempt'] + 1,
                setup_data['confidence_min'.format(setup)].apply(lambda x: x * 100 if x < 1 else x),
                setup_data['confidence_max'.format(setup)].apply(lambda x: x * 100 if x < 1 else x),
                color=output.palette()[i], alpha=0.35
            )
    if legend:
        plt.legend(loc=1)
    plt.xlabel('Reference attempt')


def plot_global_learning_curve(length, zoom_column, user_length, with_confidence, bootstrap_samples, vertical):
    if vertical:
        rcParams['figure.figsize'] = 7.5, 15
    else:
        rcParams['figure.figsize'] = 22.5, 5
    data = global_learning_curve(length, zoom_column=zoom_column, user_length=user_length, bootstrap_samples=bootstrap_samples)
    for i, (zoom_column_key, data) in enumerate(data.groupby(zoom_column)):
        plt.subplot(3, 1, i + 1) if vertical else plt.subplot(1, 3, i + 1)
        plt.title(zoom_column_key)
        plot_learning_curve(data[(data['variable'] == 'fit')], with_confidence=with_confidence)
        if vertical or i == 0:
            plt.ylabel('Error rate')
        # plt.ylim(0, 60)
    output.savefig('learning_curve_zoom_{}'.format(zoom_column))


def plot_global_learning_slope(length, zoom_column, user_length, with_confidence, bootstrap_samples, vertical):
    rcParams['figure.figsize'] = 15, 8
    data = global_learning_curve(length, zoom_column=zoom_column, user_length=user_length, bootstrap_samples=bootstrap_samples)
    for i, (experiment_setup_name, data) in enumerate(data[data['variable'] == 'slope'].groupby('experiment_setup_name')):
        data = data.sort_values(by=zoom_column)
        plt.bar(
            numpy.arange(len(data)) + i * 0.3,
            data['value'], 0.3,
            color=output.palette()[i],
            label=experiment_setup_name,
            yerr=[data['value'] - data['confidence_min'], data['confidence_max'] - data['value']],
            error_kw={'ecolor': 'black'},
        )
        plt.xticks(
            numpy.arange(len(data)) + 0.3,
            data[zoom_column]
        )
        plt.yticks(
            numpy.linspace(min(plt.yticks()[0]), max(plt.yticks()[0]), 21),
            [plt.yticks()[0][0]] + [''] * 19 + [plt.yticks()[0][-1]]
        )
    plt.legend(frameon=True, loc=0)
    plt.xlabel(zoom_column)
    plt.ylabel('k')
    plt.gca().yaxis.grid(True)
    output.savefig('learning_slope_zoom_{}'.format(zoom_column))


def execute(length=10, user_length=None, with_confidence=False, vertical=False, bootstrap_samples=100):
    print('------------------------------------------------------------------------------------------')
    print('SIZE')
    print('------------------------------------------------------------------------------------------')
    print(load_contexts().sort_values(by=['context_size', 'context_name'])[['context_name', 'term_type', 'context_size_label']])
    print('------------------------------------------------------------------------------------------')
    print('DIFFICULTY')
    print('------------------------------------------------------------------------------------------')
    print(load_contexts().sort_values(by=['context_difficulty', 'context_name'])[['context_name', 'term_type', 'context_difficulty_label']])
    for zoom_column in ['context_size_label', 'context_difficulty_label']:
        plot_global_learning_curve(
            length=length, zoom_column=zoom_column, user_length=user_length,
            with_confidence=with_confidence, bootstrap_samples=bootstrap_samples,
            vertical=vertical
        )
        plot_global_learning_slope(
            length=length, zoom_column=zoom_column, user_length=user_length,
            with_confidence=with_confidence, bootstrap_samples=bootstrap_samples,
            vertical=vertical
        )
