#!/usr/bin/env python3
import krpc
import click

@click.command()
@click.option('--start/--no-start', default=False)
@click.option('--stop/--no-stop', default=False)
@click.option('--nuke/--no-nuke', default=False)
@click.option('--all/--no-all', default=False)
@click.option('--stage', default=False)

def run(start,stop,nuke,all,stage):
    conn = krpc.connect()
    vessel = conn.space_center.active_vessel

    for engine in vessel.parts.engines:
        if not all and nuke != ( engine.part.name in ['nuclearEngine']):
            continue

        state = engine.active
        if stop and state:
            engine.active = False
        if start and not state:
            engine.active = True

        if state != engine.active:
            print(engine.part.name,state,engine.active)

if __name__ == '__main__':
    run()
