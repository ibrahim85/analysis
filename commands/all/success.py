from pylab import rcParams
from spiderpig import spiderpig
import matplotlib.pyplot as plt
import output
from . import raw


@spiderpig()
def get_user_success():
    data = raw.load_and_merge()
    return data.groupby('user').apply(lambda g: (g['item_asked'] == g['item_answered']).mean()).to_dict()


def plot_user_success_hist():
    rcParams['figure.figsize'] = 3.75, 2.5
    plt.gca().yaxis.set_ticks([])
    plt.hist(list(get_user_success().values()))
    plt.xlabel('Success rate')
    plt.ylabel('Number of users')
    plt.xticks(plt.xticks()[0], map(lambda x: '{}%'.format(int(x * 100)), plt.xticks()[0]))
    output.savefig(filename='user_success_hist')


def execute():
    plot_user_success_hist()
