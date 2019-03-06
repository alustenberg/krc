#!/usr/bin/env python3
import krpc
import click
import time
import numpy
from simple_pid import PID

@click.command()
@click.option('--alt',default=80)
@click.option('--heading',default=90)
@click.option('--rate',default=5)


def run(alt, heading, rate):

    alt = alt * 1000.0

    conn = krpc.connect()
    t = conn.mech_jeb.translatron
    a = conn.mech_jeb.smart_ass
    v = conn.space_center.active_vessel

    a.interface_mode = conn.mech_jeb.SmartASSInterfaceMode.surface
    a.autopilot_mode = conn.mech_jeb.SmartASSAutopilotMode.surface

    a.force_pitch = True
    a.force_yaw   = True
    a.force_roll  = True

    a.surface_heading = heading
    a.surface_pitch = 90
    a.surface_roll = 0

    a.update(False)

    f = v.flight(v.orbit.body.reference_frame)

    s_alt = conn.add_stream(getattr, f, 'mean_altitude')
    s_alt.rate = rate
    s_alt.start()

    s_apop = conn.add_stream(getattr, v.orbit, 'apoapsis_altitude')
    s_apop.rate = rate
    s_apop.start()

    launch_apop = [ 0, alt ]
    launch_pitch = [ 90, -20 ]

    try:
        s_alt.condition.acquire()
        while True:
            s_alt.wait()

            c_alt = s_alt()
            c_apop = s_apop()

            print('{:8.1f} {:8.2f} {:6.2f}'.format( c_alt, c_apop, a.surface_pitch))

            a.surface_pitch = numpy.interp(c_apop, launch_apop, launch_pitch)
            a.update(False)
    finally:
        s_alt.condition.release()
        s_alt.remove()

if __name__ == '__main__':
    run()
