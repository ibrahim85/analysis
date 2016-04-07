import spiderpig.config


def get_argument_parser():
    p = spiderpig.config.get_argument_parser()

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
    return p
