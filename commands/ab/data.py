from collections import defaultdict
from data import iterdicts
from metric import binomial_confidence_mean
import pandas


def get_reference_series(data, length=10, context_answer_limit=100, reverse=False, user_length=None, save_fun=None, require_length=True):

    if save_fun is None:
        save_fun = lambda row: row['item_asked_id'] != row['item_answered_id']

    def _context_series(group):
        if len(group) < context_answer_limit:
            return []
        user_answers_dict = defaultdict(list)
        for row in iterdicts(group):
            user_answers_dict[row['user_id']].append(save_fun(row))

        def _user_answers(answers):
            if reverse:
                answers = answers[::-1]
            if require_length:
                answers = answers[:min(len(answers), length)]
                nones = [None for _ in range(length - len(answers))]
            else:
                nones = []
            if reverse:
                answers = answers[::-1]
                return nones + answers
            else:
                return answers + nones

        return [
            _user_answers(answers)
            for answers in user_answers_dict.values()
            if user_length is None or len(answers) >= user_length
        ]
    return [val for (_, vals) in data.groupby(['context_name', 'term_type']).apply(_context_series).items() for val in vals]


def get_learning_curve(data, length=10, user_length=None, context_answer_limit=100, reverse=False):
    series = get_reference_series(data, length=length, user_length=user_length,
        context_answer_limit=context_answer_limit, reverse=reverse)
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
