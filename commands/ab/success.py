from .raw import load_answers, load_success, load_non_reference_answers
from metric import binomial_confidence_mean
from spiderpig import spiderpig
import matplotlib.pyplot as plt
import numpy
import output
import pandas
import seaborn as sns


def _histogram(xs, bins=10):
    hist, bins = numpy.histogram(xs, bins=bins)
    return {
        'hist': list(hist),
        'bins': list(bins),
    }


@spiderpig()
def load_error_by_attempt(skip_reference=True):
    answers = load_non_reference_answers() if skip_reference else load_answers()
    answers['attempt'] = answers.groupby([
        'experiment_setup_name',
        'user_id',
        'context_name',
        'term_type',
    ]).cumcount()

    def _apply(group):
        ci = binomial_confidence_mean(group['item_asked_id'] != group['item_answered_id'])
        return pandas.DataFrame([{
            'value': ci[0] * 100,
            'variable': 'error',
            'confidence_min': ci[1][0] * 100,
            'confidence_max': ci[1][1] * 100
        }])
    return answers.groupby(['experiment_setup_name', 'attempt']).apply(_apply).reset_index()


def error_rate_histogram():
    answers = load_answers()
    success = load_success().reset_index()
    result = []
    for setup, data in answers.groupby('experiment_setup_name'):
        users = data['user_id'].unique()
        setup_success = success[success['user_id'].isin(users)]
        hist = _histogram(setup_success[0], bins=numpy.arange(0, 1.1, step=0.1))
        for b, v in zip(hist['bins'], hist['hist']):
            result.append({
                'setup': setup,
                'value': v,
                'bin_min': numpy.round(b, 1),
                'bin_max': numpy.round(b + 0.1, 1),
            })
    return pandas.DataFrame(result)


def plot_error_rate_histogram():
    g = sns.barplot(x='bin_min', y='value', hue='setup', data=error_rate_histogram())
    g.get_legend().set_title(None)
    g.get_legend().set_frame_on(True)
    g.yaxis.grid(True)
    plt.xlabel('Success')
    plt.ylabel('Number of learners')


def plot_error_by_attempt(length, with_confidence=False, legend=True):
        data = load_error_by_attempt()
        data = data[data['attempt'] < length]
        for j, (setup, setup_data) in enumerate(data.groupby('experiment_setup_name')):
            plt.plot(setup_data['attempt'], setup_data['value'], label=setup, color=output.palette()[j], linewidth=3)
            if with_confidence:
                plt.fill_between(
                    setup_data['attempt'],
                    setup_data['confidence_min'],
                    setup_data['confidence_max'],
                    color=output.palette()[j], alpha=0.5
                )
        # plt.ylim(0, 70)
        plt.xlim(0, data['attempt'].max())
        plt.ylabel('Error rate')
        plt.xlabel('Attempt (non reference)')
        if legend:
            plt.legend(loc=1)


def execute(length=100, with_confidence=False):
    plot_error_rate_histogram()
    output.savefig('success_per_setup')
    plot_error_by_attempt(length, with_confidence)
    output.savefig('error_by_attempt')
