# SLightliMon - Street Lighting lite Monitor

SLightliMon means Street Lighting lite Monitor. It is a free open-source tool written in python v2 for the non-real time analysis and the detection of alarms on street lighting data measured by power meters. As an example, it can be used at day N to check whether in the night between day N-1 and day N any problem occurred. Moreover it provides additional relevant information on the monitored power lines that can be used for refining and planning the maintenance of street lighting.
At this stage it has to be considered as an experimental tool still under development. However, it is already successfully used for the monitoring of almost 100 power cabinets at my work place.

SLightliMon includes a profile analyzer that can automatically detect alarms on single power profiles and also detect anomalies with respect to a set of reference profiles (e.g. a number of days preceding the one that is under analysis). A web-based user interface is under development.

Using power meter data, the profile analyzer is able to detect from a single power profile:

  - Times of switch ON and switch OFF of a power line, and number of events
  - Voltage anomalies
  - Low power factor (cos(phi))
  - Total energy consumption in the period under analysis
  
If a reference period is also given as input, the profile analyzer can also automatically detect (with respect the reference period):

  - Power anomalies: periods with increased/decreased instant power
  - Total energy consumption anomalies
  
The reference period is used to calculate a reference profile that is then compared to the current profile. In this way SLightliMon can for instance automatically adapt the alarm detection to each power line by means of its recent past data.
  
As explained in detail later, the SLightliMon alarm detector can be used with two types of input:

  - a Round Robin Database (RRD)
  - text files

For further details on the principles at the basis of the profile analysis and alarm detection have a look at the related documentation.

### Usage

In the following you can find a description of the parameters of SLightliMon. Before using the software read the related documentation in order to understand what are the input requirements and what you are doing.

#### Period to be analyzed

`-ts T_START, --t_start T_START`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; start UNIX epoch timestamp [seconds]

`-te T_END, --t_end T_END`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; end UNIX epoch timestamp [seconds]

#### Input files and format

`-p1 POWER_DATA_PH1, --power_data_ph1 POWER_DATA_PH1`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; active power data for phase 1, expressed in Watts

`-p2 POWER_DATA_PH2, --power_data_ph2 POWER_DATA_PH2`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; active power data for phase 2, expressed in Watts. Do not use if single-phase data.

`-p3 POWER_DATA_PH3, --power_data_ph3 POWER_DATA_PH3`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; active power data for phase 3, expressed in Watts. Do not use if single-phase data.

`-v1 VOLTAGE_DATA_PH1, --voltage_data_ph1 VOLTAGE_DATA_PH1`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; voltage data for phase 1, expressed in Volts

`-v2 VOLTAGE_DATA_PH2, --voltage_data_ph2 VOLTAGE_DATA_PH2`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; voltage data for phase 2, expressed in Volts. Do not use if single-phase data.

`-v3 VOLTAGE_DATA_PH3, --voltage_data_ph3 VOLTAGE_DATA_PH3`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; voltage data for phase 3, expressed in Volts. Do not use if single-phase data.

`-e ENERGY_DATA, --energy_data ENERGY_DATA`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; total active energy data

`-c COSPHI_DATA, --cosphi_data COSPHI_DATA`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; cos(phi) data

`-nor, --no_one_read_meas`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; set if measurements are NOT acquired at the same time (e.g., they are obtained through separated MODBUS queries from the registers of an energy meter, instead of an unique query from all registers). Independently from this parameter, power and voltage measurements related to the same phase are assumed to be anyway taken at the same time.

`-rf {AVERAGE,MIN,MAX,LAST}, --rrd_function {AVERAGE,MIN,MAX,LAST}`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; RRD consolidation function. Default is AVERAGE.

`-txt, --text`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; set if data are in text format instead of RRD

#### Base algorithm parameters

`-dt DELTA_T, --delta_t DELTA_T`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; base analysis time interval [minutes, positive]. Default is 5.

