import sys
import sqlite3
from pathlib import Path
from crayons import blue, green, white, red, yellow,magenta, cyan
from pprint import pformat
from netmiko import ConnectHandler
import os
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime 

here = Path(__file__).parent.absolute()
repository_root = (here / ".").resolve()
output_file="./output/show.txt"

debug=0
debug_print_line=0 # line in read_all_lines_until_first_word_is() : at every letter
debug_print_line2=0 # line in read_all_lines_until_first_word_is() : returned constructed line
debug_print_txt2=1
debug_parse1=0# display text2 passed to parse()
debug_parse2=0# display each lines read by parse()
debug_parse3=1# display lines we keep in parse()
debug_parse_column1=0# displays the parsed word in columns  parse()
debug_after_parse2=1

def insert_data_to_db(data):
	sql_create="CREATE TABLE IF NOT EXISTS vpnsessions ( id text PRIMARY KEY, time TEXT ,name TEXT ,Active TEXT ,Cumulative TEXT ,Peak_Concur TEXT,Inactive TEXT,Total_Active_and_Inactive TEXT,Total_Cumulative TEXT ,Device_Total_VPN_Capacity TEXT,Device_Load TEXT ,AnyConnect_Parent_actives TEXT,AnyConnect_Parent_Cumulative TEXT ,AnyConnect_Parent_Peak_Concurrent TEXT ,SSL_Tunnel_actives TEXT ,SSL_Tunnel_Cumulative TEXT ,SSL_Tunnel_Peak_Concurrent TEXT ,DTLS_Tunnel_Actives TEXT ,DTLS_Tunnel_Cumulative TEXT ,DTLS_Tunnel_Peak_Concurrent TEXT );"
	sql_add="INSERT into vpnsessions (id , time ,name ,Active ,Cumulative ,Peak_Concur ,Inactive  ,Total_Active_and_Inactive  ,Total_Cumulative ,Device_Total_VPN_Capacity  ,Device_Load ,AnyConnect_Parent_actives  ,AnyConnect_Parent_Cumulative ,AnyConnect_Parent_Peak_Concurrent ,SSL_Tunnel_actives ,SSL_Tunnel_Cumulative ,SSL_Tunnel_Peak_Concurrent ,DTLS_Tunnel_Actives ,DTLS_Tunnel_Cumulative ,DTLS_Tunnel_Peak_Concurrent ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);"		
	#with sqlite3.connect(':memory:') as conn:
	with sqlite3.connect('./bases/vpnsession.db') as conn:
		c=conn.cursor()
		try:
			c.execute(sql_create)
		except:
			sys.exit("couldn't create sqli tables")
		try:
			c.executemany(sql_add, data)
		except:
			sys.exit("Error adding data to db")
		return(c)
	return()
	

def read_all_lines_until_first_word_is(file,mot):
	# read the text file line by lines until the string [ mot ] is found as the first word of the line. To avoid to read uselessly all the config file
	# if the string [ word ] is not found, then all the text file is readed until the end
	# If we read more than 100 empty line we consider that the end of file has been reached	
	# result is a
	fh = open(file,"r",encoding="utf-8" )
	line=''
	#txt  = fh.readline()
	stop=0
	nb_lignes_vides=0
	while( stop == 0 ):
		txt = fh.readline()
		ii=0
		debug=0
		if debug:
			print('== ',txt)
		if txt !='':
			stop=1
			while( ii < len(txt) ):
				#print (str(ii) + ' : ' + txt[ii] + ' - '+str(ord(txt[ii])))	
				if ord(txt[ii])==9:
					line += ' '
				else:
					if txt[ii]==' ' and txt[ii-1]==' ':
						a=0
						if debug_print_line:
							print(blue("constructed line :",str(ii) ,txt[ii]))
							print(line)						
					else:
						line = line + txt[ii]
						if debug_print_line:
							print(blue("constructed line ,",str(ii) ,txt[ii]))
							print(line)
				ii += 1
				i2=0
				while i2 < len(mot):
					#print (mot[i2])	
					if i2 < len(txt):						
						if txt[i2] != mot[i2]:
							stop=0
					i2 = i2+1
		else:
			#print ('empty line')
			nb_lignes_vides+=1
			if nb_lignes_vides > 100:
				stop=1
	fh.close()
	print(yellow("==> STEP 1 - READ ALL LINES FROM FILE = OK. every words had been stored in the csv like table txt2"))
	if debug_print_line2:
		print(blue("Returned line is :"))
		print(line)
		print(blue("Returned line is above :"))
	return(line)
	
