# -*- coding: UTF-8 -*-
import sys
import sqlite3

from pathlib import Path
from crayons import blue, green, white, red, yellow
from pprint import pformat

# Locate the directory containing this file and the repository root.
# Temporarily add these directories to the system path so that we can import
# local files.
here = Path(__file__).parent.absolute()
repository_root = (here / ".").resolve()
device_db=str(repository_root) + "/bases/devices.db"
device=[]
with sqlite3.connect(device_db) as conn:
	cursor=conn.cursor()
	sql_request = "SELECT * from devices"
	cursor.execute(sql_request)	
	devices=[]
	for resultat in cursor:
		#print(resultat)	
		device = {
			'device_type': resultat[1],
			'name': resultat[2],
			'ip': resultat[3],
			'username': resultat[4],
			'password': resultat[5],
			'enable_password': resultat[6],
			'selected': resultat[7]
		}
		devices.append(device)
	for equipement in devices:
		#print(equipement)	
		print(
        yellow("Device Details:", bold=True),
        pformat(equipement),
        sep="\n"
    )
