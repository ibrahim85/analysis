from .data import get_learning_curve
from .raw import load_answers
from spiderpig import spiderpig
import matplotlib.pyplot as plt
import output


@spiderpig()
def global_learning_curve(length, user_length, context_answer_limit, reverse):
    answers = load_answers()
    result = None
    for setup, data in answers.groupby('experiment_setup_name'):
        curve = get_learning_curve(
            data, length=length, user_length=user_length,
            context_answer_limit=context_answer_limit, reverse=reverse
        )
        curve['experiment_setup_name'] = setup
        result = curve if result is None else result.append(curve)
    return result


def plot_learning_curve(data, legend=True, with_confidence=False):
    for i, (setup, setup_data) in enumerate(data.groupby('experiment_setup_name')):
        plt.plot(setup_data['attempt'], setup_data['value'], label=setup, color=output.palette()[i])
        plt.gca().yaxis.grid(True)
        if with_confidence:
            plt.fill_between(
                setup_data['attempt'],
                setup_data['confidence_min'.format(setup)],
                setup_data['confidence_max'.format(setup)],
                color=output.palette()[i], alpha=0.35
            )
    if legend:
        plt.legend(loc=1, frameon=True)
    plt.xlabel('Reference attempt')
    plt.ylabel('Error rate')


def plot_global_learning_curve(length, user_length, context_answer_limit, reverse, with_confidence):
    global_curve = global_learning_curve(
        length=length, user_length=user_length,
        context_answer_limit=context_answer_limit, reverse=reverse
    )
    plot_learning_curve(global_curve, with_confidence=with_confidence)
    output.savefig('global_learning_raw')


def execute(length=10, user_length=None, context_answer_limit=100, reverse=False, with_confidence=False):
    plot_global_learning_curve(
        length=length, user_length=user_length,
        context_answer_limit=context_answer_limit, reverse=reverse,
        with_confidence=with_confidence
    )
