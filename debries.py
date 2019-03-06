#!/usr/bin/env python3
import krpc
import sys

from krpc.error import RPCError


conn = krpc.connect(name='Tidy')
for v in conn.space_center.vessels:
    if v.recoverable:
        print(v)
        v.recover()