def mac_addr(address):
	"""Convert a MAC address to a readable/printable string
	   Args:
		   address (str): a MAC address in hex form (e.g. '\x01\x02\x03\x04\x05\x06')
	   Returns:
		   str: Printable/readable MAC address
	"""
	return ':'.join('%02x' % compat_ord(b) for b in address)	

def valid_ip(address):
	try: 
		addr=ipaddress.ip_address(address)
		#print(addr)
		return True
	except:
		return False
		
def parse(texte,a,mots1:list,mots2:list,start,end,parse_first_line,colomn:list,add_eol,add_eol_when,one_time):
	#	a =	delimiter
	# 	colomn  =	colomns to keep  if colomn[0] =999 then keep all colomns
	#	mots1 = 	list of words to find in the line we want to keep. if the first and only word in the list is 'ALLWORDS' then we keep all lines
	# 	mots2 =	list of words to not find in the line we want to keep. if one word is found then the line is not kept
	#	start 	=	if the line begins with this word then start to keep all readed lines  until the [ end ] word is found in a coming line
	# 	end = 	the word which indicates the end of the chunk we parse in the file.
	#	parse_first_line = 1 if we want to parse the first kept line  of the chunk,  and = 0 if we don't want to parse it( we start to parse just the line after the [ start word ]
	#	if add_eol = 1 then add end of Line after every line read, if =0 if you want to concatenate in a line all parsed words all line read together
	#	add_eol_when = add a new line character when the word is found in the line
	#	one_time : If = 1 then stop parsing when [ end ] reached. If = 0  parse again if [ start ] is found again in the file
	if debug_parse1:
		print (cyan('parse() texte = :\n'))	
		print (texte)
	lignes = texte.split('\n')
	commencer=0
	do_it_again=1
	output=""
	x=""
	lignes_out=[]
	for ligne in lignes:
		if debug_parse2:
			print (white('parse() :'))	
			print (cyan(ligne))
		if ligne.find(start) >= 0 and do_it_again==1:
			commencer=1
			if parse_first_line ==1:
				i1=1
				while i1 != 0:		
					ligne=ligne.replace('  ',' ')
					if ligne.find("  ") >= 0:
						ligne=ligne.replace("  "," ")
						i1=1
					else :
						i1=0				
				tableau=ligne.split(a)
				i2=1
				for x in tableau:
					x=x.strip()
					if i2 in colomn:
						OK2=1
					else:
						OK2=0
					if colomn[0] == 999:
						OK2=1
					if x !='' and OK2:
						# clean unwanted characters in the parsed word : double quotes, comma, semi column
						x=x.replace('"','')
						x=x.replace(',','')	
						x=x.replace(':','')	
						x=x.replace(';','')
						if debug_parse_column1:
							print(cyan('	KEEP THIS WORD :  '+ x + ' IN COLUMN # : '+ str(i2)))						
						# add comma to separate parsed word		
						x = x + ';'
						#fa.write(x)
						#fa.write(';')
					i2=i2+1
				#print ("=====")	
				if ligne.find(add_eol_when) >= 0:						
					x = x + "\r\n"	
					if debug_parse3:
						print(yellow('KEEP THIS LINE :\n '+ x))
				output=output + x
				#fa.write('\n')				
		if ligne.find(end) >= 0:
			commencer=0
			if one_time==1:
				do_it_again=0
			lignes_out.append(output)
		if commencer:
			if mots1[0] != 'ALLWORDS':
				OK=0
				for x in mots1:
					if x in ligne:
						OK=1
			else:
				OK=1					
			for x in mots2:
				if x in ligne:
					OK=0	
			if OK:
				i1=1
				while i1 != 0:		
					ligne=ligne.replace('  ',' ')
					if ligne.find("  ") >= 0:
						ligne=ligne.replace("  "," ")
						i1=1
					else :
						i1=0				
				tableau=ligne.split(a)
				#i2=i2
				i2=1
				for x in tableau:
					x=x.strip()
					if i2 in colomn:
						OK2=1
					else:
						OK2=0
					if colomn[0] == 999:
						OK2=1
					if x !='' and OK2:
						# clean unwanted characters in the parsed word : double quotes, comma, semi column
						x=x.replace('"','')
						x=x.replace(',','')	
						x=x.replace(':','')	
						x=x.replace(';','')					
						if debug_parse_column1:
							print(cyan('	KEEP THIS WORD :  '+ x + ' IN COLUMN # : '+ str(i2)))
						# add comma to separate parsed word								
						x = x + ','	
						if add_eol:
							lignes_out.append(output)
							if debug_parse3:
								print(yellow('KEEP THIS LINE :\n '+output))							
							output=""							
						#	x = x + "\r\n"	
						if x.find(add_eol_when) >= 0:
							lignes_out.append(output)
							#x = x + "\n"
							if debug_parse3:
								print(yellow('KEEP THIS LINE :\n '+output))								
							output=""
							#print('.')
							#print('.')
						#print(x)							
						output=output + x
					i2=i2+1
	print("parse() says PARSING = OK")
	return(lignes_out)

