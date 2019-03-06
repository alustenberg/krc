#!/usr/bin/env python3
import krpc
import click
import time
import numpy
from simple_pid import PID

@click.command()
@click.option('--alt',default=1000)
@click.option('--launchaoa',default=5.0)
@click.option('--climbrate',default=300.0)
@click.option('--maxaoa',default=10.0)
@click.option('--heading',default=90)
@click.option('--rate',default=10)
@click.option('--speed',default=0)


def run(alt,launchaoa, climbrate, maxaoa, heading, rate, speed):
    conn = krpc.connect()
    t = conn.mech_jeb.translatron
    a = conn.mech_jeb.smart_ass
    v = conn.space_center.active_vessel
    c = v.control

    a.interface_mode = conn.mech_jeb.SmartASSInterfaceMode.surface
    a.autopilot_mode = conn.mech_jeb.SmartASSAutopilotMode.surface

    a.force_pitch = True
    a.force_yaw   = True
    a.force_roll  = True

    a.surface_heading = heading
    a.surface_pitch = launchaoa
    a.surface_roll = 0

    a.update(False)

    f = v.flight(v.orbit.body.reference_frame)

    s_alt = conn.add_stream(getattr, f, 'mean_altitude')
    s_alt.rate = rate
    s_alt.start()

    s_vs = conn.add_stream(getattr, f, 'vertical_speed')
    s_vs.rate = rate
    s_vs.start()

    s_spd = conn.add_stream(getattr, f, 'speed')
    s_spd.rate = rate
    s_spd.start()


    start_alt = s_alt()


    alt_pid = PID(Kp=.10, Ki=.00, Kd=.00, sample_time = None, setpoint = alt)

    vs_pid = PID(Kp=.15, Ki=.05, Kd=.01, sample_time = None, setpoint = 0)
    vs_pid.output_limits = (-1.0 * maxaoa, 1.0 * maxaoa)

    spd_pid = PID(Kp=.20, Ki=.05, Kd=.25, sample_time = None, setpoint = speed)
    spd_pid.output_limits = (0,1.0)

    climb_alts   = [         0,       14000, 18000, 20000]
    climb_speeds = [ climbrate,   climbrate,    50,     0]

    if start_alt > 1500:
        start_alt = None

    try:
        s_alt.condition.acquire()
        while True:
            s_alt.wait()

            c_alt = s_alt()
            c_vs  = s_vs()
            c_spd = s_spd()

            if start_alt:
                if  c_alt < ( start_alt + 25 ):
                    print('{:8.1f} {:6.2f} {:6.2f}'.format( c_alt, c_vs, a.surface_pitch))
                    continue

                print('going closed loop')
                start_alt = None
                conn.space_center.active_vessel.control.gear = False

                alt_pid.set_auto_mode(True, last_output = c_vs)
                vs_pid.set_auto_mode(True, last_output = a.surface_pitch)


            climbrate = numpy.interp( c_alt, climb_alts, climb_speeds )
            alt_pid.output_limits = (-1.0 * climbrate, 1.0 * climbrate)
            p_alt = alt_pid(c_alt)

            vs_pid.setpoint = p_alt
            p_vs = vs_pid(c_vs)

            a.surface_pitch = p_vs
            a.update(False)

            if speed > 0:
                c.throttle = spd_pid(c_spd)

            print("alt: {:8.1f} avs: {:6.2f} dvs: {:5.2f} dpitch: {:5.2f} speed: {:5.2f}".format(c_alt, c_vs, p_alt, p_vs, c_spd))
    finally:
        s_alt.condition.release()
        s_alt.remove()

if __name__ == '__main__':
    run()
