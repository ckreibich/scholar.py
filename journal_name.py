import matplotlib.pyplot as plt
plt.rcdefaults()
import numpy as np
import matplotlib.pyplot as plt
import json

def get_json():
	jour=0
	conf=0
	list=[]
	diction={}
	number=[]
	name=[]
	with open('bibtex1.json') as json_file:
		data = json.load(json_file)
		for a in data:
			b = a.split('\n')
			for m in b: 
				if "journal={" in m:
					jour=jour+1
					diction[m]= diction.get(m,0)+1
				elif "booktitle={" in m:
					conf= conf+1
					diction[m]= diction.get(m,0)+1
				elif "title" in m:
					list.append(m) 
		print ("the number of journal is:",jour)
		print ("the number of conference is:",conf)
		print (list)
		for key in diction:
			number.append(diction[key])
			key = key.replace("journal={","")
			key = key.replace("},","")
			name.append(key)
	plt.rcdefaults()
	fig, ax = plt.subplots()

	y_pos = np.arange(len(name))
	ax.barh(y_pos, number,
			color='blue')
	ax.set_yticks(y_pos)
	ax.set_yticklabels(name)
	ax.invert_yaxis()  # labels read top-to-bottom
	ax.set_xlabel('Number')
	ax.set_title('How many times a journal has show up')

	plt.show()
	
	
if __name__=="__main__":
	get_json()
