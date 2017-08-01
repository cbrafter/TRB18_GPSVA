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
pyplot.rcParams["font.family"] = "Times New Roman"
# We're using tex fonts so we need to bolden all text in the preambles not with fontweight='bold'
rcParams['text.latex.preamble'] = [r'\renewcommand{\seriesdefault}{\bfdefault}']

tsize = 20.5
axsize = 20.5
ticksize = 17
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
limDict = {'simpleT':[[19, 27],[0,100], 0.5, 1], 'twinT':[[0,1100], [0,1000], 50, 1], 
    'corridor':[[66,100], [0,800], 1, 1], 'manhattan':[[80,210], [0,900], 5, 1]}
ctrlDict={'fixedTime':'FT', 'VA':'VA', 'GPSVA':'GPS-VA', 'HVA':'HVA', 'HVA1':'HVA1', 'HVAbias':'HVAbias'}

# Run index and AV ration definitions
runs = np.arange(1, 16)
AVratios = np.linspace(0, 1, 11)
pctAVR = 100*AVratios
SCALING = 0

lineStyle = {'VA':'^k', 
    'fixedTime':'vC7', 
    'GPSVA':'*C2', 
    'HVA1':'sC0', 
    'HVAbias':'sC0', 
    'HVA':'oC3'}

def plotArr(x, y):
    icoVec = ['o','*','x','+','s','d','v','^','<','>','p','h','D','1','2']
    colVec = [
        [     0,         0, 1.0000],
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

    xerr = bands[0,:]
    yerr = bands[1,:]
    return xerr, yerr

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
        xe, ye = plotPercentile(delayData, pctAVR, lineStyle[controller], alpha_val=0.7)
        nn = meanDelayTravelTimePerMeter
        lines.append(pyplot.errorbar(pctAVR, meanDelayTravelTimePerMeter, 
            yerr=[nn-xe,ye-nn], 
            fmt=lineStyle[controller]+'-', 
            linewidth=2, markersize=8,
            label=ctrlDict[controller], 
            capsize=7, capthick=2, elinewidth=1))
        labels.append(ctrlDict[controller])
        pyplot.title(modDict[model]+': Delay vs. CV Penetration', fontsize=tsize)
        pyplot.xlabel('Percentage CV Penetration\n({})'.format(chr(idLetter + idx)), fontsize=axsize, fontweight='bold')
        pyplot.ylabel('Delay [s]', fontsize=axsize)
        pyplot.setp(ax.get_xticklabels(), fontsize=ticksize)
        pyplot.setp(ax.get_yticklabels(), fontsize=ticksize)

        if model in limDict.keys():
            #set label numbers
            ax.xaxis.set_ticks(np.arange(0, 110, 10))
            # turn labels to the string equivalent of the number so they can be boldened 
            ax.xaxis.set_ticklabels([str(x) for x in np.arange(0, 110, 10)])
            # repeat for y labels
            ax.yaxis.set_ticks(np.arange(0, 1300, limDict[model][2]))
            if limDict[model][3]: # we only want every second tick so set alternates invisible
                for l in ax.yaxis.get_ticklabels()[1::2]:
                    l.set_visible(False)
            ax.set_ylim(limDict[model][0])
            ax.yaxis.set_ticklabels([str(int(x)) for x in np.arange(0, 1300, limDict[model][2])])

        sample[controller+'_'+model] = meanDelayTravelTimePerMeter[-1]

#print(sample)
leg = fig.legend([x[0] for x in lines[:5]], 
    ['Fixed Time','Vehicle Actuation','GPS Vehicle Actuation', 'Hybrid Vehicle Actuation (1 Loop)', 'Hybrid Vehicle Actuation (2 Loops)'], 
    #bbox_to_anchor=(0.663, 1.16), 
    bbox_to_anchor=(0.827, 0.935), 
    ncol=3, labelspacing=1, fontsize=tsize, markerscale=2)
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
