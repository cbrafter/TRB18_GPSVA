#!/usr/bin/env python
"""
@file    signalControl.py
@author  Simon Box
@date    31/01/2013

Code to control the traffic lights in the "plainRoad" SUMO model.

"""

import subprocess, sys
sys.path.append('/usr/share/sumo/tools')
import traci

PORT = 8813

stage01="rrrrrrrrrr"
inter0102="yyyyyyyyyy"
# stage02="GGGrrrrrrr"
# inter0203="yyyrrrrrrr"
stage03="GGGGGGGGGG"
inter0301="yyyyyyyyyy"

Stages=[stage01,stage03];

sumoBinary = "sumo-gui"
sumoConfig = "plainRoad.sumocfg"

sumoProcess = subprocess.Popen("%s -c %s" % (sumoBinary, sumoConfig), shell=True, stdout=sys.stdout)

traci.init(PORT)

step = 0
lastSwitch=0;
stageIndex = 0;
while step == 0 or traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()
    timeNow = traci.simulation.getCurrentTime()
    if timeNow > 500:
        if stageIndex==0:
            stageIndex=1;
        else:
            stageIndex=0;
        traci.trafficlights.setRedYellowGreenState("1", Stages[stageIndex])
        
    
    step += 1

traci.close()
sys.stdout.flush()
