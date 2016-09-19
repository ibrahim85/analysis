from bisect import bisect_left, bisect_right
from clint.textui import progress
from collections import defaultdict
from data import iterdicts
from numpy.random import randint
from scipy.optimize import curve_fit
import numpy
import pandas
import random


def get_reference_series(data, length=10, context_answer_limit=100, user_length=None, save_fun=None, require_length=True, limit_length=False):

    if save_fun is None:
        save_fun = lambda row: row['item_asked_id'] != row['item_answered_id']

    def _context_series(group):
        if len(group) < context_answer_limit:
            return []
        user_answers_dict = defaultdict(list)
        for row in iterdicts(group):
            user_answers_dict[row['user_id']].append(save_fun(row))

        def _user_answers(answers):
            if limit_length:
                answers = answers[:min(len(answers), length)]
            if require_length:
                nones = [None for _ in range(length - min(length, len(answers)))]
            else:
                nones = []
            return answers + nones

        return [
            _user_answers(answers)
            for answers in user_answers_dict.values()
            if user_length is None or len(answers) >= user_length
        ]
    return [val for vals in data.groupby(['context_name', 'term_type']).apply(_context_series) for val in vals]


def groupped_reference_series(data, groupby='experiment_setup_name', length=10, context_answer_limit=100, user_length=None, save_fun=None, require_length=True, limit_length=False):
    group_series = {}
    for group_name, group_data in data.groupby(groupby):
        group_series[group_name] = get_reference_series(group_data, length=length, user_length=user_length,
            context_answer_limit=context_answer_limit, save_fun=save_fun, require_length=require_length,
            limit_length=limit_length)
    return group_series


def balance_series(group_series):

    def _serie_len(s):
        return len([x for x in s if x is not None])

    group_series = {
        group_name: (
            series,
            sorted([(s, _serie_len(s)) for s in series if s[0]], key=lambda xs: xs[1]),
            sorted([(s, _serie_len(s)) for s in series if not s[0]], key=lambda xs: xs[1]),
            sorted([_serie_len(s) for s in series if s[0]]),
            sorted([_serie_len(s) for s in series if not s[0]]),
        ) for group_name, series in group_series.items()
    }
    unique_lengths = {
        group_name: (None, [x[1] for x in series[1]], [x[1] for x in series[2]])
        for group_name, series in group_series.items()
    }
    sample_size = min([len(s[0]) for s in group_series.values()])
    result = defaultdict(list)
    groups = list(group_series.keys())
    diffs = set()
    bisect_memory = defaultdict(lambda: defaultdict(dict))
    for _ in range(sample_size):
        chosen_group = random.choice(groups)
        chosen_serie = random.choice(group_series[chosen_group][0])
        chosen_size = len([x for x in chosen_serie if x is not None])
        result[chosen_group].append(chosen_serie)
        for group_name, group_data in group_series.items():
            if group_name == chosen_group:
                continue
            index = 1 if chosen_serie[0] else 2
            similar_serie_size = chosen_size if chosen_size in unique_lengths[group_name][index] else min(unique_lengths[group_name][index], key=lambda x: abs(chosen_size - x))
            if similar_serie_size not in bisect_memory[group_name][index]:
                bisect_memory[group_name][index][similar_serie_size] = bisect_left(group_data[index + 2], similar_serie_size), bisect_right(group_data[index + 2], similar_serie_size) - 1

            similar_serie_index = random.randint(
                bisect_memory[group_name][index][similar_serie_size][0],
                bisect_memory[group_name][index][similar_serie_size][1],
            )
            diffs.add((abs(similar_serie_size - chosen_size), similar_serie_size, chosen_size))
            similar_serie = group_data[index][similar_serie_index][0]
            result[group_name].append(similar_serie)
    return result


