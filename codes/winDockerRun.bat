VMNAME = sumovm
ESCPATH = $(shell printf "%q\n" "$(shell pwd)")
START ?= 1
END ?= 10

FPATH = c:/Users/cbr1g15/Documents/codes

docker run \
	-v $FPATH/results/:/hardmem/results/ \
	-v $FPATH/mainCode/:/simulation/mainCode/ \
	-v $FPATH/sumoAPI/:/simulation/sumoAPI/ \
	-w /simulation/mainCode \
	$(VMNAME) python parallelRun.py $(START) $(END)