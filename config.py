import spiderpig.config


def get_argument_parser():
    p = spiderpig.config.get_argument_parser()

    p.add_argument(
        '--school',
        action='store',
        dest='school',
        default=None,
        type=str2bool
    )
    p.add_argument(
        '--top-contexts',
        dest='top_contexts',
        default=None
    )

    p.add_argument(
        "-d",
        "--data",
        action="store",
        dest="data_dir",
        default='data'
    )
    p.add_argument(
        "--lang",
        action='store',
        dest='language',
        default='en'
    )
    p.add_argument(
        '-l',
        '--answer-limit',
        action='store',
        dest='answer_limit',
        default=1
    )
    p.add_argument(
        '-o',
        '--output',
        action='store',
        dest='output_dir',
        default='output'
    )
    p.add_argument(
        '-e',
        '--extension',
        action='store',
        dest='figure_extension',
        default='png'
    )
    p.add_argument(
        '-p',
        '--palette',
        dest='palette_name',
        action='store',
        default=None
    )
    p.add_argument(
        '--style',
        action='store',
        dest='style',
        default='white'
    )
    p.add_argument(
        '--font-scale',
        action='store',
        dest='font_scale',
        default=1.5
    )
    p.add_argument(
        '--context',
        type=str,
        dest='contexts',
        action='append'
    )
    p.add_argument(
        '--nrows',
        action='store',
        dest='nrows',
        default=None
    )
    p.add_argument(
        '--workers',
        action='store',
        dest='workers',
        default=1
    )
    p.add_argument(
        '--seed',
        action='store',
        default=None
    )
    p.add_argument(
        '--only-first',
        action='store_true',
        default=False,
        dest='only_first'
    )
    p.add_argument(
        '--setups',
        nargs='*',
        default=None,
        dest='setups'
    )
    p.add_argument(
        '--flashcards',
        default=None,
        dest='flashcards_file'
    )
    p.add_argument(
        '--group-setups',
        dest='group_setups',
        action='store',
        default=None,
        type=int
    )
    return p


def str2bool(x):
    return True if x.lower() == 'true' else False
