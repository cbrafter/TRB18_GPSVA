FROM ubuntu:16.04
MAINTAINER Craig B Rafter (c.b.rafter@soton.ac.uk)
LABEL Description="Docker Container Simulation of Urban MObility(SUMO) + Python TraCI"

# Environment Variables
ENV SUMO_VERSION 0.30.0

# Updates system 
RUN apt-get update -y

# Install system tools
RUN apt-get install -y apt-utils
RUN apt-get install -y build-essential python-pip git wget

# Upgrade pip
# RUN pip install --upgrade pip

# Install python prerequisites
RUN pip install scipy numpy matplotlib psutil

# Install SUMO Prerequistites
RUN apt-get install -y autoconf
RUN apt-get install -y \
	libproj-dev proj-bin proj-data libtool \
	libgdal1-dev libxerces-c3-dev \
	libfox-1.6-0 libfox-1.6-dev

# Fetch and build SUMO
# RUN wget https://sourceforge.net/projects/sumo/files/sumo/version\ $SUMO_VERSION/sumo-all-0.30.0.tar.gz/download
RUN wget http://prdownloads.sourceforge.net/sumo/sumo-all-$SUMO_VERSION.tar.gz
RUN tar -xvf sumo-all-$SUMO_VERSION.tar.gz
WORKDIR /sumo-$SUMO_VERSION
RUN ./configure
RUN make install
RUN mkdir -p /usr/share/sumo/tools/
RUN cp -r /sumo-$SUMO_VERSION/tools/ /usr/share/sumo/
WORKDIR /

# Post install clean-up
RUN rm -rf /sumo-$SUMO_VERSION/
RUN rm -rf /sumo-all-$SUMO_VERSION.tar.gz
RUN apt-get autoremove -y
