import time
import krpc

conn = krpc.connect(name='Suborbital')

vessel = conn.space_center.active_vessel

ap = vessel.auto_pilot
ctl = vessel.control
ap.target_pitch_and_heading(90,90) # straight up
ap.engage() # make it so, number one
ctl.throttle = 1

time.sleep(1)

print('Launch!')
ctl.activate_next_stage()

while vessel.resources.amount('SolidFuel') > 0.1 :
	time.sleep(0.5)
print('Booster sep')
ctl.activate_next_stage()

while vessel.flight().mean_altitude < 10000 :
	time.sleep(1)
	
print('Gravity turn')
ap.target_pitch_and_heading(60,90)

while vessel.orbit.apoapsis_altitude < 100000 :
	time.sleep(1)

print('Booster sep')
ctl.throttle = 0
time.sleep(1)
ctl.activate_next_stage()
ap.disengage()

while vessel.flight.surface_altitude > 1000 :
	time.sleep(1)

ctl.activate_next_stage() # chutes

while vessel.flight(vessel.orbit.body.reference_frame).vertical_speed < 0.1 :
	print('Altitude %.1f m' % vessel.flight().surface_altitude)
	time.sleep(1)
	
print('Landed')