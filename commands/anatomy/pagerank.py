from commands.all.raw import load_flashcards
from .raw import load_context
from .svg import Context
from radiopaedia.graph import load_stats
import pandas


def save_context(context, name):
    context.to_file('output/{}_pagerank.svg'.format(name))


def execute(context_id):
    flashcards = load_flashcards()
    stats = load_stats(category='anatomy').rename(columns={'pagerank': 'value'})
    flashcards['term_name_canonical'] = flashcards['term_name'].apply(lambda n: n.lower() if isinstance(n, str) else None)
    stats['term_name_canonical'] = stats['name'].apply(lambda n: n.lower())
    to_plot = pandas.merge(flashcards, stats, how='inner', on='term_name_canonical')[['item', 'value']]
    context_data = load_context(context_id)
    context = Context(context_data, flashcards)
    context.set_number_colors(to_plot)
    save_context(context, context_data['id'])
