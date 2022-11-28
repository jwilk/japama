# Copyright © 2012-2022 Jakub Wilk <jwilk@jwilk.net>
# SPDX-License-Identifier: MIT

'''
Show selected password(s).

Configuration is read from <$XDG_DATA_HOME/japama/secrets.gpg>,
an OpenPGP-encrypted file in the following format:

   [https://github.com/]
   user = jwilk
   password = PnlUbPkPtqZvy2Po
   # optional for TOTP (RFC 6238) support:
   totp-secret = wxq3cgfxn77x7g7k

   ...

'''

import argparse
import configparser
import io
import subprocess as ipc

import lib.cli
import lib.conf

def add_arg_parser(subparsers):
    ap = subparsers.add_parser('show',
        help='show selected password(s)',
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ag = ap.add_mutually_exclusive_group()
    ag.add_argument('-x', '--x-selection',
        dest='x_selection', action='store_const', const='primary',
        help='copy the password to X primary selection'
    )
    ag.add_argument('--x-clipboard',
        dest='x_selection', action='store_const', const='clipboard',
        help='copy the password to X clipboard'
    )
    ag = ap.add_mutually_exclusive_group()
    ag.add_argument('--omit', action='store_true', help='omit passwords')
    ag.add_argument('--pick', metavar='N[,N...]', help='pick only some characters')
    ag.add_argument('--robot', action='store_true', help='use machine-readable output')
    ap.add_argument('keyword', metavar='KEYWORD')
    return ap

def parse_pick(s):
    if s is None:
        return str
    lst = []
    for item in s.split(','):
        if '-' in item:
            l, r = (int(x) for x in item.split('-', 1))
        else:
            l = r = int(item)
        if l < 1:
            raise IndexError(f'index should be a positive integer: {l}')
        if l > r:
            raise IndexError(f'empty range: {l} > {r}')
        lst += range(l - 1, r)
    def pick_fn(p):
        return str.join('', (p[i] for i in lst))
    return pick_fn

def run_xclip(x_selection, content):
    if isinstance(content, str):
        content = content.encode('ASCII')
    cmdline = ['xclip', '-selection', x_selection, '-l', '1', '-verbose']
    xclip = ipc.Popen(cmdline,
        stdin=ipc.PIPE,
        stderr=ipc.DEVNULL,
    )
    xclip.communicate(content)
    if xclip.wait() != 0:
        lib.cli.fatal('xclip failed')

def get_totp(secret):
    import pyotp.totp
    totp = pyotp.totp.TOTP(secret)
    return totp.now()

def run(options):
    try:
        pick_filter = parse_pick(options.pick)
    except (IndexError, ValueError) as exc:
        lib.cli.fatal(f'cannot parse --pick argument: {exc}')
    with open(lib.conf.path, 'rb') as fp:
        gpg = ipc.Popen(['gpg', '-q', '-d'], stdin=fp, stdout=ipc.PIPE)
    cp = configparser.RawConfigParser()
    with io.TextIOWrapper(gpg.stdout, encoding='UTF-8') as fp:
        cp.read_file(fp)
    if gpg.wait() != 0:
        lib.cli.fatal('gpg failed')
    gpg.stdout.close()
    if options.robot:
        kwd = options.keyword
        try:
            item = cp[kwd]
        except KeyError:
            lib.cli.fatal(f'no such entry: {kwd!r}')
        try:
            password = item['password']
        except KeyError:
            lib.cli.fatal(f'no password for entry {kwd!r}')
        print(password)
        return
    omit_next = False
    password = None
    for site in cp.sections():
        item = cp[site]
        if options.keyword not in site:
            continue
        try:
            orig_password = password = item['password']
        except KeyError:
            continue
        password = pick_filter(password)
        user = item.get('user', '<none>')
        print('[', site, ']', sep='')
        print('user', '=', user)
        if options.omit:
            password = '<omitted>'
        x_selection = None
        if options.x_selection:
            x_selection = options.x_selection
            omit_next = True
            if x_selection == 'primary':
                x_selection += '-selection'
            password = f'<in-x-{x_selection}>'
        print('password', '=', password)
        if x_selection:
            run_xclip(x_selection, orig_password)
        totp_secret = item.get('totp-secret')
        if totp_secret:
            if options.omit:
                password = '<omitted>'
            else:
                password = orig_password = get_totp(totp_secret)
            if x_selection:
                password = f'<in-x-{x_selection}>'
            print('otp', '=', password)
            if x_selection:
                run_xclip(x_selection, orig_password)
                omit_next = True
        print()
        if omit_next:
            options.x_selection = None
            options.omit = True
    if password is None:
        lib.cli.fatal('no matching passwords')

__all__ = [
    'add_arg_parser',
    'run'
]

# vim:ts=4 sts=4 sw=4 et
