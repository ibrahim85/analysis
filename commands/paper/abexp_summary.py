from commands.ab.raw import load_answers
from commands.ab.summary import plot_summary
import output


def execute(title=None):
    answers = load_answers()
    print('Number of answers:', len(answers))
    print('Running from:', answers['time'].min())
    print('Running to:', answers['time'].max())
    plot_summary(title=title)
    output.savefig('abexp_summary', tight_layout=False)
