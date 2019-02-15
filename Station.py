#!/usr/bin/env python3
import krpc
from util import mission

class StationMission(mission):
    station = None
    def doMission(self):
        self.findStation()
        #self.waitForStationOverhead()
        self.launch()
        self.transferToStation()
        #self.dockWithStation()

    def findStation(self, name='Station'):
        station = self.conn.space_center.target_vessel
        if station is None or station.name != name:
            print('looking for station: {}'.format(name))
            self.station = self.findTarget(name)
            self.conn.space_center.target_vessel = self.station
        else:
            self.station = station


    # this is iffy.  causes some werid asc behaviour
    def waitForStationOverhead(self):
        if self.vessel.control.throttle > 0:
            return

        if not self.station:
            raise RuntimeError('no station?')

        print('waiting for station')

        pos = self.conn.add_stream(self.station.position, self.vessel.reference_frame)
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

    def transferToStation(self, distance=150):
        planner = self.mj.maneuver_planner

        print('planning transfer')
        transfer = planner.operation_transfer
        transfer.make_node()

        error = transfer.error_message
        if error:
            raise RuntimeError(error)

        self.execute_node()

        print("Correcting course")
        correction = planner.operation_course_correction
        correction.intercept_distance = distance
        correction.make_node()
        self.execute_node(.01)

        print("Matching speed with the target")
        matchSpeed = planner.operation_kill_rel_vel
        matchSpeed.time_selector.time_reference = self.mj.TimeReference.closest_approach
        matchSpeed.make_node()
        self.execute_node()

        print("Rendezvous complete!")

    def dockWithStation(self):
        print("Setting the first docking port as the controlling part")
        parts = self.vessel.parts
        parts.controlling = parts.docking_ports[0].part

        print("Looking for a free docking port attached to the target vessel")
        for dp in self.station.parts.docking_ports:
            if not dp.docked_part:
                print('Found docking port')
                self.conn.space_center.target_docking_port = dp
                break
        else:
            raise RuntimeError('no open docking ports')


        print("Starting the docking process")
        docking = self.mj.docking_autopilot
        docking.enabled = True
        self.waitState(docking)

        print("Docking complete!")

if __name__ == '__main__':
    m = mission()
    m.doMission()
