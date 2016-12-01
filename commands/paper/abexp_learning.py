from commands.ab.data import fit_learning_curve, groupped_reference_series
from commands.ab.raw import load_reference_answers
from commands.ab.learning import plot_global_learning_curve, plot_learning_curve
from pylab import rcParams
from spiderpig import spiderpig
import matplotlib.pyplot as plt
import output


@spiderpig()
def reference_series_in_one():
    answers = load_reference_answers()
    return groupped_reference_series(answers, groupby=lambda x: 'all')


@spiderpig()
def learning_curve_in_one():
    group_series = reference_series_in_one()
    return fit_learning_curve(group_series, balance=False, bootstrap_samples=100)


def plot_learning_curve_in_one(vertical=False):
    rcParams['figure.figsize'] = 7.5, 4
    data = learning_curve_in_one()
    slope = data['value'][data['variable'] == 'slope'].values[0]
    intercept = data['value'][(data['variable'] == 'fit') & (data['attempt'] == 0)].values[0]
    fit = data[data['variable'] == 'fit']
    plt.plot(fit['attempt'] + 1, 100 * fit['value'], '--', color='black', label='Fitted power law')
    plt.text(2, 17, r'$y = {0:.2f}'.format(intercept) + ' \cdot x^{{-{0:.2f}}}$'.format(slope), size='x-large')
    raw = data[data['variable'] == 'raw']
    raw['experiment_setup_name'] = raw['experiment_setup_name'].apply(lambda x: 'Coarse data')
    plot_learning_curve(raw, with_confidence=True, legend=True)
    plt.ylabel('Error rate (%)')
    output.savefig('abexp_learning_curve_overview')


def execute(vertical=False):
    plot_global_learning_curve(
        length=10, user_length=None,
        context_answer_limit=100,
        with_confidence=True, bootstrap_samples=100,
        balance=False,
        vertical=vertical
    )
    plot_learning_curve_in_one(vertical=vertical)
