from commands.ab.quit_score import plot_quit_score, load_quit_score
from commands.ab.raw import load_answers, load_reference_answers
from commands.ab.summary import learning_curve
from commands.ab.survival import survival_curve
from commands.ab.survival_time import survival_curve as survival_curve_time
from pylab import rcParams
from scipy import stats
from spiderpig import execution_context, spiderpig
import main
import matplotlib.pyplot as plt
import os
import output
import pandas
import seaborn as sns


def get_top_contexts(n=10):
    result = []
    for context_name, term_type in load_answers().groupby(['term_type', 'context_name']).apply(len).reset_index().sort_values(by=0, ascending=False)[['context_name', 'term_type']].head(n).values:
        result.append('{}:{}'.format(context_name, term_type))
    return result


@spiderpig()
def load_data_to_correlate():
    result = None
    for i, data_dir in enumerate(['slepemapy-ab-random-random', 'slepemapy-ab-target-difficulty', 'slepemapy-ab-max-options-count', 'slepemapy-ab-distractors']):
        execution_context().add_global_kwargs(data_dir=os.path.join(main.BASE_DIR, data_dir))
        execution_context().add_global_kwargs(contexts=[])
        for context in get_top_contexts():
            first_ref = load_reference_answers().drop_duplicates(['user_id'])
            first_avg = (first_ref['item_asked_id'] == first_ref['item_answered_id']).mean()
            execution_context().add_global_kwargs(contexts=[context])
            quit_score = load_quit_score().rename(columns={'score': 'quit_score'})
            quit_score = quit_score.groupby(['experiment_setup_name'])['quit_score'].mean().reset_index()
            quit_score['quit_score'] = quit_score['quit_score'] - first_avg
            survival_answers = survival_curve(100)
            survival_answers_data = []
            for cond, cond_data in survival_answers.items():
                survival_answers_data.append({
                    'experiment_setup_name': cond,
                    'survival_answers_10': cond_data[9]['value'],
                    'survival_answers_100': cond_data[99]['value'],
                })
            survival_answers_data = pandas.DataFrame(survival_answers_data)
            survival_time = survival_curve_time(600)
            survival_time_data = []
            for cond, cond_data in survival_time.items():
                survival_time_data.append({
                    'experiment_setup_name': cond,
                    'survival_time_60': cond_data[59]['value'],
                    'survival_time_600': cond_data[599]['value'],
                })
            survival_time_data = pandas.DataFrame(survival_time_data)
            data_dir_result = pandas.merge(quit_score, survival_answers_data, on=['experiment_setup_name'], how='inner')
            data_dir_result = pandas.merge(data_dir_result, survival_time_data, on=['experiment_setup_name'], how='inner')
            for length in [5, 10]:
                learn_data = learning_curve(length)
                slope = learn_data[(learn_data['variable'] == 'slope') & ~learn_data['balanced']]
                slope['learning_slope_{}'.format(length)] = slope['value']
                data_dir_result = pandas.merge(data_dir_result, slope[['experiment_setup_name', 'learning_slope_{}'.format(length)]], on=['experiment_setup_name'])
            data_dir_result['experiment'] = data_dir_result['experiment_setup_name'].apply(lambda x: data_dir)
            data_dir_result['context'] = data_dir_result['experiment_setup_name'].apply(lambda x: context)
            if result is None:
                result = data_dir_result
            else:
                result = result.append(data_dir_result)
    return result


def plot_metrics_correlation():
    data = load_data_to_correlate().rename(columns={
        'quit_score': 'quit score',
        'survival_answers_10': 'survival (10 ans.)',
        'survival_answers_100': 'survival (100 ans.)',
        'survival_time_60': 'survival (1 min.)',
        'survival_time_600': 'survival (10 min.)',
        'learning_slope_5': 'learning (5)',
        'learning_slope_10': 'learning (10)',
        'learning_slope_20': 'learning (20)',
    })
    data = data[~data['context'].apply(lambda c: 'region_cz' in c)]
    plt.title('Correlation of different metrics')
    sns.heatmap(data.corr().abs(), annot=True, fmt='.2f')
    output.savefig('abexp_metric_corr')
    g = sns.PairGrid(
        data[[
            # 'quit score',
            'survival (100 ans.)',
            'survival (10 min.)',
            'survival (10 ans.)',
            'survival (1 min.)',
            # 'learning (10)',
            'experiment',
        ]], hue='experiment')
    g = g.map_diag(plt.hist)
    g = g.map_offdiag(plt.scatter)
    g = g.add_legend()
    output.savefig('abexp_metrics', tight_layout=False)


def plot_comparison(a, b):
    data = load_data_to_correlate()
    print(data[['experiment_setup_name', 'context', 'quit_score']].sort_values(by='quit_score', ascending=False))
    rcParams['figure.figsize'] = 15, 15
    plt.scatter(data[a], data[b], color=output.palette()[0])
    weired = data['context'].apply(lambda c: 'region_cz' in c)
    filtered = data[weired]
    plt.scatter(filtered[a], filtered[b], color='red')
    for n, ax, bx, c in data[['experiment_setup_name', a, b, 'context']].values:
        plt.annotate('{}:{}'.format(n, c), (ax, bx), fontsize=6)
    plt.xlabel(a)
    plt.ylabel(b)
    print(data[~weired][['experiment_setup_name', a, b, 'context']].corr())
    output.savefig('abexp_compare_{}_{}'.format(a, b))


def plot_quit_score_summary():
    rcParams['figure.figsize'] = 9, 6
    LABELS = {
        'slepemapy-ab-random-random': 'Adaptive vs. Random',
        'slepemapy-ab-target-difficulty': 'Question Difficulty',
        'slepemapy-ab-max-options-count': 'Number of Options',
    }
    for i, data_dir in enumerate(['slepemapy-ab-random-random', 'slepemapy-ab-target-difficulty', 'slepemapy-ab-max-options-count']):
        execution_context().add_global_kwargs(data_dir=os.path.join(main.BASE_DIR, data_dir))
        ax = plt.subplot(1, 3, i + 1)
        plot_quit_score()
        if i != 0:
            ax.get_yaxis().get_label().set_visible(False)
        plt.title(LABELS[data_dir])
    output.savefig('abexp_quit_score')


def reset_kwargs():
    execution_context().add_global_kwargs(data_dir='dummy')
    execution_context().add_global_kwargs(contexts=[])


def execute():
    reset_kwargs()
    plot_quit_score_summary()
    reset_kwargs()
    plot_metrics_correlation()
    reset_kwargs()
    plot_comparison('quit_score', 'survival_answers_100')
