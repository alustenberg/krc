#!/usr/bin/env python3
import krpc
import click

@click.command()
@click.option('--open/--close', 'openClose', default=True)
@click.option('--type','-t','types',multiple=True)

def run(openClose,types):
    conn = krpc.connect()
    vessel = conn.space_center.active_vessel

    for panel in vessel.parts.solar_panels:
        print(panel.part.title,panel.part.name,types,panel.part.name in types)
        if len(types) and panel.part.name not in types:
            continue
        if panel.deployable:
            panel.deployed = openClose

if __name__ == '__main__':
    run()
