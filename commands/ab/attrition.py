from .data import groupped_reference_series
from .raw import load_reference_answers
from metric import binomial_confidence_mean
from spiderpig import spiderpig
import matplotlib.pyplot as plt
import output
# import numpy
import pandas


@spiderpig()
def attrition_bias(length, user_length, context_answer_limit, balance):
    answers = load_reference_answers()
    groupped_series = groupped_reference_series(answers, balance=balance,
        length=10, context_answer_limit=context_answer_limit,
        user_length=user_length, require_length=False, limit_length=True)
    result = []
    for group_name, series in groupped_series.items():
        for i in range(length):
            firsts = [serie[0] for serie in series if len(serie) > i]
            value, confidence = binomial_confidence_mean(firsts)
            result.append({
                'length': i + 1,
                'size': len(firsts),
                'value': value,
                'confidence_min': confidence[0],
                'confidence_max': confidence[1],
                'experiment_setup_name': group_name,
            })
    return pandas.DataFrame(result)


def plot_attrition_bias(length, user_length, context_answer_limit, with_confidence, balance):
    data = attrition_bias(length, user_length, context_answer_limit, balance)
    MARKERS = "dos^" * 10
    for i, (setup, setup_data) in enumerate(data.groupby('experiment_setup_name')):
        plt.plot(setup_data['length'], setup_data['value'].apply(lambda x: x * 100), label=setup, color=output.palette()[i], marker=MARKERS[i], markersize=10)
        if with_confidence:
            plt.fill_between(
                setup_data['length'],
                setup_data['confidence_min'.format(setup)].apply(lambda x: x * 100),
                setup_data['confidence_max'.format(setup)].apply(lambda x: x * 100),
                color=output.palette()[i], alpha=0.35
            )
    plt.legend(loc=0)
    plt.xlabel('Minimal number of reference attempts')
    plt.ylabel('Error rate (%)')
    output.savefig('attrition_bias')


def execute(length=10, user_length=None, context_answer_limit=100, with_confidence=True, balance=False):
    plot_attrition_bias(length, user_length, context_answer_limit, with_confidence, balance)
