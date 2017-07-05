# -*- coding: utf-8 -*-
"""
@file    multiAVratioTest.py
@author  Simon Box, Craig Rafter
@date    29/01/2016

Code to run the "simpleT" SUMO model for various AVratios.

"""
import sys
import os
import subprocess
import time
sys.path.insert(0, '../sumoAPI')
import GPSControl
import sumoConnect
import readJunctionData
import traci
import numpy as np
from matplotlib import pyplot
from routeGen import routeGen
from sumoConfigGen import sumoConfigGen
from stripXML import stripXML

# Define road model directory
modelnames = ['simpleT', 'twinT', 'corridor','manhattan']
if len(sys.argv) > 1:
	modelnames = sys.argv[1:-1]

# Generate new routes
N = 10000  # Last time to insert vehicle at
Nruns = range(9, 16)
# AVtaus = [0.5, 0.1, 0.05]
AVtau = 1.0
AVratios = np.linspace(0, 1, 11)
stepSize = 0.1
port = int(sys.argv[-1])
for tlLogic in [GPSControl.GPSControl]:
	logicFolder = 'gpsctrl'
	for modelname in modelnames:
		model = './models1/{}/'.format(modelname)
		configFile = model + modelname + ".sumocfg"
		exportPath = '/hardmem/results/'+logicFolder+'/'+ modelname +'/'
		if not os.path.exists(exportPath): # this is relative to script not cfg file
			os.makedirs(exportPath)
			print('Results DIR made...')
		for run in Nruns:
			for AVratio in AVratios:
				runtime = time.time()
				print('Model: {} AVratio: {:.2f} tlLogic: {}'.format(modelname, AVratio, logicFolder))
				vehNr, lastVeh = routeGen(N, AVratio, AVtau, model + modelname + '.rou.xml')
				print(vehNr, lastVeh)
				print('Routes generated...')

				# Edit the the output filenames in sumoConfig
				sumoConfigGen(modelname, configFile, exportPath, AVratio, stepSize, run, port)

				# Connect to model
				connector = sumoConnect.sumoConnect(configFile, gui=False, port=port)
				connector.launchSumoAndConnect()
				print('Model connected...')

				# Get junction data
				jd = readJunctionData.readJunctionData(model + modelname + ".jcn.xml")
				junctionsList = jd.getJunctionData()

				# Add controller models to junctions
				controllerList = []
				for junction in junctionsList:
				    controllerList.append(tlLogic(junction))
				print('Junctions and controllers acquired...')

				# Step simulation while there are vehicles
				while traci.simulation.getMinExpectedNumber():
					# connector.runSimulationForSeconds(1)
					traci.simulationStep()
					for controller in controllerList:
						controller.process()

				# Disconnect from current configuration
				connector.disconnect()

				# Strip unused data from results file
				ext = '{AVR:03d}_{Nrun:03d}.xml'.format(AVR=int(AVratio*100), Nrun=run)
				for filename in ['queuedata','tripinfo']:
					target = exportPath+filename+ext
					stripXML(target)

				runtime = time.gmtime(time.time() - runtime)
				print('DONE: Run: {:03d}, AVR: {:03d}%'.format(run, int(AVratio*100)))
				print('Runtime: {}\n'.format(time.strftime("%H:%M:%S", runtime)))
