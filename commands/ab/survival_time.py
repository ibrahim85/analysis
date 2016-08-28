from .raw import load_user_time
from metric import binomial_confidence_mean, confidence_value_to_json
from spiderpig import spiderpig
import matplotlib.pyplot as plt
import output


@spiderpig()
def survival_curve(length):
    user_times = load_user_time(groupby=['experiment_setup_name'])

    def _progress_confidence(i, data):
        xs = [x > i for x in data]
        return confidence_value_to_json(binomial_confidence_mean(xs), use_format_number=False)
    result = {}
    for g, d in user_times.reset_index().groupby('experiment_setup_name'):
        inner_result = []
        for i in range(0, length):
            inner_result.append(_progress_confidence(i, d[0]))
        result[g] = inner_result
    return result


def plot_survival_curve(length, with_confidence):
    for i, (group_name, data) in enumerate(sorted(survival_curve(length=length).items())):
        output.plot_line(data, color=output.palette()[i], with_confidence=with_confidence, label=group_name)
    plt.legend(loc=3, frameon=True)
    plt.xlabel('Number of seconds')
    plt.ylabel('Proportion of learners')
    plt.ylim(0, 1)
    output.savefig(filename='survival_curve_time')


def execute(length=60, with_confidence=False):
    print(load_user_time(groupby=['experiment_setup_name']).reset_index()[0].max())
    plot_survival_curve(length, with_confidence)
