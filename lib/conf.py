# Copyright © 2018 Jakub Wilk <jwilk@jwilk.net>
# SPDX-License-Identifier: MIT

import os

xdg_data_home = os.environ.get('XDG_DATA_HOME') or ''
if not os.path.isabs(xdg_data_home):
    xdg_data_home = os.path.expanduser('~/.local/share')

path = os.path.join(xdg_data_home, 'japama', 'secrets.gpg')

__all__ = [
    'path',
]

# vim:ts=4 sts=4 sw=4 et
