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


class profile_analyzer():

	def __init__(self,ts_start,s_int,dt,avg_t,an_fdt,vm,vM):
		self.TS_START=ts_start
		self.SAMPLING_INT=s_int
		self.DELTA_T=dt
		self.AVG_INTERVAL=avg_t
		self.ANOMALY_FILTER_DELTA_T=an_fdt
		self.V_MIN=vm
		self.V_MAX=vM
		self.data_p=None
		self.data_v=None
		self.P_OFF_MAX=None
		self.first_init=True
		self.DEBUG=False
		
	
	def set_data(self,data_p,data_v,poff,preserve_avail_info):
		self.P_OFF_MAX=poff
		self.data_p=data_p				# DO NOT make a copy
		self.data_p_avg=None
		
		self.data_v=self.data_p			# fake, used when analyzing energy and cosphi data
		if data_v is not None:
			self.data_v=data_v			# DO NOT make a copy
		self.data_v_avg=None

		#~ preserve_avail_info is used to avoid calculations in the case where the new dataset to be analyzed
		#~ has the same data availability (i.e., nan positions) of the previous one
		if (not preserve_avail_info) or self.first_init:
			self.n_data_points=len(self.data_p)
			self.overall_data_availability=0
			self.nan_int_start=None
			self.nan_int_end=None
			self.n_nan_int=0

			#~ Array that indicates whether a data point should be analyzed or not (to be used in AND with ctrl_data)
			#~ = 0: no because data not available (NaN on data or on reference profile)
			#~ = 1 : yes
			self.ctrl_nan=[1 for i_data in xrange(0,self.n_data_points)]
			
			self.avail_estimated=False
			
			self.first_init=False

		#~ Array that indicates whether a data point should be analyzed or not (to be used in AND with ctrl_nan)
		#~ = 0 : no because it does not lie within an ON/OFF interval
		#~ = 1 : yes
		self.ctrl_data=[0 for i_data in xrange(0,self.n_data_points)]


	def estimate_availability(self):
		#~ estimate data availability as 1-(nan values/total number of data points)
		#~ The process also identifies nan intervals and stores their beginning/end points

		if self.data_p is not None and self.data_v is not None and self.P_OFF_MAX is not None:
			
			if self.DEBUG:
				print "Estimate availability..."
				
			nan_count=0
			self.nan_int_start=list()
			self.nan_int_end=list()
			nan_i_tmp=-1
			self.overall_data_availability=1

			for i_data in xrange(0,self.n_data_points):
				if type(self.data_p[i_data]) is not float:			# do not check data_v because it is assumed that P and V are always measured together
					
					#~ assure that both are None
					self.data_p[i_data]=None
					self.data_v[i_data]=None
					self.ctrl_nan[i_data]=0
					nan_count+=1
					
					#~ save start and end of nan intervals
					if len(self.nan_int_start)==0 or i_data-nan_i_tmp>1:
						self.nan_int_start.append(i_data)
						
					nan_i_tmp=i_data
						
				else:
					if (len(self.nan_int_end)==0 and nan_i_tmp>=0) or (len(self.nan_int_end)>0 and self.nan_int_end[-1]!=nan_i_tmp):
						self.nan_int_end.append(nan_i_tmp)
					
					
				#~ if the last nan interval spans until the end of the data...
				if nan_i_tmp==self.n_data_points-1:
					self.nan_int_end.append(nan_i_tmp)
					
					if self.DEBUG:
						print "*** data end with a nan interval ***"
					
			self.n_nan_int=len(self.nan_int_start)			

			self.overall_data_availability=1.-float(nan_count)/float(self.n_data_points)
			self.avail_estimated=True
		
		return self.overall_data_availability



	def analyze_profile(self):
		#~ data are considered reliable
		#~ The process fills short nan intervals by linear prediction. "Short" is defined as duration <= DELTA_T
		#~ Longer gaps are not filled and the algorithm infers whether during the gap an ON or OFF event occurred

		if self.avail_estimated:
			data_switch_on_markers=list()
			data_switch_off_markers=list()


			if self.DEBUG:
				print "Fill short data gaps..."
				print "# NaN intervals:			",self.n_nan_int
			
			long_nan_int_start=list()
			long_nan_int_end=list()
			
			#~ NOTE: assumption: data have 1 minute sampling *** TODO: change this and make general
			for i_nan_int in xrange(0,self.n_nan_int):
				if self.nan_int_start[i_nan_int]!=0 and self.nan_int_end[i_nan_int]!=self.n_data_points-1:
					nan_int_dt=self.nan_int_end[i_nan_int]-self.nan_int_start[i_nan_int]+1
					i_start=self.nan_int_start[i_nan_int]-1
					i_end=self.nan_int_end[i_nan_int]+1
					if nan_int_dt<=self.DELTA_T:
						p_start=self.data_p[i_start]
						p_end=self.data_p[i_end]
						v_start=self.data_v[i_start]
						v_end=self.data_v[i_end]
						
						m_p=(p_end-p_start)/(nan_int_dt+1)
						m_v=(v_end-v_start)/(nan_int_dt+1)
						
						if self.DEBUG:
							print "...filling gap (", i_nan_int, "): ", i_start, "to", i_end
						for i_data in xrange(i_start+1,i_end):
							self.data_p[i_data]=p_start+m_p*(i_data-i_start)
							self.data_v[i_data]=v_start+m_v*(i_data-i_start)

							#~ self.ctrl_data[i_data]=0		# non serve piu' ripristinare ctrl_data
							self.ctrl_nan[i_data]=1			# nan recovered
						
					else:
						if self.DEBUG:
							print "...long gap detected (", i_nan_int, "): ", i_start, "to", i_end
						
						long_nan_int_start.append(i_start)
						long_nan_int_end.append(i_end)
						
						#~ detect ON or OFF happened during a long gap
						#~ ON/OFF precision in minutes is calculated as half of the nan interval (instead of half of the avg interval)
						if self.data_p[i_start]<self.P_OFF_MAX and self.data_p[i_end]>self.P_OFF_MAX:
							
							#~ print "ON DETECTED IN LONG NAN GAP between",i_start,"and",i_end
							
							data_switch_on_markers.append((i_start+int((i_end-i_start)//2),(i_end-i_start)/2))
						elif self.data_p[i_start]>self.P_OFF_MAX and self.data_p[i_end]<self.P_OFF_MAX:
							data_switch_off_markers.append((i_start+int((i_end-i_start)//2),(i_end-i_start)/2))



			if self.DEBUG:
				print "Moving average on data..."
				
			self.data_p_avg=self.data_p[:]        # make copies to avoid zeros at the beginning and at the end
			self.data_v_avg=self.data_v[:]        # 
			
			
			if self.AVG_INTERVAL > 1:
				
				#~ the procedure skips the nan intervals in order to not lose border values in the average calculation
				
				n_long_nan_int=len(long_nan_int_start)
				i_start_abs=self.AVG_INTERVAL//2
				i_end_abs=self.n_data_points-self.AVG_INTERVAL//2
				if self.n_nan_int>0:
					if self.nan_int_start[0]==0:
						i_start_abs=self.nan_int_end[0]+1+self.AVG_INTERVAL//2+1            # the case of all nan points is not possible as overall reliability is required to be >0
					if self.nan_int_end[-1]==(self.n_data_points-1):
						i_end_abs=self.nan_int_start[-1]-self.AVG_INTERVAL//2

				if n_long_nan_int > 0:
					for i_long_nan_int in xrange(0,n_long_nan_int+1):
						if i_long_nan_int==0:
							i_start=i_start_abs
						else:
							i_start=long_nan_int_end[i_long_nan_int-1]+self.AVG_INTERVAL//2
							
						if i_long_nan_int==n_long_nan_int:
							i_end=i_end_abs
						else:
							i_end=long_nan_int_start[i_long_nan_int]-self.AVG_INTERVAL//2

						if self.DEBUG:
							print "...", i_start, "to", i_end
						for i_data in xrange(i_start,i_end):
							self.data_p_avg[i_data]=float(sum(self.data_p[i_data-self.AVG_INTERVAL//2:i_data+self.AVG_INTERVAL//2+1])/self.AVG_INTERVAL)
							self.data_v_avg[i_data]=float(sum(self.data_v[i_data-self.AVG_INTERVAL//2:i_data+self.AVG_INTERVAL//2+1])/self.AVG_INTERVAL)

				else:
					i_start=i_start_abs
					i_end=i_end_abs
					for i_data in xrange(i_start,i_end):
						self.data_p_avg[i_data]=float(sum(self.data_p[i_data-self.AVG_INTERVAL//2:i_data+self.AVG_INTERVAL//2+1])/self.AVG_INTERVAL)
						self.data_v_avg[i_data]=float(sum(self.data_v[i_data-self.AVG_INTERVAL//2:i_data+self.AVG_INTERVAL//2+1])/self.AVG_INTERVAL)



			#~ Detect switch on/off markers and voltage anomalies on current data
			#~ DEFINITIONS
			#~ ON: first timestamp of ON state (power > threshold)
			#~ OFF: first timestamp of OFF state (power < threshold)


			if self.DEBUG:
				print "Look for switch on/off markers and voltage anomalies on current data..."
			
			n_high_v_points=0
			n_low_v_points=0
			for i_data in xrange(0,self.n_data_points-1):
				if type(self.data_p_avg[i_data]) is float:
					if type(self.data_p_avg[i_data+1]) is float:
						if self.data_p_avg[i_data]<=self.P_OFF_MAX and self.data_p_avg[i_data+1]>self.P_OFF_MAX:
							data_switch_on_markers.append((i_data+1,self.AVG_INTERVAL/2))
						elif self.data_p_avg[i_data+1]<=self.P_OFF_MAX and self.data_p_avg[i_data]>self.P_OFF_MAX:
							data_switch_off_markers.append((i_data+1,self.AVG_INTERVAL/2))
					if self.data_v_avg[i_data]>self.V_MAX:
						n_high_v_points+=1
					elif self.data_v_avg[i_data]<self.V_MIN:
						n_low_v_points+=1
					

			#~ necessary to sort because markers can be detected also before when dealing with nan intervals
			data_switch_on_markers=sorted(data_switch_on_markers,key=lambda p_value: p_value[0])
			data_switch_off_markers=sorted(data_switch_off_markers,key=lambda p_value: p_value[0])


			if self.DEBUG:
				import datetime
				print "Detected switch ON markers :",[str(datetime.datetime.fromtimestamp(ts_m[0]*60+self.TS_START)) for ts_m in data_switch_on_markers]
				print "Detected switch OFF markers:",[str(datetime.datetime.fromtimestamp(ts_m[0]*60+self.TS_START)) for ts_m in data_switch_off_markers]
					   


			# crete on-off intervals by setting ctrl_data (=1 when ON, =0 when OFF)
			
			if self.DEBUG:
				print "Creates on-off intervals from data..."

			n_data_on_markers_final=len(data_switch_on_markers)
			n_data_off_markers_final=len(data_switch_off_markers)

			
			
			i_off_start_marker=0
			if n_data_on_markers_final>0:               # there's at least one ON event --> before the ON event there was an OFF state, but not necessarily an OFF event
				if n_data_off_markers_final>0:          # there's at least one OFF event...
					if data_switch_off_markers[0][0]<data_switch_on_markers[0][0]:        # --> it was ON already at the beginning, until the first OFF event
						for i_data in xrange(0,data_switch_off_markers[0][0]-self.ANOMALY_FILTER_DELTA_T):                # there cannot be other OFF before the first ON
							if self.ctrl_nan[i_data]==1:        # else it means it belongs to a long nan interval
								self.ctrl_data[i_data]=1
						i_off_start_marker=1

				i_off_marker=i_off_start_marker
				for i_on_marker in xrange(0,n_data_on_markers_final):
					i_data_end=self.n_data_points
					if i_off_marker<n_data_off_markers_final:
						i_data_end=data_switch_off_markers[i_off_marker][0]
					for i_data in xrange(data_switch_on_markers[i_on_marker][0]+self.ANOMALY_FILTER_DELTA_T+1,i_data_end-self.ANOMALY_FILTER_DELTA_T):
						if self.ctrl_nan[i_data]==1:
							self.ctrl_data[i_data]=1
					i_off_marker+=1
			else:                                       # no ON events... 1) it is always ON or 2) it is always OFF or 3) it is ON at the beginning and then goes OFF
				if n_data_off_markers_final>0:          # option 3), there should be no more than 1 OFF event (assume that)
					for i_data in xrange(0,data_switch_off_markers[0][0]-self.ANOMALY_FILTER_DELTA_T):
						if self.ctrl_nan[i_data]==1:
							self.ctrl_data[i_data]=1
				else:
					i_data=0
					while i_data<self.n_data_points and type(self.data_p[i_data]) is not float:
						i_data+=1        # i_data cannot reach self.n_data_points because the required reliability is >0 (there's at least one non-nan point)
					
					
					if self.data_p[i_data]>self.P_OFF_MAX:        # always ON
						if self.DEBUG:
							print "Current profile always ON"
						for i_data in xrange(0,self.n_data_points):
							if self.ctrl_nan[i_data]==1:
								self.ctrl_data[i_data]=1
					elif self.DEBUG:
						print "Current profile always OFF"
																# else, always OFF, alreay ctrl_data=0 from the initialization


			data_switch_on_markers=[(ts_m[0]*60+self.TS_START,ts_m[1]) for ts_m in data_switch_on_markers]
			data_switch_off_markers=[(ts_m[0]*60+self.TS_START,ts_m[1]) for ts_m in data_switch_off_markers]

			data_switch_markers={
				'on':
					{
					't': data_switch_on_markers,
					},
				'off':
					{
					't': data_switch_off_markers,
					}
				}


			if self.DEBUG:
				print "# V high points:",n_high_v_points
				print "# V low points :",n_low_v_points

			return self.data_p_avg, data_switch_markers, self.ctrl_data, n_high_v_points, n_low_v_points

		else:
			return None, None, None, None, None, None

