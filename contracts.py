#!/usr/bin/env python3
import krpc
import click
import time

@click.command()

def run():
    conn = krpc.connect()
    vessel = conn.space_center.active_vessel
    contracts = conn.space_center.contract_manager

    for contract in contracts.active_contracts:
        print(contract.title)
        for param in contract.parameters:
            if param.completed:
                continue

            print("\t",param.title)
            for sub in param.children:
                if sub.completed:
                    continue

                print("\t\t",sub.title)




if __name__ == '__main__':
    run()
