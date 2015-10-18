#!/usr/bin/env python2

#   Copyright 2015 Adamo Ferro
#
#   This file is part of SLightliMon.
#
#   SLightliMon is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   SLightliMon is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with SLightliMon. If not, see <http://www.gnu.org/licenses/>.


import sys, argparse
import json
import processing.profile_analyzer
import processing.profile_merger
import processing.anomaly_detector


SAMPLING_INT=1				# minutes, fixed. TODO: make it a parameter and handle everywhere in the rest of the code


#~ TODO: put in a JSON configuration file
ERROR_CODES=dict()
ERROR_CODES["arg_parse"]="Problem during argument parsing"
ERROR_CODES["import_io_txt"]="Cannot import text reader"
ERROR_CODES["import_io_rrd"]="Cannot import RRD reader"
ERROR_CODES["period_general"]="Inconsistent period: end timestamp precedes start timestamp"
ERROR_CODES["delta_t"]="Base analysis time interval not valid"
ERROR_CODES["delta_t_large"]="Base analysis time interval longer than analyzed period"
ERROR_CODES["avg_t"]="Average interval not valid"
ERROR_CODES["p_off"]="Maximum power consumption during off state not valid for phase "
ERROR_CODES["v_thrs"]="Minimum and/or maximum allowed voltage values not valid"
ERROR_CODES["v_dt"]="Maximum total time of non-acceptable voltage not valid"
ERROR_CODES["cosphi_min"]="Minimum acceptable cosphi not valid"
ERROR_CODES["cosphi_dt"]="Maximum total time of non-acceptable cosphi not valid"
ERROR_CODES["data_min_avail"]="Minimum data availability in % for running the whole algorithm not valid"
ERROR_CODES["ref_days"]="Number of reference days not valid"
ERROR_CODES["anomaly_abs_p_shift"]="Minimum absolute power shift for detecting an anomaly not valid"
ERROR_CODES["anomaly_rel_p_shift"]="Minimum relative power shift for detecting an anomaly in % not valid"
ERROR_CODES["anomaly_min_dt"]="Minimum duration of an anomaly state not valid"
ERROR_CODES["anomaly_guard_dt"]="Minimum time distance allowed from an on/off event to an anomaly not valid"
ERROR_CODES["energy_rel_shift"]="Minimum relative power consumption offset is not valid"
ERROR_CODES["ref_min_avail"]="Minimum data reliability for running the whole algorithm in % not valid"
ERROR_CODES["data_length"]="Input data have different lengths"

WARNING_CODES=dict()
WARNING_CODES["avg_t"]="Average interval incremented by 1 minute to get an odd number"

