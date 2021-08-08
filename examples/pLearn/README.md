# moos-ivp-agent's pLearn implementation

**DISCLAIMER:** 
- Currently only the **default fitted-Q algorithm** from pLearn is implemented. If someone is using another algorithm lmk (open an issue) as it should be straightforward to get working.
- Both running and testing is supported (training shortly as it needs more translation from python 2.7 to python 3.x).
- Like pLearn, this implementation is designed to work with vehicles on the red team.

## Running existing models

**IMPORTANT** Launch instructions are significantly different from those of pLearn. Read fully.

Firstly, make sure your trained model exists in a file structure like this...

```
- enviroment.py  # <--- this is REQUIRED
- iteration_39/ # <--- this is what YOU point the run script to
    - (2, 0).h5
    - (2, 60).h5
    - (2, 120).h5 
    - (2, 180).h5
    - (2, 240).h5
    - (2, 300).h5
```

Launching the simulation comes in two steps. You will need two consoles **INSIDE** the moos-ivp-agent's docker container... so utilize the `./docker.sh connect` functionality.

The first task is to launch the `run.py` script (inside `examples/pLearn/model`) and point it to your model.

```
cd examples/pLearn/model
./run.py --model trained/my_model/iteration_39
```

**NOTE:** If no model is provided, the `run.py` script will run the model in the `trained/topModel/model` directory.

Then we need to launch a moos-ivp simulation. The `examples/pLearn/mission` directory has such a simulation with `BHV_Agent` properly configured to be compatible with pLearn. 

```
cd examples/pLearn/mission
./launch_full.sh 6 
```

Most time warps should work. After the GUI window pops up, you can push the `DEPLOY` button in the lower right.

## Debugging existing models

The moos-ivp-agent implementation of pLearn comes equipped with some visualizations to provide insight into pLearn models. Using the `--debug` flag.

```
./run.py --model trained/my_model/iteration_39 --debug
```

Similarly to the normal usage of the run script, you will need to launch the moos-ivp simulation separately.

## Testing iterations of existing models

**IMPORTANT:** Only launch the moos-ivp simulation through the script provided.

This time we will point the `test.py` script at the folder containing the iterations. The amount of iterations does not matter.

```
- my_model/ # <--- this is what YOU point the test script to
    - enviroment.py  # <--- this is still REQUIRED
    - iteration_1/ 
        - (2, 0).h5
        - (2, 60).h5
        - (2, 120).h5 
        - (2, 180).h5
        - (2, 240).h5
        - (2, 300).h5
    .
    .
    .
    - iteration_50/ 
        - (2, 0).h5
        - (2, 60).h5
        - (2, 120).h5 
        - (2, 180).h5
        - (2, 240).h5
        - (2, 300).h5
```

We point the test script to this location through the following.

```
./test.py --test_dir trained/my_model
```

Again, in another console we will launch the moos-ivp simulation **BUT** this time through the script provided in `examples/pLearn/model/scripts/launch.sim`. This simulation has default time warp of 15.

```
cd examples/pLearn/model
./scripts/launch_sim.sh
```

**NOTE:** The script will automatically deploy and reset the vehicles... no pMarineViewer will launch.

After the simulation is launched, you will see some visualizations apear. These will update automatically after every tested model. The graphs will also be saved in a `test_graph.png` file inside the specified `--test_dir`.