from .raw import load_search_results, load_terms
import pandas
import matplotlib.pyplot as plt
import output
import numpy


def execute(n=100, bins=10):
    data = pandas.merge(load_terms(), load_search_results(n=n), on=['identifier'], how='inner')
    print(data['answers'])
    data.to_csv('./anatomy-terms.csv', index=False)
    data['search_results_bin'] = pandas.to_numeric(pandas.cut(
        data['search_results'],
        bins=numpy.percentile(data['search_results'], numpy.linspace(0, 100, bins + 1)),
        labels=list(range(1, bins + 1))
    ))
    data.plot(kind='scatter', x='search_results', y='difficulty_prob')
    plt.ylim(0, 1)
    # plt.xlim(0, bins + 1)
    output.savefig('importance')
