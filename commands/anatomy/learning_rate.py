from spiderpig import spiderpig
from commands.all.raw import load_answers, load_flashcards
from .svg import Context
from .raw import load_context
import matplotlib.pyplot as plt
import output


@spiderpig()
def learning_rate(number_of_answers=1):
    answers = load_answers()

    def _apply(group):
        if len(group) <= 1:
            return None
        first = group.iloc[0]
        if first['item_asked'] == first['item_answered']:
            return None
        second = group.iloc[1]
        return second['item_asked'] == second['item_answered']

    nums = answers.sort_values('id').drop_duplicates(['user', 'item_asked']).groupby('item_asked').apply(lambda g: (g['item_asked'] != g['item_answered']).sum())
    nums = nums[nums > number_of_answers]
    answers = answers[answers['item_asked'].isin(set(nums.to_dict().keys()))]
    groupped = answers.sort_values(by=['id']).groupby(['user', 'item_asked']).apply(_apply)
    groupped = groupped[groupped.notnull()]
    return groupped.reset_index().groupby('item_asked').apply(lambda group: group[0].mean()).reset_index().rename(columns={0: 'learning_rate', 'item_asked': 'item'})


def plot_learning_rate(number_of_answers):
    rate = learning_rate(number_of_answers)
    plt.hist(rate['learning_rate'])
    plt.xlabel('Success rate on the 2nd answer when the first one is incorrect')
    plt.title('Learning rate')
    output.savefig('learning_rate_second_hist')


def save_context(context, name):
    context.to_file('output/{}_learning_rate.svg'.format(name))


def plot_context_learning_rate(context_id):
    rate = learning_rate(10)
    flashcards = load_flashcards()
    context_data = load_context(context_id)
    context = Context(context_data, flashcards)
    context.set_learning_rate(rate)
    save_context(context, context_data['id'])


def execute(context_id=None, number_of_answers=1):
    plot_learning_rate(number_of_answers)
    if context_id is not None:
        plot_context_learning_rate(context_id)
