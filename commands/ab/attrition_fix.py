from . import raw
from .data import fit_learning_curve, groupped_reference_series
from spiderpig import spiderpig
import matplotlib.pyplot as plt
import output
import random
from metric import binomial_confidence_mean
import pandas


@spiderpig()
def create_A_A_groups(group_name, n):
    data = raw.load_reference_answers()
    data = data[data['experiment_setup_name'] == group_name]
    users = data['user_id'].unique()
    random.shuffle(users)
    chunk_size = int(len(users) / n)
    user_groups = {user: 'group-{}'.format(g + 1) for g, users in enumerate([users[i:i + chunk_size] for i in range(n)]) for user in users}
    data['experiment_setup_name'] = data['user_id'].apply(lambda u: user_groups.get(u, 'group-1'))
    return data


@spiderpig()
def create_A_A_groups_with_attrition(group_name, strength):
    data = raw.load_reference_answers()
    data = data[data['experiment_setup_name'] == group_name]

    users_division = [[], []]

    for (user, _, _), user_data in data.sort_values(by='id').groupby(['user_id', 'context_name', 'term_type']):
        if any(user in users for users in users_division):
            continue
        prior_knowledge = (user_data['item_asked_id'].values[0] == user_data['item_answered_id'].values[0])
        practice_length = len(user_data)
        lower = users_division[0] if prior_knowledge else users_division[1]
        upper = users_division[1] if prior_knowledge else users_division[0]
        chance_lower = 0.5 - min((practice_length - 1) * strength, 0.5)
        if random.random() < chance_lower:
            lower.append(user)
        else:
            upper.append(user)
    users_division = [random.sample(users_division[i], min(map(len, users_division))) for i in range(len(users_division))]
    user_groups = {user: 'group-{}'.format(g + 1) for g, users in enumerate(users_division) for user in users}
    data['experiment_setup_name'] = data['user_id'].apply(lambda u: user_groups.get(u, 'group-1'))
    return data


@spiderpig()
def A_A_reference_series(group_name, create_group_param, length, user_length, context_answer_limit):
    answers = create_A_A_groups(group_name, create_group_param) if isinstance(create_group_param, int) else create_A_A_groups_with_attrition(group_name, create_group_param)
    return groupped_reference_series(answers, length=length, user_length=user_length, context_answer_limit=context_answer_limit)


@spiderpig()
def A_A_learning_curve(group_name, create_group_param, length, user_length, context_answer_limit):
    group_series = A_A_reference_series(group_name, create_group_param, length=length, user_length=user_length, context_answer_limit=context_answer_limit)
    not_balanced = fit_learning_curve(group_series, length=length, balance=False)
    not_balanced['balanced'] = not_balanced['value'].apply(lambda x: False)
    balanced = fit_learning_curve(group_series, length=length, balance=True)
    balanced['balanced'] = balanced['value'].apply(lambda x: True)
    return balanced.append(not_balanced)


@spiderpig()
def A_A_attrition_bias(group_name, create_group_param, balance):
    answers = create_A_A_groups(group_name, create_group_param) if isinstance(create_group_param, int) else create_A_A_groups_with_attrition(group_name, create_group_param)
    groupped_series = groupped_reference_series(answers, require_length=False, limit_length=True)
    result = []
    for group_name, series in groupped_series.items():
        for i in range(10):
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


def plot_attrition_bias(attrition_bias_data, with_confidence=False):
    MARKERS = "dos^" * 10
    for i, (setup, setup_data) in enumerate(attrition_bias_data.groupby('experiment_setup_name')):
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


def plot_learning_curve(data, legend=True, with_confidence=False):
    MARKERS = "dos^" * 10
    for i, (setup, setup_data) in enumerate(data.groupby('experiment_setup_name')):
        plt.plot(setup_data['attempt'] + 1, setup_data['value'].apply(lambda x: x * 100), label=setup, color=output.palette()[i], marker=MARKERS[i], markersize=10)
        if with_confidence:
            plt.fill_between(
                setup_data['attempt'] + 1,
                setup_data['confidence_min'.format(setup)].apply(lambda x: x * 100),
                setup_data['confidence_max'.format(setup)].apply(lambda x: x * 100),
                color=output.palette()[i], alpha=0.35
            )
    if legend:
        plt.legend(loc=1)
    plt.xlabel('Reference attempt')
    plt.ylim(0, 60)


def execute(group_name, factor=0.01):
    data_biased = A_A_learning_curve(group_name, factor, 10, user_length=None, context_answer_limit=100)
    data_pure = A_A_learning_curve(group_name, 2, 10, user_length=None, context_answer_limit=100)
    plt.gcf().set_size_inches(15, 10)
    plt.subplot(221)
    plt.title('Fitted learning curve')
    plot_learning_curve(data_biased[(data_biased['variable'] == 'fit') & ~data_biased['balanced']], with_confidence=True)
    plt.subplot(222)
    plt.title('Fitted learning curve with balancing')
    plot_learning_curve(data_biased[(data_biased['variable'] == 'fit') & data_biased['balanced']], with_confidence=True)
    plt.subplot(223)
    plt.title('Fitted learning curve\n(pure A-A experiment)')
    plot_learning_curve(data_pure[(data_pure['variable'] == 'fit') & ~data_pure['balanced']], with_confidence=True)
    plt.subplot(224)
    plt.title('Attrition bias')
    plot_attrition_bias(A_A_attrition_bias(group_name, factor, False), with_confidence=True)
    output.savefig('attrition_bias_fix')
