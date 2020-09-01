"""
Module that contains the command line app.

Why does this file exist, and why not put this in __main__?

  You might be tempted to import things from __main__ later, but that will cause
  problems: the code will get executed twice:

  - When you run `python -mwsma_cryostat_selector` python will execute
    ``__main__.py`` as a script. That means there won't be any
    ``wsma_cryostat_selector.__main__`` in ``sys.modules``.
  - When you import __main__ it will get executed again (as a module) because
    there's no ``wsma_cryostat_selector.__main__`` in ``sys.modules``.

  Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""
import argparse

ip_default = '192.168.42.100'

parser = argparse.ArgumentParser(prog='selector', description='Cryostat selector wheel control.')
parser.add_argument('-a', '--address', default=ip_default, help="The IP address of the selector wheel controller. "
                                                                "Defaults to {:s}.".format(ip_default))
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-0', '--home', action="store_true", help="Home the selector wheel. Position and speed arguments "
                                                             "are ignored and the wheel will go to position 1.")
pos_group = group.add_argument_group(title="movement", description="Move the selector wheel to a position.")
pos_group.add_argument('position', metavar='position', type=int, choices=[1, 2, 3, 4],
                       help="The selector wheel position to move to.")
pos_group.add_argument('-s', '--speed', metavar="SPEED", default=1, type=int, choices=[1, 2, 3],
                       help="The speed to move at. Defaults to 1")


def main(args=None):
    args = parser.parse_args(args=args)
    print(args.names)
