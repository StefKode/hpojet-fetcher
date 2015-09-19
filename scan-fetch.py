#!/usr/bin/python3
########################################################################################
#
# Copyright by Stefan Koch <StefanKoch@gmx.org>, 2015
#
# This file is part of HP Office Jet 6500A scan fetcher (hpojet-fetcher)
#
#    hpojet-fetcher is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    hpojet-fetcher is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
#
########################################################################################

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
MNT_SHARE='/mnt/hpjet-scanner'
MNT=MNT_SHARE + '/HPSCANS'
HOST='hpjet'
NAS='/mnt/scknas/Seagate-ExpansionDesk-01/DOCUSYSTEM/Scanner'

##################################################################################
# Functions
def getFiles():
	return sorted(glob.glob1(MNT, "*scan[0-9]*.jpg"))

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
		dest = NAS + '/' + tss + "-" + f
		print('read scan file: ' + dest)
		shutil.copyfile(src, dest)
		try:
			os.remove(src)
		except:
			print("file still in use, delete destination, try next time")
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

def mountScanner():
	if (not os.path.isdir(MNT)):
		print("mount scanner")
		return subprocess.call(["mount", MNT_SHARE])
	else:
		print("skip mount scanner")
		return 0

def umountScanner():
	print("umount scanner")
	return subprocess.call(["umount", MNT_SHARE])

def do_waitHost():
	print("ping..")
	if (pingHost() == 0):
		mountScanner()
		return States.waitAnyFile
	time.sleep(30)
	return States.waitHost

def do_waitAnyFile():
	files = getFiles()
	print(files)
	if (len(files) > 1):
		return States.moveManyFiles
	if (len(files) > 0):
		return States.oneFileSleep
	time.sleep(20)
	if (pingHost() != 0):
		print("lost host")
		umountScanner()
		return States.waitHost
	return States.waitAnyFile

def do_oneFileSleep():
	time.sleep(15)
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
