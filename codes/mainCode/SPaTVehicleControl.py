import traci
from math import degrees, atan2
import numpy as np

def SPaTVehicleControl(tlLogic):
    gpsRate = 100
    ctrlRadius = 100
    # Get connected vehicles
    vehicles  = {}
    for vehID in traci.vehicle.getIDList():
        if traci.vehicle.getTypeID(vehID) == 'typeITSCV':
            vehicles[vehID] = ''

    # Get Junctions
    junctions = {'':np.array([1e3,1e3])}
    for jcnID in traci.trafficlights.getIDList():
        junctions[jcnID] = np.array(traci.junction.getPosition(jcnID))

    # Get juction we're approaching
    for vehID in vehicles.keys():
        for junction in junctions.keys():
            if junction != '':
                lane = traci.vehicle.getLaneID(vehID)
                tlLanes = traci.trafficlights.getControlledLanes(junction)
                vehPosition = np.array(traci.vehicle.getPosition(vehID))
                distance = np.linalg.norm(vehPosition - junctions[junction])

                lastJnc = getLastJnc(vehID, junctions)
                if lastJnc != '':
                    lastDistance = np.linalg.norm(vehPosition - junctions[lastJnc])
                else:
                    lastDistance = 100
                # print([vehID, lastJnc, lastDistance])
                if lane in tlLanes and distance <= 100 and lastDistance > 50 and vehicles[vehID] == '':
                    vehicles[vehID] = junction
                    break 
            else:
                vehicles[vehID] = ''


    # Get lane, get time until green
    stepSize = traci.simulation.getDeltaT()*0.001
    comfortableDecel = 2.0
    for vehID in vehicles.keys():
        if vehicles[vehID] != '':
            vehPosition = np.array(traci.vehicle.getPosition(vehID))
            distance = np.linalg.norm(vehPosition - junctions[junction]) 
            lane = traci.vehicle.getLaneID(vehID)
            tlLanes = traci.trafficlights.getControlledLanes(vehicles[vehID])

            if lane not in tlLanes:
                # continue as normal if on internal lane
                traci.vehicle.setSpeed(vehID, -1)
                #traci.vehicle.setColor(vehID, (255,255,0,0))
                continue

            for tl in tlLogic:
                if tl.junctionData.id == vehicles[vehID]:
                    spatInfo = tl.getSPaTData()
                    break
            # get time to green for this lane
            
            laneIndex = tlLanes.index(lane)
            lanePhase = spatInfo[1][laneIndex]
            greenTime = spatInfo[2][laneIndex]

            if lanePhase in 'Gy':
                # Resume Car-following
                traci.vehicle.setSpeed(vehID, -1)
                #traci.vehicle.setColor(vehID, (255,255,0,0))
            else:
                # slowDown is cumulative, reset to normal CF then set slowdown
                # (vf-v0)/dt, dt = greenTime, vf=0 -> -v0/greenTime  
                v0 = traci.vehicle.getSpeed(vehID)
                vTarget = (distance-10)/(greenTime+10)
                # target deceleration (change in v w/ t)
                dvdt =  ((vTarget-v0)/(greenTime+10))
                # maxDecel = (traci.vehicle.getDecel(vehID))*stepSize

                # vNextStep = min(abs(1.5*dvdt), comfortableDecel*stepSize)
                vNextStep = comfortableDecel*stepSize
                if dvdt < 0:
                    vNextStep = max(vTarget, v0 - vNextStep)
                elif dvdt > 0:
                    vNextStep = min(vTarget, v0 + vNextStep)
                else:
                    vNextStep = vTarget
                #print([vehID, vTarget, v0, vNextStep, dvdt])
                traci.vehicle.setSpeed(vehID, vNextStep)
                #traci.vehicle.setColor(vehID, (255,0,0,0))


    allJncLanes = []
    for jnc in junctions.keys():
        if jnc != '':
            allJncLanes += traci.trafficlights.getControlledLanes(jnc)

    for vehID in traci.vehicle.getIDList():
        if traci.vehicle.getLaneID(vehID) not in allJncLanes:
            traci.vehicle.setSpeed(vehID, -1)
            #traci.vehicle.setColor(vehID, (255,255,0,0))


def getHeading(currentLoc, prevLoc):
    dy = currentLoc[1] - prevLoc[1]
    dx = currentLoc[0] - prevLoc[0]
    if currentLoc[1] == prevLoc[1] and currentLoc[0] == prevLoc[0]:
        heading = -1
    else:
        heading = degrees(atan2(dy, dx))%360
    # Map angle to make compatible with SUMO heading
    if 0 <= heading <= 90:
        heading = 90 - heading
    elif 90 < heading < 360:
        heading = 450 - heading
    return heading


def headingMatch(source, ref, tol):
    bound1 = (source+tol)%360
    bound2 = (source-tol)%360

    if min(bound1, bound2) <= ref <=max(bound1, bound2):
        return True
    else:
        return False


def isCloser(reference, point1, point2):
    # Is ref closer to point 1 than point 2
    if len(point1) < 1 and len(point2) > 0:
        return False
    elif len(point1) > 0 and len(point2) < 1:
        return True
    else:
        dist1 = np.linalg.norm(np.diff([reference, point1], axis=0))
        dist2 = np.linalg.norm(np.diff([reference, point2], axis=0))

        if dist1 < dist2:
            return True
        else:
            return False

def velocityLimit(x, xt=100, n=3):
    assert x <= xt, 'x not <= xt'
    xt3 = xt**n

    return np.round(1.0 - (xt3 - x**n)/xt3, 1)

def getLastJnc(vehID, junctions):
    lane = traci.vehicle.getLaneID(vehID)
    a,b = lane.split('_')[0].split(':')
    oppLane = b + ':' + a + '_0'
    lastJnc = ''
    for jnc in junctions.keys():
        if jnc != '' and oppLane in traci.trafficlights.getControlledLanes(jnc):
            lastJnc = jnc
    return lastJnc

