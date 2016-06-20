from .data import fit_learning_slope, groupped_reference_series
from .raw import load_reference_answers
from spiderpig import spiderpig
import matplotlib.pyplot as plt
import numpy
import output
import seaborn as sns


@spiderpig()
def reference_series(length, user_length, context_answer_limit, balance):
    answers = load_reference_answers()
    return groupped_reference_series(answers, length=length, user_length=user_length, context_answer_limit=context_answer_limit, balance=balance)


@spiderpig()
def global_learning_slope(length, user_length, context_answer_limit, bootstrap_samples, balance):
    result = None
    for setup, series in reference_series(length=length, user_length=user_length, context_answer_limit=context_answer_limit, balance=balance).items():
        slope = fit_learning_slope(series, length=length, bootstrap_samples=bootstrap_samples)
        slope['experiment_setup_name'] = setup
        result = slope if result is None else result.append(slope)
    return result


def plot_global_learning_slope(length, user_length, context_answer_limit, with_confidence, bootstrap_samples):
    slope = global_learning_slope(
        length=length, user_length=user_length,
        context_answer_limit=context_answer_limit,
        bootstrap_samples=bootstrap_samples, balance=False
    )
    slope['balanced'] = slope['experiment_setup_name'].apply(lambda x: False)
    slope_balanced = global_learning_slope(
        length=length, user_length=user_length,
        context_answer_limit=context_answer_limit,
        bootstrap_samples=bootstrap_samples, balance=True
    )
    slope_balanced['balanced'] = slope_balanced['experiment_setup_name'].apply(lambda x: True)
    to_plot = slope.append(slope_balanced)
    for i, (balanced, data) in enumerate(to_plot.groupby('balanced')):
        data = data.sort_values(by='experiment_setup_name')
        plt.bar(
            numpy.arange(len(data)) + i * 0.4,
            data['value'], 0.4,
            color=output.palette()[i],
            label='balanced' if balanced else 'not balanced',
            yerr=[data['value'] - data['confidence_min'], data['confidence_max'] - data['value']],
            error_kw={'ecolor': 'black'},
        )
        plt.xticks(
            numpy.arange(len(data)) + 0.4,
            data['experiment_setup_name']
        )
    plt.legend(frameon=True, loc=3)
    plt.xlabel('Condition')
    plt.ylabel('k')
    plt.gca().yaxis.grid(True)
    output.savefig('global_learning_slope')


def execute(length=10, user_length=None, context_answer_limit=100, with_confidence=False, bootstrap_samples=1000):
    plot_global_learning_slope(
        length=length, user_length=user_length,
        context_answer_limit=context_answer_limit,
        with_confidence=with_confidence, bootstrap_samples=bootstrap_samples
    )
