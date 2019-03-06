#!/usr/bin/env python3

import krpc
from time import sleep

conn = krpc.connect()
vessel = conn.space_center.active_vessel
mj = conn.mech_jeb

ap = mj.ascent_autopilot
