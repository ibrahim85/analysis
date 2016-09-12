from commands.all.raw import load_flashcards
from .raw import load_context
from .svg import Context


def save_context(context, name):
    context.to_file('output/{}_difficulty.svg'.format(name))


def execute(context_id):
    flashcards = load_flashcards()
    context_data = load_context(context_id)
    context = Context(context_data, flashcards)
    context.set_difficulty()
    save_context(context, context_data['id'])
