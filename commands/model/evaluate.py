from .models import Model
from .raw import load_test_set, load_train_set
from copy import deepcopy
from data import iterdicts
from itertools import product
from spiderpig import spiderpig
import math
import numpy
import pandas


def run(model, data):
    model.setup()
    predictions = []
    for row in iterdicts(data):
        prediction = model.predict(
            row['user'], row['item_asked'], row['time'], row['guess'], row['seconds_ago'])
        model.update(
            row['user'], row['item_asked'], prediction,
            row['item_asked'] == row['item_answered'],
            row['time'],
            row['guess'],
            row['seconds_ago'])
        predictions.append(prediction)
    return model, pandas.Series(predictions, index=data.index)


@spiderpig()
def grid_search(model_name, pass_kwargs, optimize_kwargs, metric=None):
    if metric is None:
        metric = rmse
    result = []
    pass_kwargs = deepcopy(pass_kwargs)
    for p in _param_grid(optimize_kwargs):
        pass_kwargs = deepcopy(pass_kwargs)
        pass_kwargs.update(p)
        row = deepcopy(pass_kwargs)
        _, metric_value = train_with_metric(model_name, metric=metric, kwargs=pass_kwargs)
        row['metric'] = metric_value
        result.append(row)
    return pandas.DataFrame(result)


@spiderpig()
def train(model_name, kwargs=None):
    data = load_train_set()
    if kwargs is None:
        kwargs = {}
    return run(Model.from_name(model_name, **kwargs), data)


@spiderpig()
def train_with_metric(model_name, metric=None, kwargs=None):
    if metric is None:
        metric = rmse
    if kwargs is None:
        kwargs = {}
    data = load_train_set()
    model, predictions = run(Model.from_name(model_name, **kwargs), data)
    real = data['item_asked'] == data['item_answered']
    return model, metric(predictions, real)


@spiderpig()
def test(model):
    model = deepcopy(model)
    data = load_test_set()
    return run(model, data)[1]


def rmse(predictions, real):
    return math.sqrt(numpy.mean((predictions - real) ** 2))


def brier(predictions, real, bins=20):
    counts = numpy.zeros(bins)
    correct = numpy.zeros(bins)
    prediction = numpy.zeros(bins)
    for p, r in zip(predictions, real):
        bin = min(int(p * bins), bins - 1)
        counts[bin] += 1
        correct[bin] += r
        prediction[bin] += p
    prediction_means = prediction / counts
    prediction_means[numpy.isnan(prediction_means)] = ((numpy.arange(bins) + 0.5) / bins)[numpy.isnan(prediction_means)]
    correct_means = correct / counts
    correct_means[numpy.isnan(correct_means)] = 0
    size = len(predictions)
    answer_mean = sum(correct) / size
    return {
        "reliability": sum(counts * (correct_means - prediction_means) ** 2) / size,
        "resolution": sum(counts * (correct_means - answer_mean) ** 2) / size,
        "uncertainty": answer_mean * (1 - answer_mean),
        "detail": {
            "bin_count": bins,
            "bin_counts": list(counts),
            "bin_prediction_means": list(prediction_means),
            "bin_correct_means": list(correct_means),
        }
    }


def time_calibration(predictions, real, seconds_ago, bins=20):
    thresholds = [60, 90, 150, 300, 600, 1800, 10800, 86400, 259200, 2592000, 100000000]
    data = predictions.to_frame('predictions')
    data['real'] = real
    data['seconds_ago'] = seconds_ago
    bins = []
    for t in thresholds:
        t_data = data[data['seconds_ago'] <= t]
        bins.append((t_data['real'] - t_data['predictions']).mean())
    return bins


@spiderpig()
def test_rmse(model):
    data = load_test_set()
    predictions = test(model)
    return rmse(predictions, data['item_asked'] == data['item_answered'])


@spiderpig()
def test_time_calibration(model):
    data = load_test_set()
    predictions = test(model)
    return time_calibration(predictions, data['item_asked'] == data['item_answered'], data['seconds_ago'])


@spiderpig()
def test_brier(model):
    data = load_test_set()
    predictions = test(model)
    return brier(predictions, data['item_asked'] == data['item_answered'])


def _param_grid(params):
    items = sorted(params.items())
    if not items:
        yield {}
    else:
        keys, values = zip(*items)
        for v in product(*values):
            params = dict(zip(keys, v))
            yield params
