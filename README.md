# moos-ivp-agent

[![C++ Build](https://github.com/mivp-agent/moos-ivp-agent/actions/workflows/cpp-workflow.yml/badge.svg)](https://github.com/mivp-agent/moos-ivp-agent/actions/workflows/cpp-workflow.yml)
[![Python Build](https://github.com/mivp-agent/moos-ivp-agent/actions/workflows/py3-workflow.yml/badge.svg)](https://github.com/mivp-agent/moos-ivp-agent/actions/workflows/py3-workflow.yml)

Model agnostic ML tooling for MOOS-IvP. See very simple implementation below based on the [ManagerExample](./examples/ManagerExample). See the [mivp-agent.github.io](https://mivp-agent.github.io/) website for more information about getting started.

```python
VEHICLES = ['alder', ]

from mivp_agent.manager import MissionManager
with MissionManager() as mgr:
  print('Waiting for vehicle connection...')
  mgr.wait_for(VEHICLES)

  while True:
    # Get state message from server
    msg = mgr.get_message()

    # Decide on action
    action = None
    if msg.state['NAV_X'] < 100:
      action = {
        'speed': 2.0,
        'course': 90.0
      }
    if msg.state['NAV_X'] > 50:
      action = {
        'speed': 2.0,
        'course': 270.0
      }

    # Respond to BHV_Agent's message with an action
    msg.act(action)
```

This project builds upon the ground work done by [moos-ivp-pLearn](https://github.com/mnovitzky/moos-ivp-pLearn). It implements a "model bridge" from [moos-ivp](https://oceanai.mit.edu/moos-ivp/pmwiki/pmwiki.php?n=Main.HomePage) to python 3.x land.

The above example shows how to use `MissionManager` (python) with `BHV_Agent` (MOOS-IvP). This repository also contains useful tools for training MOOS-IvP agents like `pEpisodeManager`

## Installation instructions

### Install docker

See [this](https://docs.docker.com/get-docker/) page for instructions for each major OS.

### Download this repo

```
git clone https://github.com/mivp-agent/moos-ivp-agent.git
```

See the docker section below for usage of the docker container.

### Linux
---

**NOTE:** I will often have to **restart NOT log out** before the group addition and `docker run hello-world` works without root privilages
 
Follow the post install instructions for docker [here](https://docs.docker.com/engine/install/linux-postinstall/)

### Mac OSX
---

#### Installing and configuring XQuartz

Install [XQuartz](https://content.byui.edu/file/cddfb9c0-a825-4cfe-9858-28d5b4c218fe/1/Course/Setup-XQuartz.html) for the GUI components to render properly.

`pMarineViewer` has a compatibility issue with connections inside of the docker container on some versions of OSX. On your **host NOT docker** terminal enter the following command.

```
defaults write org.xquartz.X11 enable_iglx -bool true
```

[Reference](https://unix.stackexchange.com/questions/429760/opengl-rendering-with-x11-forwarding/642954#642954)

After this is done you can use the refresh script to restart XQuartz

```
./refresh_xquartz.sh
```

#### Handling pMarineViewer crashes

If you see the pMarineViewer window for a moment and then have it crash, it can be related to the following error.

```
[xcb] Unknown sequence number while processing queue
[xcb] Most likely this is a multi-threaded client and XInitThreads has not been called
[xcb] Aborting, sorry about that.
```

The first thing to make sure of is that you have set the `enable_iglx` flag correctly (see above section). 

I have noticed this happening even after the `enable_iglx` flag is set to true. For me, **XQuartz will function properly the first time** pMarineViewer is loaded. The **second time, and every time after, I will see the above error**. A workaround to this is using the `./refresh_xquartz.sh` before every time you need.

### FAQ

**My pMarine viewer will not show up** 

If on mac, read the "XQuartz on OSX section" carefully and follow the steps. After done, restart the docker container & XQuartz.

**I can't install or get something work**

Open an [issue](https://github.com/mivp-agent/moos-ivp-agent/issues) this repository is still **very** young and I need to know about any issues with the install process.

## Using the docker script

This repo comes with the `docker.sh` script for OSX and Linux to make managing it's docker container easier.

Note the **password** for the `moos` user is `moos`

### Building the container

We can build the `mivp-agent` image with the following usage. The first time you run this it will take a while.

```
./docker.sh build
```

The image will take a while to build the first time.

### Running the container

If no `mivp-agent` container is running, the following command will start one and put you in a bash shell inside the container.

**REALLY IMPORTANT NOTE:** This script will create a link between the `moos-ivp-agent/examples`, `moos-ivp-agent/src`, and `moos-ivp-agent/missions` folders on the host machine and the docker container. **Any change** on the host or docker container will be reflected in the other. This is intended to make development and data exfiltration easier but can very easily get you into trouble if not cautious.

**NOTE:** If previously run, you will need to `./docker.sh rm` before starting another container. See below.

```
./docker.sh run
```

If you want **another terminal inside the running container** use the following command.

```
./docker.sh connect
```

### Shutting down the container

The following sequence of commands will both stop the `mivp-agent` container (regardless of any activity) and remove the container.

```
./docker.sh stop
./docker.sh rm
```

## Where do I start?
See the [mivp-agent.github.io](https://mivp-agent.github.io/) website for more information about getting started.
