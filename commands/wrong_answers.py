from collections import defaultdict
from pylab import rcParams
from spiderpig import spiderpig
import format
import math
import matplotlib.pyplot as plt
import output
import raw
import seaborn as sns


@spiderpig()
def get_answer_frequency():
    data = raw.load_and_merge()
    data = data[data['guess'] == 0]
    cols = [col for col in data.columns if 'asked' in col or 'answered' in col]
    result = data.groupby(cols).apply(len).reset_index().rename(columns={0: 'answer_frequency'})
    return result


@spiderpig()
def get_context_answers():
    data = raw.load_and_merge().groupby(['context_name_asked', 'term_type_asked']).apply(len).reset_index().rename(columns={0: 'count'})

    def _format(row):
        return format.context(row['context_name_asked'], row['term_type_asked'])
    data['group_name'] = data.apply(_format, axis=1)
    return data[['group_name', 'count']].set_index('group_name')


@spiderpig()
def prepare_answer_frequency_all():
    data_all = get_answer_frequency().sort_values(by='answer_frequency', ascending=False)

    def _apply(data):
        data = data[['context_name_asked', 'term_type_asked', 'term_name_asked', 'term_name_answered', 'answer_frequency']]
        total = data['answer_frequency'].sum()
        data['answer_frequency'] = data['answer_frequency'].apply(lambda x: x / total)
        return data

    to_plot = data_all.groupby(['context_name_asked', 'term_type_asked', 'term_name_asked']).apply(_apply)

    def _format(row):
        return format.context(row['context_name_asked'], row['term_type_asked'])
    to_plot['group_name'] = to_plot.apply(_format, axis=1)
    return to_plot[['group_name', 'answer_frequency', 'term_name_asked', 'term_name_answered']]


def plot_answer_frequency_all(wrong_only=True, contexts=20, show_names=False, normalize=True, top=5):
    plot_cols = 4 if contexts >= 20 else 2
    plot_rows = math.ceil(contexts / plot_cols)
    context_answers = get_context_answers()['count'].to_dict()
    data_all = prepare_answer_frequency_all()
    plot_contexts = sorted(data_all['group_name'].unique(), key=lambda c: -context_answers[c])[:contexts]
    data_all = data_all[data_all['group_name'].isin(plot_contexts)]
    if wrong_only:
        data_all = data_all[data_all['term_name_asked'] != data_all['term_name_answered']]
    if normalize:
        def _normalize(group):
            group['answer_frequency'] = group['answer_frequency'] / group['answer_frequency'].sum()
            return group
        data_all = data_all.groupby(['group_name', 'term_name_asked']).apply(_normalize)
    rcParams['figure.figsize'] = 7.5 * plot_cols, 5 * plot_rows
    for i, (group_name, data) in enumerate(data_all.groupby('group_name')):
        plt.subplot(plot_rows, plot_cols, i + 1)
        to_plot = defaultdict(list)
        for term, term_data in data.groupby('term_name_asked'):
            to_plot[term] = list(term_data['answer_frequency'].head(top).cumsum().sort_values(ascending=False, inplace=False))
        terms, terms_data = zip(*sorted(to_plot.items(), key=lambda x: x[1][-1], reverse=True))
        plt.title(group_name[:30])
        for i in range(top):
            sns.barplot(list(range(len(terms))), list(map(lambda x: ([0] * (top - len(x)) + x)[i], terms_data)), color=output.palette()[i])
        plt.xticks(plt.xticks()[0], terms, rotation=90)
    output.savefig(filename='answer_frequencies_all')


def execute(wrong_only=True, contexts=20, show_names=False):
    plot_answer_frequency_all(wrong_only=wrong_only, contexts=contexts, show_names=show_names)
