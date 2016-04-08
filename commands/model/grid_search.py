from .evaluate import grid_search, train, test_brier
import matplotlib.pyplot as plt
import numpy as np
import output
import seaborn as sns
import spiderpig.msg as msg


def init_parser(parser):
    parser.add_argument(
        '--model_name',
        dest='model_name',
        action='store',
        required=True
    )
    parser.add_argument(
        '--grid-search-param',
        dest='grid_search_params',
        action='append',
        default=[]
    )
    parser.add_argument(
        '--model-param',
        dest='model_params',
        action='append',
        default=[]
    )
    parser.add_argument(
        '--plot-param',
        dest='plot_params',
        action='append',
        default=[]
    )
    return parser


def brier_graphs(model_name):
    model = train(model_name)[0]
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


def plot_grid_search(model_name, model_params, grid_search_params, plot_params):
    grid_search_result = grid_search(model_name, model_params, grid_search_params)
    print(grid_search_result)
    if len(plot_params) == 0:
        plot_params = grid_search_params
    if len(plot_params) != 2:
        msg.error("Can't plot grid search result, because there are {} parameters to plot (2 required).".format(len(plot_params)))
        return
    to_plot = grid_search_result.pivot(*plot_params)['metric']
    to_plot.sort_index(ascending=False, inplace=True)
    sns.heatmap(to_plot)
    plt.title(model_name)
    output.savefig('grid_search')


def execute(model_name, grid_search_params, model_params, plot_params):
    pass_model_params = {p.split(':')[0]: float(p.split(':')[1]) for p in model_params}
    pass_grid_search_params = {
        p[0]: [float(x) for x in np.arange(float(p[1]), float(p[2]) + 0.0000001, float(p[3]))]
        for p in [p.split(':') for p in grid_search_params]
    }
    plot_grid_search(model_name, pass_model_params, pass_grid_search_params, plot_params)
