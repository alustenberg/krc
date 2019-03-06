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
    target  = None
    mj      = None
    ap      = None
    sc      = None
    plan    = None

    thrust  = None
    alt     = None
    ap_enabled = None

    def doMission(self):
        self.launch()

    def __init__(self, name='Mission'):
        self.conn   = krpc.connect(name=name)
        self.sc     = self.conn.space_center

        self.mj     = self.conn.mech_jeb
        self.vessel = self.sc.active_vessel
        self.ap     = self.mj.ascent_autopilot
        self.plan   = self.mj.maneuver_planner
        self.ac     = self.conn.kerbal_alarm_clock

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

    def setTarget(self, name):
        target = self.conn.space_center.target_vessel
        if target is None or target.name != name:
            print('looking for target: {}'.format(name))
            if name in self.conn.space_center.bodies:
                self.target = self.conn.space_center.bodies[name]
                self.conn.space_center.target_body = self.target
                return

            self.target = self.findTarget(name)
            self.conn.space_center.target_vessel = self.target
        else:
            self.target = target

    def waitForLaunchWindow(self, modFactor=6*60*60):
        if not modFactor:
            return

        if self.vessel.flight().mean_altitude > 1000:
            print('already in flight, skipping wait')
            return

        ut = self.sc.ut
        m = modFactor - (int(ut) % modFactor)
        print('warping {} seconds ahead to next window'.format(m))
        self.sc.warp_to(ut+m)


    def launch(self, altitude=100, boostStage = 0, inclination=0, tidy=False, circ=True, waitForWindow=0, limitThrust=9.8*2.5):
        c = self.vessel.control
        ap = self.ap
        th = ap.thrust_controller
        sc = ap.staging_controller

        if self.vessel.flight().surface_altitude > 1500:
            print('already in flight. skipping autopilot setup')
        else:
            print('launching to {}, end stage {}'.format(altitude, boostStage))
            # Pre-launch setup
            c.sas = True
            c.rcs = False
            c.throttle = 1.0

            ap.ascent_path_index = 0
            apc = ap.ascent_path_classic

            apc.auto_path = False
            apc.turn_shape_exponent = 0.5
            apc.turn_start_altitude = 1000 + self.vessel.flight().mean_altitude
            apc.turn_start_velocity = 150

            apc.turn_end_altitude = 55000
            apc.turn_end_angle = -5

            print(inclination)
            ap.desired_inclination = int(inclination)
            ap.desired_orbit_altitude = (altitude * 1.05 ) * 1000
            ap.skip_circularization = True

            ap.force_roll = True
            ap.turn_roll = 0
            ap.vertical_roll = 0

            ap.limit_ao_a = False
            #ap.limit_ao_a = True
            #ap.max_ao_a = 7
            ap.ao_a_limit_fadeout_pressure = 2500

            ap.corrective_steering = True
            ap.autostage = True

            ap.autodeploy_solar_panels = True
            ap.auto_deploy_antennas = True

            sc.autostage_pre_delay  = 0.5
            sc.autostage_post_delay = 1.0
            sc.hot_staging = False

            th.limit_acceleration = True
            th.min_throttle = .10
            th.limit_dynamic_pressure = True
            th.max_dynamic_pressure = 30000

            # enable and launch
            if not ap.enabled:
                self.waitForLaunchWindow(waitForWindow)
                ap.enabled = True
                #print('staging for launch')
                #c.activate_next_stage()


        alt        = self.conn.add_stream(getattr, self.vessel.flight(), 'mean_altitude')
        mach       = self.conn.add_stream(getattr, self.vessel.flight(), 'mach')
        ap_enabled = self.conn.add_stream(getattr, self.ap, 'enabled')
        thrust     = self.conn.add_stream(getattr, self.vessel,'thrust')


        thrust.start()
        alt.start()
        ap_enabled.start()

        alt.rate = 1.0

        try:
            maxThrust = True

            th.max_acceleration = limitThrust

            alt.condition.acquire()
            while ap_enabled():
                print("{:8.1f} {:3.2f}".format(alt(),mach()))
                alt.wait()
        finally:
            alt.condition.release()
            alt.remove()
            ap_enabled.remove()
            thrust.remove()

        if boostStage:
            while c.current_stage > boostStage:
                print('main boost complete. staging from',c.current_stage,'to',boostStage)
                c.activate_next_stage()
        else:
            print('main boost completed, stage', c.current_stage)

        if tidy:
            inc = self.plan.operation_inclination
            inc.new_inclination = inclination
            inc.time_selector.time_reference = self.mj.TimeReference.rel_nearest_ad
            self.executePlan(inc,'inclination')

        cir = self.plan.operation_circularize
        cir.time_selector.time_reference = self.mj.TimeReference.altitude
        cir.time_selector.circularize_altitude = altitude * 1000

        if circ:
            self.executePlan(cir, 'circularize')
        else:
            cir.make_node()
            if cir.error_message:
                raise RuntimeError(cir.error_message)


    def transferToBody(self, autoWarp = False):
        plane = self.plan.operation_plane
        self.executePlan(plane, 'match planes')

        transfer = self.plan.operation_transfer
        self.executePlan(transfer, 'transfer')

    def orbitInsert(self, inclination=0, alt=20):
        plane = self.plan.operation_inclination
        plane.new_inclination = inclination
        plane.time_selector.time_reference = self.mj.TimeReference.x_from_now
        plane.time_selector.lead_time = 60
        self.executePlan(plane,'set plane')

        periapsis = self.plan.operation_periapsis
        periapsis.new_periapsis = math.floor(alt * 1000 * 0.9)
        periapsis.time_selector.time_reference = self.mj.TimeReference.x_from_now
        periapsis.time_selector.lead_time = 60
        self.executePlan(periapsis,'set periapsis')

        cir = self.plan.operation_circularize
        cir.time_selector.time_reference = self.mj.TimeReference.altitude
        cir.time_selector.circularize_altitude = alt * 1000
        self.executePlan(cir, 'circularize')

    def returnFromMoon(self, targetAlt=35):
        #self.launch(altitude=25,boostStage=0)
        moonReturn = self.plan.operation_moon_return
        moonReturn.moon_return_altitude = targetAlt * 1000
        self.executePlan(moonReturn, 'return burn')

        # wait for SOI change and reset periaps

    def setPeriapsis(self, periapsis):
        peri = self.plan.operation_periapsis
        peri.new_periapsis = periapsis * 1000
        peri.time_selector.time_reference = self.mj.TimeReference.x_from_now
        peri.time_selector.lead_time = 60
        self.executePlan(peri,'set periapsis')

    def setApopasis(self, periapsis):
        peri = self.plan.operation_periapsis
        peri.new_periapsis = periapsis * 1000
        peri.time_selector.time_reference = self.mj.TimeReference.x_from_now
        peri.time_selector.lead_time = 60
        self.executePlan(peri,'set periapsis')

    def executePlan(self, plan, title=None, tolerance = 0.1):
        plan.make_node()

        error = plan.error_message
        if error:
            raise RuntimeError(error)

        if title is not None:
            print('Execute', title)
        self.executeNode(tolerance)

    def executeNode(self, tolerance = 0.1, warp = True):
        self.mj.staging_controller.enabled = True
        self.mj.staging_controller.autostaging_once = True
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


class TransferMission(mission):
    def doMission(self,body,altitude=150,stage=0,wait=True):
        self.setTarget(body)
        if wait:
            self.waitForLaunchWindow()
        self.launch(altitude,stage)
        self.transferToBody()

