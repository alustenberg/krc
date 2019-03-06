#!/usr/bin/env python3
import krpc
import click
import time

@click.command()

def run():
    conn = krpc.connect()
    vessel = conn.space_center.active_vessel
    contracts = conn.space_center.contract_manager.active_contracts

    travel = {}
    for contract in contracts:
        if contract.completed:
            continue

        if not contract.title.startswith('Ferry'):
            continue

        for param in contract.parameters:
            if param.completed:
                continue

            if not param.title in travel:
                travel[param.title] = []

            for sub in param.children:
                if sub.completed:
                    continue

                travel[param.title].append(sub.title)

    for t in sorted(travel.keys()):
        if not len(travel[t]):
            continue
        print(t)
        for s in sorted(travel[t]):
            print("\t",s)

if __name__ == '__main__':
    run()
