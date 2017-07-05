# Makefile to build on Linux

VMNAME = sumovm
ESCPATH = $(shell printf "%q\n" "$(shell pwd)")
START ?= 1
END ?= 10

build:
	docker build -t $(VMNAME) .

ubuntu:
	docker run \
		-v /hardmem/results_TRB/:/hardmem/results/ \
		-v $(ESCPATH)/mainCode/:/simulation/mainCode/ \
		-v $(ESCPATH)/sumoAPI/:/simulation/sumoAPI/ \
		-w /simulation/mainCode \
		$(VMNAME) python parallelRun.py $(START) $(END)

mac:
	docker run \
		-v $(ESCPATH)/results/:/hardmem/results/ \
		-v $(ESCPATH)/mainCode/:/simulation/mainCode/ \
		-v $(ESCPATH)/sumoAPI/:/simulation/sumoAPI/ \
		-w /simulation/mainCode \
		$(VMNAME) python parallelRun.py $(START) $(END)

test_ubuntu:
	docker run \
		-v /hardmem/results_jun17/:/hardmem/results/ \
		-v $(ESCPATH)/mainCode/:/simulation/mainCode/ \
		-v $(ESCPATH)/sumoAPI/:/simulation/sumoAPI/ \
		$(VMNAME) /bin/bash -c \
		"cd simulation/mainCode; python dockerTest.py $(START) $(END)"

test_mac:
	docker run \
		-v $(ESCPATH)/results/:/hardmem/results/ \
		-v $(ESCPATH)/mainCode/:/simulation/mainCode/ \
		-v $(ESCPATH)/sumoAPI/:/simulation/sumoAPI/ \
		$(VMNAME) /bin/bash -c \
		"cd simulation/mainCode; python dockerTest.py $(START) $(END)"

prune:
	docker system prune
	docker container prune
	docker volume prune
	docker image prune

