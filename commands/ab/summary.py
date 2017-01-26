from .data import fit_learning_curve, groupped_reference_series
from .raw import load_reference_answers, load_user_answers, load_user_time, load_answers
from metric import binomial_confidence_mean, confidence_value_to_json
from pandas import Timedelta
from pylab import rcParams
from spiderpig import spiderpig
import matplotlib.pyplot as plt
import numpy
import output
import seaborn as sns


@spiderpig()
def reference_series(length):
    answers = load_reference_answers()
    return groupped_reference_series(answers, length=length)


@spiderpig()
def learning_curve(length):
    group_series = reference_series(length=length)
    not_balanced = fit_learning_curve(group_series, length=length, balance=False)
    not_balanced['balanced'] = not_balanced['value'].apply(lambda x: False)
    return not_balanced


@spiderpig()
def survival_curve(length):
    user_answers = load_user_answers(groupby=['experiment_setup_name'])

    def _progress_confidence(i, data):
        xs = [x > i for x in data]
        return confidence_value_to_json(binomial_confidence_mean(xs), use_format_number=False)
    result = {}
    for g, d in user_answers.reset_index().groupby('experiment_setup_name'):
        inner_result = []
        for i in range(length):
            inner_result.append(_progress_confidence(i, d[0]))
        result[g] = inner_result
    return result


@spiderpig()
def survival_curve_time(length):
    user_times = load_user_time(groupby=['experiment_setup_name'])

    def _progress_confidence(i, data):
        xs = [x > i for x in data]
        return confidence_value_to_json(binomial_confidence_mean(xs), use_format_number=False)
    result = {}
    for g, d in user_times.reset_index().groupby('experiment_setup_name'):
        inner_result = []
        for i in range(0, length):
            inner_result.append(_progress_confidence(i, d[0]))
        result[g] = inner_result
    return result


def returning(hours=12):
    answers = load_answers()
    timedelta = Timedelta('{} hours'.format(hours))

    def _apply(group):
        return (group['time'].max() - group['time'].min()) > timedelta
    return answers.groupby(['experiment_setup_name', 'user_id']).apply(_apply).reset_index().rename(columns={0: 'returned'})


def plot_summary(title=None):
    survival = survival_curve(100)
    survival_time = survival_curve_time(1800)
    learning = learning_curve(10)

    def _survival(data, i, n, label=None):
        yerr = [
            [100 * (values[n - 1]['value'] - values[n - 1]['confidence_interval']['min']) for g, values in sorted(data.items())],
            [100 * (values[n - 1]['confidence_interval']['max'] - values[n - 1]['value']) for g, values in sorted(data.items())],
        ]
        plt.bar(
            0.1 + 0.4 * i + numpy.arange(len(data)),
            [values[n - 1]['value'] * 100 for g, values in sorted(data.items())], 0.4,
            color=output.palette()[i],
            yerr=yerr,
            label=label,
            error_kw={'ecolor': 'black'},
        )

    rcParams['figure.figsize'] = 6, 10
    # learning slope
    plt.subplot(311)
    data = learning[learning['variable'] == 'slope'].sort_values(by='experiment_setup_name')
    plt.title('(A) Learning rate')
    plt.bar(
        0.1 + numpy.arange(len(data)),
        data['value'], 0.8,
        color=output.palette()[1],
        yerr=[data['value'] - data['confidence_min'], data['confidence_max'] - data['value']],
        error_kw={'ecolor': 'black'},
    )
    plt.ylim(0.3, 0.4)
    plt.ylabel('Learning rate', labelpad=-20)
    ylim = plt.ylim()
    plt.yticks(numpy.linspace(ylim[0], ylim[1], 15), [ylim[0]] + [''] * 13 + [ylim[1]])
    plt.yticks(
        plt.yticks()[0],
        [plt.yticks()[0][0]] + [''] * (len(plt.yticks()[0]) - 2) + [plt.yticks()[0][-1]]
    )
    plt.gca().yaxis.grid(True)
    plt.xticks(
        numpy.arange(len(data)) + 0.5,
        data['experiment_setup_name']
    )
    ylim = plt.ylim()
    plt.yticks(numpy.linspace(ylim[0], ylim[1], 15), [ylim[0]] + [''] * 13 + [ylim[1]])

    # short-term
    plt.subplot(312)
    plt.title('(B) Short-term survival')
    _survival(survival, 0, 20, '20 ans.')
    _survival(survival_time, 1, 120, '2 min.')
    plt.ylim(65, 75)
    plt.ylabel('Learners (%)', labelpad=-20)
    ylim = plt.ylim()
    plt.yticks(numpy.linspace(ylim[0], ylim[1], 15), [ylim[0]] + [''] * 13 + [ylim[1]])
    plt.yticks(
        plt.yticks()[0],
        [int(plt.yticks()[0][0])] + [''] * (len(plt.yticks()[0]) - 2) + [int(plt.yticks()[0][-1])]
    )
    plt.gca().yaxis.grid(True)
    plt.legend(loc=3, frameon=True, ncol=2)
    plt.xticks(
        numpy.arange(len(data)) + 0.5,
        data['experiment_setup_name']
    )
    # long-term
    plt.subplot(313)
    plt.title('(C) Long-term survival')
    _survival(survival, 0, 100, '100 ans.')
    _survival(survival_time, 1, 600, '10 min.')
    plt.ylim(25, 35)
    plt.ylabel('Learners (%)', labelpad=-20)
    ylim = plt.ylim()
    plt.yticks(numpy.linspace(ylim[0], ylim[1], 15), [ylim[0]] + [''] * 13 + [ylim[1]])
    plt.yticks(
        plt.yticks()[0],
        [int(plt.yticks()[0][0])] + [''] * (len(plt.yticks()[0]) - 2) + [int(plt.yticks()[0][-1])]
    )
    plt.gca().yaxis.grid(True)
    plt.legend(loc=3, frameon=True, ncol=2)

    plt.xticks(
        numpy.arange(len(data)) + 0.5,
        data['experiment_setup_name']
    )
    plt.xlabel('Conditions')
    plt.tight_layout()
    plt.subplots_adjust(left=0.1, right=0.98, bottom=0.08, top=0.95, hspace=0.25)

    if title is not None:
        plt.subplots_adjust(top=0.90)
        plt.suptitle(title, fontsize=20)


def execute(title=None):
    sns.barplot(x='experiment_setup_name', y='returned', data=returning(), estimator=numpy.mean, color=output.palette()[0])
    plt.gca().yaxis.grid(True)
    output.savefig('returning')
    plot_summary(title=title)
    output.savefig('summary', tight_layout=False)
