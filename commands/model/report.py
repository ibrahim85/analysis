from .evaluate import train, test_brier
import matplotlib.pyplot as plt
import numpy as np
import output


def init_parser(parser):
    parser.add_argument(
        '--model_name',
        dest='model_name',
        action='store',
        required=True
    )
    parser.add_argument(
        '--param',
        dest='model_params',
        action='append',
        default=[]
    )
    return parser


def brier_graphs(model_name, model_params):
    model = train(model_name, model_params)[0]
    brier = test_brier(model)
    plt.figure()
    plt.plot(brier['detail']['bin_prediction_means'], brier['detail']['bin_correct_means'])
    plt.plot((0, 1), (0, 1))

    bin_count = brier['detail']['bin_count']
    counts = np.array(brier['detail']['bin_counts'])
    bins = (np.arange(bin_count) + 0.5) / bin_count
    plt.bar(bins, counts / max(counts), width=(0.5 / bin_count), alpha=0.5)
    plt.title(model.__class__.__name__)

    output.savefig('brier_detail')


def plot_grid_search(model_name):
    pass


def execute(model_name, model_params):
    pass_model_params = {p.split(':')[0]: float(p.split(':')[1]) for p in model_params}
    brier_graphs(model_name, pass_model_params)
