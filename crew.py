#!/usr/bin/env python3
import krpc
import click
import time

@click.command()

def run():
    conn = krpc.connect()
    vessel = conn.space_center.active_vessel
    contracts = conn.space_center.contract_manager

    crew = {}
    for member in vessel.crew:
        crew[member.name] = member.type

    for member in sorted(crew.keys()):
        if type(crew[member]) == conn.space_center.CrewMemberType.crew:
            continue

        print(member,crew[member])

if __name__ == '__main__':
    run()
