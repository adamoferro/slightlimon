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


class profile_merger():
	
	def __init__(self,data_p_list,data_v_list,data_v_norm=None):
		
		#~ list of reference data, one entry per reference day
		self.data_p_list=data_p_list
		self.data_v_list=data_v_list
		
		#~ actual voltage, used to normalize power reference data
		self.data_v_norm=data_v_norm
		
		self.n_profiles=len(self.data_p_list)
		self.n_data_points=len(self.data_p_list[0])
		self.data_p_merged=[None for i_ref in xrange(0,self.n_data_points)]
		self.data_v_merged=[None for i_ref in xrange(0,self.n_data_points)]
		self.merge_avail=1
		self.DEBUG=False
		
		
	def merge(self):
		for i_data in xrange(0,self.n_data_points):
			p_tmp_list=list()
			v_tmp_list=list()
			
			for i_profile in xrange(0,self.n_profiles):
				p_tmp=0
				v_tmp=0
				
				#~ save P values in a list only if they are not nan. Power values are normalized wrt voltage
				if type(self.data_p_list[i_profile][i_data]) is float and type(self.data_v_list[i_profile][i_data]) is float:
					p_tmp=self.data_p_list[i_profile][i_data]
					v_tmp=self.data_v_list[i_profile][i_data]
					if self.data_v_norm is not None and type(self.data_v_norm[i_data]) is float:
						v_amp_factor=0
						if v_tmp!=0:
							v_amp_factor=self.data_v_norm[i_data]/v_tmp;
							p_tmp=p_tmp*(v_amp_factor**2)			
							v_tmp=self.data_v_norm[i_data]
					p_tmp_list.append((i_profile,p_tmp))
				
				#~  may contain 0, but if so it's not used
				v_tmp_list.append(v_tmp)

			#~ check if there is at least one point in the reference profile and calculates reference values
			if len(p_tmp_list)>0:
				
				#~ sort p values keeping the correspondence with ref day id
				p_tmp_tuple=sorted(p_tmp_list,key=lambda p_value: p_value[1])
				
				#~ select middle p value and the corresponding v value
				i_middle=len(p_tmp_tuple)/2
				p_tmp_final=p_tmp_tuple[i_middle][1]
				v_tmp_final=v_tmp_list[p_tmp_tuple[i_middle][0]]
				
				self.data_p_merged[i_data]=p_tmp_final
				self.data_v_merged[i_data]=v_tmp_final
				

			#~ reduces the overall reliability of the reference profile depending on the number of ref days that
			#~ it was possible to use.
			#~ Every data point of the reference profile weights 1/n_data_points
			#~ 1 is reduced by n_used_days/N_REF_DAYS, that is
			#~ if all ref days are used, the reliability is not reduced
			#~ if none has been used, reliability is reduced by 1/n_data_points
			#~ (these are the extreme cases that actually never happen because of the conditions)
			self.merge_avail-=(float(self.n_profiles-len(p_tmp_list))/float(self.n_profiles))/float(self.n_data_points)


		return self.data_p_merged, self.data_v_merged, self.merge_avail
		

