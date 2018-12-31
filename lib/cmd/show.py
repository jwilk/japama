# Copyright © 2012-2018 Jakub Wilk <jwilk@jwilk.net>
# SPDX-License-Identifier: MIT

'''
Show selected password(s).

Configuration is read from <$XDG_DATA_HOME/japama/secrets.gpg>,
an OpenPGP-encrypted file in the following format:

   [https://example.net/]
   user = j.r.hacker
   password = PnlUbPkPtqZvy2Po

   [https://example.org/]
   user = jrh
   password = cUUZ4oUXFv4Cs2A5

   ...

'''

import configparser
import io
import subprocess as ipc

import lib.cli
import lib.conf

def add_arg_parser(subparsers):
    ap = subparsers.add_parser('show', help='show selected password(s)', description=__doc__)
    ap.add_argument('--omit', action='store_true', help='omit passwords')
    ap.add_argument('--pick', metavar='N[,N...]', help='pick only some characters')
    group = ap.add_mutually_exclusive_group()
    group.add_argument('-x', '--x-selection',
        dest='x_selection', action='store_const', const='primary',
        help='copy the password X primary selection'
    )
    group.add_argument('--x-clipboard',
        dest='x_selection', action='store_const', const='clipboard',
        help='copy the password X clipboard'
    )
    ap.add_argument('--robot', action='store_true', help='use machine-readable output')
    ap.add_argument('keyword', metavar='KEYWORD')
    return ap

def parse_pick(s):
    if s is None:
        return str
    lst = []
    for item in s.split(','):
        if '-' in item:
            l, r = (int(x, 10) for x in item.split('-', 1))
        else:
            l = r = int(item, 10)
        if l < 1:
            raise IndexError('index should be a positive integer: {idx}'.format(idx=l))
        if l > r:
            raise IndexError('empty range: {l} > {r}'.format(l=l, r=r))
        lst += range(l - 1, r)
    def pick_fn(p):
        return ''.join(p[i] for i in lst)
    return pick_fn

def run(options):
    try:
        pick_filter = parse_pick(options.pick)
    except (IndexError, ValueError) as exc:
        lib.cli.fatal('cannot parse --pick argument: {exc}'.format(exc=exc))
    with open(lib.conf.path, 'rb') as fp:
        gpg = ipc.Popen(['gpg', '-q', '-d'], stdin=fp, stdout=ipc.PIPE)
    cp = configparser.RawConfigParser()
    with io.TextIOWrapper(gpg.stdout, encoding='UTF-8') as fp:
        cp.read_file(fp)
    if options.robot:
        item = cp[options.keyword]
        password = item['password']
        print(password)
        return
    for site in cp.sections():
        item = cp[site]
        if options.keyword not in site:
            continue
        try:
            password = item['password']
        except KeyError:
            continue
        password = pick_filter(password)
        user = item.get('user', '<none>')
        xclip = None
        if options.omit:
            password = '<omitted>'
        elif options.x_selection:
            x_selection = options.x_selection
            options.x_selection = None
            options.omit = True
            cmdline = ['xclip', '-selection', x_selection, '-l', '1', '-verbose']
            xclip = ipc.Popen(cmdline,
                stdin=ipc.PIPE,
                stderr=ipc.DEVNULL,
            )
            xclip.stdin.write(password.encode('ASCII'))
            xclip.stdin.close()
            if x_selection == 'primary':
                x_selection += '-selection'
            password = '<in-x-{sel}>'.format(sel=x_selection)
        print('{site} ({user}) {password}'.format(
            site=site, user=user, password=password)
        )
        if xclip is not None:
            if xclip.wait() != 0:
                lib.cli.fatal('xclip failed')
    if gpg.wait() != 0:
        lib.cli.cli.fatal('gpg failed')
    gpg.stdout.close()

__all__ = [
    'add_arg_parser',
    'run'
]

# vim:ts=4 sts=4 sw=4 et
