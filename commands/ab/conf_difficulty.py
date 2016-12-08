from .raw import load_answers, load_conf_difficulty_by_attempt
from metric import binomial_confidence_mean
from pylab import rcParams
from spiderpig import spiderpig
import matplotlib.pyplot as plt
import numpy
import output
import pandas
import seaborn as sns


@spiderpig()
def load_choice_by_success():
    answers = load_answers()
    answers['error_rate'] = answers['target_success'].apply(lambda v: int(_round((1 - v) * 100)))
    answers['attempt'] = answers.groupby([
        'experiment_setup_name',
        'user_id',
        'context_name',
        'term_type',
    ]).cumcount()
    answers = answers.sort_values(by=['attempt', 'id'])
    answers['serie'] = answers['attempt'].apply(lambda a: a // 10)

    def _apply_serie_stats(group):
        return pandas.DataFrame([{
            'real_error_rate': int(round(100 * (group['item_asked_id'] != group['item_answered_id']).mean())),
            'target_error_rate': int(group['error_rate'].mean()),
            'valid': len(group) == 10,
        }])
    data = answers.groupby(['experiment_setup_name', 'user_id', 'practice_set_id', 'context_name', 'term_type']).apply(_apply_serie_stats).reset_index()
    data = data[data['valid']]
    data.drop('valid', 1)

    def _apply_serie_next(group):
        group['next_target_error_rate'] = group['target_error_rate'].shift(-1)
        return group
    data = data.groupby(['experiment_setup_name', 'user_id', 'context_name', 'term_type']).apply(_apply_serie_next).reset_index()
    return data.drop('level_5', 1)


def plot_choice_by_success():
    data = load_choice_by_success()
    data['choice'] = (data['next_target_error_rate'] - data['target_error_rate'])
    data[data['experiment_setup_name'] == 'adjustment']
    data = data[~data['choice'].isnull()].sort_values(by=['choice'])
    data = data[data['choice'].isin({-20, -10, 0, 10, 20})]
    mapping = {
        -20: '- 20',
        -10: '- 10',
        0: '-',
        10: '+ 10',
        20: '+ 20',
    }
    data['choice'] = data['choice'].apply(lambda c: mapping[c])
    data['changed'] = data['target_error_rate'] != data['next_target_error_rate']

    def _apply(group):
        result = []
        for choice in group['choice'].unique():
            mean = binomial_confidence_mean(group['choice'] == choice)
            result.append({
                'choice': choice,
                'learners': 100 * mean[0],
                'learners_min': 100 * mean[1][0],
                'learners_max': 100 * mean[1][1],
            })
        return pandas.DataFrame(result)
    to_plot = data.groupby(['real_error_rate']).apply(_apply).reset_index()
    print(to_plot)
    # to_plot = to_plot[to_plot['choice'] != 0]
    rcParams['figure.figsize'] = 9, 5
    plt.ylim(0, 20)
    # plt.ylim(0, 100)
    for i, (choice, choice_data) in enumerate(to_plot.groupby('choice')):
        plt.plot(
            choice_data['real_error_rate'],
            choice_data['learners'],
            label=choice,
            color=output.palette()[i],
            marker='.',
            markersize=20
        )
        plt.fill_between(
            choice_data['real_error_rate'],
            choice_data['learners_min'],
            choice_data['learners_max'],
            color=output.palette()[i], alpha=0.35
        )
    plt.legend(ncol=5, loc='upper left', frameon=True)
    plt.ylabel('Choice (%)')
    plt.xlabel('Real error rate')
    plt.twinx()
    size = data.groupby('real_error_rate').apply(len).reset_index().rename(columns={0: 'size'})
    plt.plot(size['real_error_rate'], size['size'], '.-', color='gray')
    plt.ylabel('Data size')
    output.savefig('choice_by_success', tight_layout=False)


def plot_conf_difficulty_by_attempt(length, filter_passive_users):
    data = load_conf_difficulty_by_attempt(filter_passive_users=filter_passive_users)
    data = data[(data['attempt'] < length)]
    cols = len(data['experiment_setup_name'].unique())
    rcParams['figure.figsize'] = cols * 5, int(4 * length / 50)
    # vmax = data[data['error_rate'] != 35]['value'].max()
    vmax = data['value'].max()
    for j, (setup, setup_data) in enumerate(data.groupby('experiment_setup_name')):
        for e in numpy.arange(0, 101, 5):
            if e not in setup_data['error_rate'].unique():
                for attempt in range(0, int(length)):
                    setup_data = setup_data.append(pandas.DataFrame([{'attempt': attempt, 'error_rate': e, 'value': 0}]))
        plt.subplot(1, cols, j + 1)
        to_plot = setup_data.pivot_table(columns='error_rate', index='attempt', values='value', dropna=False, fill_value=0)
        plt.title(setup)
        sns.heatmap(to_plot, annot=False, cbar=False, linewidths=.01, vmin=0, vmax=vmax)
        plt.xticks(plt.xticks()[0][::2], [int(float(lab.get_text())) for lab in plt.xticks()[1][::2]])
        if j != 0:
            plt.gca().axes.get_yaxis().set_ticks([])
            plt.ylabel('')
        else:
            pos = plt.yticks()[0]
            lab = plt.yticks()[1]
            plt.yticks([pos[0], pos[-1]], [int(lab[0].get_text()) + 1, int(lab[-1].get_text()) + 1])
    output.savefig('conf_difficulty_by_attempt')


def execute(length=50):
    plot_conf_difficulty_by_attempt(length, filter_passive_users=False)
    plot_choice_by_success()
