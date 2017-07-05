# -*- coding: utf-8 -*-
"""
@file    resultParser.py
@author  Craig Rafter
@date    29/01/2016

Code to parse the SUMO simulation XML output.

"""

import numpy as np
from numpy.matlib import repmat
from matplotlib import rcParams
from matplotlib import pyplot
import xml.etree.ElementTree as ET
import sys, os
import sumoDict 

# Use T1 fonts for plots not bitmap
rcParams['ps.useafm'] = True
rcParams['pdf.use14corefonts'] = True
rcParams['text.usetex'] = True
tsize = 18
axsize = 18

nolab = '_nolegend_'

def setsavefig(figure, filepath):
	''' Save figure at publication quality using desired settings
	'''
	dpiVal = 300
	padding = 0.1
	#figure.savefig(filepath+'.png', dpi=dpiVal, bbox_inches='tight', pad_inches=padding)
	figure.savefig(filepath+'.pdf', dpi=dpiVal, bbox_inches='tight', pad_inches=padding)


def IQR(data, qrange=75):
    return (np.percentile(data, qrange), np.percentile(data, 100-qrange))

models = ['simpleT', 'twinT', 'corridor', 'manhattan']
controllers = ['fixed', 'actuated', 'gpsctrl', 'spatctrl_va']

modDict = {'simpleT':'Simple-T', 'twinT':'Twin-T', 'corridor':'Corridor', 'manhattan':'Manhattan'}
limDict = {'simpleT':[[18, 36],[0,100], 2, 10], 'twinT':[[0,1100], [0,400], 100, 25], 
	'corridor':[[0,300], [0,400], 25, 50], 'manhattan':[[0,300], [0,300], 25, 25]}
ctrlDict={'fixed':'FT', 'actuated':'VA', 'gpsctrl':'GPS-VA', 'spatctrl_va':'SPaT-VA'}

# Run index and AV ration definitions
runs = np.arange(1, 16)
AVratios = np.linspace(0, 1, 11)
pctAVR = 100*AVratios
SCALING = 0

lineStyle = {'actuated':'k^', 
	'fixed':'gv', 
	'gpsctrl':'ro', 
	'spatctrl_ft':'c*', 
	'spatctrl_va':'bs'}

def plotArr(x, y):
	icoVec = ['o','*','x','+','s','d','v','^','<','>','p','h','D','1','2']
	colVec = [
		[     0,    	 0, 1.0000],
		[1.0000,         0,      0],
		[     0,    1.0000,      0],
		[     0,         0, 0.1724],
		[1.0000,    0.1034, 0.7241],
		[1.0000,    0.8276,      0],
		[     0,    0.3448,      0],
		[0.5172,    0.5172, 1.0000],
		[0.6207,    0.3103, 0.2759],
		[     0,    1.0000, 0.7586],
		[     0,    0.5172, 0.5862],
		[     0,         0, 0.4828],
		[0.5862,    0.8276, 0.3103],
		[0.9655,    0.6207, 0.8621],
		[0.8276,    0.0690, 1.0000]
	]
	for i, vec in enumerate(y):
		pyplot.plot(x, vec, '--'+icoVec[i%len(icoVec)], color=colVec[i%len(colVec)], linewidth=1)

def plotPercentile(data, scale, style='k-'):
	if len(data.shape) == 1:
		bands = np.percentile(data, [5, 95], axis=0)
		bands = repmat(bands, scale.shape[0], 1).T
	elif len(data.shape) == 2:
		bands = np.percentile(data, [5, 95], axis=0)
	else:
		print('This data is not a vector/2D-Matrix!')

	pyplot.plot(scale, bands[0,:], style+'--', linewidth=1)
	pyplot.plot(scale,bands[1,:], style+'--', linewidth=1)

