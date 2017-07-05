def SPaTVehicleControl(junctions):
	gpsRate = 100
    # Get connected vehicles
    vehicles  = defaultdict(list)
    for vehID in traci.vehicle.getIDList():
        if traci.vehicle.getTypeID(vehID) == 'typeITSCV':
            vehicles[vehID]

    junctions = defaultdict(list)
    for jcnID in traci.trafficlights.getIDList():
        junctions[jcnID] = traci.juction.getPosition()