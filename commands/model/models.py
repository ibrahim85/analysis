from collections import defaultdict
import abc
import math
import pandas.tslib


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
    def predict(self, user_id, item_id, time, guess):
        pass

    @abc.abstractmethod
    def update(self, user_id, item_id, prediction, correct, time):
        pass


class ItemAverage(Model):

    def __init__(self, init_prediction=0.5):
        self._init_prediction = init_prediction

    def setup(self):
        self._corrects = defaultdict(ZERO)
        self._counts = defaultdict(ZERO)

    @abc.abstractmethod
    def predict(self, user_id, item_id, time, guess):
        return self._corrects[item_id] / self._counts[item_id] if self._counts[item_id] > 0 else self._init_prediction

    @abc.abstractmethod
    def update(self, user_id, item_id, prediction, correct, time):
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

    def predict(self, user_id, item_id, time, guess):
        user_id = str(user_id)
        item_id = str(item_id)
        return _sigmoid(self._skills[user_id] - self._difficulties[item_id], guess)

    def update(self, user_id, item_id, prediction, correct, time):
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
        self._last_times = defaultdict(ZERO_TIME)

    def predict(self, user_id, item_id, time, guess):
        if self.number_of_answers(user_id, item_id) == 0:
            return Elo.predict(self, user_id, item_id, time, guess)
        user_id = str(user_id)
        item_id = str(item_id)
        seconds_ago = (time - pandas.tslib.Timestamp(self._last_times['{} {}'.format(user_id, item_id)])).total_seconds()
        return _sigmoid(
            self._local_skills[user_id] -
            self._difficulties[item_id] +
            self._local_skills['{} {}'.format(user_id, item_id)] +
            self._time_shift / max(seconds_ago, 0.001),
            guess
        )

    def update(self, user_id, item_id, prediction, correct, time):
        user_id = str(user_id)
        item_id = str(item_id)
        self._last_times['{} {}'.format(user_id, item_id)] = str(time)
        if self.number_of_answers(user_id, item_id) == 0:
            Elo.update(self, user_id, item_id, prediction, correct, time)
        elif correct:
            self._local_skills['{} {}'.format(user_id, item_id)] += self._correct * (correct - prediction)
        else:
            self._local_skills['{} {}'.format(user_id, item_id)] += self._wrong * (correct - prediction)


def _sigmoid(x, guess=0):
    return guess + (1 - guess) * (1.0 / (1 + math.exp(-x)))
