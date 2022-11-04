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
import wsma_cryostat_selector

default_ip = '192.168.42.100'

parser = argparse.ArgumentParser(description="Move the selector wheel to given position, "
                                             "or print current position.")

parser.add_argument("-v", "--verbosity", action="store_true",
                    help="Display detailed output from controller")
parser.add_argument("-a", "--address", default=default_ip,
                    help="The IP address of the controller")
parser.add_argument("-0", "--home", action="store_true",
                    help="Home the Selector Wheel. "
                         "Will move to position 1 after completion of homing operation "
                         "and then to requested position if given.")
parser.add_argument("-s", "--speed", type=int, choices=[1,2,3],
                    help="Speed to move at. "
                         "Does not affect the speed of homing operations.")
parser.add_argument("position", type=int, choices=[1,2,3,4], nargs="?",
                    help="The wheel position to move to.")

def main(args=None):
    args = parser.parse_args(args=args)

    # Create the selector wheel object for communication with the controller
    # If address is 0.0.0.0, create a dummy selector for testing purposes.
    if args.address=="0.0.0.0":
        sel = wsma_cryostat_selector.DummySelector()
    else:
        sel = wsma_cryostat_selector.Selector(ip_address=args.address)

    if args.home:
        print("Homing selector.")
        speed = sel.speed
        sel.home()
        if args.verbosity:
            print("Homing complete.")
        sel.set_speed(speed)

    if args.speed:
        if args.verbosity:
            print("Setting speed to {}".format(args.speed))
        sel.set_speed(args.speed)

    if args.position:
        print("Moving to position {}".format(args.position))
        sel.set_position(args.position)
        if args.verbosity:
            print("Done")
    else:
        print("Current selector position : {}".format(sel.position))

    if args.verbosity:
        print("Selector speed setting    : {}".format(sel.speed))
        print("Selector position error   : {:.2f} deg".format(sel.delta))
        print("Time for last move        : {} ms".format(sel.time))
