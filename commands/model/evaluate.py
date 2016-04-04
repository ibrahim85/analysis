from .models import Model
from .raw import load_test_set, load_train_set
from data import iterdicts
from spiderpig import spiderpig
import pandas


def run(model, data):
    model.setup()
    predictions = []
    for row in iterdicts(data):
        prediction = model.predict(
            row['user_id'], row['item_asked_id'], row['time'], row['guess'])
        model.update(
            row['user_id'], row['item_asked_id'], prediction,
            row['item_asked_id'] == row['item_answered_id'])
        predictions.append(prediction)
    return model, pandas.Series(predictions, index=data.index)


@spiderpig()
def train(model_name=None, **kwargs):
    data = load_train_set()
    return run(Model.from_name(model_name), data)[0]


@spiderpig()
def test(model):
    data = load_test_set()
    return run(model, data)[1]
