from .raw import load_ratings_with_contexts, load_school_usage
import output
import seaborn as sns
import pandas
from pylab import rcParams
import matplotlib.pyplot as plt
from spiderpig import spiderpig


MAPPING = {
    4: 2,
    5: 1,
    6: 0,
    7: -1,
    8: -2,
}


# @spiderpig()
def load_data(n=12, length=12):
    school_usage = load_school_usage().reset_index().rename(columns={'ip_address': 'school', 'user_id': 'user'})
    data = load_ratings_with_contexts().sort_values(by='time')
    data = pandas.merge(data, school_usage, on='user', how='inner')
    data['context'] = data.apply(lambda g: '{}, {}'.format(g['context_name'].replace('Czech Rep.', 'CZ').replace('United States', 'US'), g['term_type'].replace('region_cz', 'region')), axis=1)
    data['value'] = data['value'].apply(lambda x: MAPPING[int(x)])
    data['order'] = data.groupby(['context', 'user']).cumcount()
    contexts = set(data[data['order'] == 0].groupby(['context']).apply(len).reset_index().sort_values(by=0, ascending=False)['context'].values[:n])
    from_schools = data.groupby(['context']).apply(lambda g: int(round(100 * g['school'].mean()))).to_dict()
    data = data[data['context'].isin(contexts)]
    data['context'] = data['context'].apply(lambda c: '{} ({}%)'.format(c, from_schools[c]))
    return data[data['order'] < length]


def plot_average_difficulty_by_attempt(n=12, length=10):
    rcParams['figure.figsize'] = 15, 10
    data = load_data(n, length)
    data = data.groupby(['context', 'order', 'school']).apply(lambda g: g['value'].mean()).reset_index().rename(columns={0: 'value'})
    g = sns.FacetGrid(data, col="context", col_wrap=4, hue='school', aspect=1.5)
    bp = g.map(plt.plot, 'order', 'value').set_titles('{col_name}')
    for ax in bp.axes:
        ax.yaxis.grid(True)
    g.add_legend()

    output.savefig('average_ratings_by_attempt', tight_layout=False)


def execute():
    plot_average_difficulty_by_attempt()
