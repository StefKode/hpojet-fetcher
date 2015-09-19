#!/usr/bin/python3

##################################################################################
# Imports
import os
import glob
import shutil
import time
import datetime
import subprocess
from enum import Enum

##################################################################################
# Defines
MNT='/mnt/hpjet-scanner/HPSCANS'
HOST='hpjet'
NAS='/mnt/scknas/Seagate-ExpansionDesk-01/DOCUSYSTEM/Scanner'

##################################################################################
# Functions
def getFiles():
	return sorted(glob.glob1(MNT, "*.pdf"))

def easyCopy(fileList, onlyFirst):
	num  = len(fileList)

	if (not onlyFirst):
		if (num == 1):
			print("error - just one file")
			return False
	
	count = 0
	for f in fileList:
		#skip last file
		if (not onlyFirst):
			if (count + 1 >= num):
				break
		src  = MNT  + '/' +f
		ts   = time.time()
		tss  = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H%M%S')
		dest = NAS + '/' + tss + "-scan.pdf"
		print('read scan file: ' + dest)
		shutil.copyfile(src, dest)
		try:
			os.remove(src)
		except:
			print("file still in use, delete destination again")
			os.remove(dest)
			return False
			
		count += 1
		if (onlyFirst):
			return True

	return True

class States(Enum):
	waitHost      = 1
	waitAnyFile   = 2
	oneFileSleep  = 3
	moveManyFiles = 4
	moveOneFile   = 5
	error         = 6
	exit          = 7
	max = 7

def pingHost():
	return subprocess.call(["ping", "-c", "1", "-t", "1", HOST])

def do_waitHost():
	print("ping..")
	if (pingHost() == 0):
		return States.waitAnyFile
	return States.waitHost

def do_waitAnyFile():
	files = getFiles()
	print(files)
	if (len(files) > 1):
		return States.moveManyFiles
	if (len(files) > 0):
		return States.oneFileSleep
	time.sleep(20)
	return States.waitAnyFile

def do_oneFileSleep():
	time.sleep(30)
	files = getFiles()
	print(files)
	if (len(files) > 1):
		return States.moveManyFiles
	return States.moveOneFile

def do_moveManyFiles():
	files = getFiles()
	print(files)
	easyCopy(files, False)
	return States.oneFileSleep

def do_moveOneFile():
	files = getFiles()
	print(files)
	easyCopy(files, True)
	return States.waitAnyFile

def do_error():
	return States.exit

def FSMmap(state):
	switcher = {
		States.waitHost:      do_waitHost,
		States.waitAnyFile:   do_waitAnyFile,
		States.oneFileSleep:  do_oneFileSleep,
		States.moveManyFiles: do_moveManyFiles,
		States.moveOneFile:   do_moveOneFile,
		States.error:         do_error,
	}
	func = switcher.get(state)
	return func()

def mainFSM():
	state = States.waitHost
	while (1):
		print(state)
		state = FSMmap(state)
		if (state == States.exit):
			break
	
mainFSM()
