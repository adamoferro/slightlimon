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


import rrdtool

class data_reader():	
	
	SECONDS_PER_DAY=24*60*60
	ERROR_MESSAGE_DATA="Error while reading data"
	ERROR_MESSAGE_REF_DATA="Error while reading reference data"
	
	def __init__(self,filename=None,ts_start=0,ts_end=0,s_int=0,n_ref_days=0,err=None,extra=""):
		self.filename=filename
		self.ts_start=ts_start
		self.ts_end=ts_end
		self.sampling_int=s_int
		self.errors=err
		self.rrd_function=extra
		self.n_data_points=int((self.ts_end-self.ts_start)/60/self.sampling_int)+1
		self.set_n_ref_days(n_ref_days)
						
		self.data=None
		self.ref_data=None
		
		self.DEBUG=False

	
	def set_n_ref_days(self,n_ref_days):
		self.n_ref_days=n_ref_days
		self.start_ref_ts=self.ts_start-(self.n_ref_days)*self.SECONDS_PER_DAY
		self.end_ref_ts=self.ts_end-self.SECONDS_PER_DAY				


	def read(self,fn):
		
		db_filename=self.filename
		if fn!="":
			db_filename=fn
			
		try:
			
			#~ -60 because RRDTool returns the next value wrt what asked
			self.data=rrdtool.fetch(db_filename, self.rrd_function, '-s', "%s" %(self.ts_start-60), '-e', '%s' %(self.ts_end-60) )[2]    # DATA ARE IN [2]
						
			if self.DEBUG:
				print "Actual # data points:			",len(self.data)
			
			self.data=[self.data[i_data][0] for i_data in xrange(0,self.n_data_points)]
		except:
			self.errors.append(self.ERROR_MESSAGE_DATA)
		else:
			if self.n_ref_days>0:
				self.ref_data=list()
				try:
					for i_ref_day in xrange(0,self.n_ref_days):
						
						#~ -60 because RRDTool returns the next value wrt what asked
						start_ref_ts_tmp=self.start_ref_ts-60 + self.SECONDS_PER_DAY*i_ref_day
						end_ref_ts_tmp=self.end_ref_ts-60-self.SECONDS_PER_DAY*(self.n_ref_days-1-i_ref_day)
						
						data_ref_tmp=rrdtool.fetch(db_filename, self.rrd_function, '-s', "%s" %(start_ref_ts_tmp), '-e', '%s' %(end_ref_ts_tmp ))[2]
						data_ref_tmp=[data_ref_tmp[i_data][0] for i_data in xrange(0,self.n_data_points)]
						self.ref_data.append(data_ref_tmp)
						
					if self.DEBUG:
						print "# reference profiles:		",len(self.ref_data)
				except:
					self.errors.append(self.ERROR_MESSAGE_REF_DATA)

		
