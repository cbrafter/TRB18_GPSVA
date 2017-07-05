import sys
import os
import shutil
import psutil
import subprocess
import time
import numpy as np
# from matplotlib import pyplot
from routeGen import routeGen
from sumoConfigGen import sumoConfigGen
from stripXML import stripXML
import multiprocessing as mp

print('Running the script! {} {}'.format(sys.argv[1], sys.argv[2]))
with open('/hardmem/results/sample.txt', 'w') as f:
	f.write('Hello World! {} {}'.format(sys.argv[1], sys.argv[2]))
print([psutil.cpu_count(), psutil.cpu_count(logical=False)])