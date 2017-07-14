# -*- coding: utf-8 -*-
import sys
import os
import shutil
import psutil
import subprocess
import time
import numpy as np
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
import sumoConnect
import readJunctionData
print(sys.path)
import traci
import scipy.optimize as sopt
import itertools

print('Running the script! {} {}'.format(sys.argv[1], sys.argv[2]))
#os.mkdir('/hardmem/results/stuff/')
# with open('/hardmem/results/stuff/sampleT.txt', 'w') as f:
#     f.write('Hello World! {} {}'.format(sys.argv[1], sys.argv[2]))

# print(os.path.exists('/hardmem/results/stuff/'))
# print([psutil.cpu_count(), psutil.cpu_count(logical=False)])
def simulation(x):
    #assert len(x) == 4
    runtime = time.time()
    # Define Simulation Params
    FLOW, modelName, tlLogic, CAVratio, run = x
    procID = int(mp.current_process().name[-1])
    model = './models/{}_{}/'.format(modelName, procID)
    simport = 8812 + procID
    N = 2500  # Last time to insert vehicle at
    stepSize = 0.1
    CAVtau = 1.0
    configFile = model + modelName + ".sumocfg"
    # Configure the Map of controllers to be run
    tlControlMap = {'fixedTime': fixedTimeControl.fixedTimeControl,
                    'VA': actuatedControl.actuatedControl,
                    'GPSVA': GPSControl.GPSControl,
                    'HVA': HybridVAControl.HybridVAControl}
    tlController = tlControlMap[tlLogic]

    exportPath = '/hardmem/results/' + tlLogic + '/' + modelName + '/'
    #print(exportPath + str(os.path.exists(exportPath)))
    # Check if model copy for this process exists
    if not os.path.isdir(model):
        shutil.copytree('./models/{}/'.format(modelName), model)

    # this is relative to script not cfg file
    if not os.path.exists(exportPath):
        print('MADE PATH')
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
        controllerList.append(tlController(junction, flowarg=FLOW))

    # Step simulation while there are vehicles
    while traci.simulation.getMinExpectedNumber():
        # connector.runSimulationForSeconds(1)
        traci.simulationStep()
        for controller in controllerList:
            controller.process()

    # Disconnect from current configuration
    finTime = traci.simulation.getCurrentTime()*0.001
    print(finTime)
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
    return finTime

def fopt(x):
    print(x)
    config = list(itertools.product([x], ['simpleT'], ['HVA'], [0.], [1,2,3,4]))
    workpool = mp.Pool(processes=4)
    # Run simualtions in parallel
    result = workpool.map(simulation, config, chunksize=1)
    return np.mean(result)

print(sopt.fmin(fopt, 2, xtol=0.5, ftol=0.5))
# x=1
# a = simulation([x, 'simpleT', 'HVA', 0, 1])
# b = simulation([x, 'simpleT', 'HVA', 0, 2])
# c = simulation([x, 'simpleT', 'HVA', 0, 3])