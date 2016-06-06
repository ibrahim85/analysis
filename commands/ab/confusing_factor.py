from .raw import load_answers, load_options
from collections import defaultdict
from output import savefig
from spiderpig import spiderpig
import matplotlib.pyplot as plt
import pandas
import seaborn as sns


@spiderpig()
def load_confusing_factor():
    all_answers = load_answers()
    items = set(all_answers['item_asked_id'].unique())
    result = []
    for experiment_setup_name, answers in all_answers.groupby('experiment_setup_name'):
        cf = {(x, y): 0 for x in items for y in items if x != y}
        counts = defaultdict(lambda: 0)
        for item_asked, item_answered in answers[(answers['guess'] == 0) & (answers['item_answered_id'].notnull()) & (answers['item_asked_id'] != answers['item_answered_id'])][['item_asked_id', 'item_answered_id']].values:
            if (item_asked, item_answered) not in cf:
                continue
            cf[item_asked, item_answered] += 1
        for (item_asked, item_answered), val in cf.items():
            result.append({
                'item': item_asked,
                'other': item_answered,
                'value': val,
                'experiment_setup_name': experiment_setup_name,
                'size': counts[item_asked, item_answered],
                'size_all': [v for (asked, answered), v in counts.items() if asked == item_asked],
            })
    return pandas.DataFrame(result)


@spiderpig()
def load_distractor_factor():
    all_options = load_options()
    items = set(all_options['item_asked_id'].unique()) | set(all_options['item_answered_id'].unique())
    result = []
    for experiment_setup_name, options in all_options.groupby('experiment_setup_name'):
        df = {(x, y): 0 for x in items for y in items if x != y}
        counts = defaultdict(lambda: 0)
        for item_asked, item_answered, item_option in options[['item_asked_id', 'item_answered_id', 'item_option_id']].values:
            counts[item_asked, item_option] += 1
            if item_answered == item_option and item_asked != item_answered:
                df[item_asked, item_answered] += 1
        for (item_asked, item_answered), val in df.items():
            result.append({
                'item': item_asked,
                'other': item_answered,
                'value': val / counts[item_asked, item_answered] if val > 0 else 0,
                'experiment_setup_name': experiment_setup_name,
                'size': counts[item_asked, item_answered],
                'size_all': [v for (asked, answered), v in counts.items() if asked == item_asked],
            })
    return pandas.DataFrame(result)


@spiderpig()
def data_to_plot():
    answers = load_answers()
    names = dict(answers[['item_asked_id', 'term_name']].drop_duplicates().values)
    cf = load_confusing_factor().rename(columns={'value': 'confusing_factor', 'size': 'cf_size', 'size_all': 'cf_size_all'})
    df = load_distractor_factor().rename(columns={'value': 'distrator_factor', 'size': 'cf_size', 'size_all': 'cf_size_all'})
    data = pandas.merge(cf, df, on=['item', 'other', 'experiment_setup_name'], how='inner')
    print(set(data['item'].unique()) - set(names.keys()))
    data['item_name'] = data['item'].apply(lambda i: names.get(i, 'unknown'))
    data['other_name'] = data['other'].apply(lambda i: names.get(i, 'unknown'))
    return data


@spiderpig(cached=False)
def plot_confusing_factor(contexts):
    if contexts is None or len(contexts) != 1:
        raise Exception('There has to be exactly one context specified.')

    data = data_to_plot()

    def _plot(x, y1, y2, **kwargs):
        plt.plot(list(y1 / max(max(y1), 0.0000001)), label='confusing factor (orig)')
        plt.plot(list(y2 / max(max(y2), 0.0000001)), label='distracting factor')
        plt.xticks(list(range(len(x))), [label[:10] for label in x], rotation=90, size='x-small')

    for experiment_setup_name, group_cf in data.groupby('experiment_setup_name'):
        group_cf = group_cf.sort_values(by=['item_name', 'confusing_factor'], ascending=[True, False])
        grid = sns.FacetGrid(group_cf, col='item_name', col_wrap=5, sharex=False)
        grid.map(_plot, "other_name", "confusing_factor", "distrator_factor").set_titles("{col_name}").set_ylabels('Value').set_xlabels('Distractor')
        grid.set(xlim=(0, 15))
        grid.fig.suptitle(contexts[0])
        savefig('confusing_factor_analysis_{}'.format(experiment_setup_name))
        # break


def execute():
    plot_confusing_factor()
