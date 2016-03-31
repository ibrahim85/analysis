from .raw import load_answers, load_success
import matplotlib.pyplot as plt
import numpy
import output
import pandas
import seaborn as sns


def _histogram(xs, bins=10):
    hist, bins = numpy.histogram(xs, bins=bins)
    return {
        'hist': list(hist),
        'bins': list(bins),
    }


def error_rate_histogram():
    answers = load_answers()
    success = load_success().reset_index()
    result = []
    for setup, data in answers.groupby('experiment_setup_name'):
        users = data['user_id'].unique()
        setup_success = success[success['user_id'].isin(users)]
        hist = _histogram(setup_success[0], bins=numpy.arange(0, 1.1, step=0.1))
        for b, v in zip(hist['bins'], hist['hist']):
            result.append({
                'setup': setup,
                'value': v,
                'bin_min': numpy.round(b, 1),
                'bin_max': numpy.round(b + 0.1, 1),
            })
    return pandas.DataFrame(result)


def plot_error_rate_histogram():
    g = sns.barplot(x='bin_min', y='value', hue='setup', data=error_rate_histogram())
    g.get_legend().set_title(None)
    g.get_legend().set_frame_on(True)
    g.yaxis.grid(True)
    plt.xlabel('Success')
    plt.ylabel('Number of learners')
    output.savefig('success_per_setup')


def execute():
    plot_error_rate_histogram()
    pass
