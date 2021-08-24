# Copyright © 2013-2021 Jakub Wilk <jwilk@jwilk.net>
# SPDX-License-Identifier: MIT

import os
import sys

def fatal(message):
    prog = os.path.basename(sys.argv[0])
    print(
        f'{prog}: error: {message}',
        file=sys.stderr
    )
    sys.exit(1)

# vim:ts=4 sts=4 sw=4 et
