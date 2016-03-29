from spiderpig import spiderpig
from spiderpig import msg
from threading import RLock
import os.path
import matplotlib.pyplot as plt
import seaborn as sns


_SNS_PALETTE = None
_LOCK = RLock()


def plot_line(data, color, with_confidence=True, **kwargs):
    plt.plot(
        range(1, len(data) + 1),
        [y['value'] for y in data],
        color=color, markersize=5, **kwargs
    )
    if with_confidence:
        plt.fill_between(
            range(1, len(data) + 1),
            [x['confidence_interval']['min'] for x in data],
            [x['confidence_interval']['max'] for x in data],
            color=color, alpha=0.35
        )
    plt.xlim(1, len(data))


def palette():
    global _SNS_PALETTE
    if _SNS_PALETTE is None:
        raise Exception("The palette is not initialized!")
    return _SNS_PALETTE


def init_plotting(palette=None, palette_name=None, font_scale=None, style='white'):
    with _LOCK:
        sns_kwargs = {'style': style}
        if font_scale is not None:
            sns_kwargs['font_scale'] = font_scale
        sns.set(**sns_kwargs)
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
