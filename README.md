# moos-ivp-agent

Model agnostic ML tooling for MOOS-IvP. See very simple implementation below based on the [ManagerExample](./examples/ManagerExample)

```
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
git clone https://github.com/CarterFendley/moos-ivp-agent.git
```

See the docker section below for usage of the docker container.

### XQuartz and OSX

Install [XQuartz](https://content.byui.edu/file/cddfb9c0-a825-4cfe-9858-28d5b4c218fe/1/Course/Setup-XQuartz.html) for the GUI components to render properly.

#### Fix multi-threading issue

`pMarineViewer` has a compatibility issue with connections inside of the docker container on some versions of OSX. On your **host NOT docker** terminal enter the following command.

```
defaults write org.xquartz.X11 enable_iglx -bool true
```

[Reference](https://unix.stackexchange.com/questions/429760/opengl-rendering-with-x11-forwarding/642954#642954)

#### Allow networked connections

Run the following command to start XQuartz (again, on a host terminal).

```
xhost +
```

After the command completes go to the task bar and `XQuarts > Preferences > Security` and check the box labeled `Allow connections from network clients`. After doing this you will need to restart xhost. The following method will work among others.

```
killall Xquartz
xhost +
```

### FAQ

**My pMarine viewer will not show up** 

If on mac, read the "XQuartz on OSX section" carefully and follow the steps. After done, restart the docker container & XQuartz.

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

