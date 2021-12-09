FROM moosivp/moos-ivp:r9767-gui
LABEL maintainer = Carter Fendley (http://carterfendley.com)

# ================================== #
# Configure system
# ================================== #
# The moosivp/moos-ivp docker contains will set the user to `moos` after it is finished with it's work. Either we run `sudo ...` for each command or we temporarily switch back to root for system level work. See the docker file here: https://gitlab.com/moos-ivp/moosdocker/-/blob/master/docker/moos-ivp/Dockerfile
USER root

ARG USER_ID
ARG GROUP_ID

RUN groupadd -g $GROUP_ID host_group
RUN usermod -g $GROUP_ID moos 
RUN usermod -u $USER_ID moos 
RUN usermod -aG sudo moos
RUN echo "moos:moos" | chpasswd

# ================================== #
# Install system dependencies
# ================================== #
# Some apt-get install will pause for user input if the following is not set
ENV DEBIAN_FRONTEND="noninteractive"

# Core dependencies 
RUN apt-get update && apt-get install -y sudo python3.7-dev python3-pip 
# Add utilities
RUN apt-get install -y vim emacs-nox tmux
# Add debuging utilities
RUN apt-get install -y gdb psmisc
# Matplotlib X11 forwarding with GTK
RUN apt-get install -y python3-tk

# Clean up any caches that installations made, makes total docker image size smaller.
RUN apt-get clean

# ================================== #
# Configure python / pip
# ================================== #
# Okay... little bit about the below! There is an underlying python3 version that comes with the docker container this is FROM (maybe originally from the linux dist). So here we set the default python3 to be python3.7. This makes sure that any hash bangs in files will be run by the python which we are installing mivp_agent for.
RUN update-alternatives --install /usr/bin/python3 python3 $(which python3.7) 10
# Then, more recent pip packages have stopped distributing wheels for the `manylinux1` platform tag in favor of the `manylinux2010` tag which is only available from pip versions >=19.0. Without upgrading, as done below, the pip version will be around 9.0.x from the apt repos and will be forced to, very slowly, build wheels manually. More on platform tags here: https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/
RUN python3 -m pip install --upgrade pip
# Finally, this will create a mismatch between pip and the wrapper that runs the `pip3` command from the console. If run from this method it will print warnings to console and according to these warnings it will eventually break. Thus, below I use `python3 -m pip install ....` to install packages so everyone is happy and no yelling goes on in the console. ore here: https://github.com/pypa/pip/issues/5599

# We should have done all system level work by now, so switch user
USER moos

# ================================== #
# Setup moos-ivp-aquaticus repo
# ================================== #
# For some reason the bellow is not set properly
ENV HOME="/home/moos"
# Configure some environment vars
ENV AQUATICUS="moos-ivp-aquaticus"
ENV AQUATICUS_PATH="${HOME}/${AQUATICUS}"

# Download and build aquaticus tree
RUN svn co "https://oceanai.mit.edu/svn/${AQUATICUS}-oai/trunk/" "${AQUATICUS_PATH}"
RUN cd "${AQUATICUS_PATH}" && ./build.sh

# Add binaries and libraries to correct paths
ENV PATH="${AQUATICUS_PATH}/bin:${PATH}"
ENV IVP_BEHAVIOR_DIRS="${IVP_BEHAVIOR_DIRS}:${AQUATICUS_PATH}/lib"

# ================================== #
# Copy moos-ivp-agent from local version
# ================================== #
# mivp-agent tree
ENV AGENT="moos-ivp-agent"
ENV AGENT_PATH="${HOME}/${AGENT}"

RUN mkdir -p ${AGENT_PATH}
COPY --chown=moos:moos . ${AGENT_PATH}/

# ================================== #
# Install the mivp_agent python package
# ================================== #
# Yay more fun pip / python things (potentially the last)! I am putting pip install in -e to make development of the mivp_agent package easier here (so it live updates). However b/c the system level python package dir (/usr/local/lib/python3.7/site-packages in this case) is not editable by the `moos` user pip will default to user mode regardless of the --user flag being added. But there seems to be a conflict between -e and --user (https://github.com/pypa/pip/issues/7953). To fix this you can use --prefix=~/.local instead of --user. However some of the path comparison inside pip will output warnings unless I specify --prefix=/home/moos/.local (I think this is due to some docker user stangeness)
RUN cd ${AGENT_PATH}/src/python_module && python3 -m pip install -e . --prefix=/home/moos/.local
RUN cd ${AGENT_PATH}/src/python_module && python3 -m pip install -e .[test] --prefix=/home/moos/.local

# ================================== #
# Setup moos-ivp-agent C++ package
# ================================== #
RUN cd ${AGENT_PATH} && ./build.sh

ENV PATH="${AGENT_PATH}/bin:${PATH}"
ENV IVP_BEHAVIOR_DIRS="${IVP_BEHAVIOR_DIRS}:${AGENT_PATH}/lib"

# ================================== #
# Install python deps for examples
# ================================== #
# Install examples' deps
RUN python3 -m pip install tqdm wandb==0.11.2
# For plearn examples
RUN python3 -m pip install --no-cache-dir 'tensorflow==1.14' 'keras==2.0.8' colorama 'h5py==2.10.0'