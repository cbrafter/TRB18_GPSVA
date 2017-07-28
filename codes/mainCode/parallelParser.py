# -*- coding: utf-8 -*-
"""
@file    resultParser.py
@author  Craig Rafter
@date    29/01/2016

Code to parse the SUMO simulation XML output.

"""

import numpy as np
from matplotlib import pyplot
import xml.etree.ElementTree as ET
import multiprocessing as mp
import sys, os
import sumoDict 
import itertools

def parallelParser(x):
    try:
        model, controller = x
        print('Starting '+ repr(x))
        # Run index and AV ration definitions
        runs = np.arange(1, 16)
        if controller in ['HVA', 'HVA1', 'GPSVA']:
            AVratios = np.linspace(0, 1, 11)
        else:
            AVratios = np.array([0])

        SCALING = 0

        resultFolder = '/hardmem/results_TRB2/'+controller+'/'+model+'/'
        # Storage for Results
        travelData = np.zeros([runs.shape[0], AVratios.shape[0]])
        stdDevTravel = travelData.copy()

        delayData = travelData.copy()
        stdDevDelay = travelData.copy()

        qLenData = travelData.copy()
        qTimeData = travelData.copy()

        # Parse tripinfo XML files
        for i, run in enumerate(runs):
            for j, AVratio in enumerate(AVratios):
                indexStr = "{:03d}_{:03d}.xml".format(int(AVratio*100), run)
                # Write progress to terminal
                # sys.stdout.write("Parsing: {}/{}, {}\r".format(models.index(model)+1,
                #     len(models), indexStr))
                # sys.stdout.flush()

                # Open XML files
                summaryTree = ET.parse(resultFolder+'tripinfo'+indexStr)
                summaryRoot = summaryTree.getroot()
                # queueTree = ET.parse(resultFolder+'queuedata'+indexStr)
                # queueRoot = queueTree.getroot()

                # Storage for info 
                travList = []
                delayList = []
                # qtimeList = []
                # qlenList = []

                # Parse XML files
                for root in summaryRoot:
                    tripinfo = root.attrib
                    freeflow = sumoDict.getFreeflowTime(model, 
                        tripinfo['departLane'].split('_')[0], 
                        tripinfo['arrivalLane'].split('_')[0], SCALING)
                    # Get route length for normalisation
                    routeLength = float(tripinfo['routeLength']) if SCALING else 1.0
                    # Journey time per meter
                    travList.append((float(tripinfo['duration'])-freeflow)/routeLength)
                    # Delay per meter
                    delayList.append(float(tripinfo['departDelay'])/routeLength)

                # Store for max qlen and qtime
                # maxQtime = 0.0
                # maxQlen = 0.0

                # for root in queueRoot:
                #     for child in list(root[0]):
                #         laneinfo = child.attrib
                #         maxQtime = max(maxQtime, float(laneinfo['qtime']))
                #         maxQlen = max(maxQlen, float(laneinfo['qlen']))

                # Mean Travel time per meter data
                travelData[i, j] = np.mean(travList)
                stdDevTravel[i, j] = np.std(travList)
                # Mean Travel time + delay per meter data
                travWithDelay = np.array(delayList) + np.array(travList)
                delayData[i, j] = np.mean(travWithDelay)
                stdDevDelay[i, j] = np.std(travWithDelay)
                # Max Qtimes and Qlens
                # qLenData[i, j] = maxQlen
                # qTimeData[i, j] = maxQtime

        # Means
        dataFolder = './data/'+controller+'/'
        if not os.path.exists(dataFolder): # this is relative to script not cfg file
            os.makedirs(dataFolder)

        savePath = dataFolder + model
        np.savetxt(savePath + '_travelData.txt', travelData, delimiter=',')
        np.savetxt(savePath + '_stdDevTravel.txt', stdDevTravel, delimiter=',')
        np.savetxt(savePath + '_delayData.txt', delayData, delimiter=',')
        np.savetxt(savePath + '_stdDevDelay.txt', stdDevDelay, delimiter=',')
        # np.savetxt(savePath + '_qLenData.txt', qLenData, delimiter=',')
        # np.savetxt(savePath + '_qTimeData.txt', qTimeData, delimiter=',')

        print('Finished '+ repr(x))
    except Exception as e:
        # Use try except so that we can identify corrupted data and reun without
        # stopping the other parser instances
        print('*FAILED* '+ repr(x) + ' ' + repr((run, AVratio)))
        print(str(e))

################################################################################
################################################################################
################################################################################

models = ['simpleT', 'twinT', 'corridor', 'manhattan']
#models = ['simpleT']
tlControllers = ['fixedTime', 'VA', 'HVA', 'HVA1', 'GPSVA']
configs = list(itertools.product(models[:1:-1], ['HVA', 'HVA1']))
configs = list(itertools.product(['simpleT'], ['HVA']))

workpool = mp.Pool(processes=6)
# Run simualtions in parallel
result = workpool.map(parallelParser, configs, chunksize=1)

print('~DONE~')
