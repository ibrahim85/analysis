from commands.all.raw import load_flashcards, load_answers
from .raw import load_context, load_search_results
from .svg import Context


def save_context(context, name):
    context.to_file('output/{}_search_results.svg'.format(name))


def execute(context_id):
    flashcards = load_flashcards()
    search_results = load_search_results()
    context_data = load_context(context_id)
    context = Context(context_data, flashcards)
    context.set_search_results(search_results)
    save_context(context, context_data['id'])
