#!/usr/bin/env python3
import krpc
import click

from util import mission

@click.command()
@click.option('--alt', default=35, help='final orbit alt (km)')

def run(alt):
    mission().setPeriapsis(periapsis=alt)


if __name__ == '__main__':
    run()


