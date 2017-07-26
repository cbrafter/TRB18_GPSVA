# -*- coding: utf-8 -*-
import sys
import os
import shutil
import psutil
import subprocess
import time
import numpy as np
import itertools
# from matplotlib import pyplot
from routeGen import routeGen
from sumoConfigGen import sumoConfigGen
from stripXML import stripXML
import multiprocessing as mp
from glob import glob
#os.chdir(os.path.dirname(sys.argv[0]))
sys.path.insert(0, '../sumoAPI')
import GPSControl
import fixedTimeControl
import actuatedControl
import HybridVAControl
import HVA1
import sumoConnect
import readJunctionData
print(sys.path)
import traci


def simulation(x):
    try:
        assert len(x) == 4
        runtime = time.time()
        # Define Simulation Params
        modelName, tlLogic, CAVratio, run = x
        procID = int(mp.current_process().name[-1])
        model = './models/{}_{}/'.format(modelName, procID)
        simport = 8812 + procID
        N = 10000  # Last time to insert vehicle at (10800=3hrs)
        stepSize = 0.1
        CAVtau = 1.0
        configFile = model + modelName + ".sumocfg"
        # Configure the Map of controllers to be run
        tlControlMap = {'fixedTime': fixedTimeControl.fixedTimeControl,
                        'VA': actuatedControl.actuatedControl,
                        'GPSVA': GPSControl.GPSControl,
                        'HVA1': HVA1.HybridVA1Control,
                        'HVA': HybridVAControl.HybridVAControl}
        tlController = tlControlMap[tlLogic]

        exportPath = '/hardmem/results/' + tlLogic + '/' + modelName + '/'

        # Check if model copy for this process exists
        if not os.path.isdir(model):
            shutil.copytree('./models/{}/'.format(modelName), model)

        # this is relative to script not cfg file
        if not os.path.exists(exportPath):
            os.makedirs(exportPath)

        #seed = int(sum([ord(X) for x in modelName + tlLogic]) + int(10*CAVratio) + run)
        seed = int(run)
        vehNr, lastVeh = routeGen(N, CAVratio, CAVtau,
                                  routeFile=model + modelName + '.rou.xml',
                                  seed=seed)

        # Edit the the output filenames in sumoConfig
        sumoConfigGen(modelName, configFile, exportPath,
                      CAVratio, stepSize, run, simport)

        # Connect to model
        connector = sumoConnect.sumoConnect(configFile, gui=False, port=simport)
        connector.launchSumoAndConnect()

        # Get junction data
        jd = readJunctionData.readJunctionData(model + modelName + ".jcn.xml")
        junctionsList = jd.getJunctionData()

        # Add controller models to junctions
        controllerList = []
        for junction in junctionsList:
            controllerList.append(tlController(junction))

        # Step simulation while there are vehicles
        while traci.simulation.getMinExpectedNumber():
            # connector.runSimulationForSeconds(1)
            traci.simulationStep()
            for controller in controllerList:
                controller.process()

        # Disconnect from current configuration
        connector.disconnect()

        # Strip unused data from results file
        ext = '{AVR:03d}_{Nrun:03d}.xml'.format(AVR=int(CAVratio*100), Nrun=run)
        for filename in ['queuedata', 'tripinfo']:
            target = exportPath+filename+ext
            stripXML(target)

        runtime = time.gmtime(time.time() - runtime)
        print('DONE: {}, {}, Run: {:03d}, AVR: {:03d}%, Runtime: {}\n'
            .format(modelName, tlLogic, run, int(CAVratio*100), 
                    time.strftime("%H:%M:%S", runtime)))
        return True
    except:
        # Print if an experiment fails and provide repr of params to repeat run
        print('***FAILURE*** ' + repr(x))
        return False

################################################################################
# MAIN SIMULATION DEFINITION
################################################################################
models = ['simpleT', 'twinT', 'corridor', 'manhattan']
#tlControllers = ['fixedTime', 'VA', 'HVA', 'GPSVA']
tlControllers = ['HVA']
CAVratios = np.linspace(0, 1, 11)
if len(sys.argv) >=3:
    runArgs = sys.argv[1:3]
    runArgs = [int(arg) for arg in runArgs]
    runArgs.sort()
    runStart, runEnd = runArgs
else:
    runStart, runEnd = [1, 11]

runIDs = np.arange(runStart, runEnd)

configs = []
# Generate all simulation configs for fixed time and VA 
#configs += list(itertools.product(models, ['VA'], [0.], runIDs))
# # Generate runs for CAV dependent controllers
configs += list(itertools.product(models[::-1], ['HVA', 'HVA1'], CAVratios, runIDs))
print(len(configs))

# define number of processors to use (avg of logical and physical cores)
nproc = np.mean([psutil.cpu_count(), 
                 psutil.cpu_count(logical=False)], 
                 dtype=int)

print('Starting simulation on {} cores'.format(nproc))  
# define work pool
workpool = mp.Pool(processes=8)
# Run simualtions in parallel
result = workpool.map(simulation, configs, chunksize=1)
# remove spawned model copies
for rmdir in glob('./models/*_*'):
    if os.path.isdir(rmdir):
        shutil.rmtree(rmdir)

# Inform of failed expermiments
if all(result):
    print('Simulations complete, no errors')
else:
    print('Failed Experiment Runs:')
    for i, j in zip(configs, result):
        if not j:
            print(i)
