#!/usr/bin/env python3
import krpc
import click

@click.command()

from util import mission

class DockingMission(mission):
    def doMission(self):

def run():
    conn = krpc.connect()
    vessel = conn.space_center.active_vessel
    print("Setting the first docking port as the controlling part")

    parts = self.vessel.parts
    parts.controlling = parts.docking_ports[0].part

    print("Looking for a free docking port attached to the target vessel")
    for dp in self.target.parts.docking_ports:
        if not dp.docked_part:
            print('Found docking port')
            self.conn.space_center.target_docking_port = dp
            break
    else:
        raise RuntimeError('no open docking ports')


    print("Starting the docking process")
    docking = self.mj.docking_autopilot
    docking.force_roll = True
    docking.roll = 0
    docking.enabled = True
    self.waitState(docking)

