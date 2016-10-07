from .confusing_factor import load_confusing_factor
from .raw import load_non_reference_answers, load_options
from pylab import rcParams
from matplotlib import gridspec
from spiderpig import spiderpig
import matplotlib.pyplot as plt
import output
import pandas
import seaborn as sns


@spiderpig()
def load_options_by_attempt():
    answers = load_non_reference_answers()
    answers['attempt'] = answers.groupby([
        'experiment_setup_name',
        'user_id',
        'context_name',
        'term_type',
    ]).cumcount()
    answers['options'] = answers['guess'].apply(lambda x: int(round(1 / x)) if x != 0 else 0)

    def _apply(group):
        return group.groupby('options').apply(lambda g: len(g) / len(group)).reset_index().rename(columns={0: 'value'})
    return answers.groupby(['experiment_setup_name', 'attempt']).apply(_apply).reset_index()


@spiderpig()
def load_distractors_usage(length=None, by_attempt=True):
    cf = load_confusing_factor()

    def _apply(g):
        g['ratio'] = g['value'] / g['value'].sum()
        return g
    cf = cf.groupby(['experiment_setup_name', 'item']).apply(_apply).reset_index().sort_values(by=['experiment_setup_name', 'item', 'ratio'], ascending=False)
    cf['ratio_rank'] = cf.groupby([
        'experiment_setup_name',
        'item'
    ]).cumcount()
    answers = load_non_reference_answers()
    answers['attempt'] = answers.groupby([
        'experiment_setup_name',
        'user_id',
        'context_name',
        'term_type',
    ]).cumcount()
    if length is not None:
        answers = answers[answers['attempt'] < length]
    answers = pandas.merge(answers, load_options().rename(columns={'answer_id': 'id'}), on=['id', 'item_asked_id', 'experiment_setup_name', 'experiment_setup_id'], how='inner')[['item_asked_id', 'experiment_setup_name', 'attempt', 'item_option_id']]
    answers = pandas.merge(
        answers,
        cf[['experiment_setup_name', 'item', 'other', 'ratio_rank']].rename(columns={'item': 'item_asked_id', 'other': 'item_option_id', 'ratio_rank': 'confusing_rank'}),
        on=['experiment_setup_name', 'item_asked_id', 'item_option_id'], how='inner')

    def _apply(group):
        total = len(group)
        return group.groupby('confusing_rank').apply(lambda g: len(g) / total).reset_index().rename(columns={0: 'value'})
    groupby_add = ['attempt'] if by_attempt else []
    return answers.groupby(['experiment_setup_name'] + groupby_add).apply(_apply).reset_index()


def plot_number_of_options_by_attempt(length):
    data = load_options_by_attempt()
    data = data[(data['attempt'] < length)]
    max_options = data['options'][data['options'] != 0].max()
    data['options'] = data['options'].apply(lambda x: max_options + 1 if x == 0 else x)
    cols = len(data['experiment_setup_name'].unique())
    gs = gridspec.GridSpec(1, cols, width_ratios=[3.5] * (cols - 1) + [4])
    rcParams['figure.figsize'] = cols * 1.5, int(5 * length / 50)
    rcParams['axes.linewidth'] = 1
    for j, (setup, setup_data) in enumerate(data.groupby('experiment_setup_name')):
        for opt in range(2, max_options + 1):
            if opt not in setup_data['options'].unique():
                for attempt in range(0, int(length)):
                    setup_data = setup_data.append(pandas.DataFrame([{'attempt': attempt, 'options': opt, 'value': 0}]))
        plt.subplot(gs[j])
        to_plot = setup_data.pivot_table(columns='options', index='attempt', values='value', dropna=False, fill_value=0)
        plt.title(setup)
        sns.heatmap(to_plot, annot=False, cbar=(j == cols - 1), linewidths=0.1)
        plt.xticks(plt.xticks()[0], [lab.get_text() if int(lab.get_text()) <= max_options else 'O' for lab in plt.xticks()[1]])
        if j != 0:
            plt.gca().axes.get_yaxis().set_ticks([])
            plt.ylabel('')
        else:
            pos = plt.yticks()[0]
            lab = plt.yticks()[1]
            plt.yticks([pos[0], pos[-1]], [int(lab[0].get_text()) + 1, int(lab[-1].get_text()) + 1])
    output.savefig('options_by_attempt')


def plot_distractors_by_attempt(length, distractors):
    data = load_distractors_usage(length=length, by_attempt=True)
    data = data[data['confusing_rank'] < distractors]
    data['confusing_rank'] = data['confusing_rank'] + 1
    vmax = data['value'].max()
    vmin = data['value'].min()
    cols = len(data['experiment_setup_name'].unique())
    rcParams['figure.figsize'] = cols * 2.5, int(5 * length / 50)
    gs = gridspec.GridSpec(1, cols, width_ratios=[3.5] * (cols - 1) + [4])
    for j, (setup, setup_data) in enumerate(data.groupby('experiment_setup_name')):
        plt.subplot(gs[j])
        to_plot = setup_data.pivot_table(columns='confusing_rank', index='attempt', values='value', dropna=False, fill_value=0)
        plt.title(setup)
        sns.heatmap(to_plot, annot=False, cbar=(j == cols - 1), linewidths=0.1, vmin=vmin, vmax=vmax)
        if j != 0:
            plt.gca().axes.get_yaxis().set_ticks([])
            plt.ylabel('')
        else:
            pos = plt.yticks()[0]
            lab = plt.yticks()[1]
            plt.yticks([pos[0], pos[-1]], [int(lab[0].get_text()) + 1, int(lab[-1].get_text()) + 1])
    output.savefig('distractors_by_attempt')


def plot_distractors(number_of_distractors=10):
    rcParams['figure.figsize'] = 7.5, 4
    data = load_distractors_usage().sort_values(by=['confusing_rank'])
    data = data[data['confusing_rank'] < 10]
    data['value'] *= 100
    data['confusing_rank'] += 1
    sns.barplot(x='confusing_rank', y='value', hue='Condition', data=data.rename(columns={'experiment_setup_name': 'Condition'}), ci=None)
    plt.ylabel('Average usage (%)')
    plt.xlabel('Top {} most competitive distractors'.format(number_of_distractors))
    output.savefig('distractors_usage')


def execute(length=50, distractors=5):
    plot_distractors_by_attempt(length, distractors)
    plot_number_of_options_by_attempt(length)
    plot_distractors(number_of_distractors=distractors)
