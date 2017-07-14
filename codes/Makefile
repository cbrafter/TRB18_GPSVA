# Makefile to build on Linux

VMNAME = sumovm
ESCPATH = $(shell printf "%q\n" "$(shell pwd)")
UESCPATH = $(shell pwd | sed -e 's/ /\\ /g' -e 's/\[/\\\[/g' -e 's/\]/\\\]/g')
START ?= 1
END ?= 16

build:
	docker build -t $(VMNAME) .

ubuntu:
	docker run \
		-v /hardmem/results_TRB2/:/hardmem/results/ \
		-v $(UESCPATH)/mainCode/:/simulation/mainCode/ \
		-v $(UESCPATH)/sumoAPI/:/simulation/sumoAPI/ \
		-w /simulation/mainCode \
		$(VMNAME) python parallelRun.py $(START) $(END)

ubuntu_special:
	docker run \
		-v /hardmem/results_TRB2/:/hardmem/results/ \
		-v $(UESCPATH)/mainCode/:/simulation/mainCode/ \
		-v $(UESCPATH)/sumoAPI/:/simulation/sumoAPI/ \
		-w /simulation/mainCode \
		$(VMNAME) python ParallelSpecial.py $(START) $(END)

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
		-v $(UESCPATH)/mainCode/:/simulation/mainCode/ \
		-v $(UESCPATH)/sumoAPI/:/simulation/sumoAPI/ \
		-w /simulation/mainCode \
		$(VMNAME) python dockerTest.py $(START) $(END)

test_mac:
	docker run \
		-v $(ESCPATH)/results/:/hardmem/results/ \
		-v $(ESCPATH)/mainCode/:/simulation/mainCode/ \
		-v $(ESCPATH)/sumoAPI/:/simulation/sumoAPI/ \
		-w /simulation/mainCode \
		$(VMNAME) python dockerTest.py $(START) $(END)

echo_test:
	echo $(UESCPATH)

prune:
	docker system prune
	docker container prune
	docker volume prune
	docker image prune
