from .raw import load_answers, load_school_usage, load_ratings
from metric import binomial_confidence_mean
import matplotlib.pyplot as plt
import output
import pandas


def ratings_per_setup(in_school=None):
    ratings = load_ratings().sort_values(by=['inserted']).drop_duplicates(['user_id'])
    answers = load_answers()
    if in_school is not None:
        school_usage = load_school_usage()
        if in_school:
            valid_users = school_usage[school_usage].reset_index()['user_id']
        else:
            valid_users = school_usage[~school_usage].reset_index()['user_id']
        ratings = ratings[ratings['user_id'].isin(valid_users)]
    result = []

    for setup_name, setup_data in answers.groupby('experiment_setup_name'):
        setup_users = setup_data['user_id'].unique()
        setup_ratings = ratings[ratings['user_id'].isin(setup_users)]
        easy = binomial_confidence_mean(setup_ratings['value'] == 1)
        appropriate = binomial_confidence_mean(setup_ratings['value'] == 2)
        difficult = binomial_confidence_mean(setup_ratings['value'] == 3)
        result.append({
            'setup': setup_name,
            'easy_value': easy[0],
            'easy_confidence_min': easy[1][0],
            'easy_confidence_max': easy[1][1],
            'appropriate_value': appropriate[0],
            'appropriate_confidence_min': appropriate[1][0],
            'appropriate_confidence_max': appropriate[1][1],
            'difficult_value': difficult[0],
            'difficult_confidence_min': difficult[1][0],
            'difficult_confidence_max': difficult[1][1],
            'total': len(setup_ratings),
        })

    return pandas.DataFrame(result)


def plot_ratings_per_setup(in_school=None, legend=True, with_confidence=True):
    data = ratings_per_setup(in_school=in_school)
    for i, (r_type, marker) in enumerate(zip(['easy', 'appropriate', 'difficult'], ['o', 's', '^'])):
        plt.plot(data['setup'], data['{}_value'.format(r_type)], label=r_type, color=output.palette()[i], marker=marker)
        if with_confidence:
            plt.fill_between(
                data['setup'],
                data['{}_confidence_min'.format(r_type)],
                data['{}_confidence_max'.format(r_type)],
                color=output.palette()[i], alpha=0.35
            )
    if legend:
        plt.legend(loc=1)
    plt.xlabel('Target error rate')
    plt.ylim(0, 1)


def plot_ratings(with_confidence):
    plot_ratings_per_setup()
    output.savefig('ratings_per_setup')


def execute(with_confidence=True):
    plot_ratings(with_confidence)
