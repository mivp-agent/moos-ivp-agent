FROM moosivp/moos-ivp:r9767-gui
LABEL maintainer = Michael Misha Novitzky <michael.novitzky@westpoint.edu>

ENV MOOS="moos-ivp-aquaticus"
ENV PATH="/home/moos/${MOOS}/bin:${PATH}"
ENV IVP_BEHAVIOR_DIRS="${IVP_BEHAVIOR_DIRS}:/home/moos/${MOOS}/lib"

# System Setup
USER root
RUN usermod -aG sudo moos
RUN echo "moos:moos" | chpasswd
# Add dependencies
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y sudo python3-dev python3-pip && apt-get clean
# Add utilities
RUN apt-get install -y vim emacs-nox tmux git
# Add debuging utilities
RUN apt-get install -y gdb psmisc 
# Legacy plearn stuff
RUN pip3 install --no-cache-dir numpy matplotlib 'tensorflow==1.5' 'keras==2.0.8' colorama 'h5py==2.10.0'
# Matplotlib X11 forwarding with GTK
ENV DEBIAN_FRONTEND="noninteractive"
RUN apt-get install -y python3-tk
RUN pip3 install tqdm wandb

USER moos

# Aquaticus tree
RUN svn co "https://oceanai.mit.edu/svn/${MOOS}-oai/trunk/" "${HOME}/${MOOS}"
RUN cd "${HOME}/${MOOS}" && ./build.sh

# mivp-agent tree
ENV MIVP_AGENT="moos-ivp-agent"
ENV PATH="/home/moos/${MIVP_AGENT}/bin:${PATH}"
ENV PYTHONPATH="${PYTHONPATH}:/home/moos/${MIVP_AGENT}/src/python_module"
ENV IVP_BEHAVIOR_DIRS="${IVP_BEHAVIOR_DIRS}:/home/moos/${MIVP_AGENT}/lib"

RUN mkdir -p ${MIVP_AGENT}
COPY --chown=moos:moos . ${MIVP_AGENT}/

RUN cd ${MIVP_AGENT} && ./build.sh
