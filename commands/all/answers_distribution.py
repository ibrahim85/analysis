from .raw import load_answers
import output
import matplotlib.pyplot as plt


def execute():
    nums = list(sorted(load_answers().groupby('item_asked').apply(len).to_dict().values(), key=lambda x: -x))
    plt.plot(nums)
    plt.xlabel('Item (sorted according to the number of answers)')
    plt.ylabel('Number of answers')
    plt.title('Distribution of answers')
    output.savefig('answers_distribition')
