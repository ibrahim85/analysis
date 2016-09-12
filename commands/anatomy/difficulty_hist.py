from commands.all.raw import load_flashcards
import seaborn as sns
import matplotlib.pyplot as plt
import output
import numpy


def execute():
    flashcards = load_flashcards()
    contexts = list(list(zip(*sorted(flashcards.groupby('context_id').apply(len).to_dict().items(), key=lambda x: - x[1])))[0])[:20]
    flashcards = flashcards[flashcards['context_id'].isin(contexts)]
    g = sns.FacetGrid(flashcards, col="context_name", col_wrap=2, aspect=2)
    g.map(plt.hist, 'difficulty_prob', bins=numpy.linspace(0, 1, 11)).set_titles('{col_name}').set_xlabels('Prediction')
    for ax in g.axes.flat:
        if len(ax.get_title()) > 40:
            ax.set_title('{} ...'.format(ax.get_title()[:40]))
    output.savefig('difficulty_hist_per_context')
