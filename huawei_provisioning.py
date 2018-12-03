#!/usr/bin/python3
##
## Script for provisioning bridge ONT to the Huawei OLT
## Leandro Fabris Milani - Sep 2018
##
## Usage: python3 huawei_provisioning.py -o 10.126.126.94 -s0 -p15 -f file.csv
import sys
import time
import telnetlib
import getopt
import ipaddress
import os
import time

def printUsage():
    print ("Usage: huawei_provisioning.py -o <oltip> -s <slot> -p <pon> -f <file> \nUse -h for help (--help) or -d (--debug) for debug mode.\n")

def validateIP(ip):
	try:
		ipaddress.ip_address(ip)
	except ValueError:
		return False
	else:
		return True
    
def validateNumber(number):
	try:
		integer = int(number)
	except ValueError:
		return False
	else:
		return True

def getOnuID(tn,serial):
	tn.write("display ont info by-sn ".encode('utf-8') + serial.encode('utf-8') + b"\n\n")
	time.sleep(.3)
	return_onuid = tn.read_until('Control flag'.encode('utf-8'),3).decode('utf-8')
	dados_arq = return_onuid.splitlines()
	for linha in dados_arq:
		if "ONT-ID" in linha:
			str_onuid = linha.split(':')
			onu_id = str_onuid[1].lstrip().rstrip('\r')
			tn.write(b"q\n")
			time.sleep(.3)
			return onu_id
		elif "Failure" in linha:
			print (linha.lstrip() + ' --- Serial: ' + serial)
			tn.write(b"q\n")
			time.sleep(.3)
			return False

def getLineProfileId(tn,name_lineprofile):
	tn.write("display ont-lineprofile gpon profile-name ".encode('utf-8') + name_lineprofile.encode('utf-8') + b"\n\n")
	time.sleep(.3)
	return_lineid = tn.read_until('Profile-name'.encode('utf-8'),3).decode('utf-8')
	data_return = return_lineid.splitlines()
	for line in data_return:
		if "Profile-ID" in line:
			str_onuid = line.split(':')
			line_id = str_onuid[1].lstrip().rstrip('\r')
			tn.write(b"q\n")
			time.sleep(.3)
			return line_id
		elif "Failure" in line:
			print (line.lstrip())
			tn.write(b"q\n")
			time.sleep(.3)
			sys.exit()

def getServiceProfileId(tn,name_srvprofile):
	tn.write("display ont-srvprofile gpon profile-name ".encode('utf-8') + name_srvprofile.encode('utf-8') + b"\n\n")
	time.sleep(.3)
	return_lineid = tn.read_until('Profile-name'.encode('utf-8'),3).decode('utf-8')
	data_return = return_lineid.splitlines()
	for line in data_return:
		if "Profile-ID" in line:
			str_onuid = line.split(':')
			line_id = str_onuid[1].lstrip().rstrip('\r')
			tn.write(b"q\n")
			time.sleep(.3)
			return line_id
		elif "Failure" in line:
			print (line.lstrip())
			tn.write(b"q\n")
			time.sleep(.3)
			sys.exit()

def importFile(file):
	try:
		arq = open(file,'r')
	except OSError:
		print ('Error opening file')
		sys.exit()
	else:
		linhas = arq.readlines()
		arq.close()
		return linhas

