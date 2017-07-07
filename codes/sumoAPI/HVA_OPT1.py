#!/usr/bin/env python
"""
@file    HybridVAControl.py
@author  Craig Rafter
@date    19/08/2016

class for fixed time signal control

"""
import signalControl, readJunctionData, traci
from math import atan2, degrees, hypot
import numpy as np
from collections import defaultdict

class HybridVAControl(signalControl.signalControl):
    def __init__(self, junctionData, minGreenTime=10, maxGreenTime=60, scanRange=250, packetRate=0.2):
        super(HybridVAControl, self).__init__()
        self.junctionData = junctionData
        self.firstCalled = self.getCurrentSUMOtime()
        self.lastCalled = self.getCurrentSUMOtime()
        self.lastStageIndex = 0
        traci.trafficlights.setRedYellowGreenState(self.junctionData.id, 
            self.junctionData.stages[self.lastStageIndex].controlString)
        
        self.packetRate = int(1000*packetRate)
        self.transition = False
        self.CAMactive = False
        # dict[vehID] = [position, heading, velocity, Tdetect]
        self.newVehicleInfo = {}
        self.oldVehicleInfo = {}
        self.scanRange = scanRange
        self.jcnPosition = np.array(traci.junction.getPosition(self.junctionData.id))
        self.jcnCtrlRegion = self._getJncCtrlRegion()
        # print(self.junctionData.id)
        # print(self.jcnCtrlRegion)
        self.controlledLanes = traci.trafficlights.getControlledLanes(self.junctionData.id)
        # dict[laneID] = [heading, shape]
        self.laneDetectionInfo = self._getIncomingLaneInfo()
        self.stageTime = 0.0
        self.minGreenTime = minGreenTime
        self.maxGreenTime = maxGreenTime
        self.secondsPerMeterTraffic = 0.45
        self.nearVehicleCatchDistance = 25
        self.extendTime = 1.0 # 5 m in 10 m/s (acceptable journey 1.333)
        self.laneInductors = self._getLaneInductors()

        self.TIME_MS = self.getCurrentSUMOtime()
        self.TIME_SEC = 0.001 * self.TIME_MS

    def process(self):
        self.TIME_MS = self.getCurrentSUMOtime()
        self.TIME_SEC = 0.001 * self.TIME_MS
        # Packets sent on this step
        # packet delay + only get packets towards the end of the second
        if (not self.TIME_MS % self.packetRate) and (not 50 < self.TIME_MS % 1000 < 650):
            self.CAMactive = True
            self._getCAMinfo()
        else:
            self.CAMactive = False

        # Update stage decisions
        # If there's no ITS enabled vehicles present use VA ctrl
        if len(self.oldVehicleInfo) < 1 and not self.TIME_MS % 1000:
            detectTimePerLane = self._getLaneDetectTime()
            #print(detectTimePerLane)
            # Set adaptive time limit
            #print(detectTimePerLane < 3)
            if np.any(detectTimePerLane < 2):
                extend = self.extendTime
            else:
                extend = 0.0

            self.stageTime = max(self.stageTime + extend, self.minGreenTime)
            self.stageTime = min(self.stageTime, self.maxGreenTime)
        # If active and on the second, or transition then make stage descision
        elif (self.CAMactive and not self.TIME_MS % 1000) or self.transition:
            oncomingVeh = self._getOncomingVehicles()
            # If new stage get furthest from stop line whose velocity < 5% speed
            # limit and determine queue length
            if self.transition:
                furthestVeh = self._getFurthestStationaryVehicle(oncomingVeh)
                if furthestVeh[0] != '':
                    meteredTime = self.secondsPerMeterTraffic*furthestVeh[1]
                    self.stageTime = max(self.minGreenTime, meteredTime)
                    self.stageTime = min(self.stageTime, self.maxGreenTime)
                # If we're in this state this should never happen but just in case
                else:
                    self.stageTime = self.minGreenTime
            # If currently staging then extend time if there are vehicles close 
            # to the stop line
            else:
                nearestVeh = self._getNearestVehicle(oncomingVeh)
                # If a vehicle detected
                if nearestVeh != '' and nearestVeh[1] <= self.nearVehicleCatchDistance:
                    if (self.oldVehicleInfo[nearestVeh[0]][2] != 1e6 
                        and self.oldVehicleInfo[nearestVeh[0]][2] > 1.0/self.secondsPerMeterTraffic):
                        meteredTime = nearestVeh[1]/self.oldVehicleInfo[nearestVeh[0]][2]
                    else:
                        meteredTime = self.secondsPerMeterTraffic*nearestVeh[1]
                    elapsedTime = 0.001*(self.TIME_MS - self.lastCalled)
                    Tremaining = self.stageTime - elapsedTime
                    self.stageTime = elapsedTime + max(meteredTime, Tremaining)
                    self.stageTime = min(self.stageTime, self.maxGreenTime)
                # no detectable near vehicle try inductive loop info
                elif nearestVeh == '' or nearestVeh[1] <= self.nearVehicleCatchDistance:
                    detectTimePerLane = self._getLaneDetectTime()
                    # Set adaptive time limit
                    if np.any(detectTimePerLane < 2):
                        extend = self.extendTime
                    else:
                        extend = 0.0

                    self.stageTime = max(self.stageTime + extend, self.minGreenTime)
                    self.stageTime = min(self.stageTime, self.maxGreenTime)
                else:
                    pass
        # process stage as normal
        else:
            pass

        # print(self.stageTime)
        self.transition = False
        if self.transitionObject.active:
            # If the transition object is active i.e. processing a transition
            pass
        elif (self.TIME_MS - self.firstCalled) < (self.junctionData.offset*1000):
            # Process offset first
            pass
        elif (self.TIME_MS - self.lastCalled) < self.stageTime*1000:
            # Before the period of the next stage
            pass
        else:
            # Not active, not in offset, stage not finished
            if len(self.junctionData.stages) != (self.lastStageIndex)+1:
                # Loop from final stage to first stage
                self.transitionObject.newTransition(
                    self.junctionData.id, 
                    self.junctionData.stages[self.lastStageIndex].controlString,
                    self.junctionData.stages[self.lastStageIndex+1].controlString)
                self.lastStageIndex += 1
            else:
                # Proceed to next stage
                #print(0.001*(self.getCurrentSUMOtime() - self.lastCalled))
                self.transitionObject.newTransition(
                    self.junctionData.id, 
                    self.junctionData.stages[self.lastStageIndex].controlString,
                    self.junctionData.stages[0].controlString)
                self.lastStageIndex = 0

            #print(0.001*(self.getCurrentSUMOtime() - self.lastCalled))
            self.lastCalled = self.TIME_MS
            self.transition = True
            self.stageTime = 0.0

        super(HybridVAControl, self).process()
        

    def _getHeading(self, currentLoc, prevLoc):
        dy = currentLoc[1] - prevLoc[1]
        dx = currentLoc[0] - prevLoc[0]
        if currentLoc[1] == prevLoc[1] and currentLoc[0] == prevLoc[0]:
            heading = -1
        else:
            if dy >= 0:
                heading = degrees(atan2(dy, dx))
            else:
                heading = 360 + degrees(atan2(dy, dx))
        
        # Map angle to make compatible with SUMO heading
        if 0 <= heading <= 90:
            heading = 90 - heading
        elif 90 < heading < 360:
            heading = 450 - heading

        return heading


    def _getJncCtrlRegion(self):
        jncPosition = traci.junction.getPosition(self.junctionData.id)
        otherJuncPos = [traci.junction.getPosition(x) for x in traci.trafficlights.getIDList() if x != self.junctionData.id]
        ctrlRegion = {'N':jncPosition[1]+self.scanRange, 'S':jncPosition[1]-self.scanRange, 
            'E':jncPosition[0]+self.scanRange, 'W':jncPosition[0]-self.scanRange}

        TOL = 10 # Exclusion region around junction boundary
        if otherJuncPos != []:
            for pos in otherJuncPos:
                dx = jncPosition[0] - pos[0]
                dy = jncPosition[1] - pos[1]
                # North/South Boundary
                if abs(dy) < self.scanRange:
                    if dy < -TOL:
                        ctrlRegion['N'] = min(pos[1] - TOL, ctrlRegion['N'])
                    elif dy > TOL:
                        ctrlRegion['S'] = max(pos[1] + TOL, ctrlRegion['S'])
                    else:
                        pass
                else:
                    pass

                # East/West Boundary
                if abs(dx) < self.scanRange:
                    if dx < -TOL:
                        ctrlRegion['E'] = min(pos[0] - TOL, ctrlRegion['E'])
                    elif dx > TOL:
                        ctrlRegion['W'] = max(pos[0] + TOL, ctrlRegion['W'])
                    else:
                        pass
                else:
                    pass

        return ctrlRegion


    def _isInRange(self, vehPosition):
        distance = np.linalg.norm(vehPosition - self.jcnPosition)
        if (distance < self.scanRange 
            and self.jcnCtrlRegion['W'] <= vehPosition[0] <= self.jcnCtrlRegion['E']
            and self.jcnCtrlRegion['S'] <= vehPosition[1] <= self.jcnCtrlRegion['N']):
            return True
        else:
            return False


    def _getVelocity(self, vehID, vehPosition, Tdetect):
        if vehID in self.oldVehicleInfo.keys():
            oldX = np.array(self.oldVehicleInfo[vehID][0])
            newX = np.array(vehPosition)

            dx = np.linalg.norm(newX - oldX)
            dt = Tdetect - self.oldVehicleInfo[vehID][3]
            velocity = dx/dt

            return velocity
        else:
            return 1e6


    def _getCAMinfo(self):
        self.oldVehicleInfo = self.newVehicleInfo.copy()
        self.newVehicleInfo = {}
        Tdetect = self.TIME_SEC
        for vehID in traci.vehicle.getIDList():
            vehPosition = traci.vehicle.getPosition(vehID)
            if traci.vehicle.getTypeID(vehID) == 'typeITSCV' and self._isInRange(vehPosition):
                vehHeading = traci.vehicle.getAngle(vehID)
                vehVelocity = self._getVelocity(vehID, vehPosition, Tdetect)
                self.newVehicleInfo[vehID] = [vehPosition, vehHeading, vehVelocity, Tdetect]


    def _getIncomingLaneInfo(self):
        laneInfo = defaultdict(list) 
        for lane in list(np.unique(np.array(self.controlledLanes))):
            shape = traci.lane.getShape(lane)
            width = traci.lane.getWidth(lane)
            heading = self._getHeading(shape[1], shape[0])

            dx = shape[0][0] - shape[1][0] 
            dy = shape[0][1] - shape[1][1]
            if abs(dx) > abs(dy):
                roadBounds = ((shape[0][0], shape[0][1] + width), (shape[1][0], shape[1][1] - width))
            else: 
                roadBounds = ((shape[0][0] + width, shape[0][1]), (shape[1][0] - width, shape[1][1]))
            laneInfo[lane] = [heading, roadBounds]

        return laneInfo


    def _getOncomingVehicles(self):
        # Oncoming if (in active lane & heading matches oncoming heading & 
        # is in lane bounds)
        activeLanes = self._getActiveLanes()
        vehicles = []
        for lane in activeLanes:
            for vehID in self.oldVehicleInfo.keys():
                # If on correct heading pm 10deg
                if (np.isclose(self.oldVehicleInfo[vehID][1], self.laneDetectionInfo[lane][0], atol=10)
                    # If in lane x bounds
                    and min(self.laneDetectionInfo[lane][1][0][0], self.laneDetectionInfo[lane][1][1][0]) < 
                    self.oldVehicleInfo[vehID][0][0] < 
                    max(self.laneDetectionInfo[lane][1][0][0], self.laneDetectionInfo[lane][1][1][0])
                    # If in lane y bounds
                    and min(self.laneDetectionInfo[lane][1][0][1], self.laneDetectionInfo[lane][1][1][1]) < 
                    self.oldVehicleInfo[vehID][0][1] < 
                    max(self.laneDetectionInfo[lane][1][0][1], self.laneDetectionInfo[lane][1][1][1])):
                    # Then append vehicle
                    vehicles.append(vehID)

        vehicles = list(np.unique(np.array(vehicles)))
        return vehicles


    def _getActiveLanes(self):
        # Get the current control string to find the green lights
        stageCtrlString = self.junctionData.stages[self.lastStageIndex].controlString
        activeLanes = []
        for i, letter in enumerate(stageCtrlString):
            if letter == 'G':
                activeLanes.append(self.controlledLanes[i])
        # Get a list of the unique active lanes
        activeLanes = list(np.unique(np.array(activeLanes)))
        return activeLanes


    def _getLaneInductors(self):
        laneInductors = defaultdict(list)

        for loop in traci.inductionloop.getIDList():
            loopLane = traci.inductionloop.getLaneID(loop)
            if loopLane in self.controlledLanes and 'upstream' not in loop:
                laneInductors[loopLane].append(loop)
            
        return laneInductors


    def _getFurthestStationaryVehicle(self, vehIDs):
        furthestID = ''
        maxDistance = -1
        speedLimit = traci.lane.getMaxSpeed(self._getActiveLanes()[0])
        for ID in vehIDs:
            vehPosition = np.array(self.oldVehicleInfo[ID][0])
            distance = np.linalg.norm(vehPosition - self.jcnPosition)
            if distance > maxDistance and self.oldVehicleInfo[ID][2] < 0.05*speedLimit:
                furthestID = ID
                maxDistance = distance

        return [furthestID, maxDistance]


    def _getNearestVehicle(self, vehIDs):
        nearestID = ''
        minDistance = self.nearVehicleCatchDistance + 1
        
        for ID in vehIDs:
            vehPosition = np.array(self.oldVehicleInfo[ID][0])
            distance = np.linalg.norm(vehPosition - self.jcnPosition)
            if distance < minDistance:
                nearestID = ID
                minDistance = distance

        return [nearestID, minDistance]


    def _getLaneDetectTime(self):
        activeLanes = self._getActiveLanes()
        meanDetectTimePerLane = np.zeros(len(activeLanes))
        for i, lane in enumerate(activeLanes):
            detectTimes = []
            for loop in self.laneInductors[lane]:
                detectTimes.append(traci.inductionloop.getTimeSinceDetection(loop))
            meanDetectTimePerLane[i] = np.mean(detectTimes)

        return meanDetectTimePerLane
