from commands.ab.success import plot_error_by_attempt
from pylab import rcParams
import output


def execute():
    rcParams['figure.figsize'] = 7.5, 4
    plot_error_by_attempt(100, with_confidence=True)
    output.savefig('abexp_error_by_attempt')
