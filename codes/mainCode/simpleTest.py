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
import HybridVAControl
import actuatedControl
import sumoConnect
import readJunctionData
import traci
from routeGen import routeGen
from sumoConfigGen import sumoConfigGen
import numpy as np

controller = HybridVAControl.HybridVAControl
#controller = actuatedControl.actuatedControl
#controller = fixedTimeControl.fixedTimeControl

# Define road model directory
modelname = 'simpleT'
model = './models/{}/'.format(modelname)
# Generate new routes
N = 500  # Last time to insert vehicle at
stepSize = 0.1
AVratio = 0.0
AVtau = 1.0
seed = 10
vehNr, lastVeh = routeGen(N, AVratio, AVtau, routeFile=model + modelname + '.rou.xml', seed=seed)
print(vehNr, lastVeh)
print('Routes generated')

# Edit the the output filenames in sumoConfig
configFile = model + modelname + ".sumocfg"
exportPath = '../../simple/'
if not os.path.exists(model+exportPath): # this is relative to script not cfg file
    os.makedirs(model+exportPath)

simport = 8813
sumoConfigGen(modelname, configFile, exportPath, stepSize, port=simport, seed=seed)

# Connect to model
connector = sumoConnect.sumoConnect(model + modelname + ".sumocfg", gui=False, port=simport)
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
    controllerList.append(controller(junction))

print('Junctions and controllers acquired')

# Step simulation while there are vehicles
vehIDs = []
juncIDs = traci.trafficlights.getIDList()
juncPos = [traci.junction.getPosition(juncID) for juncID in juncIDs]

while traci.simulation.getMinExpectedNumber():
    traci.simulationStep()
    for c in controllerList:
        c.process()

connector.disconnect()
print('DONE')
