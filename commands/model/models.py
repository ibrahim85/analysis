from collections import defaultdict
import abc
import math
import numpy


def ZERO():
    return 0


def ZERO_TIME():
    return '01-01-1970 00:00:01'


class Model:

    @staticmethod
    def from_name(model_name, root=True, *args, **kwargs):
        for model_class in Model._transitive_subclasses():
            if model_class.__name__ == model_name:
                return model_class(*args, **kwargs)
        raise Exception('There is no model with name {}.'.format(model_name))

    @staticmethod
    def _transitive_subclasses(given_class=None):
        if given_class is None:
            given_class = Model
        here = given_class.__subclasses__()
        return here + [sc for scs in [Model._transitive_subclasses(c) for c in here] for sc in scs]

    def setup(self):
        pass

    @abc.abstractmethod
    def predict(self, user_id, item_id, time, guess, seconds_ago):
        pass

    @abc.abstractmethod
    def update(self, user_id, item_id, prediction, correct, time, guess, seconds_ago):
        pass


class ItemAverage(Model):

    def __init__(self, init_prediction=0.5):
        self._init_prediction = init_prediction

    def setup(self):
        self._corrects = defaultdict(ZERO)
        self._counts = defaultdict(ZERO)

    @abc.abstractmethod
    def predict(self, user_id, item_id, time, guess, seconds_ago):
        return self._corrects[item_id] / self._counts[item_id] if self._counts[item_id] > 0 else self._init_prediction

    @abc.abstractmethod
    def update(self, user_id, item_id, prediction, correct, time, guess, seconds_ago):
        self._counts[item_id] += 1
        self._corrects[item_id] += correct


class Elo(Model):

    def __init__(self, alpha=0.8, dynamic_alpha=0.05):
        self._alpha = alpha
        self._dynamic_alpha = dynamic_alpha

    def setup(self):
        self._skills = defaultdict(ZERO)
        self._difficulties = defaultdict(ZERO)
        self._user_answers = defaultdict(ZERO)
        self._item_answers = defaultdict(ZERO)
        self._user_item_answers = defaultdict(ZERO)

    def predict(self, user_id, item_id, time, guess, seconds_ago):
        user_id = str(user_id)
        item_id = str(item_id)
        return _sigmoid(self._skills[user_id] - self._difficulties[item_id], guess)

    def update(self, user_id, item_id, prediction, correct, time, guess, seconds_ago):
        user_id = str(user_id)
        item_id = str(item_id)
        if self.number_of_answers(user_id, item_id) > 0:
            self._user_item_answers['{} {}'.format(user_id, item_id)] += 1
            return
        item_alpha = self._alpha / (1 + self._dynamic_alpha * self._item_answers[item_id])
        user_alpha = self._alpha / (1 + self._dynamic_alpha * self._item_answers[user_id])
        self._skills[user_id] += user_alpha * (correct - prediction)
        self._difficulties[item_id] -= item_alpha * (correct - prediction)
        self._user_item_answers['{} {}'.format(user_id, item_id)] += 1
        self._user_answers[user_id] += 1
        self._item_answers[item_id] += 1

    def number_of_answers(self, user_id, item_id):
        user_id = str(user_id)
        item_id = str(item_id)
        return self._user_item_answers['{} {}'.format(user_id, item_id)]


class PFAE(Elo):

    def __init__(self, elo_alpha=0.8, elo_dynamic_alpha=0.05, correct=3.4, wrong=0.2, time_shift=0.8):
        Elo.__init__(self, elo_alpha, elo_dynamic_alpha)
        self._correct = correct
        self._wrong = wrong
        self._time_shift = time_shift

    def setup(self):
        Elo.setup(self)
        self._local_skills = defaultdict(ZERO)

    def predict(self, user_id, item_id, time, guess, seconds_ago):
        if self.number_of_answers(user_id, item_id) == 0:
            return Elo.predict(self, user_id, item_id, time, guess, seconds_ago)
        user_id = str(user_id)
        item_id = str(item_id)
        return _sigmoid(
            self._local_skills[user_id] -
            self._difficulties[item_id] +
            self._local_skills['{} {}'.format(user_id, item_id)] +
            self._time_shift / max(seconds_ago, 0.001),
            guess
        )

    def update(self, user_id, item_id, prediction, correct, time, guess, seconds_ago):
        user_id = str(user_id)
        item_id = str(item_id)
        if self.number_of_answers(user_id, item_id) == 0:
            Elo.update(self, user_id, item_id, prediction, correct, time, guess, seconds_ago)
        elif correct:
            self._local_skills['{} {}'.format(user_id, item_id)] += self._correct * (correct - prediction)
        else:
            self._local_skills['{} {}'.format(user_id, item_id)] += self._wrong * (correct - prediction)


