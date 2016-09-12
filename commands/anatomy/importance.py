from .raw import load_search_results
from commands.all.raw import load_answers, load_flashcards
from spiderpig import spiderpig
from radiopaedia.graph import load_stats
import pandas
import output
import seaborn as sns


@spiderpig()
def load_terms(data_dir='data'):
    flashcards = load_flashcards()
    term_answers = load_answers().groupby('term_id_asked').apply(len).reset_index().rename(columns={'term_id_asked': 'term_id', 0: 'answers'})
    # print(flashcards.head())

    def _aggr(group):
        return pandas.DataFrame([{
            'difficulty': float(group['difficulty'].mean()),
            'difficulty_prob': group['difficulty_prob'].mean(),
        }])
    terms = flashcards.groupby(['term_name', 'term_id']).apply(_aggr).reset_index().drop('level_2', 1)
    terms = pandas.merge(terms, term_answers, how='left', on='term_id')
    return terms


@spiderpig()
def load_radiopaedia_terms():
    terms = load_terms()
    stats = load_stats(category='anatomy')
    terms['term_name_canonical'] = terms['term_name'].apply(lambda n: n.lower())
    stats['term_name_canonical'] = stats['name'].apply(lambda n: n.lower())
    result = pandas.merge(terms, stats, how='inner', on='term_name_canonical')[['term_id', 'term_name', 'pagerank', 'degree_in', 'degree_out']]
    return result


def execute(bins=10):
    data = pandas.merge(load_terms(), load_search_results().rename(columns={'identifier': 'term_id'}), on=['term_id'], how='inner')
    data = data[data['term_name'].apply(lambda x: len(x.split(';')[0]) > 5)]
    data = data[data['term_id'].apply(lambda x: x.startswith('A'))]
    data = pandas.merge(data, load_radiopaedia_terms(), on=['term_id', 'term_name'], how='inner')
    load_radiopaedia_terms()
    g = sns.pairplot(data, vars=['search_results_log', 'degree_in', 'pagerank', 'difficulty_prob'])
    print('TOP PAGERANK')
    print(data.sort_values(by='pagerank', ascending=False)[['term_name', 'degree_in', 'difficulty_prob']].tail(n=20))
    print()
    print('BOTTOM PAGERANK')
    print(data.sort_values(by='pagerank')[['term_name', 'degree_in', 'difficulty_prob']].tail(n=20))
    print()
    for ax in g.axes.flat:
        if ax.get_xlabel() in ['difficulty_prob', 'pagerank']:
            ax.set_xlim(0, 1)
        if ax.get_ylabel() in ['difficulty_prob', 'pagerank']:
            ax.set_ylim(0, 1)
        if min(ax.get_xticks()) < 0:
            ax.set_xlim(0, max(ax.get_xticks()))
        if min(ax.get_yticks()) < 0:
            ax.set_ylim(0, max(ax.get_yticks()))

    output.savefig('importance', tight_layout=False)