def fit_learning_curve(group_series, length=10, fix_beginning=True, balance=False, bootstrap_samples=100):

    confidence_vals = defaultdict(lambda: [[] for i in range(length)])
    confidence_fit_vals = defaultdict(lambda: [[] for i in range(length)])
    confidence_fit_slopes = defaultdict(list)
    confidence_quit_score = defaultdict(list)
    confidence_size = defaultdict(lambda: [[] for i in range(length)])

    def _fit_learning_curve(group_series):
        to_fit = balance_series(group_series) if balance else group_series
        first = numpy.mean([s[0] for series in group_series.values() for s in series])

        if fix_beginning:
            def _learn_fun(attempt, k):
                return first * (1.0 / (attempt + 1) ** k)
        else:
            def _learn_fun(attempt, a, k):
                return a * (1.0 / (attempt + 1) ** k)

        for group_name, group_data in to_fit.items():
            references_by_attempt = map(lambda references: [r for r in references if r is not None], zip(*group_data))
            learning_curve = [(numpy.mean(xs), len(xs)) for xs in references_by_attempt]
            for i, (_, size) in enumerate(learning_curve):
                confidence_size[group_name][i] = size
            confidence_quit_score[group_name].append(numpy.mean([[r for r in s if r is not None][-1] for s in group_data]))
            for i, (point, _) in enumerate(learning_curve):
                confidence_vals[group_name][i].append(point)

            opt, _ = curve_fit(
                _learn_fun,
                numpy.arange(len(learning_curve)),
                numpy.array([x[0] for x in learning_curve]),
                sigma=numpy.array([numpy.sqrt((x[0] * (1 - x[0])) / x[1]) for x in learning_curve])
            )
            confidence_fit_slopes[group_name].append(opt[0] if fix_beginning else opt[1])
            fit = [_learn_fun(attempt, *opt) for attempt in range(length)]
            for i, r in enumerate(fit):
                confidence_fit_vals[group_name][i].append(r)

    _bootstrap_group_series(group_series, _fit_learning_curve, bootstrap_samples=bootstrap_samples)

    result = []

    for group_name in group_series.keys():
        for attempt in range(length):
            result.append({
                'experiment_setup_name': group_name,
                'variable': 'raw',
                'attempt': attempt,
                'value': numpy.median(confidence_vals[group_name][attempt]),
                'confidence_min': numpy.percentile(confidence_vals[group_name][attempt], 2.5),
                'confidence_max': numpy.percentile(confidence_vals[group_name][attempt], 97.5),
            })
            result.append({
                'experiment_setup_name': group_name,
                'variable': 'fit',
                'attempt': attempt,
                'value': numpy.median(confidence_fit_vals[group_name][attempt]),
                'confidence_min': numpy.percentile(confidence_fit_vals[group_name][attempt], 2.5),
                'confidence_max': numpy.percentile(confidence_fit_vals[group_name][attempt], 97.5),
            })
            result.append({
                'experiment_setup_name': group_name,
                'variable': 'size',
                'attempt': attempt,
                'value': numpy.median(confidence_size[group_name][attempt]),
                'confidence_min': numpy.percentile(confidence_size[group_name][attempt], 2.5),
                'confidence_max': numpy.percentile(confidence_size[group_name][attempt], 97.5),
            })
        result.append({
            'experiment_setup_name': group_name,
            'variable': 'slope',
            'attempt': None,
            'value': numpy.median(confidence_fit_slopes[group_name]),
            'confidence_min': numpy.percentile(confidence_fit_slopes[group_name], 2.5),
            'confidence_max': numpy.percentile(confidence_fit_slopes[group_name], 97.5),
        })
        result.append({
            'experiment_setup_name': group_name,
            'variable': 'quit_score',
            'attempt': None,
            'value': numpy.median(confidence_quit_score[group_name]),
            'confidence_min': numpy.percentile(confidence_quit_score[group_name], 2.5),
            'confidence_max': numpy.percentile(confidence_quit_score[group_name], 97.5),
        })

    return pandas.DataFrame(result)


def _bootstrap_group_series(group_series, fun, bootstrap_samples=100):
    group_series = {name: numpy.array(values) for name, values in group_series.items()}
    for _ in progress.bar(range(bootstrap_samples)):
        fun({
            group_name: group_values[randint(group_values.shape[0], size=len(group_values))]
            for group_name, group_values in group_series.items()
        })