def main(argv):

	def parse_args():
		parser=argparse.ArgumentParser(description='SLightliMon ALARM DETECTOR - Analyzes and detects alarms from public lighting power profiles.')

		#~ PERIOD TO BE ANALYZED
		parser.add_argument('-ts','--t_start',required=True,type=int,help='start UNIX epoch timestamp [seconds]')
		parser.add_argument('-te','--t_end',required=True,type=int,help='end UNIX epoch timestamp [seconds]')
		
		#~ INPUT FILES AND FORMAT
		parser.add_argument('-p1','--power_data_ph1',required=True,type=str,help='active power data for phase 1, expressed in Watts')
		parser.add_argument('-p2','--power_data_ph2',type=str,default='',help='active power data for phase 2, expressed in Watts. Do not use if single-phase data.')
		parser.add_argument('-p3','--power_data_ph3',type=str,default='',help='active power data for phase 3, expressed in Watts. Do not use if single-phase data.')
		parser.add_argument('-v1','--voltage_data_ph1',required=True,type=str,help='voltage data for phase 1, expressed in Volts')
		parser.add_argument('-v2','--voltage_data_ph2',type=str,default='',help='voltage data for phase 2, expressed in Volts. Do not use if single-phase data.')
		parser.add_argument('-v3','--voltage_data_ph3',type=str,default='',help='voltage data for phase 3, expressed in Volts. Do not use if single-phase data.')
		parser.add_argument('-e','--energy_data',type=str,default='',help='total active energy data. Optional.')
		parser.add_argument('-c','--cosphi_data',type=str,default='',help='cos(phi) data. Optional.')
		parser.add_argument('-nor','--no_one_read_meas',dest='no_one_read_meas',action='store_true',help='set if measurements are NOT acquired at the same time (e.g., they are obtained through separated MODBUS queries from the registers of an energy meter, instead of an unique query from all registers). Independently from this parameter, power and voltage measurements related to the same phase are assumed to be anyway taken at the same time.')
		parser.add_argument('-rf','--rrd_function',default='AVERAGE',choices=['AVERAGE','MIN','MAX','LAST'],help='RRD consolidation function. Default is AVERAGE.')
		parser.add_argument('-txt','--text',dest='text',action='store_true',help='set if data are in text format instead of RRD')
			
		#~ BASE ALGORITHM PARAMETERS
		parser.add_argument('-dt','--delta_t',type=int,help='base analysis time interval [minutes, positive]. Default is 5.',default='5')
		parser.add_argument('-at','--avg_t',type=int,help='average interval [minutes, positive odd number]. Default is 5.',default='5')
		parser.add_argument('-po1','--poff_ph1',type=int,help='maximum power consumption during off state for phase 1 [watts]. Default is 100.',default='100')
		parser.add_argument('-po2','--poff_ph2',type=int,help='maximum power consumption during off state for phase 2 [watts]. Default is 100.',default='100')
		parser.add_argument('-po3','--poff_ph3',type=int,help='maximum power consumption during off state for phase 3 [watts]. Default is 100.',default='100')
		parser.add_argument('-vm','--v_min',type=float,help='minimum value of acceptable voltage [volts]. Default is 210.',default='210')
		parser.add_argument('-vM','--v_max',type=float,help='maximum value of acceptable voltage [volts]. Default is 250.',default='250')    
		parser.add_argument('-vt','--v_dt',type=int,help='maximum total non-consecutive time of non-acceptable voltage allowed [hours]. Default is 3.',default='3')    
		parser.add_argument('-cm','--cosphi_min',type=float,help='minimum value of acceptable cosphi. Default is 0.9.',default='0.9')
		parser.add_argument('-ct','--cosphi_dt',type=int,help='maximum total non-consecutive time [hours] of low cosphi allowed during ON state. Default is 3.',default='3')
		parser.add_argument('-da','--data_min_avail',type=float,help='minimum data availability for running the whole algorithm [percent]. Default is 70.',default='70')

		#~ EXTENDED ALGORITHM PARAMETERS
		parser.add_argument('-rd','--ref_days',type=int,help='number of reference days. Default is 0, that is no comparison with past data is performed. If >0 input files must contain also past data.',default='0')
		parser.add_argument('-aps','--anomaly_abs_p_shift',type=int,help='minimum absolute power shift for detecting an anomaly [watts]. Default is 200.',default='200')
		parser.add_argument('-arps','--anomaly_rel_p_shift',type=float,help='minimum relative power shift for detecting an anomaly [percent of reference profile]. Default is 2.',default='2')
		parser.add_argument('-atm','--anomaly_min_dt',type=int,help='minimum duration of an anomaly state [minutes]. Default is 7.',default='7')
		parser.add_argument('-agt','--anomaly_guard_dt',type=int,help='minimum time distance allowed from an on/off event to an anomaly [minutes]. Default is 10.',default='10')
		parser.add_argument('-ers','--energy_rel_shift',type=float,help='minimum relative total energy offset for detecting an anomaly [percent of reference profile total energy]. Default is 15.',default='15')
		parser.add_argument('-ra','--ref_min_avail',type=float,help='minimum reference data availability for running the detection of anomalies [percent]. Default is 70.',default='70')

		parser.add_argument('-d','--debug',dest='debug',action='store_true',help='debug mode.')
		parser.add_argument('-v','--version',action='version',version='%(prog)s 0.3')
		
		parser.set_defaults(text=False)
		parser.set_defaults(no_one_read_meas=False)
		parser.set_defaults(debug=False)

		args=None
		try:
			args=parser.parse_args()
		except:
			pass

		return args
		

	output_json=dict()
	output_json["errors"]=list()
	output_json["warnings"]=list()
	output_json_results=None

	
	args=parse_args()

	if args is not None:

		#~ ********** ARGUMENT DETAILED PARSING **********
		
		DEBUG=args.debug
		
		#~ --- PERIOD TO BE ANALYZED ---
		TS_START=args.t_start
		TS_END=args.t_end
		ANALYSIS_PERIOD=TS_END-TS_START
		if ANALYSIS_PERIOD<=0:
			output_json["errors"].append(ERROR_CODES["period_general"])
			ANALYSIS_PERIOD=0


		#~ --- INPUT FILES AND FORMAT ---
		P_DATA_FILENAMES=list()
		P_DATA_FILENAMES.append(args.power_data_ph1)
		V_DATA_FILENAMES=list()
		V_DATA_FILENAMES.append(args.voltage_data_ph1)
		if (args.power_data_ph2 != "" and
			args.power_data_ph3 != "" and
			args.voltage_data_ph2 != "" and
			args.voltage_data_ph3 != ""):
			P_DATA_FILENAMES.append(args.power_data_ph2)
			P_DATA_FILENAMES.append(args.power_data_ph3)
			V_DATA_FILENAMES.append(args.voltage_data_ph2)
			V_DATA_FILENAMES.append(args.voltage_data_ph3)
		N_PHASES=len(P_DATA_FILENAMES)
			
		E_DATA_FILENAME=args.energy_data
		C_DATA_FILENAME=args.cosphi_data

		NO_ONE_READ_MEAS=False
		if args.no_one_read_meas:
			NO_ONE_READ_MEAS=True

		RRD_FUNCTION=args.rrd_function

		IN_FILE_FORMAT=""
		if args.text:
			IN_FILE_FORMAT="txt"
			try:
				from io import data_reader_txt as io_dr
			except:
				output_json["errors"].append(ERROR_CODES["import_io_txt"])
		else:
			IN_FILE_FORMAT="rrd"
			try:
				from io import data_reader_rrd as io_dr
			except:
				output_json["errors"].append(ERROR_CODES["import_io_rrd"])


		#~ --- BASE ALGORITHM PARAMETERS ---		
		DELTA_T=args.delta_t     # minutes, used to detect power shifts
		if DELTA_T<=0:
			output_json["errors"].append(ERROR_CODES["delta_t"])
		elif DELTA_T>=ANALYSIS_PERIOD and ANALYSIS_PERIOD>0:
			output_json["errors"].append(ERROR_CODES["delta_t_large"])
			
		AVG_INTERVAL=args.avg_t
		if AVG_INTERVAL<=0:
			output_json["errors"].append(ERROR_CODES["avg_t"])
		else:
			if AVG_INTERVAL % 2 ==0:
				AVG_INTERVAL+=1
				output_json["warnings"].append(WARNING_CODES["avg_t"])

		P_OFF_MAXS=list()
		P_OFF_MAXS.append(args.poff_ph1)
		if N_PHASES>1:
			P_OFF_MAXS.append(args.poff_ph2)
			P_OFF_MAXS.append(args.poff_ph3)
		for i_ph in xrange(0,N_PHASES):
			if P_OFF_MAXS[i_ph] <= 0:
				output_json["errors"].append(ERROR_CODES["p_off"]+str(i_ph+1))
		
		V_MIN=args.v_min
		V_MAX=args.v_max
		if V_MIN>=V_MAX or V_MIN<=0 or V_MAX<=0:
			output_json["errors"].append(ERROR_CODES["v_thrs"])

		V_DT_MAX=args.v_dt*60                # given in hours by the user, converted in minutes
		if V_DT_MAX<=0:
			output_json["errors"].append(ERROR_CODES["v_dt"])
		
		COSPHI_MIN=args.cosphi_min         
		if COSPHI_MIN<=0:
			output_json["errors"].append(ERROR_CODES["cosphi_min"])
			
		COSPHI_DT_MAX=args.cosphi_dt*60		# given in hours by the user, converted in minutes
		if COSPHI_DT_MAX<=0:
			output_json["errors"].append(ERROR_CODES["cosphi_dt"])

		MIN_OVERALL_DATA_AVAILABILITY=args.data_min_avail/100.
		if MIN_OVERALL_DATA_AVAILABILITY<=0:
			output_json["errors"].append(ERROR_CODES["data_min_avail"])



		#~ --- COMPARISON TO REFERENCE PARAMETERS ---
		N_REF_DAYS=args.ref_days
		if N_REF_DAYS<0:
			output_json["errors"].append(ERROR_CODES["ref_days"])
		
		
		ANOMALY_DELTA_P=args.anomaly_abs_p_shift
		if ANOMALY_DELTA_P<=0:
			output_json["errors"].append(ERROR_CODES["anomaly_abs_p_shift"])

			
		ANOMALY_DELTA_P_REL=args.anomaly_rel_p_shift/100.
		if ANOMALY_DELTA_P_REL<=0:
			output_json["errors"].append(ERROR_CODES["anomaly_rel_p_shift"])


		ANOMALY_MIN_DELTA_T=args.anomaly_min_dt
		if ANOMALY_MIN_DELTA_T<=0:
			output_json["errors"].append(ERROR_CODES["anomaly_min_dt"])

		
		ANOMALY_FILTER_DELTA_T=args.anomaly_guard_dt
		if ANOMALY_FILTER_DELTA_T<=0:
			output_json["errors"].append(ERROR_CODES["anomaly_guard_dt"])

			
		ENERGY_REL_OFFSET=args.energy_rel_shift/100.
		if ENERGY_REL_OFFSET<=0:
			output_json["errors"].append(ERROR_CODES["energy_rel_shift"])

			
		MIN_OVERALL_REF_AVAILABILITY=args.ref_min_avail/100.
		if MIN_OVERALL_REF_AVAILABILITY<=0:
			output_json["errors"].append(ERROR_CODES["ref_min_avail"])			


	else:
		output_json["errors"].append(ERROR_CODES["arg_parse"])





	if len(output_json["errors"])==0:			# if no errors

		#~ create data reader
		dr=io_dr.data_reader(ts_start=TS_START,ts_end=TS_END,n_ref_days=N_REF_DAYS,s_int=SAMPLING_INT,err=output_json["errors"],extra=RRD_FUNCTION)
		dr.DEBUG=DEBUG

		#~ create profile analyzers
		pa_data=processing.profile_analyzer.profile_analyzer(TS_START,SAMPLING_INT,DELTA_T,AVG_INTERVAL,ANOMALY_FILTER_DELTA_T,V_MIN,V_MAX)
		pa_data.DEBUG=DEBUG
		pa_ref=processing.profile_analyzer.profile_analyzer(TS_START,SAMPLING_INT,DELTA_T,AVG_INTERVAL,ANOMALY_FILTER_DELTA_T,V_MIN,V_MAX)
		pa_ref.DEBUG=DEBUG

		#~ if necessary, create the anomaly detector
		ad=None
		if N_REF_DAYS>0:
			ad=processing.anomaly_detector.anomaly_detector(TS_START,SAMPLING_INT,DELTA_T,ANOMALY_DELTA_P,ANOMALY_DELTA_P_REL,ANOMALY_MIN_DELTA_T)
			ad.DEBUG=DEBUG

		#~ prepare outputs and working variables
		output_json_results=dict()
		output_json_results["phases"]=dict()
		n_data_points=int((TS_END-TS_START)/60/SAMPLING_INT)+1	
		data_availability=0
		ref_availability=0
		ctrl_data=dict()
		
		#~ this variables are used to skip calculations when data and/or reference data have low reliability
		avoid_calcs=False
		ref_avoid_calcs=False
		
		
		#~ POWER ANALYSIS, for each phase
		for i_phase in xrange(0,N_PHASES):
			data_p=None
			data_p_ref=None
			data_v=None
			data_v_ref=None
			
			if DEBUG:
				print "\n\n********** PHASE",(i_phase+1),"**********"
			
			if not avoid_calcs:
				
				#~ read power data and reference power data
				dr.read(P_DATA_FILENAMES[i_phase])
				if len(output_json["errors"])==0:
					data_p=dr.data
					data_p_ref=dr.ref_data
				else:
					break
				
				#~ read voltage data and reference voltage data	
				dr.read(V_DATA_FILENAMES[i_phase])
				if len(output_json["errors"])==0:
					data_v=dr.data
					data_v_ref=dr.ref_data
				else:
					break
				
		
				if len(output_json["errors"])==0:
					phase_data=dict()
					output_json_results["phases"][i_phase]=phase_data
					
					#~ use the profile analyzer to estimate data availability.
					#~ If three-phase data are collected at the same time for all the phases (e.g. with one single query)
					#~ availability is the same for all the phases, so it's calculated only for the first one.
					pa_data.set_data(data_p,data_v,P_OFF_MAXS[i_phase],(not NO_ONE_READ_MEAS))
					if i_phase==0 or NO_ONE_READ_MEAS:
						data_availability=pa_data.estimate_availability()
					phase_data["availability"]=data_availability

					if data_availability>=MIN_OVERALL_DATA_AVAILABILITY:
						
						#~ analyze data to get the averaged power profile, switch on/off markers and voltage anomalies
						data_p_avg,data_switch_markers,ctrl_data[i_phase],n_high_v_points,n_low_v_points=pa_data.analyze_profile()

						phase_data["switch_markers"]=data_switch_markers
						phase_data["v"]=dict()
						phase_data["v"]["high_dt"]=n_high_v_points
						phase_data["v"]["low_dt"]=n_low_v_points
						phase_data["v"]["alarm"]=(1 if n_high_v_points+n_low_v_points>V_DT_MAX else 0)


						if N_REF_DAYS>0:
							phase_data["reference"]=dict()
							if not ref_avoid_calcs:
								
								#~ merge the reference power profile into an unique "median" profile and calculates reference data availability
								pm=processing.profile_merger.profile_merger(data_p_ref,data_v_ref,data_v)
								pm.DEBUG=DEBUG
								ref_p, ref_v, ref_availability = pm.merge()								
								phase_data["reference"]["availability"]=ref_availability
								
								if ref_availability>=MIN_OVERALL_REF_AVAILABILITY:
									
									#~ use the same processing steps of actual data in order to analyze the reference profile and get
									#~ the information necessary to detect power anomalies
									pa_ref.set_data(ref_p,ref_v,P_OFF_MAXS[i_phase],(not NO_ONE_READ_MEAS))
									if i_phase==0 or NO_ONE_READ_MEAS:
										pa_ref.estimate_availability()		# used only to find NaN intervals
									
									ref_p_avg,_,ctrl_ref,_,_=pa_ref.analyze_profile()
									
									#~ detect anomalies using the averaged power profiles (actual and reference)
									ad.set_data(data_p_avg,ctrl_data[i_phase],ref_p_avg,ctrl_ref)
									anomaly_markers=ad.detect()

									phase_data["reference"]["anomaly_markers"]=anomaly_markers
								
								else:		# low reference availability
									phase_data["reference"]["anomaly_markers"]={}
									ref_avoid_calcs=True and (not NO_ONE_READ_MEAS)
							else:
								phase_data["reference"]["availability"]=ref_availability
								phase_data["reference"]["anomaly_markers"]={}

					else:		# low data availability
						phase_data["switch_markers"]={}
						phase_data["v"]={}
						avoid_calcs=True and (not NO_ONE_READ_MEAS)
				else:
					break	# errors while reading input data, block everything
			else:
				phase_data=dict()
				output_json_results["phases"][i_phase]=phase_data
				phase_data["availability"]=data_availability
				phase_data["switch_markers"]={}
				phase_data["v"]={}
		
		
		#~ ENERGY ANALYSIS
		if E_DATA_FILENAME != "":
			output_json_results["energy"]=dict()
			if not avoid_calcs:
				
				#~ read energy data
				dr.read(E_DATA_FILENAME)
				if len(output_json["errors"])==0:
					data_e=dr.data
					data_e_ref=dr.ref_data
					
					
					#~ find the first and the last data point with available energy data
					data_e_start=0
					data_e_end=0
					i_data_start=0                 
					while i_data_start<n_data_points:
						if type(data_e[i_data_start]) is float:
						   data_e_start=data_e[i_data_start]
						   break
						i_data_start+=1
						
					i_data_end=n_data_points-1
					while i_data_end>=0:
						if type(data_e[i_data_end]) is float:
						   data_e_end=data_e[i_data_end]
						   break
						i_data_end-=1                        

					#~ calculates energy data availability as the ratio between the duration
					#~ of the measurable period and the duration of the whole period under analysis
					i_data_offset=max(i_data_end-i_data_start+1,0)
					data_e_availability=float(i_data_offset)/n_data_points
					output_json_results["energy"]["availability"]=data_e_availability
					
					if data_e_availability>MIN_OVERALL_DATA_AVAILABILITY:
						
						#~ if availability is sufficient, energy consumption is calculated as the difference
						#~ between the energy values measured at the beginning and at the times retrieved before
						data_e_offset=data_e_end-data_e_start
						output_json_results["energy"]["offset"]=data_e_offset

						if N_REF_DAYS>0:
							output_json_results["energy"]["reference"]=dict()
							
							#~ Do the same for each reference day
							ref_e_offsets=list()
							ref_e_availability=1
							for i_ref_day in xrange(0,N_REF_DAYS):
								i_ref_start=0                 
								while i_ref_start<n_data_points:
									if type(data_e_ref[i_ref_day][i_ref_start]) is float:
									   ref_e_start=data_e_ref[i_ref_day][i_ref_start]
									   break
									i_ref_start+=1
									
								i_ref_end=n_data_points-1
								while i_ref_end>=0:
									if type(data_e_ref[i_ref_day][i_ref_end]) is float:
									   ref_e_end=data_e_ref[i_ref_day][i_ref_end]
									   break
									i_ref_end-=1                        

								i_ref_offset=max(i_ref_end-i_ref_start+1,0)
								ref_e_availability_tmp=float(i_ref_offset)/n_data_points
								
								#~ each reference day power consumption must have a sufficient reliability to be considered in the reference measurement
								if ref_e_availability_tmp>=MIN_OVERALL_DATA_AVAILABILITY:
									ref_e_offset=ref_e_end-ref_e_start
									ref_e_offsets.append(ref_e_offset)
								else:
									
									#~ the overall reliability of reference data is calculated as the ratio between
									#~ reliable reference days and total number of reference days
									ref_e_availability-=1/float(N_REF_DAYS)
							
							output_json_results["energy"]["reference"]["availability"]=ref_e_availability		
							if ref_e_availability>=MIN_OVERALL_REF_AVAILABILITY:
								
								#~ reference energy consumption is calculated as the median of the
								#~ daily energy consumption of the reference days
								ref_e_offsets=sorted(ref_e_offsets)
								ref_e_offset_median=ref_e_offsets[len(ref_e_offsets)//2]
								output_json_results["energy"]["reference"]["offset"]=ref_e_offset_median
							
								#~ alarm = 1 if actual energy consumption is more than expected
								#~ -1 if it's less
								#~ 0 if there's no alarm
								if data_e_offset>=ref_e_offset_median*(1+ENERGY_REL_OFFSET):
									output_json_results["energy"]["reference"]["alarm"]=1
								elif data_e_offset<=ref_e_offset_median*(1-ENERGY_REL_OFFSET):
									output_json_results["energy"]["reference"]["alarm"]=-1
								else:
									output_json_results["energy"]["reference"]["alarm"]=0
		

		#~ COS(PHI) ANALYSIS
		if C_DATA_FILENAME != "":
			output_json_results["cosphi"]=dict()
			if not avoid_calcs:
				
				if DEBUG:
					print "\nLooking for cosphi anomalies with COSPHI_MIN =",COSPHI_MIN, "for at least", COSPHI_DT_MAX, "minutes"
				
				c_low_count=0
				c_low_sum=0

				#~ read cosphi data
				dr.set_n_ref_days(0)
				dr.read(C_DATA_FILENAME)
				if len(output_json["errors"])==0:
					data_c=dr.data
					
					#~ cosphi data availability is supposed to be the same of power data. If it's not the case (NO_ONE_READ_MEAS = True)
					#~ then it's estimated separately from data
					c_availability=data_availability
					if NO_ONE_READ_MEAS:
						pa_data.set_data(data_c,None,0,False)
						c_availability=pa_data.estimate_availability()
					
					output_json_results["cosphi"]["availability"]=c_availability
					
					
					#~ count the number of data points with low cosphi
					for i_data in xrange(0,n_data_points):

						#~ use as reference the intersection of the ON periods of the available phases
						#~ that is, for each data point checks whether all the phases where in ON state
						ctrl_all=True
						for i_phase in xrange(0,N_PHASES):
							ctrl_all=ctrl_all and (ctrl_data[i_phase][i_data]==1)

						if ctrl_all and (type(data_c[i_data]) is float):
							if data_c[i_data]<COSPHI_MIN:
								c_low_count+=1
								c_low_sum+=data_c[i_data]
					
					if DEBUG:
						print "# of data points with low cosphi:", c_low_count
					
					#~ convert # of data points in time
					c_low_dt=c_low_count*SAMPLING_INT
					
					#~ calculate average cosphi during low cosphi periods
					if c_low_count>0:
						c_low_avg=c_low_sum/float(c_low_count)
					else:
						c_low_avg=None
					output_json_results["cosphi"]["low_dt"]=c_low_dt
					output_json_results["cosphi"]["low_avg"]=c_low_avg
					output_json_results["cosphi"]["alarm"]=0
					if c_low_dt > COSPHI_DT_MAX:
						output_json_results["cosphi"]["alarm"]=1
						

				
	if len(output_json["errors"])==0:
		output_json["results"]=output_json_results

	print json.dumps(output_json)




if __name__ == "__main__":
	main(sys.argv)

