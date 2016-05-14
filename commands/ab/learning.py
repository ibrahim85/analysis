from .data import get_learning_curve, fit_learning_curve, groupped_reference_series
from .raw import load_reference_answers
from pylab import rcParams
from spiderpig import spiderpig
import matplotlib.pyplot as plt
import output


@spiderpig()
def reference_series(length, user_length, context_answer_limit, balance):
    answers = load_reference_answers()
    return groupped_reference_series(answers, length=length, user_length=user_length, context_answer_limit=context_answer_limit, balance=balance)


@spiderpig()
def global_learning_curve(length, user_length, context_answer_limit, balance):
    result = None
    for setup, series in reference_series(length=length, user_length=user_length, context_answer_limit=context_answer_limit, balance=balance).items():
        # print(series)
        curve = get_learning_curve(series, length=length)
        curve['experiment_setup_name'] = setup
        result = curve if result is None else result.append(curve)
    return result


@spiderpig()
def global_learning_curve_fit(length, user_length, context_answer_limit, bootstrap_samples, balance):
    result = None
    for setup, series in reference_series(length=length, user_length=user_length, context_answer_limit=context_answer_limit, balance=balance).items():
        # print(series)
        curve = fit_learning_curve(series, length=length, bootstrap_samples=bootstrap_samples)
        curve['experiment_setup_name'] = setup
        result = curve if result is None else result.append(curve)
    return result


def plot_learning_curve(data, legend=True, with_confidence=False):
    MARKERS = "dos^" * 10
    for i, (setup, setup_data) in enumerate(data.groupby('experiment_setup_name')):
        plt.plot(setup_data['attempt'] + 1, setup_data['value'].apply(lambda x: int(x * 100)), label=setup, color=output.palette()[i], marker=MARKERS[i], markersize=10)
        if with_confidence:
            plt.fill_between(
                setup_data['attempt'] + 1,
                setup_data['confidence_min'.format(setup)].apply(lambda x: int(x * 100)),
                setup_data['confidence_max'.format(setup)].apply(lambda x: int(x * 100)),
                color=output.palette()[i], alpha=0.35
            )
    if legend:
        plt.legend(loc=1)
    plt.xlabel('Reference attempt')
    plt.ylim(0, 60)


def plot_global_learning_curve(length, user_length, context_answer_limit, with_confidence, bootstrap_samples, balance):
    global_curve = global_learning_curve(
        length=length, user_length=user_length,
        context_answer_limit=context_answer_limit
    )
    global_curve_fit = global_learning_curve_fit(
        length=length, user_length=user_length,
        context_answer_limit=context_answer_limit, bootstrap_samples=bootstrap_samples
    )
    rcParams['figure.figsize'] = 15, 5
    plt.subplot(121)
    plt.ylabel('Error rate (%)')
    plt.title('Coarse data')
    plot_learning_curve(global_curve, with_confidence=with_confidence)
    plt.subplot(122)
    plt.title('Fitted power law')
    plot_learning_curve(global_curve_fit, with_confidence=with_confidence)
    output.savefig('global_learning_raw')


def execute(length=10, user_length=None, context_answer_limit=100, with_confidence=False, bootstrap_samples=1000, balance=False):
    plot_global_learning_curve(
        length=length, user_length=user_length,
        context_answer_limit=context_answer_limit,
        with_confidence=with_confidence, bootstrap_samples=bootstrap_samples,
        balance=balance
    )
