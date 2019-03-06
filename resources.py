#!/usr/bin/env python3
import krpc
import click
import time

@click.command()
@click.option('--supply/--no-supply', default=True)
@click.option('--amount', default=250)

def run(supply,amount):
    conn = krpc.connect()
    vessel = conn.space_center.active_vessel
    trans = conn.space_center.ResourceTransfer

    active = []

    for t in vessel.resources.names:
        if t in ['ElectricCharge']:
            continue

        print(t)

        stores = []
        supplies = []
        consumers = []

        for r in vessel.resources.with_resource(t):
            w = ( r.amount / r.max, r.part )
            tag = r.part.tag
            #print(w,r.part.name,tag)

            if tag in ['supply']:
                if r.amount > 0:
                    supplies.append(w)
            elif tag in ['store'] and r.amount < r.max:
                stores.append(w)
            elif r.amount < r.max:
                consumers.append(w)

        print("\t{} supplies: {}".format(len(supplies), ','.join([ x[1].name for x in sorted(supplies)])))
        print("\t{} stores".format(len(stores)))
        print("\t{} consumers".format(len(consumers)))

        supplies = sorted(supplies)
        stores = sorted(stores)
        consumers = sorted(consumers)

        fmt = '{}/{:.1%} -> {}/{:.1%}'
        for source in supplies:
            if len(consumers):
                for consumer in consumers:
                    print(fmt.format(source[1].name,source[0],consumer[1].name,consumer[0]))
                    active.append(trans.start(source[1],consumer[1],t,amount))
            elif len(stores):
                for consumer in stores:
                    print(fmt.format(source[1].name,source[0],consumer[1].name,consumer[0]))
                    active.append(trans.start(source[1],consumer[1],t,amount))
            else:
                print('no remaining consumers')

        for source in stores:
            if len(consumers):
                for consumer in consumers:
                    print(fmt.format(source[1].name,source[0],consumer[1].name,consumer[0]))
                    active.append(trans.start(source[1],consumer[1],t,amount))
            else:
                print('no remaining consumers')

    while len(active):
        print('{:.2f} transfered'.format(active[0].amount))
        if active[0].complete:
            print('txn done')
            active.pop(0)
        else:
            time.sleep(1)




if __name__ == '__main__':
    run()
