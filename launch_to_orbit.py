import krpc
import time
import math

m = 1
km = 1000

turn_start_alt = 250
turn_end_alt = 45*km
target_alt = 150*km

conn = krpc.connect(name='Launch to orbit')
vessel = conn.space_center.active_vessel

ut = conn.add_stream(getattr, conn.space_center, 'ut')
altitude = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')
apoapsis = conn.add_stream(getattr, vessel.orbit, 'apoapsis_altitude')
periapsis = conn.add_stream(getattr, vessel.orbit, 'periapsis_altitude')
eccentricity = conn.add_stream(getattr, vessel.orbit, 'eccentricity')

stage_2_resources = vessel.resources_in_decouple_stage(stage=2, cumulative=False)
stage_3_resources = vessel.resources_in_decouple_stage(stage=3, cumulative=False)
srb_fuel = conn.add_stream(stage_3_resources.amount, 'SolidFuel')
launcher_fuel = conn.add_stream(stage_2_resources, 'LiquidFuel')

vessel.control.sas = False
vessel.control.rcs = False
vessel.control.throttle = 1

time.sleep(1)
print('Launch!')

vessel.control.activate_next_stage()
vessel.auto_pilot.engage()
vessel.auto_pilot.target_pitch_and_heading(90,90)

# ascent loop
srbs_separated = false
turn_angle = 0
while True:
	# grav turn
	if altitude() > turn_start_altitude and altitude() < turn_end_altitude :
		frac = (altitude()-turn_start_altitude)/(turn_end_altitude-turn_start_altitude)
		new_turn_angle = frac*90
		if abs(new_turn_angle-turn_angle) > 0.5 : #degrees
			turn_angle = new_turn_angle
			vessel.auto_pilot.target_pitch_and_heading(90-turn_angle, 90)
		
	#check srbs
	if not srbs_separated :
		if srb_fuel() < 0.1 :
			vessel.control.activate_next_stage()
			srbs_separated = True
			print('Booster sep')
			
	if apoapsis() > 0.9*target_altitude :
		print('Approaching target apoapsis')
		break
		
vessel.control.throttle = 0.25
while apoapsis() < target_altitude :
	pass

print ('Target apoapsis reached')
vessel.control.throttle = 0

print('Coasting out of atmo')
while altitude() < 70500 :
	pass

print('Circularizing...')
#is this math right?
mu = vessel.orbit.body.gravitational_parameter
r = vessel.orbit.apoapsis
a1 = vessel.orbit.semi_major_axis
a2 = r
v1 = math.sqrt(mu*((2./r)-(1./a1)))
v2 = math.sqrt(mu*((2./r)-(1./a2)))
delta_v = v2-v1
node = vessel.control.add_node(ut() + vessel.orbit.time_to_apoapsis, prograde=delta_v)

F = vessel.available_thrust
Isp = vessel.specific_impulse*9.81
m0 = vessel.mass
m1 = m0*math.exp(-delta_v/Isp)
flow_rate = F/Isp
burn_time = (m0-m1)/flow_rate

#set orientation
vessel.auto_pilot.reference_frame = node.reference_frame
vessel.auto_pilot.target_direction = (0,1,0)
vessel.auto_pilot.wait()

#wait until burn
print('Coasting to burn')
burn_ut = ut() + vessel.orbit.time_to_apoapsis - burn_time/2.
lead_time = 5
conn.space_center.warp_to(burn_ut - lead_time)

#execute burn
print('Burning')
time_to_apoapsis = conn.add_stream(getattr, vessel.orbit, 'time_to_apoapsis')
while time_to_apoapsis() - burn_time/2. > 0 :
	pass

vessel.control.throttle = 1
time.sleep(burn_time-0.5)

vessel.control.throttle = 0.05
remaining_burn = conn.add_stream(node.remaining_burn_vector, node.reference_frame)
while remaining_burn()[1] > 0 :
	pass
vessel.control.throttle = 0
node.remove()

print('Launch complete')