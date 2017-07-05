# edges = ['a1','a2','a3','b0','c0','d0','b4','c4','d4','e1','e2','e3']
entries = [
'a1:b1',
'a2:b2',
'a3:b3',
'b0:b1',
'c0:c1',
'd0:d1',
'b4:b3',
'c4:c3',
'd4:d3',
'e1:d1',
'e2:d2',
'e3:d3',
'e3:ed'
]

listFile = open('manhattan.trips.xml','w')

print >> listFile, """<?xml version="1.0"?>
<trips>"""
i=0
for x in entries:
	for y in entries:
		y = y[3:]+':'+y[:2] # change direction of stuff
		print >> listFile, '''\t<trip id="{val}" depart="{val}.00" from="{src}" to="{dest}" />'''.format(val=str(i), src=x, dest=y)
		i += 1

print >> listFile, '</trips>'
listFile.close()
