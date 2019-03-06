#!/usr/bin/env python3
import krpc
import click
from util import mission

@click.command()
@click.option('--alt',  type=int, default=80, help='final orbit alt (km)')
@click.option('--inc',  type=int, default=0, help='final orbit inclination (deg)')
@click.option('--stage',type=int, default=0, help='boost stage')
@click.option('--wait', type=float, default=0, help='launch window time mod, in hours. 6 is "midnight" daily')
@click.option('--max',  type=float, default=4, help='max g after mach limit')
@click.option('--skip', is_flag=True, help='skip exec of circ burn')


def run(**kwargs):
    m = mission()
    m.launch(
        altitude = kwargs['alt'],
        boostStage = kwargs['stage'],
        inclination = kwargs['inc'],
        waitForWindow = int(3600.0 * kwargs['wait']),
        circ = not kwargs['skip'],
        limitThrust = 9.8 * kwargs['max'],
    )

if __name__ == '__main__':
    run()


