from collections import defaultdict
import abc


class Model:

    @staticmethod
    def from_name(model_name, *args, **kwargs):
        for model_class in Model.__subclasses__():
            if model_class.__name__ == model_name:
                return model_class(*args, **kwargs)
        raise Exception('There is no model with name {}.'.format(model_name))

    def setup(self):
        pass

    @abc.abstractmethod
    def predict(self, user_id, item_id, time, guess):
        pass

    @abc.abstractmethod
    def update(self, user_id, item_id, prediction, correct, guess):
        pass


class ItemAverage(Model):

    def __init__(self, init_prediction=0.5):
        self._init_prediction = init_prediction

    def setup(self):
        self._corrects = defaultdict(lambda: 0)
        self._counts = defaultdict(lambda: 0)

    @abc.abstractmethod
    def predict(self, user_id, item_id, time, guess):
        return self._corrects[item_id] / self._counts[item_id] if self._counts[item_id] > 0 else self._init_prediction

    @abc.abstractmethod
    def update(self, user_id, item_id, prediction, correct):
        self._counts[item_id] += 1
        self._corrects[item_id] += correct
