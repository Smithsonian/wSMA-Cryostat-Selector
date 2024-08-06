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
import os
import argparse
import wsma_cryostat_selector

default_ip = '192.168.42.100'

if "WSMASELECTOR" in os.environ:
    default_ip = os.environ['WSMASELECTOR']

parser = argparse.ArgumentParser(description="Move the selector wheel to given position, "
                                             "or print current position.")

parser.add_argument("-v", "--verbosity", action="store_true",
                    help="Display detailed output from controller")
parser.add_argument("-p", "--pos", action="store_true",
                    help="Display the wheel positions.")
parser.add_argument("-r", "--resolver", action="store_true",
                    help="Display detailed output from resolver")
parser.add_argument("-a", "--address", default=default_ip,
                    help="The IP address of the controller")
parser.add_argument("-0", "--home", action="store_true",
                    help="Home the Selector Wheel. "
                         "Will move to position 1 after completion of homing operation "
                         "and then to requested position if given.")
parser.add_argument("-s", "--speed", type=int, choices=[1,2,3],
                    help="Set the speed to move at. "
                         "Does not affect the speed of homing operations.")
parser.add_argument("-t", "--tolerance", type=float,
                    help="Set the angular position tolerance for the wheel in degrees")
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

    sel.update_all()

    if args.tolerance:
        print(f"Setting angle tolerance to {args.tolerance:.2f} degrees")
        sel.set_angle_tolerance(args.tolerance)

    if args.home:
        print("Homing selector.")
        speed = sel.speed
        sel.home()
        if args.verbosity:
            print("Homing complete.")
        sel.set_speed(speed)

    if args.speed:
        if args.verbosity:
            print(f"Setting speed to {args.speed}")
        sel.set_speed(args.speed)

    if args.position:
        print(f"Moving to position {args.position}")
        sel.set_position(args.position)
        if args.verbosity:
            print("Done")
    else:
        print(f"Current selector position : {sel.position}")

    if args.verbosity:
        print(f"Time for last move        : {sel.time} ms")
        print(f"Selector speed setting    : {sel.speed}")
        print(f"Selector angle            : {sel.angle:.3f} deg")
        print(f"Selector angle error      : {sel.angle_error:.3f} deg")
        print(f"Selector angle tolerance  : {sel.angle_tolerance:.3f}")
        
    if args.pos:
        print(f"Position 1 location : {sel.pos_1:d}")
        print(f"Position 2 location : {sel.pos_2:d}")
        print(f"Position 3 location : {sel.pos_3:d}")
        print(f"Position 4 location : {sel.pos_4:d}")
        
    if args.resolver:
        print(f"Resolver turns count      : {sel.resolver_turns}")
        print(f"Resolver position         : {sel.resolver_position}")
        
        