#!/usr/bin/env python3

import krpc
from time import sleep

conn = krpc.connect()
print(dir(conn))

vessel = conn.space_center.active_vessel
print(dir(vessel))
