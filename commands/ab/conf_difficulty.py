from .raw import load_conf_difficulty_by_attempt, load_ratings_with_contexts, load_school_usage
from metric import binomial_confidence_mean
from pylab import rcParams
import matplotlib.pyplot as plt
import numpy
import output
import pandas
import seaborn as sns


def plot_label_by_success(setup_name, school, context_name=None, term_type=None, legend=True, linetype='-', show_data_size=True, set_order=None):
    data = load_ratings_with_contexts()
    if set_order is not None:
        data = data[data['practice_set_order'] == set_order]
    data = data[(data['experiment_setup_name'] == setup_name)]
    if context_name is not None:
        data = data[data['context_name'] == context_name]
    if term_type is not None:
        data = data[data['term_type'] == term_type]
    if school is not None:
        school_usage = load_school_usage().reset_index().rename(columns={'ip_address': 'school', 'user_id': 'user'})
        data = pandas.merge(data, school_usage, on='user', how='inner')
        data = data[data['school'] == school]
    data = data[data['error_rate'].apply(lambda x: x % 10 == 0)]

    def _apply(group):
        result = []
        for label in group['label'].unique():
            mean = binomial_confidence_mean(group['label'] == label)
            result.append({
                'label': label,
                'learners': 100 * mean[0],
                'learners_min': 100 * mean[1][0],
                'learners_max': 100 * mean[1][1],
            })
        return pandas.DataFrame(result)
    to_plot = data.groupby(['experiment_setup_name', 'error_rate']).apply(_apply).reset_index().sort_values(by=['label', 'error_rate'])
    for i, (label, label_data) in enumerate(to_plot.groupby('label')):
        plt.plot(
            label_data['error_rate'],
            label_data['learners'],
            linetype,
            label=label.split('-')[-1],
            color=output.palette()[i],
            marker='.',
            markersize=20
        )
        plt.fill_between(
            label_data['error_rate'],
            label_data['learners_min'],
            label_data['learners_max'],
            color=output.palette()[i], alpha=0.35
        )
    if legend:
        plt.legend(ncol=3, loc='upper left', frameon=True)
    plt.ylabel('Label (%)')
    plt.xlabel('Real error rate')
    plt.gca().xaxis.grid(True)
    plt.gca().yaxis.grid(True)
    if show_data_size:
        plt.twinx()
        size = data.groupby('error_rate').apply(len).reset_index().rename(columns={0: 'size'})
        plt.plot(size['error_rate'], size['size'], '.-', color='gray')
        plt.ylabel('Data size')
    plt.ylim(0, 70)


def plot_conf_difficulty_by_attempt(length, filter_passive_users):
    data = load_conf_difficulty_by_attempt(filter_passive_users=filter_passive_users)
    data = data[(data['attempt'] < length)]
    cols = len(data['experiment_setup_name'].unique())
    rcParams['figure.figsize'] = cols * 5, int(4 * length / 50)
    vmax = data[data['error_rate'] != 35]['value'].max()
    for j, (setup, setup_data) in enumerate(data.groupby('experiment_setup_name')):
        for e in numpy.arange(0, 101, 5):
            if e not in setup_data['error_rate'].unique():
                for attempt in range(0, int(length)):
                    setup_data = setup_data.append(pandas.DataFrame([{'attempt': attempt, 'error_rate': e, 'value': 0}]))
        plt.subplot(1, cols, j + 1)
        to_plot = setup_data.pivot_table(columns='error_rate', index='attempt', values='value', dropna=False, fill_value=0)
        plt.title(setup)
        sns.heatmap(to_plot, annot=False, cbar=False, linewidths=.01, vmin=0, vmax=vmax)
        plt.xticks(plt.xticks()[0][::2], [int(float(lab.get_text())) for lab in plt.xticks()[1][::2]])
        if j != 0:
            plt.gca().axes.get_yaxis().set_ticks([])
            plt.ylabel('')
        else:
            pos = plt.yticks()[0]
            lab = plt.yticks()[1]
            plt.yticks([pos[0], pos[-1]], [int(lab[0].get_text()) + 1, int(lab[-1].get_text()) + 1])
    output.savefig('conf_difficulty_by_attempt')


def execute(length=50, school_diff=False, context_diff=False):
    if school_diff:
        rcParams['figure.figsize'] = 15, 7
        for school in [True, False]:
            plt.title('in-school' if school else 'out-of-school')
            for setup_name, linetype in zip(['placebo', 'adjustment'], ['-', '--']):
                plot_label_by_success(setup_name, school, legend=setup_name == 'placebo', linetype=linetype, show_data_size=False)
            output.savefig('label_by_success_{}'.format('in_school' if school else 'out_of_school'), tight_layout=False)
    elif context_diff:
        rcParams['figure.figsize'] = 24, 35
        data = load_ratings_with_contexts()
        top_contexts = [(c, t) for (c, t), _ in list(sorted(data.groupby(['context_name', 'term_type']).apply(len).to_dict().items(), key=lambda x: -x[1]))[:10]]
        for i, (context_name, term_type) in enumerate(top_contexts):
            plt.subplot(5, 2, i + 1)
            plt.title('{}, {}'.format(context_name, term_type))
            for col, (setup_name, linetype) in enumerate(zip(['placebo', 'adjustment'], ['-', '--'])):
                plot_label_by_success(setup_name, None, context_name=context_name, term_type=term_type, legend=(i == 0 and linetype == '-'), show_data_size=False, linetype=linetype)
                plt.ylim(0, plt.ylim()[1])
        output.savefig('label_by_success', tight_layout=False)
    else:
        rcParams['figure.figsize'] = 8.5, 4
        for col, (setup_name, linetype) in enumerate(zip(['placebo', 'adjustment'], ['-', '--'])):
            plot_label_by_success(setup_name, None, legend=(col == 0), show_data_size=False, linetype=linetype)
        output.savefig('label_by_success', tight_layout=False)
    # plot_conf_difficulty_by_attempt(length, filter_passive_users=False)
