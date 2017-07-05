# -*- coding: utf-8 -*-
"""
@file    resultParser.py
@author  Craig Rafter
@date    29/01/2016

Code to parse the SUMO simulation XML output.

"""

import numpy as np
from scipy import stats
import xml.etree.ElementTree as ET
from sys import stdout
import pandas as pd

models = ['simpleT', 'twinT', 'corridor', 'manhattan']
# Run index and AV ration definitions
runs = np.arange(1, 16)
AVratios = np.linspace(0, 1, 21)

pvec = np.zeros([20, 4])
modelct = 0
dataFolder = './data/'
for model in models:
	# travelData = np.loadtxt(dataFolder+model+'_travelData.txt', delimiter=',')
	# stdDevTravel = np.loadtxt(dataFolder+model+'_stdDevTravel.txt', delimiter=',')
	delayData = np.loadtxt(dataFolder+model+'_delayData.txt', delimiter=',')
	# stdDevDelay = np.loadtxt(dataFolder+model+'_stdDevDelay.txt', delimiter=',')
	# qLenData = np.loadtxt(dataFolder+model+'_qLenData.txt', delimiter=',')
	# qTimeData = np.loadtxt(dataFolder+model+'_qTimeData.txt', delimiter=',')
	'''
	# Means
	meanTravelTimePerMeter = np.mean(travelData, 0)
	meanDelayTravelTimePerMeter = np.mean(delayData, 0)
	# meanTimeLossPerMeter = np.mean(lossData, 0)
	meanMaxQlen = np.mean(qLenData, 0)
	meanMaxQtime = np.mean(qTimeData, 0)

	# Standard Deviations
	stdTravelTimePerMeter = np.std(stdDevTravel, 0)
	stdDelayTravelTimePerMeter = np.std(stdDevDelay, 0)
	# stdTimeLossPerMeter = np.std(stdDevLoss, 0)
	stdMaxQlen = np.std(qLenData, 0)
	stdMaxQtime = np.std(qTimeData, 0)
	'''

	statrix = delayData.T
	H0 = statrix[0]
	print(model+' p-values')
	for i, H1 in enumerate(statrix[1:]):
		s, p = stats.ttest_ind(H0, H1)
		p = p if p > np.finfo(float).eps else np.finfo(float).eps
		pvec[i, modelct] = p
	modelct += 1
	print('\n')
pDF = pd.DataFrame(pvec)
print pDF.to_latex(column_format='c|'+'c'*(pvec.shape[0]))
print('~DONE~')
