from .raw import load_answers, load_ratings_with_contexts
from .learning_by_ratings import get_ratings_group, MAPPING
from metric import binomial_confidence_mean, confidence_value_to_json
from spiderpig import spiderpig
import matplotlib.pyplot as plt
import output
import numpy
import pandas


@spiderpig()
def load_user_answers():
    answers = load_answers()
    ratings = load_ratings_with_contexts()
    ratings['value'] = ratings['value'].apply(lambda x: MAPPING[int(x)])
    ratings = ratings.groupby(['user', 'context_name', 'term_type']).apply(lambda g: get_ratings_group(g['value'].values)).reset_index().rename(columns={0: 'ratings_group', 'user': 'user_id'})
    answers = pandas.merge(answers, ratings, on=['user_id', 'context_name', 'term_type'], how='left')
    answers['ratings_group'].fillna('unknown', inplace=True)
    data = answers.groupby(['ratings_group', 'experiment_setup_name', 'user_id']).apply(len).reset_index()
    return data.rename(columns={0: 'answers'})


def survival_curve(length):
    user_answers = load_user_answers()

    def _progress_confidence(i, data):
        xs = [x > i for x in data]
        return confidence_value_to_json(binomial_confidence_mean(xs), use_format_number=False)
    result = []
    for (setup, ratings), d in user_answers.groupby(['experiment_setup_name', 'ratings_group']):
        for i in range(length):
            progress = _progress_confidence(i, d['answers'])
            result.append({
                'experiment_setup_name': setup,
                'attempt': i + 1,
                'ratings_group': ratings,
                'value': 100 * progress['value'],
                'confidence_min': 100 * progress['confidence_interval']['min'],
                'confidence_max': 100 * progress['confidence_interval']['max'],
                'datapoints': len(d),
            })
    return pandas.DataFrame(result)


def plot_survival_curve(length, with_confidence, legend=False):
    data = survival_curve(length)
    data.sort_values(by=['experiment_setup_name', 'ratings_group'], inplace=True)
    users = data.groupby(['ratings_group']).apply(lambda g: 100 * g['datapoints'].sum() / data['datapoints'].sum()).to_dict()
    for i, (setup_name, to_plot) in enumerate(data[data['attempt'] == length].groupby('experiment_setup_name')):
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
            to_plot['ratings_group'].apply(lambda g: '{0}\n{1:.1f}%'.format(g, users[g]))
        )
    plt.yticks(
        numpy.linspace(min(plt.yticks()[0]), max(plt.yticks()[0]), 25),
        [plt.yticks()[0][0]] + [''] * 23 + [plt.yticks()[0][-1]]
    )
    plt.gca().yaxis.grid(True)
    plt.legend(loc=0, frameon=True, fontsize='x-small')
    plt.title('Survival per context (at least {} answers)'.format(length))
    plt.ylabel('Learners (%)')


def execute(length=60, with_confidence=False):
    plot_survival_curve(length, with_confidence)
    output.savefig(filename='survival_by_ratings')
