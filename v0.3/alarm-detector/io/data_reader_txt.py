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


class data_reader():
	
	ERROR_MESSAGE_DATA="Error while reading data"
	ERROR_MESSAGE_DATA_LENGTH="Input data length shorter than expected"
	ERROR_MESSAGE_DATA_CORRUPTED="Data contain non-numeric characters"
	
	def __init__(self,filename=None,ts_start=0,ts_end=0,s_int=0,n_ref_days=0,err=None,extra=""):
		self.filename=filename
		self.ts_start=ts_start
		self.ts_end=ts_end
		self.sampling_int=s_int
		self.errors=err
		self.n_data_points=int((self.ts_end-self.ts_start)/60/self.sampling_int)+1
		self.n_ref_days=n_ref_days
		self.data=None
		self.ref_data=None
		
		self.DEBUG=False
		
		
	def set_n_ref_days(self,n_ref_days):
		self.n_ref_days=n_ref_days
		
		
	def read(self,fn):
		
		db_filename=self.filename
		if fn!="":
			db_filename=fn
		
		#~ read text file
		try:
			lines = open(db_filename).read().splitlines()
			
		except:
			self.errors.append(self.ERROR_MESSAGE_DATA)
			
		else:
			#~ check the number of lines wrt the number of expected data points
			if len(lines)<self.n_data_points*(self.n_ref_days+1):
				self.errors.append(self.ERROR_MESSAGE_DATA_LENGTH)
			else:
				#~ convert text into floating point numbers and create data list and reference data list
				try:
					self.data=[float(lines[i_data]) if lines[i_data]!="nan" else None for i_data in xrange(0,self.n_data_points)]
					
					if self.n_ref_days>0:
						self.ref_data=list()
						for i_ref_day in xrange(0,self.n_ref_days):
							ref_data_tmp=[float(lines[i_data]) if lines[i_data]!="nan" else None for i_data in xrange(self.n_data_points*(i_ref_day+1),self.n_data_points*(i_ref_day+2))]
							self.ref_data.append(ref_data_tmp)
				except:
					self.data=None
					self.ref_data=None
					self.errors.append(self.ERROR_MESSAGE_DATA_CORRUPTED)
