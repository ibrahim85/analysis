from .raw import load_term_id_mapping
from commands.all.raw import load_flashcards
import pandas


def execute(output_dir='output'):
    mapping = load_term_id_mapping()
    flashcards = load_flashcards()

    def _aggr(group):
        return pandas.DataFrame([{
            'firs_time_success_prob_avg': group['difficulty_prob'].mean(),
        }])
    terms = flashcards.groupby(['term_name', 'term_id']).apply(_aggr).reset_index().drop('level_2', 1)
    pandas.merge(mapping, terms[['term_id', 'first_time_success_prob_avg']].rename(columns={'term_id': 'anatom_id'}), how='inner', on='anatom_id').to_csv('{}/terms_mapping.csv'.format(output_dir), index=False)
