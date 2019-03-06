#!/usr/bin/env python3
import krpc
import click
from util import mission

@click.command()
@click.option('--name','-n','name')
@click.option('--target','-t','target')
@click.option('--periapsis','--low','-a','periapsis')
@click.option('--apopapsis','--high','-a','apop')
@click.option('--inclination','-i','inc')
@click.option('--time','inc',default='1m')

def run(name,target,periapsis,apop,inc):
    m = mission()
    vessel = m.vessel

    if name:
        vessel.name = name
        print('set vessel name "{}"'.format(vessel.name))

    if target:
        m.setTarget(target)


    if periapsis:
        m.setPeriapsis(float(periapsis))

    if apop:
        m.setApopapsis(float(periapsis))

if __name__ == '__main__':
    run()
