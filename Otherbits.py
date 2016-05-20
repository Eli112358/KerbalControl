import krpc

conn = krpc.connect()

vessel = conn.space_center.active_vessel

def OhShit() : # presented without comment
	for parachute in vessel.parts.parachutes:
		parachute.deploy()

# control from here
ports = vessel.parts.docking_ports
port = list(filter(lambda p : p.part.title == 'Clamp-O-Tron Docking Port', ports))[0]
part = port.partitionvessel.parts.controlling = part