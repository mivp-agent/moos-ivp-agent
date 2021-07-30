
# Author: Arjun Gupta
# Date: December 6 2017
import os

class State:
   """------------------------------------------------------------------------
   Structure to hold information about a state parameter to be passed on to the rest
   of the codebase
   
   self.index -> index of parameter in state representation

   self.type -> whether it is "binary", "distance", "angle", or "raw" (other inputs such as position)

   self.range -> the range of values that it can go between (not applicable for binary)

   self.bucket -> the size of. blocks that you are descritizing this parameter into. Set
   to 1 if not descritized

   self.var -> the object that this paraemter is relative to. Used by distance and theta.
   For example, if the parameter type is distance and obj is "flag", then the parameter
   defines the distance to the flag. Possibilities include "flag", "team", "has_flag", 
   "tagged". Of these, only "flag" can be used with non-binary values (distance and angle). 
   In addition, you can get raw "x", "y", and "heading" values by setting type to "raw" (only for
   the robot that is running the behavior.)

   self.var_mod -> not fully implemented yet. Goal is to have additional specifiers to self.var 
   such as "self", "enemy", "felix", "evan" that would allow you to specify which vehicle/team's 
   information you want to access. The "self" and "enemy" specifiers do work for things like distance
   and heading to flag

   self.standardized -> the value is standardized when used in the neural net to be 
   a value between 0 and 1
   ------------------------------------------------------------------------"""
   
   def __init__(self, index=0, typ="binary", rang=(0, 200), bucket=1, var="flag", var_mod="self", standardized=False, vehicle="self"):
      self.index=index
      self.type=typ
      self.range=rang
      self.bucket=bucket
      self.var=var
      self.var_mod=var_mod
      self.standardized=standardized
      self.vehicle=vehicle
      