`-at AVG_T, --avg_t AVG_T`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; average interval [minutes, positive odd number]. Default is 5.

`-po1 POFF_PH1, --poff_ph1 POFF_PH1`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; maximum power consumption during off state for phase 1 [watts]. Default is 100.

`-po2 POFF_PH2, --poff_ph2 POFF_PH2`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; maximum power consumption during off state for phase 2 [watts]. Default is 100.

`-po3 POFF_PH3, --poff_ph3 POFF_PH3`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; maximum power consumption during off state for phase 3 [watts]. Default is 100.

`-vm V_MIN, --v_min V_MIN`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; minimum value of acceptable voltage [volts]. Default is 210.

`-vM V_MAX, --v_max V_MAX`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; maximum value of acceptable voltage [volts]. Default is 250.

`-vt V_DT, --v_dt V_DT`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; maximum total non-consecutive time of non-acceptable voltage allowed [hours]. Default is 3.

`-cm COSPHI_MIN, --cosphi_min COSPHI_MIN`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; minimum value of acceptable cosphi. Default is 0.9.

`-ct COSPHI_DT, --cosphi_dt COSPHI_DT`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; maximum total non-consecutive time [hours] of low cosphi allowed during ON state. Default is 3.

`-da DATA_MIN_AVAIL, --data_min_avail DATA_MIN_AVAIL`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; minimum data availability for running the whole algorithm [percent]. Default is 70.

#### Comparison with reference parameters

`-rd REF_DAYS, --ref_days REF_DAYS`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; number of reference days. Default is 0, that is no comparison with past data is performed. If >0 input files must contain also past data.

`-aps ANOMALY_ABS_P_SHIFT, --anomaly_abs_p_shift ANOMALY_ABS_P_SHIFT`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; minimum absolute power shift for detecting an anomaly [watts]. Default is 200.

`-arps ANOMALY_REL_P_SHIFT, --anomaly_rel_p_shift ANOMALY_REL_P_SHIFT`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; minimum relative power shift for detecting an anomaly [percent of reference profile]. Default is 2.

`-atm ANOMALY_MIN_DT, --anomaly_min_dt ANOMALY_MIN_DT`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; minimum duration of an anomaly state [minutes]. Default is 7.

`-agt ANOMALY_GUARD_DT, --anomaly_guard_dt ANOMALY_GUARD_DT`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; minimum time distance allowed from an on/off event to an anomaly [minutes]. Default is 10.

`-ers ENERGY_REL_SHIFT, --energy_rel_shift ENERGY_REL_SHIFT`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; minimum relative total energy offset for detecting an anomaly [percent of reference profile total energy]. Default is 15.

`-ra REF_MIN_AVAIL, --ref_min_avail REF_MIN_AVAIL`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; minimum reference data availability for running the detection of anomalies [percent]. Default is 70.

### Other parameters

`-d, --debug`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; debug mode

`-v, --version`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; show program's version number and exit

`-h, --help`<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; show help message and exit.

### Text input format

Input text files must be single-column files containing only numbers or the word 'nan' (without quotes) to represent no data values. Each row reports the measured value at a certain time instant. The software assumes that the first row corresponds to the start timestamp and that the time interval between consecutive rows is 1 minute. If past reference data are also given, they must follow the present data in the same file without any additional empty line. Each reference day must have the same number of data points of present data. You may have a look at https://github.com/adamoferro/slightlimon/tree/master/test-data for a practical example.

### Dependencies

SLightliMon is written in python v2.x. Thus, in order to execute it you need a python v2.x environment. The following libraries are needed:

  - sys
  - argparse
  - json
  - rrdtool (necessary for using RRD databases as input)
  - datetime (only if executed in debug mode)

### Current version

0.3

### Disclaimer

The author does not guarantee that this software will always provide correct results nor that it will not crash your system. As mentioned above, SLightliMon is experimental and still under development. In any case, any use of SLightliMon is ONLY user responsibility.
