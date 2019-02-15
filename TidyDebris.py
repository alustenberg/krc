#!/usr/bin/env python3
import krpc
import sys

from krpc.error import RPCError


conn = krpc.connect(name='Tidy')
for v in conn.space_center.vessels:
    if v.name.endswith('Debris') and v.recoverable:
        print(v.name)
