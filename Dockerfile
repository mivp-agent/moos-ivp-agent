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
RUN pip3 install tqdm

USER moos

# Aquaticus tree
RUN svn co "https://oceanai.mit.edu/svn/${MOOS}-oai/trunk/" "${HOME}/${MOOS}"
RUN cd "${HOME}/${MOOS}" && ./build.sh

# RLquaticus tree
ENV RLQUATICUS="moos-ivp-RLquaticus"
ENV PATH="/home/moos/${RLQUATICUS}/bin:${PATH}"
ENV PYTHONPATH="${PYTHONPATH}:/home/moos/${RLQUATICUS}/src/python_module"
ENV IVP_BEHAVIOR_DIRS="${IVP_BEHAVIOR_DIRS}:/home/moos/${RLQUATICUS}/lib"

RUN mkdir -p moos-ivp-RLquaticus
COPY --chown=moos:moos . moos-ivp-RLquaticus/

RUN cd ${RLQUATICUS} && ./build.sh
