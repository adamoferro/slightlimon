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


class anomaly_detector():
	
	def __init__(self,ts_start,s_int,delta_t,an_dp,an_dpr,an_dt):
		self.TS_START=ts_start
		self.SAMPLING_INT=s_int
		self.DELTA_T=delta_t
		self.ANOMALY_DELTA_P=an_dp
		self.ANOMALY_DELTA_P_REL=an_dpr
		self.ANOMALY_MIN_DELTA_T=an_dt
		self.DEBUG=False


	def set_data(self,data_p_avg,ctrl_data,profile_p_ref_avg,ctrl_ref):
		self.data_p_avg=data_p_avg
		self.ctrl_data=ctrl_data
		self.profile_p_ref_avg=profile_p_ref_avg
		self.ctrl_ref=ctrl_ref
		self.ctrl_final=None
		
		self.n_data_points=len(self.data_p_avg)

		
		
	def detect(self):
								 
  			
			# anomalies are searched only where both actual and reference profiles are in ON state (within guard intervals)
			self.ctrl_final=[(self.ctrl_data[i_data]==1 and self.ctrl_ref[i_data]==1) for i_data in xrange(0,self.n_data_points)]

		  
			if self.DEBUG:
				print "Look for anomaly markers on current data..."
			anomaly_on_markers=list()
			anomaly_on_markers_delta=list()
			anomaly_off_markers=list()
			anomaly_off_markers_delta=list()
			
			
			#~ detect anomaly points
			for i_data in xrange(0,self.n_data_points-self.DELTA_T):
					
				if self.ctrl_final[i_data]==True:					
					delta_p_ref_tmp=self.data_p_avg[i_data]-self.profile_p_ref_avg[i_data];
					if delta_p_ref_tmp>self.ANOMALY_DELTA_P and delta_p_ref_tmp>self.data_p_avg[i_data]*self.ANOMALY_DELTA_P_REL:
						anomaly_on_markers.append(i_data)
						anomaly_on_markers_delta.append(delta_p_ref_tmp)
					elif -delta_p_ref_tmp>self.ANOMALY_DELTA_P and -delta_p_ref_tmp>self.data_p_avg[i_data]*self.ANOMALY_DELTA_P_REL:
						anomaly_off_markers.append(i_data)
						anomaly_off_markers_delta.append(-delta_p_ref_tmp)


			if self.DEBUG:
				print "Detected anomaly + markers :",anomaly_on_markers
				print "Detected anomaly + deltas  :",anomaly_on_markers_delta
				print "Detected anomaly - makers :",anomaly_off_markers
				print "Detected anomaly - deltas ;",anomaly_off_markers_delta


			anomaly_markers={'on': anomaly_on_markers, 'off': anomaly_off_markers}
			anomaly_markers_delta={'on': anomaly_on_markers_delta, 'off': anomaly_off_markers_delta}


			anomaly_on_markers_final=list()
			anomaly_on_markers_final_dt=list()
			anomaly_on_markers_final_dp=list()
			anomaly_off_markers_final=list()
			anomaly_off_markers_final_dt=list()
			anomaly_off_markers_final_dp=list()
			
			anomaly_markers_final={
				'on':
					{
					't': anomaly_on_markers_final,
					'dt': anomaly_on_markers_final_dt,
					'dp': anomaly_on_markers_final_dp
					},
				'off':
					{
					't': anomaly_off_markers_final,
					'dt': anomaly_off_markers_final_dt,
					'dp': anomaly_off_markers_final_dp
					}
				}

			
			#~ anomaly points are filtered or joined in order to get only relevant anomalies and their main parameters (start, duration, max power shift)
			for i_type in anomaly_markers:

				if self.DEBUG:
					print "Filter anomaly ON markers and get one per event..."

				tmp_anomaly_markers=anomaly_markers[i_type]
				tmp_anomaly_markers_delta=anomaly_markers_delta[i_type]
				n_tmp_markers=len(tmp_anomaly_markers)
				tmp_anomaly_markers_final=anomaly_markers_final[i_type]['t']
				tmp_anomaly_markers_final_dt=anomaly_markers_final[i_type]['dt']
				tmp_anomaly_markers_final_dp=anomaly_markers_final[i_type]['dp']
				if n_tmp_markers>0:
					i_marker=1
					i_marker_tmp=0
					tmp_anomaly_markers_tmp=list()
					tmp_anomaly_markers_delta_tmp=list()
					
					tmp_anomaly_markers_tmp.append(tmp_anomaly_markers[0])
					tmp_anomaly_markers_delta_tmp.append(tmp_anomaly_markers_delta[0])
					while i_marker<=n_tmp_markers:
						if i_marker!=n_tmp_markers and (len(tmp_anomaly_markers_tmp)==0 or tmp_anomaly_markers[i_marker]-tmp_anomaly_markers_tmp[i_marker_tmp]<=self.DELTA_T):
							tmp_anomaly_markers_tmp.append(tmp_anomaly_markers[i_marker])
							tmp_anomaly_markers_delta_tmp.append(tmp_anomaly_markers_delta[i_marker])
							i_marker_tmp+=1
							i_marker+=1
						
						else:
							if len(tmp_anomaly_markers_tmp)>0:
								if len(tmp_anomaly_markers_tmp)>=self.ANOMALY_MIN_DELTA_T:
									
									# find max delta
									tmp_anomaly_markers_delta_tmp_max=max(tmp_anomaly_markers_delta_tmp)
									
									# save the first marker (beginning of event), the duration of the anomaly and the max power shift
									tmp_anomaly_markers_final.append(tmp_anomaly_markers_tmp[0])
									tmp_anomaly_markers_final_dt.append((tmp_anomaly_markers_tmp[-1]-tmp_anomaly_markers_tmp[0]+1));
									tmp_anomaly_markers_final_dp.append(tmp_anomaly_markers_delta_tmp_max//1)

								i_marker_tmp=0
								tmp_anomaly_markers_tmp=list()
								tmp_anomaly_markers_delta_tmp=list()

							if i_marker<n_tmp_markers:
								tmp_anomaly_markers_tmp.append(tmp_anomaly_markers[i_marker])
								tmp_anomaly_markers_delta_tmp.append(tmp_anomaly_markers_delta[i_marker])

							i_marker+=1

			anomaly_markers_final['on']['t']=[ts_m*60+self.TS_START for ts_m in anomaly_on_markers_final]
			anomaly_markers_final['off']['t']=[ts_m*60+self.TS_START for ts_m in anomaly_off_markers_final]

			return anomaly_markers_final


		
		
