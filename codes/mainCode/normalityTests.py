from scipy.stats import shapiro
import numpy as np

models = ['simpleT', 'twinT', 'corridor', 'manhattan']
controllers = ['fixed', 'actuated', 'gpsctrl', 'spatctrl_va']

for ctrl in controllers:
	for model in models:
		delay = np.loadtxt('./data/'+ctrl+'/'+model+'_delayData.txt', delimiter=',')
		queue = np.loadtxt('./data/'+ctrl+'/'+model+'_qTimeData.txt', delimiter=',')
		for i in range(delay.shape[0]):
			if len(delay.shape) == 1:
				s1 = shapiro(delay)
				s2 = shapiro(queue)
			else:
				s1 = shapiro(delay[i,:])
				s2 = shapiro(queue[i,:])
			print([s1, s2])