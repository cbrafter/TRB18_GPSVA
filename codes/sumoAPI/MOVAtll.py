#!/usr/bin/env python
"""
@file    GPSControl.py
@author  Craig Rafter
@date    19/08/2016

class for fixed time signal control

"""
import signalControl, readJunctionData, traci
from math import atan2, degrees, floor
import numpy as np
from collections import defaultdict

class MOVAtll(signalControl.signalControl):
    def __init__(self, junctionData, minGreenTime=10, maxGreenTime=60, h=2):
        super(MOVAtll, self).__init__(qx)
        self.junctionData = junctionData
        self.Nstages = len(self.junctionData.stages)
        self.firstCalled = self.getCurrentSUMOtime()
        self.lastCalled = self.getCurrentSUMOtime()
        self.lastStageIndex = 0
        self.nextStageIndex = 0
        traci.trafficlights.setRedYellowGreenState(self.junctionData.id, 
            self.junctionData.stages[self.lastStageIndex].controlString)
        self.controlledLanes = self.getLanes()
        self.laneWidth = self.getLaneWidth()
        self.laneDetectionInfo = self._getIncomingLaneInfo()
        self.h = h # calculation interval/period
        self.sx = self.getSatFlows() # S = N/T (N=# veh in x secs, T=x/3600 [hrs])
        self.a = self.amberTime + self.setAllRedTime
        self.lx = 10 # time loss
        self.dx = 0 # #vehicles expected to pass through the junction in h
        self.minGreenTime = minGreenTime
        self.maxGreenTime = maxGreenTime
        
    def process(self, qxRaw, loopMap):
        # Assume if called that h seconds has elapsed e.g.
        # while simActive:
        #   connector.processSimForSeconds(h)
        #   tll.process for tll in junctionList
        # If it's time to recalculate choices
        
        # Get inactive stage information
        

        redStages = [i for i in range(Nstages) if i != self.lastStageIndex]
        # Get beta values
        nx = self.getNXs()
        qx = self.aggregateQX(qxRaw, loopMap)
        # expected flow is between the saturation flow and upstream flow
        dx = 0.5*(sx[self.lastStageIndex]+qx[self.lastStageIndex])
        kx = [self.getKX(n, q) for n, q in zip(nx, qx)]
        bx = [getBetaX(nx[i], kx[i], qx[i] for i in range(len(nx)))]
        delayCaused = self.getDelayCaused(bx, n=1.0)
        # get active stage information - alpha
        delaySaved = self.getDelaySaved(self.dx, 
                      qx[self.lastStageIndex], 
                      self.getRX([nx[i] for i in redStages]))
        # Get Test quantity
        #T = delaySaved - delayCaused

        if delayCaused > delaySaved:
            # find next stage
            self.nextStageIndex = redStages[bx.index(min(bx))]
        
        # process stage as normal
        else:
            pass # next and last stage indices remain unchanged


        if self.transitionObject.active:
            # If the transition object is active i.e. processing a transition
            pass
        elif (self.getCurrentSUMOtime() - self.firstCalled) < (self.junctionData.offset*1000):
            # Process offset first
            pass
        else:
            # Not active, not in offset, stage not finished
            if self.lastStageIndex != self.nextStageIndex:
                # Loop from final stage to first stage
                self.transitionObject.newTransition(
                    self.junctionData.id, 
                    self.junctionData.stages[self.lastStageIndex].controlString,
                    self.junctionData.stages[self.nextStageIndex].controlString
                )
                self.lastStageIndex = self.nextStageIndex

            self.lastCalled = self.getCurrentSUMOtime()

        super(GPSControl, self).process()

    def getAlpha(self, dx, qx, rx):
        A = dx - qx*((1 - (dx/self.sx))/(1 - (dx/self.sx)))
        waitSaving = self.a + rx + self.lx
        return A*B

    def getBeta(self, bx, n=1.0):
        return n*self.h*sum(bx)

    def getBetaX(self, nx, kx, qx):
        return nx + self.getKX(nx, kx)*qx

    def getKX(self, nx, qx, sx):
        '''Use some sort of root finding/bisection here?'''
        j = floor(2 + self.lx/self.h)
        kx = j
        j += 1 # need kx - j + 1 so pre add 1 to save time
        while kx < 1000:
            if (nx + kx*qx - (kx - j)*sx) <= 0:
                return kx
            kx += 1
        return False

    def getLanes(self):
        return list(np.unique([y.split('_')[0] for y in 
                traci.trafficlights.getControlledLanes(self.junctionData.id)]))

    def getLaneWidth(self):
        lw = {x:0 for x in self.controlledLanes}
        for lane in traci.trafficlights.getControlledLanes(self.junctionData.id):
            for ctrlLane in sx.keys():
                if ctrlLane in lane:
                    sx[ctrlLane] += 1
        return [lw[lane] for lane in self.controlledLanes]

    def getNXs(self):
        nx = np.zeros_like(self.controlledLanes)
        for lane in list(np.unique(traci.trafficlights.getControlledLanes(self.junctionData.id))):
            for i, ctrlLane in enumerate(self.controlledLanes):
                if ctrlLane in lane:
                    nx[i] += traci.lane.getLastStepVehicleNumber(self, lane)
        return max(nx, 15)

    def getRX(self, nx):
        return 10 + sum(nx)

    def getSatFlows(self):
        roadMinWidth = 4
        sx = {x:0 for x in self.controlledLanes}
        for lane in traci.trafficlights.getControlledLanes(self.junctionData.id):
            for ctrlLane in sx.keys():
                if ctrlLane in lane:
                    sx[ctrlLane] += max(roadMinWidth, traci.lane.getWidth(lane))

        for ctrlLane in sx.keys():
        # TRA - Estimation of saturation flow at signalised intersections of 
        # developing cities: a micro-simulation modelling approach - M Hossain
            sx[ctrlLane] = (840 + 460*sx[ctrlLane])*self.h/3600.0
        return [sx[lane] for lane in self.controlledLanes]

    def aggregateQX(self, qxRaw, loopMap):
        qx = [0 for x in self.controlledLanes]
        for i, loop in enumerate(loopMap):
            loopLane = traci.inductionloop.getLaneID(loop).split('_')[0]
            if loopLane in self.controlledLanes:
                qx[self.controlledLanes.index(loopLane)] += qxRaw[i]
        return qx
