#!/usr/bin/env python3
import math
import time
import krpc
import getopt
import signal

from krpc.error import RPCError

class mission(object):
    conn    = None
    vessel  = None
    mj      = None
    ap      = None

    thrust  = None
    alt     = None
    ap_enabled = None

    def doMission(self):
        self.launch()

    def __init__(self, name='Mission'):
        self.conn   = krpc.connect(name=name)
        self.mj     = self.conn.mech_jeb
        self.vessel = self.conn.space_center.active_vessel
        self.ap     = self.mj.ascent_autopilot

    def doScience(self):
        if not self.vessel:
            raise RuntimeError


        seen = {}
        #for part in self.vessel.parts.with_module('ModuleScienceContainer'):
        for part in self.vessel.parts.with_module('ModuleScienceExperiment'):
            if part.experiment:
                e = part.experiment
                s = e.science_subject
                p = s.science / s.science_cap
                r = s.science_cap - s.science

                print(round(r, 2), s.data_scale, s.subject_value,  s.scientific_value, s.title, s.is_complete)

                if s.is_complete:
                    continue

                if r < 1:
                    continue

                if s.subject_value < 1.0:
                    continue



                for data in e.data:
                    print(data.data_amount, data.science_value, data.transmit_value)
                    if e.rerunnable and data.transmit_value > 1:
                        print('transmitting')
                        e.transmit()
                        continue

                    if data.science_value < 0.1:
                        print('dumping')
                        e.dump()


                if not e.has_data and not part.experiment.inoperable and s.title not in seen:
                    print('running',s.subject_value)
                    part.experiment.run()
                    seen[s.title] = 1

    def findTarget(self, name, single=True):
        found = []
        for v in self.conn.space_center.vessels:
            if name == v.name:
                found.append(v)

        if not single:
            return found

        try:
            return found[0]
        except:
            raise ValueError('target not found')

    def launch(self, altitude=100, boostStage = 0):
        # Pre-launch setup
        c = self.vessel.control
        c.sas = True
        c.rcs = False
        c.throttle = 1.0

        ap = self.ap
        ap.auto_path = False
        ap.turn_start_altitude = 250
        ap.turn_end_altitude = 60000
        ap.turn_end_angle = 0
        ap.turn_shape_exponent = 0.5

        ap.desired_inclination = 0
        ap.desired_orbit_altitude = altitude * 1000
        ap.skip_circularization = False

        ap.force_roll = True
        ap.turn_roll = 0
        ap.vertical_roll = 0

        ap.limit_ao_a = True
        ap.max_ao_a = 5
        ap.ao_a_limit_fadeout_pressure = 2500

        ap.corrective_steering = True
        ap.autostage = True

        ap.autodeploy_solar_panels = True
        ap.auto_deploy_antennas = True

        th = ap.thrust_controller
        th.limit_acceleration = True
        th.min_throttle = .10
        th.max_acceleration = 25

        # enable and launch
        if not ap.enabled:
            ap.enabled = True
            self.vessel.control.activate_next_stage()


        thrust     = self.conn.add_stream(getattr, self.vessel,'thrust')
        alt        = self.conn.add_stream(getattr, self.vessel.flight(), 'mean_altitude')
        ap_enabled = self.conn.add_stream(getattr, self.ap, 'enabled')

        thrust.start()
        alt.start()
        ap_enabled.start()

        alt.rate = 5

        try:
            staged = False
            alt.condition.acquire()
            while ap_enabled():
                if not staged and thrust() == 0 and alt() > 50000:
                    if c.current_stage >= boostStage:
                        print('main boost complete. staging.')
                        c.activate_next_stage()

                    staged = True

                alt.wait()
        finally:
            alt.condition.release()
            alt.remove()
            thrust.remove()
            ap_enabled.remove()

        print("Launch complete!")

    def execute_node(self, tolerance = 0.1, warp = True):
        print("Executing next maneuver node")
        e = self.mj.node_executor
        e.tolerance = tolerance
        e.autowarp = warp
        e.execute_one_node()
        self.waitState(e)

    def waitState(self, obj, attr = 'enabled', state=True):
        with self.conn.stream(getattr, obj, attr) as stream:
            stream.rate = 1
            with stream.condition:
                while stream() == state:
                    stream.wait()

