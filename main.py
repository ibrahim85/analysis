#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

import commands.all
import commands.ab
import commands.model
import commands.importance
import output
from spiderpig import run_spiderpig
from config import get_argument_parser


if __name__ == '__main__':
    run_spiderpig(
        namespaced_command_packages={
            'ab': commands.ab,
            'all': commands.all,
            'model': commands.model,
            'imp': commands.importance,
        },
        argument_parser=get_argument_parser(),
        setup_functions=[output.init_plotting]
    )
