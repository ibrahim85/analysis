from commands.all.raw import load_misanswers, load_flashcards
from .raw import load_context
from .svg import Context


def save_context(context, name, term):
    context.to_file('output/{}_misanswers_{}.svg'.format(name, term))


def execute(context_id):
    misanswers = load_misanswers()
    flashcards = load_flashcards()
    context_data = load_context(context_id)
    for term_id in flashcards['term_id'][flashcards['context_id'] == context_id].values:
        try:
            context = Context(context_data, flashcards)
            context.set_misanswers(term_id, misanswers)
            save_context(context, context_id, term_id)
        except:
            pass
