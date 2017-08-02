model;

param nWeeks;
param nDays;
param nAllowedRests;

set REQSHIFTS;
set NONREQSHIFTS;
set SHIFTS := REQSHIFTS union NONREQSHIFTS;
set WEEKS := 1..nWeeks;
set ALLWEEKS := {0} union WEEKS;	# superset including dummy week
set DAYS := 1..nDays;
set ALLDAYS := {0} union DAYS;		# superset including dummy day
set NIGHTSHIFTPREVDAYS;
set NIGHTSHIFTDAYS;
set RESTSHIFTDAYS;
set WEEKDAYS;
set WEEKENDS;

var schedule {SHIFTS, ALLWEEKS, ALLDAYS} binary;
var nightShift {ALLWEEKS} binary;
var weekendsOff {ALLWEEKS} binary;

# CONSTRAIN DUMMY SCHEDULE WEEKS/DAYS
s.t. DummyWeek {s in SHIFTS, d in DAYS}:
	schedule[s, 0, d] = schedule[s, nWeeks, d];
s.t. DummyDay {s in SHIFTS, w in WEEKS}:
	schedule[s, w-1, nDays] = schedule[s, w, 0]; 

# every slot has a shift assigned, except for nightshift week with 2
s.t. AlwaysShift {w in WEEKS, d in DAYS}:
	sum {s in SHIFTS} schedule[s, w, d] - nightShift[w] = 1;

# every day has one A/P/N
s.t. ReqShift {s in REQSHIFTS, d in DAYS}:
	sum {w in WEEKS} schedule[s, w, d] = 1;
	
# A followed by P
s.t. PAfterA {w in WEEKS, d in DAYS diff {7}}:
	schedule['P', w, d] = schedule['A', w, d-1];
s.t. AAfterASunday {w in WEEKS, d in {7}}:
	schedule['A', w, d] = schedule['A', w, d-1];

# only one night shift
s.t. OneNightShift:
	sum {w in WEEKS} nightShift[w] = 1;
	
# CREATE NIGHT SHIFT
# Fri - Sun night shift
s.t. NightShiftPrevWeek {w in WEEKS, d in NIGHTSHIFTPREVDAYS}:
	schedule['N', w-1, d] - nightShift[w] = 0;
# Mon - Thurs night shift
s.t. NightShiftWeek {w in ALLWEEKS, d in NIGHTSHIFTDAYS}:
	schedule['N', w, d] - nightShift[w] = 0;
# Fri - Sun rests
s.t. RestShiftWeek {w in WEEKS, d in RESTSHIFTDAYS}:
	schedule['Z', w, d] - nightShift[w] = 0;
# only three rests in whole schedule
s.t. RestLimit:
	sum {w in WEEKS, d in DAYS} schedule['Z', w, d] = nAllowedRests;

# weekdays on
s.t. WeekdaysOn{w in WEEKS, d in WEEKDAYS}:
	schedule['X', w, d] = 0;	
# weekends can be off
s.t. WeekendsOff{w in WEEKS, d in WEEKENDS}:
	schedule['X', w, d] >= weekendsOff[w];
# no consecutive weekends forced on
s.t. ConsecutiveWeekendsOff{w in WEEKS}:
	weekendsOff[w] + weekendsOff[w-1] >= 1;
	