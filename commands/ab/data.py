from collections import defaultdict
from data import iterdicts
from metric import binomial_confidence_mean
from scipy.optimize import curve_fit
import numpy
import pandas
import random
import scikits.bootstrap as bootstrap


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
            if require_length or limit_length:
                answers = answers[:min(len(answers), length)]
            if require_length:
                nones = [None for _ in range(length - len(answers))]
            else:
                nones = []
            return answers + nones

        return [
            _user_answers(answers)
            for answers in user_answers_dict.values()
            if user_length is None or len(answers) >= user_length
        ]
    return [val for vals in data.groupby(['context_name', 'term_type']).apply(_context_series) for val in vals]


def groupped_reference_series(data, balance=False, groupby='experiment_setup_name', length=10, context_answer_limit=100, user_length=None, save_fun=None, require_length=True, limit_length=False):
    group_series = {}
    for group_name, group_data in data.groupby(groupby):
        series = get_reference_series(group_data, length=length, user_length=user_length,
            context_answer_limit=context_answer_limit, save_fun=save_fun, require_length=require_length,
            limit_length=limit_length)
        group_series[group_name] = (
            series,
            [(s, len([x for x in s if x is not None])) for s in series if s[0]],
            [(s, len([x for x in s if x is not None])) for s in series if not s[0]]
        )
    if not balance:
        return {group_name: group_data[0] for group_name, group_data in group_series.items()}
    sample_size = min([len(s[0]) for s in group_series.values()])
    result = defaultdict(list)
    diffs = set()
    for _ in range(sample_size):
        chosen_group = random.choice(list(group_series.keys()))
        chosen_serie = random.choice(group_series[chosen_group][0])
        chosen_size = len([x for x in chosen_serie if x is not None])
        result[chosen_group].append(chosen_serie)
        for group_name, group_data in group_series.items():
            if group_name == chosen_group:
                continue
            index = 1 if chosen_serie[0] else 2
            similar_serie = min(group_data[index], key=lambda serie: abs(chosen_size - serie[1]))
            similar_serie_size = similar_serie[1]
            diffs.add((abs(similar_serie_size - chosen_size), similar_serie_size, chosen_size))
            similar_serie = random.choice([serie[0] for serie in group_data[index] if serie[1] == similar_serie_size])
            result[group_name].append(similar_serie)
    return result


def fit_learning_slope(series, length=10, bootstrap_samples=100):

    def _fit_learning_curve(series):
        references_by_attempt = map(lambda references: [r for r in references if r is not None], zip(*series))
        learning_curve = [(numpy.mean(xs), len(xs)) for xs in references_by_attempt]

        def _learn_fun(attempt, a, k):
            return a * (1.0 / (attempt + 1) ** k)

        opt, _ = curve_fit(
            _learn_fun,
            numpy.arange(len(learning_curve)),
            numpy.array([x[0] for x in learning_curve]),
            sigma=numpy.array([numpy.sqrt((x[0] * (1 - x[0])) / x[1]) for x in learning_curve])
        )
        return opt[1]

    if len(series) == 0:
        return pandas.DataFrame([{
            'value': None,
            'confidence_min': None,
            'confidence_max': None,
            'size': 0,
        }])
    confidence = bootstrap.ci(series, _fit_learning_curve, method='pi', n_samples=bootstrap_samples)
    return pandas.DataFrame([{
        'value': _fit_learning_curve(series),
        'confidence_min': confidence[0],
        'confidence_max': confidence[1],
        'size': None,
    }])


def fit_learning_curve(series, length=10, bootstrap_samples=100):

    confidence_vals = [[] for i in range(length)]

    def _fit_learning_curve(series):
        references_by_attempt = map(lambda references: [r for r in references if r is not None], zip(*series))
        learning_curve = [(numpy.mean(xs), len(xs)) for xs in references_by_attempt]

        def _learn_fun(attempt, a, k):
            return a * (1.0 / (attempt + 1) ** k)

        opt, _ = curve_fit(
            _learn_fun,
            numpy.arange(len(learning_curve)),
            numpy.array([x[0] for x in learning_curve]),
            sigma=numpy.array([numpy.sqrt((x[0] * (1 - x[0])) / x[1]) for x in learning_curve])
        )
        fit = [_learn_fun(attempt, opt[0], opt[1]) for attempt in range(length)]
        for i, r in enumerate(fit):
            confidence_vals[i].append(r)
        return fit[-1]

    if len(series) == 0:
        return pandas.DataFrame([{
            'attempt': attempt,
            'value': None,
            'confidence_min': None,
            'confidence_max': None,
            'size': 0,
        } for attempt in range(length)])
    bootstrap.ci(series, _fit_learning_curve, method='pi', n_samples=bootstrap_samples)
    return pandas.DataFrame([{
        'attempt': i,
        'value': numpy.median(rs),
        'confidence_min': numpy.percentile(rs, 2.5),
        'confidence_max': numpy.percentile(rs, 97.5),
        'size': sum(map(lambda x: x > i, series)),
    } for i, rs in enumerate(confidence_vals)])


def get_learning_curve(series, length=10):
    references_by_attempt = map(lambda references: [r for r in references if r is not None], zip(*series))

    def _weighted_mean(attempt, xs):
        value, confidence = binomial_confidence_mean(xs)
        return {
            'attempt': attempt,
            'value': value,
            'confidence_min': confidence[0],
            'confidence_max': confidence[1],
            'size': len(xs),
        }
    return pandas.DataFrame([_weighted_mean(i, refs) for i, refs in enumerate(references_by_attempt)])
