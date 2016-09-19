from .data import fit_learning_curve, groupped_reference_series
from .raw import load_reference_answers
from pylab import rcParams
from spiderpig import spiderpig
import matplotlib.pyplot as plt
import numpy
import output


@spiderpig()
def reference_series(length, user_length, context_answer_limit):
    answers = load_reference_answers()
    return groupped_reference_series(answers, length=length, user_length=user_length, context_answer_limit=context_answer_limit)


@spiderpig()
def global_learning_curve(length, user_length, context_answer_limit, bootstrap_samples):
    group_series = reference_series(length=length, user_length=user_length, context_answer_limit=context_answer_limit)
    not_balanced = fit_learning_curve(group_series, length=length, balance=False, bootstrap_samples=bootstrap_samples)
    not_balanced['balanced'] = not_balanced['value'].apply(lambda x: False)
    # return not_balanced
    balanced = fit_learning_curve(group_series, length=length, balance=True, bootstrap_samples=bootstrap_samples)
    balanced['balanced'] = balanced['value'].apply(lambda x: True)
    return balanced.append(not_balanced)


def plot_learning_curve(data, legend=True, with_confidence=False):
    MARKERS = "dos^" * 10
    for i, (setup, setup_data) in enumerate(data.groupby('experiment_setup_name')):
        plt.plot(setup_data['attempt'] + 1, setup_data['value'].apply(lambda x: x * 100), label=setup, color=output.palette()[i], marker=MARKERS[i], markersize=10)
        if with_confidence:
            plt.fill_between(
                setup_data['attempt'] + 1,
                setup_data['confidence_min'.format(setup)].apply(lambda x: x * 100),
                setup_data['confidence_max'.format(setup)].apply(lambda x: x * 100),
                color=output.palette()[i], alpha=0.35
            )
    if legend:
        plt.legend(loc=1)
    plt.xlabel('Reference attempt')
    plt.ylim(0, 60)


def plot_global_learning_slope(length, user_length, context_answer_limit, with_confidence, bootstrap_samples, balance):
    rcParams['figure.figsize'] = 7.5, 5
    data = global_learning_curve(length, user_length, context_answer_limit, bootstrap_samples)
    if not balance:
        data = data[~data['balanced']]
    for i, (data_balanced, data) in enumerate(data[data['variable'] == 'slope'].groupby('balanced')):
        data = data.sort_values(by='experiment_setup_name')
        plt.bar(
            numpy.arange(len(data)) + i * 0.4,
            data['value'], 0.4 if balance else 0.8,
            color=output.palette()[i],
            label=None if balance else ('balanced' if data_balanced else 'not balanced'),
            yerr=[data['value'] - data['confidence_min'], data['confidence_max'] - data['value']],
            error_kw={'ecolor': 'black'},
        )
        plt.xticks(
            numpy.arange(len(data)) + 0.4,
            data['experiment_setup_name']
        )
    if balance:
        plt.legend(frameon=True, loc=3)
    plt.xlabel('Condition')
    plt.ylabel('k')
    plt.gca().yaxis.grid(True)
    output.savefig('learning_slope')


def plot_global_learning_curve(length, user_length, context_answer_limit, with_confidence, bootstrap_samples, balance, vertical):
    if vertical:
        rcParams['figure.figsize'] = 7.5, 10
    else:
        rcParams['figure.figsize'] = 15, 5
    data = global_learning_curve(length, user_length, context_answer_limit, bootstrap_samples)
    balance_filter = data['balanced'] if balance else ~data['balanced']
    plt.subplot(211) if vertical else plt.subplot(121)
    plt.title('Coarse data')
    plot_learning_curve(data[(data['variable'] == 'raw') & balance_filter], with_confidence=with_confidence)
    plt.ylabel('Error rate')
    plt.subplot(212) if vertical else plt.subplot(122)
    plt.title('Fitted power law')
    if vertical:
        plt.ylabel('Error rate')
    plot_learning_curve(data[(data['variable'] == 'fit') & balance_filter], with_confidence=with_confidence)
    output.savefig('learning_curve')


def execute(length=10, user_length=None, context_answer_limit=100, with_confidence=False, bootstrap_samples=100, balance=False, vertical=False):
    plot_global_learning_curve(
        length=length, user_length=user_length,
        context_answer_limit=context_answer_limit,
        with_confidence=with_confidence, bootstrap_samples=bootstrap_samples,
        balance=balance,
        vertical=vertical
    )
    plot_global_learning_slope(
        length=length, user_length=user_length,
        context_answer_limit=context_answer_limit,
        with_confidence=with_confidence, bootstrap_samples=bootstrap_samples,
        balance=balance
    )