class Constants:
   def __init__(self):
      #Define number of terms in state and index of each term
      """---------------------------------------------------------------------
      NOTE: If changing state definition, BHV_Input will automatically adjust
      state definition accordingly
      ---------------------------------------------------------------------"""
      self.state={}
      self.state["out"]= State(index=0, typ="binary", var="tagged", var_mod="self")
      self.state["flag_dist"]= State(index=1, typ="distance", rang=(0, 200), var= "flag", var_mod="enemy")
      self.state["flag_theta"]= State(index=2, typ="angle", rang=(0, 360), var= "flag", var_mod="enemy")
      self.state["heading"]=State(index=3, typ="raw", var="heading", rang=(0, 360))
      self.state["color"]= State(index=4, typ="binary", var="team", var_mod="self")

      self.state["leftBound"] = State(index=5, typ="distance", var="leftBound", var_mod="self")
      self.state["rightBound"] = State(index=6, typ="distance", var="rightBound", var_mod="self")
      self.state["upperBound"] = State(index=7, typ="distance", var="upperBound", var_mod="self")
      self.state["lowerBound"] = State(index=8, typ="distance", var="lowerBound", var_mod="self")

      self.state["enemy_dist"]= State(index=9, typ="distance", var="player", rang=(0, 200), vehicle="evan")
      self.state["enemy_angle"]=State(index=10, typ="angle", var="player", rang=(0, 360), vehicle="evan")
      self.state["enemy_heading"]=State(index=11, typ="raw", var="heading", rang=(0, 360), vehicle="evan")

      #maybe add speed info
      self.num_states=len(self.state)
      
      #define learning parameters to be passed to learning function
      """---------------------------------------------------------------------
      self.num_layers -> number of layers in the neural network

      self.num_units -> number of units per layer in network

      self.num_traj -> number of times a simulation is run per iteration to
      make dataset
      
      self.iters -> number of iterations for training (can be arbitrarily high
      since model is saved on each iteration and training can be stopped any time)
      
      self.lr -> learning rate for the Adam optimizer used to train the neural net

      self.training_type -> whether trained with "stochastic" gradient descent or "batch" gradient descent

      self.eps_min -> minimum rate at which actions are picked at random when generating table
      
      self.eps_init -> the starting rate at which actions are picked at random when generating table

      self.eps_decay -> the rate at which the randomness of actions diminishes per iteration

      self.epochs -> how many epochs of training the network goes through to train
      each neural net

      self.batch_size -> the number of examples picked from memory when training with DQN

      self.batches_per_training -> how many times we pick out and train on batch of size self.batch_size per iteration

      self.alg_type -> selects which algorithm to use, can be "DQL" or "fitted"

      ----------------------------------------------------------------------"""
      
      self.num_layers= 2
      self.num_units = 10
      self.activation_function = "relu"
      self.num_traj = 1
      self.iters = 200
      self.lr = .005
      self.training_type = "batch"
      self.eps_min = .01
      self.eps_init = 1
      self.eps_decay = .98
      self.epochs = 2
      self.batch_size = 600
      self.batches_per_training = 3
      self.epoch_batch_size = 1
      self.alg_type = "fitted"

      
      #define constants/defaults to be used
      """-----------------------------------------------------------------------
      self.speeds -> possible speeds that actions can have
      
      self.relative -> switch to actions that add or subtract from heading rather
      than define an absolute heading to take (switch this boolean in BHV_Input.cpp
      as well)... in practice I have found that absolute headings work better

      self.rel_headings -> possible headings for relative actions (only relavent if
      relative is defined)

      self.theta_size_act -> the block size for how spaced out the possible thetas are 
      in the action space
      
      self.discount_factor -> the rate at which future rewards are discounted

      self.max_reward -> maximum positive reward for reaching the goal state

      self.neg_reward -> negative reward for going out of bounds
      
      self.reward_dropoff -> the rate at which reward diminish as you move away from 
      the goal
      
      self.max_reward_radius -> the radius around the goal that has max reward.

      self.smooth_reward -> which type of reward function we use

      self.save_iteration -> boolean will have the given model save itself to a new
      folder for every self.save_iter_num iterations

      self.save_iter_num -> number of iterations before saving to a new folder

      self.players -> lists other players that are in the simulation (for use by BHV_Input)

      self.mem_type -> whether the memory is a "set", a "deque", or "memory per action". A set makes an unbounded memory with no 
      repeating experiences, while a deque makes a memory of fixed length (self.mem_length) that may have multiple
      of the same experiences, putting weight on the experiences that are seen more often. Memory per Action keeps seperate deque 
      memories per action and samples are taken evenly from each memory pool.

      self.mem_length -> the length of deque memory

      self.mem_thresh -> the threshold at which we go from sampling one batch per iteration to 
      sampling self.batches_per_training batches per iteration

      self.end_at_tagged -> Flag that decides whether tagged states count as terminal states (i.e. 
      there are no transitions recorded that go from a tagged state to another state) 

      self.num_test_iters -> the number of times to run the simulation per model when testing

      self.num_eval_iters -> the number of times to run the simulation per model when evaluating
      -----------------------------------------------------------------------"""
      self.speeds = [2]
      self.relative = False
      self.rel_headings = [-30,0,30]
      self.theta_size_act = 60
      self.discount_factor = .999
      self.max_reward = 100
      self.neg_reward = -50
      self.reward_dropoff = .96
      self.max_reward_radius = 10
      self.smooth_reward = True
      self.save_iteration=True
      self.save_iter_num = 4
      self.players = "evan"
      self.mem_type = "memory per action"
      self.mem_length = 40000
      self.mem_thresh = 4000
      self.end_at_tagged = True
      self.num_test_iters = 1
      self.num_eval_iters = 100
      
      #define locations for storing/reading and scripts
      """-----------------------------------------------------------------------
      self.sim_cmd -> path to script that will run the simulation
      
      self.process_path -> path to folder to get data to be processed
      
      self.process_cmd -> path to script to process the raw data at self.process_path

      self.read_path -> path to processed data

      self.out_address -> path to where the table.csv file should be output so that
      it can be read by BHV_Input

      self.load_model_dir -> path to the folder where we should load a model from, 
      only important if we want to start training or testing from a model we have 
      already partially trained

      self.save_model_dir -> path to the foler where we should save the model to
      (model gets saved on every iteration)
      
      self.mem_address -> path to memory to load in

      self.eval_address -> path to the folder holding the models that need to be evaluated

      self.test_address -> path to the folder holding the models that need to be tested
      -----------------------------------------------------------------------"""
      user_path = os.getenv("HOME") + '/'
      learning_path = user_path + 'moos-ivp-pLearn/pLearn/learning_code/'
      simulation_path = user_path + 'moos-ivp-pLearn/pLearn/simulation_engine/'
      self.sim_cmd = learning_path+'train.sh'
      self.eval_sim_cmd = learning_path+'evaluator.sh'
      self.test_sim_cmd = learning_path+'tester.sh'
      self.process_path = learning_path+'results'
      self.process_cmd = learning_path+'log_converter.py'
      self.read_path = learning_path+'processed'
      self.out_address = simulation_path+'m200/table.csv'
      self.load_model_dir = learning_path+'examples/Simple_Opponent_BHV/topModel/'
      self.save_model_dir = learning_path+'models/new_model/'
      self.mem_address = learning_path+'models/new_model/'
      self.eval_address = learning_path+'examples/Simple_Opponent_BHV/topModel/'
      self.test_address = learning_path+'examples/Simple_Opponent_BHV/topModel/'

