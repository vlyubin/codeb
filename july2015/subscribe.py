import socket
import sys
import time
import datetime
import copy
import csv

OUR_USERNAME = "Team6"
OUR_PASSWORD = "bird"


try:
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect(("codebb.cloudapp.net", 17429))
	sock.sendall(OUR_USERNAME + " " + OUR_PASSWORD + "\nSUBSCRIBE\n")
	sfile = sock.makefile()
	rline = sfile.readline()
	while 1:
		if (rline):
			print rline
		rline = sfile.readline()

except KeyboardInterrupt:
	raise

finally:
	sock.sendall(OUR_USERNAME + " " + OUR_PASSWORD + "\nCLOSE_CONNECTION\n")
	sock.close()
