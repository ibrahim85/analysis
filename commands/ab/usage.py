from . raw import load_answers
from spiderpig import spiderpig
import matplotlib.pyplot as plt
import output
import seaborn as sns


@spiderpig()
def context_usage():
    answers = load_answers()
    data = answers.groupby(['context_name', 'term_type']).apply(lambda g: round(len(g) * 100.0 / len(answers))).reset_index().rename(columns={0: 'usage'}).sort_values(by='usage', ascending=False)
    data['context_name'] = data['context_name'].apply(lambda c: c.replace('Czech Rep.', 'CZ').replace('United States', 'US').replace('region_cz', 'region'))
    return data


def plot_context_usage(n):
    data = context_usage().head(n)
    data['group'] = data.apply(lambda r: '{}, {}'.format(r['context_name'], r['term_type']), axis=1)
    g = sns.barplot(x='group', y='usage', data=data, color=output.palette()[0])
    g.set_xticklabels(g.get_xticklabels(), rotation=60)
    g.yaxis.grid(True)
    plt.xlabel('')
    plt.ylabel('Number of answers (%)')
    output.savefig('usage')


def execute(n=10):
    plot_context_usage(n)
