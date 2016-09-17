from .evaluate import train, test
from .raw import load_test_set
from pylab import rcParams
from spiderpig import spiderpig
import matplotlib.pyplot as plt
import numpy as np
import output


@spiderpig()
def correlated_predictions(first_model_name, second_model_name):
    first_model = train(first_model_name, {})[0]
    second_model = train(second_model_name, {})[0]
    test_data = load_test_set()
    test_data['first_model_predictions'] = test(first_model)
    test_data['second_model_predictions'] = test(second_model)
    return test_data


def plot_correlated_predictions(first_model_name, second_model_name):
    data = correlated_predictions(first_model_name, second_model_name)
    not_first = data[data['seconds_ago'].notnull()]
    rcParams['figure.figsize'] = 15, 5
    plt.subplot(121)
    correct = not_first[not_first['item_asked'] == not_first['item_answered']]
    correlation = np.corrcoef(correct['first_model_predictions'], correct['second_model_predictions'])[0, 1]
    correct = correct.sample(1000)
    plt.title(correlation)
    plt.plot(correct['first_model_predictions'], correct['second_model_predictions'], 'go', alpha=0.2)
    plt.xlabel(first_model_name)
    plt.ylabel(second_model_name)
    plt.subplot(122)
    incorrect = not_first[not_first['item_asked'] != not_first['item_answered']]
    correlation = np.corrcoef(incorrect['first_model_predictions'], incorrect['second_model_predictions'])[0, 1]
    incorrect = incorrect.sample(1000)
    plt.title(correlation)
    plt.plot(incorrect['first_model_predictions'], incorrect['second_model_predictions'], 'ro', alpha=0.2)
    plt.xlabel(first_model_name)
    plt.ylabel(second_model_name)
    output.savefig('correlated_predictions')


def execute(first_model_name, second_model_name):
    plot_correlated_predictions(first_model_name, second_model_name)
