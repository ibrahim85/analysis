from spiderpig import spiderpig
from spiderpig import msg
from threading import RLock
import os.path
import matplotlib.pyplot as plt
import seaborn as sns


sns.set_style(style='white')
_SNS_PALETTE = None
_LOCK = RLock()


def palette():
    global _SNS_PALETTE
    if _SNS_PALETTE is None:
        raise Exception("The palette is not initialized!")
    return _SNS_PALETTE


def init_palette(palette=None, palette_name=None):
    with _LOCK:
        global _SNS_PALETTE
        if palette is None and palette_name is None:
            _SNS_PALETTE = sns.color_palette()
            return
        if palette is not None and palette_name is not None:
            raise Exception('Both palette itself or palette name can not be given.')
        if palette is not None:
            _SNS_PALETTE = palette
        else:
            _SNS_PALETTE = sns.color_palette(palette_name)
        sns.set_palette(_SNS_PALETTE)


@spiderpig(cached=False)
def savefig(filename, output_dir, figure_extension):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    plt.tight_layout()
    filename = '{}/{}.{}'.format(output_dir, filename, figure_extension)
    plt.savefig(filename)
    msg.success(filename)
