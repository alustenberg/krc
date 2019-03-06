#!/usr/bin/env python3
import krpc
import argparse
import time

from util import mission

class StationMission(mission):
    def doMission(self,boostStage):
        self.setTarget('Station')
        #self.waitForStationOverhead()
        self.launch(altitude=100, boostStage=boostStage)
        time.sleep(5)
        self.transferToStation()
        self.dockWithStation()


    # this is iffy.  causes some werid asc behaviour
    def waitForStationOverhead(self):
        if self.vessel.control.throttle > 0:
            return

        if not self.station:
            raise RuntimeError('no station?')

        print('waiting for station')

        pos = self.conn.add_stream(self.target.position, self.vessel.reference_frame)
        pos.start()

        pos.condition.acquire()

        try:
            while True:
                apos = abs(pos()[2])
                if apos < 500 and pos()[1] > 0:
                    print('station overhead')
                    break
                pos.wait()
        finally:
            pos.condition.release()
            pos.remove()

    def transferToStation(self, distance=50):
        try:
            plane = self.plan.operation_plane
            plane.time_selector.time_reference = self.mj.TimeReference.rel_nearest_ad
            self.executePlan(plane,'Plane change')
        except:
            print('failure in plane match?')
            pass

        transfer = self.plan.operation_transfer
        self.executePlan(transfer, 'transfer')

        correction = self.plan.operation_course_correction
        correction.intercept_distance = distance
        self.executePlan(correction, 'mid course correction',.01)

        matchSpeed = self.plan.operation_kill_rel_vel
        matchSpeed.time_selector.time_reference = self.mj.TimeReference.closest_approach
        self.executePlan(matchSpeed, 'match speed with target')

        print("Rendezvous complete!")

    def dockWithStation(self):
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

        print("Docking complete!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='station intercept')
    parser.add_argument('boostStage',type=int, default=0, help='primary boost (not circ) end stage')

    args = parser.parse_args()
    StationMission().doMission(args.boostStage)
