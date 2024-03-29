# Copyright © 2012-2022 Jakub Wilk <jwilk@jwilk.net>
# SPDX-License-Identifier: MIT

'''
Generate one or more passwords.

The passwords use ASCII letters (a-z, A-Z) and digits (0-9).
That is, they have
   lg (26 + 26 + 10) = 5.95
bits of entropy per character.
'''

import argparse
import math
import secrets
import string

alphabet = string.ascii_letters + string.digits

def add_arg_parser(subparsers):
    ap = subparsers.add_parser('generate',
        help='generate passwords',
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    class set_bits(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            length = values * math.log(2, len(alphabet))
            namespace.length = int(math.ceil(length))
    ap.add_argument('--length', default=16, type=int, help='password length (default: 16)')
    ap.add_argument('--bits', type=int, help='password entropy', action=set_bits)
    ap.add_argument('count', metavar='COUNT', nargs='?', type=int, help='number of passwords to generate')
    return ap

def run(options):
    if options.count is None:
        options.count = 1
    limit = len(alphabet) ** options.length
    for i in range(options.count):
        bigint = secrets.randbelow(limit)
        password = [None] * options.length
        for j in range(options.length):
            bigint, password[j] = divmod(bigint, len(alphabet))
        assert bigint == 0
        password = str.join('', (alphabet[ch] for ch in password))
        print(password)

__all__ = [
    'add_arg_parser',
    'run'
]

# vim:ts=4 sts=4 sw=4 et
