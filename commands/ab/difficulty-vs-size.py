from .raw import load_context_difficulty, load_context_size, load_answers
from pylab import rcParams
from spiderpig import spiderpig
import math
import matplotlib.pyplot as plt
import output
import pandas


@spiderpig()
def load_contexts():
    answers = load_answers().groupby(['context_name', 'term_type']).apply(len).reset_index().rename(columns={0: 'context_answers'})
    return pandas.merge(pandas.merge(load_context_size(), load_context_difficulty(), on=['term_type', 'context_name'], how='inner'), answers, on=['term_type', 'context_name'], how='inner')


def plot_scatter(ylim, n):
    rcParams['figure.figsize'] = 5.5, 5.5
    contexts = load_contexts().sort_values(by='context_answers', ascending=False).head(n)
    contexts['context_answers'] = contexts['context_answers'].apply(lambda a: a / contexts['context_answers'].sum())
    print(contexts)
    for i, (context_name, term_type, difficulty, size, answers) in enumerate(contexts[['context_name', 'term_type', 'context_difficulty', 'context_size', 'context_answers']].values):
        difficulty = 100 * difficulty
        context_name = context_name.replace('Czech Rep.', 'CZ').replace('United States', 'US')
        term_type = term_type.replace('region_cz', 'region')
        plt.plot(difficulty, size, marker='.', color='white', linewidth=0, alpha=0, label="{}: {}, {}".format((i + 1) if i >= 9 else ('0' + str(i + 1)), context_name, term_type))
        plt.plot(
            difficulty,
            size,
            marker='.',
            markersize=max(300 * math.sqrt(answers), 1),
            color=output.palette()[1],
            alpha=0.5
        )
        plt.text(difficulty, size, i + 1, fontsize='small', horizontalalignment='center',  verticalalignment='center')
    plt.xlabel('Average errror rate on the first question (%)')
    if ylim:
        plt.ylim(0, ylim)
    plt.ylabel('Number of items available in the context')
    plt.legend(loc='center left', fontsize='xx-small', bbox_to_anchor=(0.95, 0.5))


def execute(ylim=None, n=10):
    plot_scatter(ylim, n)
    output.savefig('difficulty_vs_size')
