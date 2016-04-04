from .evaluate import train


def rmse(model_name):
    train(model_name)


def execute(model_name):
    rmse(model_name)