for model in models:
	fig1 = pyplot.figure('delay')
	fig2 = pyplot.figure('queue')

	for controller in controllers:
		dataFolder = './data/'+controller+'/'

		travelData = np.loadtxt(dataFolder+model+'_travelData.txt', delimiter=',')
		stdDevTravel = np.loadtxt(dataFolder+model+'_stdDevTravel.txt', delimiter=',')
		delayData = np.loadtxt(dataFolder+model+'_delayData.txt', delimiter=',')
		stdDevDelay = np.loadtxt(dataFolder+model+'_stdDevDelay.txt', delimiter=',')
		qLenData = np.loadtxt(dataFolder+model+'_qLenData.txt', delimiter=',')
		qTimeData = np.loadtxt(dataFolder+model+'_qTimeData.txt', delimiter=',')

		# Means
		meanTravelTimePerMeter = np.mean(travelData, 0)
		meanDelayTravelTimePerMeter = np.mean(delayData, 0)
		# meanTimeLossPerMeter = np.mean(lossData, 0)
		meanMaxQlen = np.mean(qLenData, 0)
		meanMaxQtime = np.mean(qTimeData, 0)

		# Standard Deviations
		stdTravelTimePerMeter = np.mean(stdDevTravel, 0)
		stdDelayTravelTimePerMeter = np.mean(stdDevDelay, 0)
		# stdTimeLossPerMeter = np.std(stdDevLoss, 0)
		stdMaxQlen = np.std(qLenData, 0)
		stdMaxQtime = np.std(qTimeData, 0)

		if controller in ['actuated', 'fixed']:
			meanTravelTimePerMeter *= np.ones_like(pctAVR)
			meanDelayTravelTimePerMeter *= np.ones_like(pctAVR)
			meanMaxQlen *= np.ones_like(pctAVR)
			meanMaxQtime *= np.ones_like(pctAVR)
		
		# Plot Results
		print('\nRendering {} Plots...'.format(controller+'_'+model))

		# AVR vs. Mean Travel Time + Delay Per Meter
		pyplot.figure('delay')
		ax = pyplot.gca()
		plotPercentile(delayData, pctAVR, lineStyle[controller])
		pyplot.plot(pctAVR, meanDelayTravelTimePerMeter, lineStyle[controller]+'-', linewidth=1.5, label=ctrlDict[controller])
		pyplot.title(modDict[model]+': Network Delay vs. ITSC Vehicle Penetration', fontsize=tsize)
		pyplot.xlabel('Percentage of ITSC vehicles', fontsize=axsize)
		pyplot.ylabel('Delay [s]', fontsize=axsize)

		if model in limDict.keys():
			ax.yaxis.set_ticks(np.arange(0, 1300, limDict[model][2]))
			ax.set_ylim(limDict[model][0])
			ax.xaxis.set_ticks(np.arange(0, 110, 10))

		# AVR vs. STD Mean Travel Time + Delay Per Meter
		'''
		fig = pyplot.figure()
		plotArr(pctAVR, stdDevDelay)
		pyplot.plot(pctAVR, stdDelayTravelTimePerMeter, 'k-', linewidth=5)
		pyplot.title('Delay Standard Deviation', fontsize=tsize)
		pyplot.xlabel('Percentage of FR vehicles', fontsize=axsize)
		pyplot.ylabel('Standard Deviation', fontsize=axsize)
		setsavefig(fig, './figures/'+model+'_stdDelay')
		pyplot.close(fig)
		'''

		# AVR vs. Mean Max Queuing Time Per Run
		pyplot.figure('queue')
		ax = pyplot.gca()
		pyplot.plot(pctAVR, meanMaxQtime, lineStyle[controller]+'-', linewidth=1.5)
		plotPercentile(qTimeData, pctAVR, lineStyle[controller])
		pyplot.title(modDict[model]+': Queuing Time vs. ITSC Vehicle Penetration', fontsize=tsize)
		pyplot.xlabel('Percentage of ITSC vehicles', fontsize=axsize)
		pyplot.ylabel('Queuing Time [s]', fontsize=axsize)

		if model in limDict.keys():
			ax.yaxis.set_ticks(np.arange(0, 1200, limDict[model][3]))
			ax.set_ylim(limDict[model][1])
			ax.xaxis.set_ticks(np.arange(0, 110, 10))

		# AVR vs. STD Max Queuing Time Per Run
		'''
		fig = pyplot.figure()
		pyplot.plot(pctAVR, stdMaxQtime, 'bo--')
		pyplot.title('Max. Queuing Time Standard Deviation', fontsize=tsize)
		pyplot.xlabel('Percentage of FR vehicles', fontsize=axsize)
		pyplot.ylabel('Standard Deviation', fontsize=axsize)
		setsavefig(fig, './figures/'+model+'_stdMaxQtime')
		pyplot.close(fig)
		'''
	pyplot.figure('delay')
	#pyplot.legend(['FT', nolab, nolab, 'VA', nolab, nolab, 'GPS-VA', nolab, nolab, 'SPaT-VA'])
	#pyplot.legend(['FT', 'VA', 'GPS-VA', 'SPaT-VA'])
	#pyplot.legend()
	setsavefig(fig1, './figures/'+model+'_delay')
	
	pyplot.figure('queue')
	#pyplot.legend(['FT', 'VA', 'GPS-VA', 'SPaT-VA'])
	setsavefig(fig2, './figures/'+model+'_queue')
	
	pyplot.close(fig1)
	pyplot.close(fig2)

print('~DONE~')
