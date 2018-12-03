# Huawei-Ont-Provisioning
Python3 script for provisioning ont for huawei olt using telnet.

This script was developed for provide a easy way to provisioning ont to huawei olt, by default it will add an ont in bridge mode, a few variables that define the default configuration of the olt.

At the main def you can find the follow variables:
	user = 'root' # The login for telnet
	password = 'admin' # Password for telnet
	frame = '0' #Default frame of OLT
	name_srvprofile = 'ONT_BRIDGE' # The name of service profile of OLT for bridge
	name_lineprofile = 'ONT_BRIDGE' # The name of line profile of OLT for bridge
	vlan = '1001' # VLAN of communication with the ONT and router, (all ont ports are untagged)
	number_lanports = 4 (Max number of lan ports of ont)
	gemport = '0' # Default gem port number of profile
	traffic_table = '6' # Default traffic-table of Huawei OLT (6 = no bandwith controll)
	debug = False # Debug disable by default
  
  *Change it for your OLT configuration
 
 The file .csv follow the structure of the file example.csv.
 
 Example of usage: python3 huawei_provisioning.py -o 192.168.155.3 -s3 -p15 -f file.csv
