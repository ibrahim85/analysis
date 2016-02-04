from spiderpig import spiderpig
from spiderpig import msg
import os.path
import matplotlib.pyplot as plt


@spiderpig(cached=False)
def savefig(filename, output_dir, figure_extension):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    plt.tight_layout()
    filename = '{}/{}.{}'.format(output_dir, filename, figure_extension)
    plt.savefig(filename)
    msg.success(filename)
