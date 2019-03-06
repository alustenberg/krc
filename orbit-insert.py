#!/usr/bin/env python3
import krpc
import click
from util import mission

@click.command()
@click.option('--alt', default=25, help='final orbit alt (km)')
@click.option('--inc',type=int, default=0, help='final orbit inclination (deg)')

def run(alt, inc):
    mission().orbitInsert(inclination=inc, alt=alt)


if __name__ == '__main__':
    run()
