routes = open('routes.txt','r')
outfile = open('routeheader.xml','w')
for line in routes:
	path  = line[1:-2].split(' ')
	#print >> outfile, """<route edges={} id="{}"/>""".format(line[:-1], path[0]+'TO'+path[-1])
	# Just IDs
	print >> outfile, """["{}", prob],""".format(path[0]+'TO'+path[-1])
routes.close()
outfile.close()