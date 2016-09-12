from commands.all.raw import load_answers
import matplotlib.pyplot as plt
import numpy
import output


def execute(n=10):
    context_answers = load_answers().groupby('context_name_asked').apply(len)
    context_answers.sort_values(ascending=False, inplace=True)
    context_answers = context_answers.reset_index().rename(columns={0: 'answers'}).head(n=n)
    ticks = numpy.array(range(len(context_answers)))[::-1]
    plt.barh(ticks, context_answers['answers'])
    plt.yticks(ticks + 0.4, context_answers['context_name_asked'])
    plt.xticks([0, max(plt.xticks()[0])], [0, int(max(plt.xticks()[0]))])
    plt.xlabel('Number of answers')
    plt.title('Top {} contexts'.format(n))
    output.savefig('answers_per_context')
