#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

import commands
from spiderpig import run_spiderpig
from config import get_argument_parser


if __name__ == '__main__':
    run_spiderpig([commands], argument_parser=get_argument_parser())
