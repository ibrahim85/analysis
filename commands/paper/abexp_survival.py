from commands.ab.raw import load_user_answers, load_user_time
from commands.ab.survival_zoom import load_survival_curve_answers as load_survival_curve_answers_zoom,\
    load_survival_curve_time as load_survival_curve_time_zoom,\
    plot_survival_curve as plot_survival_curve_zoom
from commands.ab.survival_time import plot_survival_curve as plot_survival_curve_time_orig
from commands.ab.survival import plot_survival_curve as plot_survival_curve_answers_orig
from metric import binomial_confidence_mean
from pylab import rcParams
from spiderpig import spiderpig
import matplotlib.pyplot as plt
import output
import pandas


def compute_survival_curve_answers(user_answers, length):

    def _progress_confidence(i, data):
        xs = [x > i for x in data]
        return binomial_confidence_mean(xs)
    result = []
    for i in range(length):
        ci = _progress_confidence(i, user_answers)
        row = {
            'variable': 'survival_answers',
            'value': ci[0],
            'confidence_min': ci[1][0],
            'confidence_max': ci[1][1],
            'attempt': i + 1,
        }
        result.append(row)
    return pandas.DataFrame(result)


def compute_survival_curve_time(user_times, length):
    user_times = load_user_time()

    def _progress_confidence(i, data):
        xs = [x > i for x in data]
        return binomial_confidence_mean(xs)
    result = []
    for i in range(length):
        ci = _progress_confidence(i, user_times)
        row = {
            'variable': 'survival_time',
            'value': ci[0],
            'confidence_min': ci[1][0],
            'confidence_max': ci[1][1],
            'attempt': i + 1,
        }
        result.append(row)
    return pandas.DataFrame(result)


@spiderpig()
def load_survival_curve_answers(length):
    user_answers = load_user_answers()
    return compute_survival_curve_answers(user_answers)


@spiderpig()
def load_survival_curve_time(length):
    user_times = load_user_time()
    return compute_survival_curve_time(user_times)


def plot_survival_curve_overview(survival_data):
    plt.plot(survival_data['attempt'], survival_data['value'].apply(lambda x: x * 100), color=output.palette()[0], linewidth=2)
    plt.fill_between(
        survival_data['attempt'],
        [0] * len(survival_data['attempt']),
        survival_data['value'].apply(lambda x: x * 100),
        color=output.palette()[0], alpha=0.25
    )
    plt.xlim(1, survival_data['attempt'].max())
    plt.ylim(0, 100)


def plot_overview():
    def _highlight(data, attempt, text, horizontal_shift=2, vertical_shift=2):
        plt.axvline(x=attempt, ymin=0, ymax=data['value'][data['attempt'] == attempt].values[0], linewidth=2, color='black')
        plt.plot(attempt, 100 * data['value'][data['attempt'] == attempt].values[0], '.', color='black', markersize=20)
        plt.text(attempt + horizontal_shift, vertical_shift + 100 * data['value'][data['attempt'] == attempt].values[0], '{} ({}%)'.format(text, int(round(data['value'][data['attempt'] == attempt].values[0] * 100))))

    rcParams['figure.figsize'] = 15, 4
    plt.subplot(121)
    answers = load_survival_curve_answers(150)
    plot_survival_curve_overview(answers)
    _highlight(answers, 10, 'short-term')
    _highlight(answers, 100, 'long-term')
    plt.ylabel('Proportion of learners')
    plt.xlabel('Attempts')
    plt.subplot(122)
    time = load_survival_curve_time(900)
    plot_survival_curve_overview(time)
    _highlight(time, 60, 'short-term', horizontal_shift=15, vertical_shift=2)
    _highlight(time, 600, 'long-term', horizontal_shift=15, vertical_shift=2)
    plt.xlabel('Seconds')
    plt.gca().axes.get_yaxis().set_ticks([])
    plt.gca().yaxis.set_major_formatter(plt.NullFormatter())
    output.savefig('abexp_survival_overview')


def plot_difficulty_zoom():

    def _swap(data):
        if len(data['experiment_setup_name'].unique()) == 2:
            first = data[data['experiment_setup_name'] == data['experiment_setup_name'].unique()[0]].sort_values('attempt').set_index('attempt')
            second = data[data['experiment_setup_name'] == data['experiment_setup_name'].unique()[1]].sort_values('attempt').set_index('attempt')
            if first.ix[5]['value'] > second.ix[10]['value']:
                first, second = second, first
            found = first[(first['value'] > second['value'])].reset_index()[['attempt', 'value']]
            found = found[found['attempt'] > 5]
            if len(found) == 0:
                return
            found = found.values[0]
            plt.plot(found[0] + 1, 100 * found[1], '.', markersize=20, color='black')
            plt.axvline(x=found[0] + 1, ymin=0, ymax=found[1], linewidth=2, color='black')
            plt.text(found[0] + 2, 5 + 100 * found[1], 'swap')

    answers = load_survival_curve_answers_zoom(100, 'context_difficulty_label')
    rcParams['figure.figsize'] = 7.5, 8

    plt.subplot(211)
    plt.title('Top 25% easiest contexts')
    easy_data = answers[answers['zoom_column_value'] =='too easy']
    plot_survival_curve_zoom(easy_data, with_confidence=True, legend=True)
    _swap(easy_data)
    plt.ylabel('Proportion of learners')

    plt.subplot(212)
    plt.title('Top 25% most difficult contexts')
    difficulty_data = answers[answers['zoom_column_value'] =='difficult']
    plot_survival_curve_zoom(difficulty_data, with_confidence=True, legend=False)
    plt.ylabel('Proportion of learners')
    plt.xlabel('Attempts')

    output.savefig('abexp_survival_zoom_difficulty')


def plot_attempts_vs_time():
    rcParams['figure.figsize'] = 7.5, 8

    plt.subplot(211)
    plot_survival_curve_answers_orig(100, True, legend=True)

    plt.subplot(212)
    plot_survival_curve_time_orig(600, True)
    output.savefig('abexp_survival_attempt_vs_time')


def execute():
    plot_overview()
    plot_difficulty_zoom()
    plot_attempts_vs_time()
