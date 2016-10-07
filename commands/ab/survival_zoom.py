from .raw import load_answers, load_contexts
from spiderpig import spiderpig
from metric import binomial_confidence_mean
import matplotlib.pyplot as plt
import pandas
import output
from pylab import rcParams


@spiderpig()
def load_survival_curve_answers(length, zoom_column):
    data = pandas.merge(load_answers(), load_contexts(), on=['context_name', 'term_type'], how='inner')
    user_answers = data.groupby([zoom_column, 'experiment_setup_name', 'user_id']).apply(len)

    def _progress_confidence(i, data):
        xs = [x > i for x in data]
        return binomial_confidence_mean(xs)
    result = []
    for (g, zoom_column_value), d in user_answers.reset_index().groupby(['experiment_setup_name', zoom_column]):
        for i in range(length):
            ci = _progress_confidence(i, d[0])
            row = {
                'variable': 'survival_answers',
                'value': ci[0],
                'experiment_setup_name': g,
                'confidence_min': ci[1][0],
                'confidence_max': ci[1][1],
                'zoom_column': zoom_column,
                'zoom_column_value': zoom_column_value,
                'attempt': i,
            }
            result.append(row)
    return pandas.DataFrame(result)


@spiderpig()
def load_survival_curve_time(length, zoom_column):
    data = pandas.merge(load_answers(), load_contexts(), on=['context_name', 'term_type'], how='inner')

    def _apply(data):
        return (data['response_time'][data['response_time'] != -1]).apply(lambda x: min(x / 1000.0, 30)).sum()
    user_times = data.groupby([zoom_column, 'experiment_setup_name', 'user_id']).apply(_apply)

    def _progress_confidence(i, data):
        xs = [x > i for x in data]
        return binomial_confidence_mean(xs)
    result = []
    for (g, zoom_column_value), d in user_times.reset_index().groupby(['experiment_setup_name', zoom_column]):
        for i in range(length):
            ci = _progress_confidence(i, d[0])
            row = {
                'variable': 'survival_time',
                'value': ci[0],
                'experiment_setup_name': g,
                'confidence_min': ci[1][0],
                'confidence_max': ci[1][1],
                'zoom_column': zoom_column,
                'zoom_column_value': zoom_column_value,
                'attempt': i,
            }
            result.append(row)
    return pandas.DataFrame(result)


def plot_survival_curve(survival_data, legend=True, with_confidence=False):
    for i, (setup, setup_data) in enumerate(survival_data.sort_values(by='attempt').groupby('experiment_setup_name')):
        plt.plot(setup_data['attempt'] + 1, setup_data['value'].apply(lambda x: x * 100), label=setup, color=output.palette()[i])
        if with_confidence:
            plt.fill_between(
                setup_data['attempt'] + 1,
                setup_data['confidence_min'.format(setup)].apply(lambda x: x * 100),
                setup_data['confidence_max'.format(setup)].apply(lambda x: x * 100),
                color=output.palette()[i], alpha=0.35
            )
    if legend:
        plt.legend(loc=1)
    plt.ylim(0, 100)


def plot_global_survival_curve(survival_data, vertical, with_confidence=False):
    if vertical:
        rcParams['figure.figsize'] = 7.5, 15
    else:
        rcParams['figure.figsize'] = 22.5, 5
    for i, (zoom_column_value, data) in enumerate(survival_data.groupby('zoom_column_value')):
        plt.subplot(3, 1, i + 1) if vertical else plt.subplot(1, 3, i + 1)
        plt.title(zoom_column_value)
        plot_survival_curve(data, with_confidence=with_confidence)
        if vertical or i == 0:
            plt.ylabel('Proportion of learners')


def execute(answers=60, time=600, vertical=False, with_confidence=False):
    for zoom_column in ['context_size_label', 'context_difficulty_label']:
        raw_data = load_survival_curve_answers(answers, zoom_column).append(load_survival_curve_time(time, zoom_column))
        for variable in ['survival_time', 'survival_answers']:
            data = raw_data[raw_data['variable'] == variable]
            plot_global_survival_curve(data[data['zoom_column'] == zoom_column], vertical=vertical, with_confidence=with_confidence)
            output.savefig('{}_zoom_{}'.format(variable, zoom_column))
