from .raw import load_success, load_school_usage, load_ratings
from pylab import rcParams
from spiderpig import spiderpig
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
        easy = group_ratings[group_ratings['value'] == 1]
        appropriate = group_ratings[group_ratings['value'] == 2]
        difficult = group_ratings[group_ratings['value'] == 3]
        result.append({
            'success': group_success,
            'easy': len(easy) / float(len(group_ratings)),
            'appropriate': len(appropriate) / float(len(group_ratings)),
            'difficult': len(difficult) / float(len(group_ratings)),
            'total': len(group_ratings),
        })

    return pandas.DataFrame(result)


def plot_ratings_per_success(user_limit, in_school=None, legend=True):
    data = ratings_per_success(user_limit=user_limit, in_school=in_school)
    plt.plot(data['success'], data['easy'], label='too easy')
    plt.plot(data['success'], data['appropriate'], label='appropriate')
    plt.plot(data['success'], data['difficult'], label='too difficult')
    if legend:
        plt.legend(loc=1)
    plt.xlabel('Success rate')
    plt.ylim(0, 1)


def plot_ratings(user_limit):
    plot_ratings_per_success(user_limit)
    output.savefig(filename='ratings_per_success')
    rcParams['figure.figsize'] = 15, 5
    plt.subplot(121)
    plt.title('in-school users')
    plot_ratings_per_success(user_limit, in_school=True)
    plt.xlim(0.5, 1)
    plt.subplot(122)
    plt.title('out-of-school users')
    plot_ratings_per_success(user_limit, in_school=False)
    plt.xlim(0.5, 1)
    output.savefig(filename='ratings_per_success_school_usage')


def execute(user_limit=50):
    plot_ratings(user_limit)
