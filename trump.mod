model;

# ==============================================================
# DATA
# ==============================================================

param nWeeks;
param nAllowedRests;

# shifts
set REQSHIFTS;
set NONREQSHIFTS;
set SHIFTS := REQSHIFTS union NONREQSHIFTS;

# weeks
set WEEKS := 1..nWeeks;

# days
set WEEKDAYS;
set WEEKENDS;
set DAYS := WEEKDAYS union WEEKENDS;
set NIGHTSHIFTPREVDAYS;
set NIGHTSHIFTDAYS;
set RESTSHIFTDAYS;

# decision variables - include dummy weeks/days 0
var schedule {SHIFTS, {0} union WEEKS, {0} union DAYS} binary;
var nightShift {{0} union WEEKS} binary;
var weekendsOff {WEEKS} binary;		# no dummy, uses wraparound 'mod' instead

# ==============================================================
# FEASIBILITY CONSTRAINTS
# ==============================================================

# continuity for dummy weeks/days
s.t. DummyWeek {s in SHIFTS, d in DAYS}:
	schedule[s, 0, d] = schedule[s, card(WEEKS), d];
s.t. DummyDay {s in SHIFTS, w in WEEKS}:
	schedule[s, w-1, card(DAYS)] = schedule[s, w, 0]; 

# every slot has a shift assigned, except for nightshift week with 2
s.t. AlwaysShift {w in WEEKS, d in DAYS}:
	sum {s in SHIFTS} schedule[s, w, d] - nightShift[w] = 1;

# every day has one A/P/N
s.t. ReqShift {s in REQSHIFTS, d in DAYS}:
	sum {w in WEEKS} schedule[s, w, d] = 1;
	
# A followed by P or A on Sunday
s.t. PAfterA {w in WEEKS, d in DAYS diff {7}}:
	schedule['P', w, d] = schedule['A', w, d-1];
s.t. AAfterASunday {w in WEEKS, d in {7}}:
	schedule['A', w, d] = schedule['A', w, d-1];

# only one night shift week in roster
s.t. OneNightShiftWeek:
	sum {w in WEEKS} nightShift[w] = 1;
	
# create night shift
# Fri - Sun night shift in previous week
s.t. NightShiftPrevWeek {w in WEEKS, d in NIGHTSHIFTPREVDAYS}:
	schedule['N', w-1, d] - nightShift[w] = 0;
# Mon - Thurs night shift
s.t. NightShiftWeek {w in WEEKS, d in NIGHTSHIFTDAYS}:
	schedule['N', w, d] - nightShift[w] = 0;
# Fri - Sun rest shifts
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
	weekendsOff[w] + weekendsOff[w mod card(WEEKS) + 1] >= 1;
	
# ==============================================================
# OBJECTIVE CONSTRAINTS
# ==============================================================

param totalDays;
param nRegistrars;	 						# no. registrars per ward
param discountRate;
param WEEKLYADMISSIONRATE {1..7}; 			# average admissions per day
set ROSTERDAYS := 1..totalDays;
set WARDS;	 								# LIME NAVY YELLOW
var occupancy {WARDS, ROSTERDAYS};
var admitting {WARDS, ROSTERDAYS} binary;
var wardDiff {ROSTERDAYS};					# daily ward imbalance
var totalWardDiff;
param startingWeeks {WARDS, 1..nRegistrars};# roster starting week per registrar

# calculate occupancy for the next day
# is the ward admitting?
# note: week = ceil(r/card(DAYS))
# 		day  = (r-1) mod card(DAYS) + 1
s.t. Admittance {wa in WARDS, r in ROSTERDAYS}:
	admitting[wa, (r+1) mod totalDays + 1] = sum {re in 1..nRegistrars} schedule['A', ceil((r+7*(startingWeeks[wa, re]-1))/card(DAYS)) mod card(WEEKS)+1, (r-1) mod card(DAYS) + 1];
	
# calculate occupancy
s.t. Occupancy {wa in WARDS, r in ROSTERDAYS}:
	occupancy[wa, r mod totalDays + 1] = occupancy[wa, r]*(1-discountRate) + admitting[wa, r]*WEEKLYADMISSIONRATE[(r-1) mod card(DAYS) + 1];
	
# calculate ward differences
s.t. WardDifferenceA {r in ROSTERDAYS, wa in WARDS, wb in WARDS}:
	wardDiff[r] >= occupancy[wa, r] - occupancy[wb, r];
	
s.t. TotalWardDifference:
	totalWardDiff = sum {r in ROSTERDAYS} wardDiff[r];
	
# ==============================================================
# OBJECTIVE FUNCTION
# ==============================================================

minimize ObjectiveOn: sum {r in ROSTERDAYS} wardDiff[r];
#minimize ObjectiveOff: 0;
