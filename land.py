#!/usr/bin/env python3
import krpc
import click
import time
import numpy
import math
from simple_pid import PID

@click.command()
@click.option('--alt',default=40000) # this is mean, not surface!
@click.option('--final',default=25)
@click.option('--rate',default=10)

def run(alt,rate,final):

    conn = krpc.connect()
    t = conn.mech_jeb.translatron
    a = conn.mech_jeb.smart_ass
    v = conn.space_center.active_vessel

    decent_speed = [    -1, -100,  -500 ]
    decent_alt   = [    10, 1000,   alt ]

    # 0 approach
    # 1 kill h velocity
    # 2 decent coast
    # 3 final landing
    # 4 'shutdown'
    mode = 0

    v.control.sas_mode = conn.space_center.SASMode.stability_assist
    v.control.sas = False

    a.interface_mode = conn.mech_jeb.SmartASSInterfaceMode.surface
    a.autopilot_mode = conn.mech_jeb.SmartASSAutopilotMode.off

    a.force_pitch = True
    a.force_yaw   = True
    a.force_roll  = True

    a.surface_heading = 0
    a.surface_pitch = 0
    a.surface_roll = 0

    a.update(False)

    t.mode = conn.mech_jeb.TranslatronMode.off
    t.translation_speed = decent_speed[-1]
    t.kill_horizontal_speed = False # handled by smartass

    f = v.flight(v.orbit.body.reference_frame)

    s_alt_s = conn.add_stream(getattr, f, 'surface_altitude')
    s_alt_s.rate = rate
    s_alt_s.start()

    h_speed_s = conn.add_stream(getattr, f, 'horizontal_speed')
    h_speed_s.rate = rate
    h_speed_s.start()

    v_speed_s = conn.add_stream(getattr, f, 'vertical_speed')
    v_speed_s.rate = rate
    v_speed_s.start()

    a.autopilot_mode = conn.mech_jeb.SmartASSAutopilotMode.surface_retrograde
    a.update(False)


    try:
        s_alt_s.condition.acquire()
        while True:
            s_alt_s.wait()

            s_alt   = s_alt_s()
            h_speed = h_speed_s()
            v_speed = v_speed_s()

            print('{:2d} {:8.1f} {:6.2f} {:6.2f}'.format( mode, s_alt, v_speed - t.translation_speed, h_speed))

            if mode == 0:
                if s_alt < alt:
                    print('killing h velo')
                    t.mode = conn.mech_jeb.TranslatronMode.keep_vertical
                    mode = 1
            elif mode == 1:
                t.translation_speed = numpy.interp( s_alt, decent_alt, decent_speed )
                if s_alt < final:
                    print('final approach')
                    a.autopilot_mode = conn.mech_jeb.SmartASSAutopilotMode.vertical_plus
                    a.update(False)
                    mode = 3
            elif mode == 3:
                if abs(v_speed) < 0.5:
                    print('shut down')
                    mode = 4
            elif mode == 4:
                v.control.sas = True
                t.mode = conn.mech_jeb.TranslatronMode.off
                t.translation_speed = 0
                #a.autopilot_mode = conn.mech_jeb.SmartASSAutopilotMode.off
                #a.update(False)
                break
            else:
                raise Exception('what?')
        print('done')

    finally:
        s_alt_s.condition.release()
        s_alt_s.remove()
        h_speed_s.remove()

if __name__ == '__main__':
    run()
