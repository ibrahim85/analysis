from commands.all.raw import load_flashcards, load_answers
from .raw import load_context
from .svg import Context


def save_context(context, name):
    context.to_file('output/{}_answers.svg'.format(name))


def execute(context_id):
    flashcards = load_flashcards()
    answers = load_answers()
    context_data = load_context(context_id)
    context = Context(context_data, flashcards)
    context.set_answers(answers)
    save_context(context, context_data['id'])
