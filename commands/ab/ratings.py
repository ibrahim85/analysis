from .raw import load_answers, load_school_usage, load_ratings, load_ratings_with_contexts
from metric import binomial_confidence_mean
import matplotlib.pyplot as plt
import output
import pandas
import seaborn as sns
from spiderpig import spiderpig


MAPPING = {
    4: 2,
    5: 1,
    6: 0,
    7: -1,
    8: -2,
}


@spiderpig()
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
        data = {}
        for label in setup_ratings['label'].unique():
            data[label] = binomial_confidence_mean(setup_ratings['label'] == label)
        for category, category_data in data.items():
            result.append({
                'setup': setup_name,
                'value'.format(category): category_data[0],
                'confidence_min'.format(category): category_data[1][0],
                'confidence_max'.format(category): category_data[1][1],
                'category': category,
                'total': len(setup_ratings),
            })

    return pandas.DataFrame(result)


def plot_ratings_per_setup(in_school=None, with_confidence=True):
    data = ratings_per_setup(in_school=in_school)
    g = sns.barplot(x='setup', y='value', hue='category', data=data, hue_order=sorted(data['category'].unique()))
    g.set_xticklabels(g.get_xticklabels(), rotation=30)
    g.get_legend().set_title(None)
    g.get_legend().set_frame_on(True)

    g.yaxis.grid(True)
    plt.xlabel('AB group')
    plt.ylabel('')
    plt.ylim(0, 1)


def plot_ratings(with_confidence):
    plot_ratings_per_setup()
    output.savefig('ratings_per_setup')


def plot_number_of_user_ratings_per_context():
    nums = load_ratings_with_contexts().groupby(['user', 'context_name', 'term_type']).apply(len).reset_index().rename(columns={0: 'num'}).groupby('num').apply(len).reset_index().rename(columns={0: 'count'})
    nums = nums.head(n=20)
    sns.barplot(x='num', y='count', data=nums, color=output.palette()[0])
    plt.ylabel('Number of users')
    plt.xlabel('Number of ratings per context')
    output.savefig('number_of_ratings')


def plot_avg_user_ratings_per_context():
    data = load_ratings_with_contexts()
    data['value'] = data['value'].apply(lambda x: MAPPING[int(x)])
    to_plot = data.groupby(['user', 'context_name', 'term_type']).apply(lambda g: g['value'].mean())
    sns.distplot(to_plot, bins=20, kde=False)
    output.savefig('average_rating')


def execute(with_confidence=True):
    plot_ratings(with_confidence)
    plot_number_of_user_ratings_per_context()
    plot_avg_user_ratings_per_context()
