from .raw import load_non_reference_answers, load_contexts
from metric import binomial_confidence_mean
from pylab import rcParams
from spiderpig import spiderpig
import matplotlib.pyplot as plt
import output
import pandas
import seaborn as sns


@spiderpig()
def load_error_by_attempt(zoom_column):
    answers = pandas.merge(load_non_reference_answers(), load_contexts(), on=['context_name', 'term_type'], how='inner')
    answers['attempt'] = answers.groupby([
        'experiment_setup_name',
        zoom_column,
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
    return answers.groupby(['experiment_setup_name', zoom_column, 'attempt']).apply(_apply).reset_index()


@spiderpig()
def load_options_by_attempt(zoom_column):
    answers = pandas.merge(load_non_reference_answers(), load_contexts(), on=['context_name', 'term_type'], how='inner')
    answers['attempt'] = answers.groupby([
        'experiment_setup_name',
        zoom_column,
        'user_id',
        'context_name',
        'term_type',
    ]).cumcount()
    answers['options'] = answers['guess'].apply(lambda x: int(round(1 / x)) if x != 0 else 0)

    def _apply(group):
        return group.groupby('options').apply(lambda g: len(g) / len(group)).reset_index().rename(columns={0: 'value'})
    return answers.groupby(['experiment_setup_name', zoom_column, 'attempt']).apply(_apply).reset_index()


def plot_error_by_attempt(length, vertical=False, with_confidence=False):
    if vertical:
        rcParams['figure.figsize'] = 7.5, 15
    else:
        rcParams['figure.figsize'] = 22.5, 5
    for zoom_column in ['context_difficulty_label', 'context_size_label']:
        data = load_error_by_attempt(zoom_column)
        data = data[data['attempt'] < length]
        for i, (zoom_column_value, zoom_data) in enumerate(data.groupby(zoom_column)):
            plt.subplot(3, 1, i + 1) if vertical else plt.subplot(1, 3, i + 1)
            for j, (setup, setup_data) in enumerate(zoom_data.groupby('experiment_setup_name')):
                plt.plot(setup_data['attempt'], setup_data['value'], label=setup, color=output.palette()[j])
                if with_confidence:
                    plt.fill_between(
                        setup_data['attempt'],
                        setup_data['confidence_min'],
                        setup_data['confidence_max'],
                        color=output.palette()[j], alpha=0.35
                    )
            plt.title(zoom_column_value)
            plt.ylim(0, 70)
            if vertical or i == 0:
                plt.ylabel('Error rate')
            if not vertical or i == 2:
                plt.xlabel('Attempt (non reference)')
            if i == 1:
                plt.legend(loc=1)
        output.savefig('error_by_attempt_zoom_{}'.format(zoom_column))


def plot_options_by_attempt(length):
    length = length / 2
    for zoom_column in ['context_difficulty_label', 'context_size_label']:
        data = load_options_by_attempt(zoom_column)
        data = data[(data['attempt'] < length) & (data['options'] != 0)]
        max_options = data['options'].max()
        for i, (zoom_column_value, zoom_data) in enumerate(data.groupby(zoom_column)):
            for j, (setup, setup_data) in enumerate(zoom_data.groupby('experiment_setup_name')):
                for opt in range(2, max_options + 1):
                    if opt not in setup_data['options'].unique():
                        for attempt in range(0, int(length)):
                            setup_data = setup_data.append(pandas.DataFrame([{'attempt': attempt, 'options': opt, 'value': 0}]))
                cols = len(zoom_data['experiment_setup_name'].unique())
                plt.subplot(1, cols, j + 1)
                to_plot = setup_data.pivot_table(columns='options', index='attempt', values='value', dropna=False)
                plt.title(setup)
                sns.heatmap(to_plot, annot=False, cbar=False, linewidths=.5)
                if j != 0:
                    plt.ylabel('')
                plt.gca().axes.get_yaxis().set_ticks([])
                plt.suptitle('{}: {}'.format(zoom_column, zoom_column_value))
            output.savefig('options_by_attempt_zoom_{}_{}'.format(zoom_column, zoom_column_value))


def execute(length=100, vertical=False, with_confidence=False):
    plot_options_by_attempt(length)
    plot_error_by_attempt(length, vertical=vertical, with_confidence=with_confidence)
