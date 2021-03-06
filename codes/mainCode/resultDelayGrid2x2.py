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
tsize = 21
axsize = 19

nolab = '_nolegend_'

def setsavefig(figure, lgnd, filepath):
	''' Save figure at publication quality using desired settings
	'''
	dpiVal = 300
	padding = 0.1
	#figure.savefig(filepath+'.png', dpi=dpiVal, bbox_inches='tight', pad_inches=padding)
	figure.savefig(filepath+'.eps', dpi=dpiVal, bbox_extra_artists=(lgnd,), bbox_inches='tight', pad_inches=padding)
	figure.savefig(filepath+'.pdf', dpi=dpiVal, bbox_extra_artists=(lgnd,), bbox_inches='tight', pad_inches=padding)


def IQR(data, qrange=75):
    return (np.percentile(data, qrange), np.percentile(data, 100-qrange))

models = ['simpleT', 'twinT', 'corridor', 'manhattan']
controllers = ['fixedTime', 'VA', 'GPSVA', 'HVA1','HVA']

modDict = {'simpleT':'Simple-T', 'twinT':'Twin-T', 'corridor':'Corridor', 'manhattan':'Manhattan'}
limDict = {'simpleT':[[18, 28],[0,100], 1, 10], 'twinT':[[0,1100], [0,1000], 100, 100], 
	'corridor':[[65,100], [0,800], 5, 100], 'manhattan':[[80,210], [0,900], 10, 100]}
ctrlDict={'fixedTime':'FT', 'VA':'VA', 'GPSVA':'GPS-VA', 'HVA':'HVA', 'HVA1':'HVA1', 'HVAbias':'HVAbias'}

# Run index and AV ration definitions
runs = np.arange(1, 16)
AVratios = np.linspace(0, 1, 11)
pctAVR = 100*AVratios
SCALING = 0

lineStyle = {'VA':'^k', 
	'fixedTime':'vC2', 
	'GPSVA':'*C1', 
	'HVA1':'sC0',
	'HVAbias':'sC0', 
	'HVA':'oC3'}

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

def plotPercentile(data, scale, style='k-', alpha_val=1):
	if len(data.shape) == 1:
		bands = np.percentile(data, [5, 95], axis=0)
		bands = repmat(bands, scale.shape[0], 1).T
	elif len(data.shape) == 2:
		bands = np.percentile(data, [5, 95], axis=0)
	else:
		print('This data is not a vector/2D-Matrix!')

	pyplot.plot(scale, bands[0,:], style+'--', linewidth=1, alpha=alpha_val)
	pyplot.plot(scale,bands[1,:], style+'--', linewidth=1, alpha=alpha_val)

fig = pyplot.figure(figsize=(20, 18))
# ig = pyplot.figure(figsize=(20, 15))
idLetter= ord('a') - 1
#pltID = 140 # Line 1x4
pltID = 220 # Square 2x2
lines = []
labels = []
sample = {}
for i, model in enumerate(models):
	idx = i+1
	for controller in controllers:
		dataFolder = './data/'+controller+'/'

		travelData = np.loadtxt(dataFolder+model+'_travelData.txt', delimiter=',')
		stdDevTravel = np.loadtxt(dataFolder+model+'_stdDevTravel.txt', delimiter=',')
		delayData = np.loadtxt(dataFolder+model+'_delayData.txt', delimiter=',')
		stdDevDelay = np.loadtxt(dataFolder+model+'_stdDevDelay.txt', delimiter=',')
		# Means
		meanTravelTimePerMeter = np.mean(travelData, 0)
		meanDelayTravelTimePerMeter = np.mean(delayData, 0)

		# Standard Deviations
		stdTravelTimePerMeter = np.mean(stdDevTravel, 0)
		stdDelayTravelTimePerMeter = np.mean(stdDevDelay, 0)

		# Extend CAV independant mode arrays to correct length
		if controller in ['VA', 'fixedTime']:
			meanTravelTimePerMeter *= np.ones_like(pctAVR)
			meanDelayTravelTimePerMeter *= np.ones_like(pctAVR)
		
		# Plot Results
		print('\nRendering {} Plots...'.format(controller+'_'+model))

		# AVR vs. Mean Travel Time + Delay Per Meter
		ax = fig.add_subplot(pltID+idx)
		plotPercentile(delayData, pctAVR, lineStyle[controller], alpha_val=0.7)
		lines.append(pyplot.plot(pctAVR, meanDelayTravelTimePerMeter, lineStyle[controller]+'-', linewidth=2, label=ctrlDict[controller], markersize=7))
		labels.append(ctrlDict[controller])
		pyplot.title(modDict[model]+': Delay vs. CV Penetration', fontsize=tsize)
		pyplot.xlabel('Percentage CV Penetration\n({})'.format(chr(idLetter + idx)), fontsize=axsize)
		pyplot.ylabel('Delay [s]', fontsize=axsize)
		pyplot.setp(ax.get_xticklabels(), fontsize=15)
		pyplot.setp(ax.get_yticklabels(), fontsize=15)

		if model in limDict.keys():
			ax.yaxis.set_ticks(np.arange(0, 1300, limDict[model][2]))
			ax.set_ylim(limDict[model][0])
			ax.xaxis.set_ticks(np.arange(0, 110, 10))
		sample[controller+'_'+model] = meanDelayTravelTimePerMeter[-1]

#print(sample)
leg = fig.legend([x[0] for x in lines[:5]], 
	['Fixed Time','Vehicle Actuation','GPS Vehicle Actuation', 'Hybrid Vehicle Actuation (1 Loop)', 'Hybrid Vehicle Actuation (2 Loop)'], 
	#bbox_to_anchor=(0.663, 1.16), 
	bbox_to_anchor=(0.8, 0.93), 
	ncol=3, labelspacing=1, fontsize=tsize+2, markerscale=2)
st_leg = pyplot.suptitle('.', y=0.98)
for legobj in leg.legendHandles:
    legobj.set_linewidth(3.0)

for t in leg.texts:
    t.set_multialignment('center')

setsavefig(fig, st_leg, './figures/delay_grid')
pyplot.close(fig)

# Some result metrics
k = sample.keys()
k.sort()
tll = ['GPSVA', 'HVA', 'HVA1']
mods = ['simpleT','twinT','corridor','manhattan']
for t in tll:
	avg = 0.
	for m in mods:
		pct = 100*(1-sample[t+'_'+m]/sample['VA_'+m])
		avg += pct
		print('{}_{}: {:.2f}%'.format(t, m, pct))
	print('MEAN {}: {:.2f}'.format(t, avg/len(mods)))

print('~DONE~')