def parse_show_result(file):
	# STEP 1 : read the whole configuration file
	print(yellow('=========================================================================================='))
	print(cyan('		STEP 1 : read the whole source file [ ./temp/show_result.txt ]'))
	file_to_read="./temp/"+file
	#file_to_read="./temp/show.txt"
	txt2=read_all_lines_until_first_word_is(file_to_read,'****???****')
	if debug_print_txt2:
		print(yellow('=================== DEBUG TEXT2 ==========================================================='))
		print(red("txt2 =\n"))	
		print(cyan(txt2))	
		fb = open("./output/txt2.txt", "w")	
		fb.write(txt2)
		fb.close()
		print("		you can check ./output/txt2.txt")
	if txt2.find('No sessions to display')>=0:
		print(red("NO session",bold=True))
		time = datetime.now().isoformat()
		time_list=time.split('.')			
		for item in txt2.splitlines():
			if item.find('hostname')>=0:
				nom=item.split(' = ')
		index=nom[1]+'-'+time_list[1]	
		exit_data=[]
		exit_data.append((index,time_list[1],nom[1],'0', '0','0','0','0','0','0','0', '0','0','0','0','0','0','0','0','0'))
	else:
		#STEP 2 : Parsing
		print(yellow('==========================================================================================='))
		print(cyan('		STEP 2 : Let\'s parse txt2'))	
		print(green('==========================================================================================='))
			
		keep_lines_which_contains=['hostname','Client','Load','Tunnel','otals']
		and_then_dont_keep_lines_which_contains=["****???****"]
		start_to_parse_when_found="hostname"
		stop_to_parse_when_found="****???****" 
		columns=[999] # we keep all words in the line
		delimiter=" "
		parse_first_line=0
		add_eol_after_each_readed_line=0
		add_a_new_line_when_found="Totals"
		add_a_new_line_when_found=add_a_new_line_when_found.strip()
		if add_a_new_line_when_found!="":
			keep_lines_which_contains.append(add_a_new_line_when_found)
		Parse_group_only_one_time=0

		lignes = parse(txt2,delimiter,keep_lines_which_contains,and_then_dont_keep_lines_which_contains,start_to_parse_when_found,stop_to_parse_when_found,parse_first_line,columns,add_eol_after_each_readed_line,add_a_new_line_when_found,Parse_group_only_one_time)	
		
		if debug_after_parse2:
			print(green('=================== DEBUG Print lignes ==========================================================='))
			print(lignes)
		print(yellow('=================================================================================================='))
	  	# STEP 3 Normalization and Panda DataFrame Creation 
		print(cyan('		STEP 3 Normalization and Panda DataFrame Creation '))
		database_name='sqlite:///bases/vpnsession.db'
		#table_name = 'vpn_indicators'
		print(yellow('		NO PANDA DATAFRAME HERE '))
		# STEP 3 Normalization and save results into a CSV File
		print(green('=================================================================================================='))
		print(cyan('STEP 4 Normalization and save results into a CSV File '))	
		fa = open("./output/result.csv", "w")	
		fa.write("time,name,Active,Cumulative,Peak_Concur,Inactive,Total_Active_and_Inactive,Total_Cumulative,Device_Total_VPN_Capacity,Device_Load,AnyConnect-Parent_actives,AnyConnect-Parent_Cumulative,AnyConnect-Parent_Peak_Concurrent,SSL-Tunnel_actives,SSL-Tunnel_Cumulative,SSL-Tunnel_Peak_Concurrent,DTLS-Tunnel_Actives,DTLS-Tunnel_Cumulative,DTLS-Tunnel_Peak_Concurrent")
		fa.write("\n")
		print('		Normalization step 1 : open ./output/result.csv and see how to normalize the saved lines')
		index=1	
		ligne_out2=""
		for ligne in lignes:
			print('**')
			print(yellow('		before search and replace'))
			print (ligne)
			ligne_out=ligne.replace('AnyConnect,Client,,','')
			ligne_out=ligne_out.replace(',,',',')
			ligne_out=ligne_out.replace(',Total,Active,and,Inactive,',',')
			ligne_out=ligne_out.replace('Total,Cumulative,',',')
			ligne_out=ligne_out.replace(',Device,Total,VPN,Capacity,',',')
			ligne_out=ligne_out.replace(',Device,Load,',',')
			ligne_out=ligne_out.replace(',Tunnels,Summary,AnyConnect-Parent,',',')
			ligne_out=ligne_out.replace(',DTLS-Tunnel,',',')
			ligne_out=ligne_out.replace(',SSL-Tunnel,',',')		
			ligne_out=ligne_out.replace('%','')
			ligne_out=ligne_out.replace('hostname,=,','')
			ligne_out=ligne_out.replace(',,',',')
			ligne_out=ligne_out.strip()
			index+=1
			time = datetime.now().isoformat()
			ligne_out2=time+','+ligne_out
			print(yellow('		and After search and replace'))
			print (ligne_out)
			print('**')
		print('		Normalization step 2 : do complexes if() treatements on parsed word if needed')
		lignes=ligne_out2.split('\n')
		exit_data=[]
		for ligne in lignes:
			#print (ligne)
			index=""
			if len(ligne)>10:
				fa.write(ligne)
				fa.write('\r')
				variables=ligne.split(',')
				time_list=time.split('.')
				index=variables[1]+'-'+time_list[1]			
				exit_data.append((index,variables[0],variables[1], variables[2], variables[3], variables[4], variables[5], variables[6], variables[7], variables[8], variables[9], variables[10], variables[11], variables[12], variables[13], variables[14], variables[15], variables[16], variables[17], variables[18]))

	#print(index,variables[0],variables[1], variables[2], variables[3], variables[4], variables[5], variables[6], variables[7], variables[8], variables[9], variables[10], variables[11], variables[12], variables[13], variables[14], variables[15], variables[16], variables[17], variables[18], variables[19])
	for variable in exit_data:
		print(variable)
	cursor=insert_data_to_db(exit_data)
	cursor.close() 
	fa.close()  	
	print('	=>  Normalization and Save result into CSV File = OK . You can check ./output/result.csv')	