def authOnt(ip,slot,pon,file,debug,user,password,frame,name_srvprofile,name_lineprofile,vlan,number_lanports,gemport,traffic_table):
	print ('Connecting to olt {0}'.format(ip))
	try:
		tn = telnetlib.Telnet(ip,23,10)
	except Exception as e:
		print ("Erro connecting to OLT, please check the IP address")
		sys.exit()

	if debug:
		tn.set_debuglevel(100)

	tn.read_until(b"name:")
	tn.write(user.encode('utf-8') + b"\n")
	time.sleep(.3)
	tn.read_until(b"password:")
	tn.write(password.encode('utf-8') + b"\n")
	time.sleep(.3)

	tn.write(b"enable\n")
	time.sleep(.3)
	tn.write(b"config\n")
	time.sleep(.3)

	srvprofile = getServiceProfileId(tn,name_srvprofile)
	lineprofile = getLineProfileId(tn,name_lineprofile)

	#Open .csv file and start configuring
	arquivo = importFile(file)
	for linha in arquivo:
		parte = linha.split(';')
		cod = parte[0].rstrip()
		nome = parte[1].rstrip()
		serial = parte[2].rstrip().upper()
		descricao = 'C' + cod + '-' + nome.replace(' ', '_').upper()
		
		print ("---")

		print ('Opening board number {0}/{1}...'.format(frame,slot))
		tn.write("interface gpon ".encode('utf-8') + frame.encode('utf-8') + "/".encode('utf-8') + slot.encode('utf-8') + b"\n")
		time.sleep(.3)

		print ('Adding ONT to the PON number {0}'.format(pon))
		tn.write("ont add ".encode('utf-8') + pon.encode('utf-8') + " sn-auth \"".encode('utf-8') + serial.encode('utf-8') + "\" omci ont-lineprofile-id ".encode('utf-8') + lineprofile.encode('utf-8') + " ont-srvprofile-id ".encode('utf-8') + srvprofile.encode('utf-8') + " desc \"".encode('utf-8') + descricao.encode('utf-8') + b"\" \n\n")
		time.sleep(.3)
		tn.write(b"quit\n")
		time.sleep(.3)

		#Find the id of the ont
		print ('Searching for ONT id...')
		if getOnuID(tn,serial):
			onu_id = getOnuID(tn,serial)
		else:
			continue

		#Open the interface gpon again
		tn.write("interface gpon 0/".encode('utf-8') + slot.encode('utf-8') + b"\n")
		time.sleep(.3)

		#Apply the alarm perfil to the ont
		print ('Applying alarm profile...')
		tn.write("ont alarm-profile ".encode('utf-8') + pon.encode('utf-8') + " ".encode('utf-8') + onu_id.encode('utf-8') + b" profile-id 1\n")
		time.sleep(.3)
		tn.write("ont optical-alarm-profile ".encode('utf-8') + pon.encode('utf-8') + " ".encode('utf-8') + onu_id.encode('utf-8') + b" profile-id 1\n")
		time.sleep(1)

		#Apply vlan to the ont ports
		print ('Applying vlan on lan ports...')
		for port in range(1,number_lanports+1):
			tn.write("ont port native-vlan ".encode('utf-8') + pon.encode('utf-8') + " ".encode('utf-8') + onu_id.encode('utf-8') + " eth ".encode('utf-8') + str(port).encode('utf-8') + " vlan ".encode('utf-8') + vlan.encode('utf-8') + b" priority 0\n")
			time.sleep(1)
		tn.write(b"quit\n")
		time.sleep(1)

		#Apply service-port to the ont
		print ('Applying service port...')
		tn.write("service-port vlan ".encode('utf-8') + vlan.encode('utf-8') + " gpon ".encode('utf-8') + frame.encode('utf-8') + "/".encode('utf-8') + slot.encode('utf-8') + "/".encode('utf-8') + pon.encode('utf-8') + " ont ".encode('utf-8') + onu_id.encode('utf-8') + " gemport ".encode('utf-8') + gemport.encode('utf-8') + " multi-service user-vlan ".encode('utf-8') + vlan.encode('utf-8') + " tag-transform translate inbound traffic-table index ".encode('utf-8') + traffic_table.encode('utf-8') + " outbound traffic-table index ".encode('utf-8') + traffic_table.encode('utf-8') + b"\n")
		
		print ('Success ONT: {0} Serial: {1}'.format(descricao,serial))
		time.sleep(2)

	#Close connection to the OLT
	tn.write(b"quit\n")
	time.sleep(.3)
	tn.write(b"quit\n")
	time.sleep(.3)
	tn.write(b"quit\n")
	time.sleep(.3)
	tn.write("y".encode('utf-8') + b"\n")
	time.sleep(.3)
	tn.close()

def main(argv):
	if sys.version_info[0] < 3:
		raise Exception("Python 3 or a more recent version is required.")

	start_time = time.time()

	#Default variables for the OLTs configuration
	user = 'root'
	password = 'admin'
	frame = '0'
	name_srvprofile = 'ONT_BRIDGE'
	name_lineprofile = 'ONT_BRIDGE'
	vlan = '1001'
	number_lanports = 4
	gemport = '0'
	traffic_table = '6'
	debug = False

	try:
		opts, args = getopt.getopt(argv,"o:s:p:f:hd",["olt=","slot=","pon=","file=","help","debug"])
	except getopt.GetoptError:
		printUsage()
		sys.exit(2)

	if not opts:
		printUsage()
		sys.exit()

	for opt, arg in opts:
		if opt in ("-h", "--help"):
			printUsage()
			sys.exit()

		elif opt in ("-d", "--debug"):
			debug = True

		elif opt in ("-o", "--olt"):
			if validateIP(arg):
				ip = arg
			else:
				print ('IP address invalid')
				sys.exit()

		elif opt in ("-s", "--slot"):
			if validateNumber(arg):
				slot = arg
			else:
				print ('Slot must be a number')
				sys.exit()

		elif opt in ("-p", "--pon"):
			if validateNumber(arg):
				pon = arg
			else:
				print ('Pon must be a number')
				sys.exit()

		elif opt in ("-f", "--file"):
			if os.path.isfile(arg):
				file = arg
			else:
				print ('File unknown')
				sys.exit()

	authOnt(ip,slot,pon,file,debug,user,password,frame,name_srvprofile,name_lineprofile,vlan,number_lanports,gemport,traffic_table)

	print ("---")
	print("End of the script! \nTime elapsed: %s seconds" % (time.time() - start_time))

if __name__ == "__main__":
	main(sys.argv[1:])