class Forgetting(Elo):

    def __init__(self, elo_alpha=0.8, elo_dynamic_alpha=0.05, correct=1.814, wrong=0.827):
        Elo.__init__(self, elo_alpha, elo_dynamic_alpha)
        self._correct = correct
        self._wrong = wrong
        self._staircase = {
            0: None,
            30: None,
            60: None,
            90: None,
            150: None,
            300: None,
            600: None,
            1800: None,
            10800: None,
            86400: None,
            259200: None,
            2592000: None,
            10 * 365 * 24 * 60 * 50: None,
        }

    def setup(self):
        Elo.setup(self)
        self._local_skills = defaultdict(ZERO)
        self._staircase = {k: None for k in self._staircase.keys()}

    def predict(self, user_id, item_id, time, guess, seconds_ago):
        if self.number_of_answers(user_id, item_id) == 0:
            return Elo.predict(self, user_id, item_id, time, guess, seconds_ago)
        user_id = str(user_id)
        item_id = str(item_id)
        activation = self._skills[user_id] - self._difficulties[item_id] + self._local_skills['{} {}'.format(user_id, item_id)]
        return _sigmoid(activation, guess=guess, shift_activation=self._get_shift(seconds_ago))

    def update(self, user_id, item_id, prediction, correct, time, guess, seconds_ago):
        user_id = str(user_id)
        item_id = str(item_id)
        if self.number_of_answers(user_id, item_id) == 0:
            Elo.update(self, user_id, item_id, prediction, correct, time, guess, seconds_ago)
        else:
            activation = self._skills[user_id] - self._difficulties[item_id] + self._local_skills['{} {}'.format(user_id, item_id)]
            self._update_shift(seconds_ago, logit(correct, guess=guess) - activation)
            if correct:
                self._local_skills['{} {}'.format(user_id, item_id)] += self._correct * (correct - prediction)
            else:
                self._local_skills['{} {}'.format(user_id, item_id)] += self._wrong * (correct - prediction)

    def _update_shift(self, seconds_ago, diff):
        seconds_ago = max(0.01, min(10 * 365 * 24 * 60 * 50 - 1, seconds_ago))
        lower = max([mod for mod in self._staircase.keys() if mod <= seconds_ago])
        upper = min([mod for mod in self._staircase.keys() if mod > seconds_ago])
        seconds_ago_log = numpy.log(seconds_ago)
        lower_log = numpy.log(lower) if lower > 1 else 0
        upper_log = numpy.log(upper)
        distance = (seconds_ago_log - lower_log) / (upper_log - lower_log)
        stored_lower = self._staircase[lower]
        stored_upper = self._staircase[upper]
        if stored_lower is None:
            stored_lower = (0, 0)
        if stored_upper is None:
            stored_upper = (0, 0)
        self._staircase[lower] = (stored_lower[0] + diff * (1 - distance), stored_lower[1] + 1 - distance)
        self._staircase[upper] = (stored_upper[0] + diff * distance, stored_upper[1] + distance)

    def _get_shift(self, seconds_ago):
        seconds_ago = max(0.01, min(10 * 365 * 24 * 60 * 50 - 1, seconds_ago))
        lower = max([mod for mod in self._staircase.keys() if mod <= seconds_ago])
        upper = min([mod for mod in self._staircase.keys() if mod > seconds_ago])
        seconds_ago_log = numpy.log(seconds_ago)
        lower_log = numpy.log(lower) if lower > 1 else 0
        upper_log = numpy.log(upper)
        distance = (seconds_ago_log - lower_log) / (upper_log - lower_log)
        stored_lower = self._staircase[lower]
        stored_upper = self._staircase[upper]
        if stored_lower is None:
            stored_lower = (0, 0)
        if stored_upper is None:
            stored_upper = (0, 0)
        return numpy.round(
            (1 - distance) * (0 if stored_lower[1] == 0 else stored_lower[0] / stored_lower[1])
            +
            distance * (0 if stored_upper[1] == 0 else stored_upper[0] / stored_upper[1]),
            4)


def _sigmoid(x, guess=0, shift_prob=0, shift_activation=0):
    result = guess + (1 - guess) * (1.0 / (1 + math.exp(-x - shift_activation)) + shift_prob)
    return result


def logit(p, guess=0):
    p = max(0.01, min(p, 0.99))
    result = numpy.log(p * (1 - guess)) - numpy.log(1 - p * (1 - guess))
    return result
