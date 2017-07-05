# -*- coding: utf-8 -*-
"""
@file    simpleTest.py
@author  Simon Box, Craig Rafter
@date    29/01/2016

test Miller's algorithm
"""
import sys, os
sys.path.insert(0, '../sumoAPI')
import fixedTimeControl
import MOVAtll
import sumoConnect
import readJunctionData
import traci
from routeGen import routeGen
from sumoConfigGen import sumoConfigGen
import numpy as np

# Define road model directory
modelname = 'simpleT'
model = './models/{}/'.format(modelname)
# Generate new routes
N = 500  # Last time to insert vehicle at
stepSize = 0.1
AVratio = 0
AVtau = 1.0
vehNr, lastVeh = routeGen(N, AVratio, AVtau, routeFile=model + modelname + '.rou.xml')
print(vehNr, lastVeh)
print('Routes generated')

# Edit the the output filenames in sumoConfig
configFile = model + modelname + ".sumocfg"
exportPath = '../../simple/'
if not os.path.exists(model+exportPath): # this is relative to script not cfg file
    os.makedirs(model+exportPath)

simport = 8813
sumoConfigGen(modelname, configFile, exportPath, stepSize, port=simport)

# Connect to model
connector = sumoConnect.sumoConnect(model + modelname + ".sumocfg", gui=True, port=simport)
connector.launchSumoAndConnect()
print('Model connected')

# Get junction data
jd = readJunctionData.readJunctionData(model + modelname + ".jcn.xml")
junctionsList = jd.getJunctionData()

# Add controller models to junctions
controllerList = []
minGreenTime = 10
maxGreenTime = 60
for junction in junctionsList:
    controllerList.append(fixedTimeControl.fixedTimeControl(junction))

print('Junctions and controllers acquired')

# Step simulation while there are vehicles
vehIDs = []
juncIDs = traci.trafficlights.getIDList()
juncPos = [traci.junction.getPosition(juncID) for juncID in juncIDs]

flowLoops = [loopID for loopID in traci.inductionloop.getIDList() if 'upstream' in loopID]
T = 60.0 # period to calcFlow over
interval = int(np.round(T/h))
vehIDcode = traci.constants.LAST_STEP_VEHICLE_ID_LIST
flowSteps = np.empty([len(flowLoops), interval], dtype=str)
for loop in flowLoops:
	traci.inductionloop.subscribe(loop, [vehIDcode])

i = 0
h = 2
scaling = float(h)/float(T)
qx = np.zeros_like(flowLoops)
while traci.simulation.getMinExpectedNumber():
    traci.simulationStep()
    # Calc qx continuously but only update control every h seconds
    if traci.simulation.getCurrentTime()%(1000*h) < 1e-3:
	    for c in controllerList:
	        c.process(qx)

    flowSteps[:, i%interval] = [traci.inductionloop.getSubscriptionResults(loop)[vehIDcode][0] for loop in flowLoops]
    qx = [len(np.unique(x[x!=''])) * scaling for x in flowSteps]
    i += 1

connector.disconnect()
print('DONE')
