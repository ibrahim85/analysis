from .raw import load_user_answers
from metric import binomial_confidence_mean, confidence_value_to_json
from spiderpig import spiderpig
import matplotlib.pyplot as plt
import output


@spiderpig()
def survival_curve(length):
    user_answers = load_user_answers(groupby=['experiment_setup_name'])

    def _progress_confidence(i, data):
        xs = [x > i for x in data]
        return confidence_value_to_json(binomial_confidence_mean(xs))
    result = {}
    for g, d in user_answers.reset_index().groupby('experiment_setup_name'):
        inner_result = []
        for i in range(length):
            inner_result.append(_progress_confidence(i, d[0]))
        result[g] = inner_result
    return result


def plot_survival_curve(length, with_confidence):
    for i, (group_name, data) in enumerate(survival_curve(length=length).items()):
        output.plot_line(data, color=output.palette()[i], with_confidence=with_confidence, label=group_name)
    plt.legend(loc=1, frameon=True)
    plt.xlabel('Number of attempts')
    plt.ylabel('Proportion of learners')
    output.savefig(filename='survival_curve')


def execute(length=60, with_confidence=False):
    plot_survival_curve(length, with_confidence)
