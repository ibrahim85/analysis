from .raw import load_success, load_school_usage, load_ratings
from pylab import rcParams
from spiderpig import spiderpig
from metric import binomial_confidence_mean
import matplotlib.pyplot as plt
import output
import pandas


@spiderpig()
def ratings_per_success(user_limit=50, in_school=None):
    ratings = load_ratings().sort_values(by=['inserted']).drop_duplicates(['user_id'])
    if in_school is not None:
        school_usage = load_school_usage()
        if in_school:
            valid_users = school_usage[school_usage].reset_index()['user_id']
        else:
            valid_users = school_usage[~school_usage].reset_index()['user_id']
        ratings = ratings[ratings['user_id'].isin(valid_users)]

    success = load_success(first=30, round_base=5)
    result = []

    for group_success, group_data in success.reset_index().groupby(0):
        group_ratings = ratings[ratings['user_id'].isin(group_data['user_id'])]
        if len(group_ratings) < user_limit:
            continue
        easy = binomial_confidence_mean(group_ratings['value'] == 1)
        appropriate = binomial_confidence_mean(group_ratings['value'] == 2)
        difficult = binomial_confidence_mean(group_ratings['value'] == 3)
        result.append({
            'success': group_success,
            'easy_value': easy[0],
            'easy_confidence_min': easy[1][0],
            'easy_confidence_max': easy[1][1],
            'appropriate_value': appropriate[0],
            'appropriate_confidence_min': appropriate[1][0],
            'appropriate_confidence_max': appropriate[1][1],
            'difficult_value': difficult[0],
            'difficult_confidence_min': difficult[1][0],
            'difficult_confidence_max': difficult[1][1],
            'total': len(group_ratings),
        })

    return pandas.DataFrame(result)


def plot_ratings_per_success(user_limit, in_school=None, legend=True, with_confidence=True):
    data = ratings_per_success(user_limit=user_limit, in_school=in_school)
    for i, (r_type, marker) in enumerate(zip(['easy', 'appropriate', 'difficult'], ['o', 's', '^'])):
        plt.plot(data['success'], data['{}_value'.format(r_type)], label=r_type, color=output.palette()[i], marker=marker)
        if with_confidence:
            plt.fill_between(
                data['success'],
                data['{}_confidence_min'.format(r_type)],
                data['{}_confidence_max'.format(r_type)],
                color=output.palette()[i], alpha=0.35
            )
    if legend:
        plt.legend(loc=1)
    plt.xlabel('Success rate')
    plt.ylim(0, 1)


def plot_ratings(user_limit, with_confidence):
    plot_ratings_per_success(user_limit, with_confidence=with_confidence)
    output.savefig('ratings_per_success')
    rcParams['figure.figsize'] = 15, 5
    plt.subplot(121)
    plt.title('in-school users')
    plot_ratings_per_success(user_limit, in_school=True, with_confidence=with_confidence)
    plt.xlim(0.5, 1)
    plt.subplot(122)
    plt.title('out-of-school users')
    plot_ratings_per_success(user_limit, in_school=False, with_confidence=with_confidence, legend=False)
    plt.xlim(0.5, 1)
    output.savefig('ratings_per_success_school_usage')


def execute(user_limit=50, with_confidence=True):
    plot_ratings(user_limit, with_confidence)
