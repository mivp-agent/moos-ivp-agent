FROM moosivp/moos-ivp:r9767-gui
LABEL maintainer = Carter Fendley (http://carterfendley.com)

ENV MOOS="moos-ivp-aquaticus"
ENV PATH="/home/moos/${MOOS}/bin:${PATH}"
ENV IVP_BEHAVIOR_DIRS="${IVP_BEHAVIOR_DIRS}:/home/moos/${MOOS}/lib"

# System Setup
USER root

ARG USER_ID
ARG GROUP_ID

RUN groupadd -g $GROUP_ID host_group
RUN usermod -g $GROUP_ID moos 
RUN usermod -u $USER_ID moos 
RUN usermod -aG sudo moos
RUN echo "moos:moos" | chpasswd
# Add dependencies
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y sudo python3.7-dev python3-pip && apt-get clean

# Okay... little bit about the below! There is an underlying python3 version that comes with the docker container this is FROM (maybe originally from the linux dist). So here we set the default python3 to be python3.7. This makes sure that any hash bangs in files will be run by the python which we are installing mivp_agent for.
RUN update-alternatives --install /usr/bin/python3 python3 $(which python3.7) 10
# Then, more recent pip packages have stopped distributing wheels for the `manylinux1` platform tag in favor of the `manylinux2010` tag which is only available from pip versions >=19.0. Without upgrading, as done below, the pip version will be around 9.0.x from the apt repos and will be forced to, very slowly, build wheels manually. More on platform tags here: https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/
RUN python3 -m pip install --upgrade pip
# Finally, this will create a mismatch between pip and the wrapper that runs the `pip3` command from the console. If run from this method it will print warnings to console and according to these warnings it will eventually break. Thus, below I use `python3 -m pip install ....` to install packages so everyone is happy and no yelling goes on in the console. ore here: https://github.com/pypa/pip/issues/5599


# Add utilities
RUN apt-get install -y vim emacs-nox tmux git
# Add debuging utilities
#RUN apt-get install -y gdb psmisc 

# Matplotlib X11 forwarding with GTK
ENV DEBIAN_FRONTEND="noninteractive"
RUN apt-get install -y python3-tk

USER moos

# Aquaticus tree
RUN svn co "https://oceanai.mit.edu/svn/${MOOS}-oai/trunk/" "${HOME}/${MOOS}"
RUN cd "${HOME}/${MOOS}" && ./build.sh

# mivp-agent tree
ENV MIVP_AGENT="moos-ivp-agent"
ENV PATH="/home/moos/${MIVP_AGENT}/bin:${PATH}"
ENV PATH="${PATH}:/home/moos/${MIVP_AGENT}/src/python_module/scripts"
ENV IVP_BEHAVIOR_DIRS="${IVP_BEHAVIOR_DIRS}:/home/moos/${MIVP_AGENT}/lib"

RUN mkdir -p ${MIVP_AGENT}
COPY --chown=moos:moos . ${MIVP_AGENT}/

# ====================================================== #
# Install the mivp_agent python package in editable mode
# ====================================================== #
# Yay more fun pip / python things (potentially the last)! I am putting pip install in -e to make development of the mivp_agent package easier here (so it live updates). However b/c the system level python package dir (/usr/local/lib/python3.7/site-packages in this case) is not editable by the `moos` user pip will default to user mode regardless of the --user flag being added. But there seems to be a conflict between -e and --user (https://github.com/pypa/pip/issues/7953). To fix this you can use --prefix=~/.local instead of --user. However some of the path comparison inside pip will output warnings unless I specify --prefix=/home/moos/.local (I think this is due to some docker user stangeness)
RUN cd ${MIVP_AGENT}/src/python_module && python3 -m pip install -e . --prefix=/home/moos/.local
RUN cd ${MIVP_AGENT}/src/python_module && python3 -m pip install -e .[test] --prefix=/home/moos/.local

RUN cd ${MIVP_AGENT} && ./build.sh --test

# Install examples' deps
RUN python3 -m pip install tqdm wandb==0.11.2
# For plearn examples
RUN python3 -m pip install --no-cache-dir 'tensorflow==1.14' 'keras==2.0.8' colorama 'h5py==2.10.0'