def read_db(database):
	liste=[]
	with sqlite3.connect(database) as conn:
		cursor=conn.cursor()
		sql_request = "SELECT * from devices"
		try:
			cursor.execute(sql_request)
			for resultat in cursor:
				#print(resultat)		
				liste.append(resultat)
		except:
			sys.exit("couldn't read database")
	return(liste)

def main():
	#database="devices.db"
	database=str(repository_root) + "/bases/devices.db"	
	devices = read_db(database)	
	if devices :
		for device in devices:
			print(yellow("Collect VPN Indicators From :", bold=True))
			print(cyan(device[1]))
			#print(white ("  DO SOMETHING HERE"))
			selected_device = {
				'selected': device[7]
			} 
			if selected_device['selected']==1:
				selected_device = {
					'device_type': device[1],
					'ip': device[3],
					'username': device[4],
					'password': device[5],
					'secret': device[6]
				}	
				if selected_device['device_type']=='cisco_asa':
					print(green("Device type is : cisco_asa", bold=True))
					net_connect = ConnectHandler(**selected_device)
					net_connect.find_prompt()
					net_connect.enable()
					output = '**==>\n  hostname = '+net_connect.send_command("show hostname")
					output = output + '**vpn-sessiondb \n' + net_connect.send_command("show vpn-sessiondb")
					print(output)
					with open (output_file,'w') as fichier:
						fichier.write(output)
				elif selected_device['device_type']=='cisco_ftd':
					print(red("Device type is : cisco_ftd - NOT AVAILABLE YET - STILL UNDER DEVELOPMENT !", bold=True))
					#print(output)
				else:
					print(red("Device type is : UNKNOWN !", bold=True))
					
			else:
				print(red("   => Not Selected"))
			print(cyan("OK Let's parse result of the show vpnsession-db", bold=True))
			parse_show_result('show_result.txt')
	else:
		print('NO RESULTS')
	print('====================================================================================================')
	print()
	print(green("                                     OK ALL DONE !!", bold=True))		
if __name__=='__main__':
	main()