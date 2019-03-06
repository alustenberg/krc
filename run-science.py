#!/usr/bin/env python3

import krpc
import click
import time

@click.command()

def run():
    conn = krpc.connect()
    vessel = conn.space_center.active_vessel

    print(f'{vessel.situation} {vessel.biome}')
    seen = {}


    for part in vessel.parts.with_module('ModuleScienceExperiment'):

        if not part.experiment:
            continue

        try:
            if part.name in seen:
                continue

            e = part.experiment

            if not e.available:
                print(f"{part.name:20s} unavailable")
                continue

            if e.inoperable:
                print(f"{part.name:20s} inoperaable")
                continue

            s = e.science_subject
            if s.is_complete:
                print(f"{part.name:20s} completed")
                continue

            r = round(s.science_cap - s.science,3)
            print(f'{part.name:20s} {r:5.1f} science remaining')
            if r < 5:
                continue


            #print("\tscience:{:5.2f} cap: {:5.2f} value: {:5.2f}/{:5.2f} scale: {:5.2f} r:{:5.2f}".format(s.science, s.science_cap, s.scientific_value, s.subject_value, s.data_scale, r))

            if not e.has_data:
                seen[part.name] = 1

                #print("\trunning")
                e.run()

                while not e.has_data:
                    time.sleep(0.1)

            if e.has_data:
                for data in e.data:
                    print("\tdata: {:5.0f} data {:5.2f}/{:5.2f} science".format(data.data_amount, data.transmit_value, data.science_value))

                    if data.transmit_value > 0.5 and e.rerunnable:
                        e.transmit()
                        print("\ttransmit")
                    elif data.transmit_value > 30:
                        e.transmit()
                        print("\ttransmit and render interoperable")
                    elif data.science_value > 15:
                        print("\tstoring")
                    else:
                        e.reset()
                        print("\treset")




        except krpc.error.RPCError:
            print('rpc error')
            pass

    for m in vessel.parts.modules_with_name('ModuleScienceContainer'):
        print(f'container {m.part.name}')
        m.set_action('Collect All')
        continue

if __name__ == '__main__':
    run()