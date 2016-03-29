#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

import commands
import output
from spiderpig import run_spiderpig
from config import get_argument_parser


if __name__ == '__main__':
    run_spiderpig(
        [commands],
        argument_parser=get_argument_parser(),
        setup_functions=[output.init_palette]
    )
