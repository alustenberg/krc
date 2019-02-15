#!/usr/bin/env python3
import krpc
from util import mission

class LaunchMission(mission):
    def doMission(self):
        self.launch(150,6)

if __name__ == '__main__':
    LaunchMission().doMission()


