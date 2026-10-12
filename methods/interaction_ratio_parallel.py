#!/usr/bin/env python
# coding: utf-8

# This module takes the output csv assignments of cbgs to districts for a recom chain, and returns a csv of interaction ratio values for eahc map in the chain.
# MOST importantly, this is done IN PARALLEL, where is map is evaluated indepedently

import argparse
import multiprocessing
import signal
import time
import timeit
import sys, importlib, os
import pandas as pd
import numpy as np
from multiprocessing import Pool, cpu_count, Process, Queue, Pool, Manager, Value
# Could make these much faster by using np instead of df's 
    # - try this first before running parts fo the df in parallel
def district_within_flows_return(df, cbg_flow_matrix):
        alt_flows_dict = {0:0,1:0,2:0,3:0,4:0,5:0,6:0,7:0}
        for dis_id in range(8):
            cbg_in_dis = df[df['assignment']==dis_id]['cbg'].to_list() # filter down to just a particular district
            for cbg_origin in cbg_in_dis:
                for cbg_dest in cbg_in_dis:
                    alt_flows_dict[dis_id] += cbg_flow_matrix[cbg_origin][cbg_dest]
        return alt_flows_dict  

def district_between_flows_return(df, cbg_flow_matrix):
    alt_flows_dict = {0:0,1:0,2:0,3:0,4:0,5:0,6:0,7:0}
    for dis_id in range(8):
        cbg_out_dis = df[df['assignment']!=dis_id]['cbg'].to_list() # get all cbgs in df that are NOT in dis
        cbg_in_dis = df[df['assignment']==dis_id]['cbg'].to_list() # get all cbgs in df that ARE in dis
        for cbg_origin in cbg_in_dis: # everytime a cbg in the district is the origin 
            for cbg_dest in cbg_out_dis:
                alt_flows_dict[dis_id] += cbg_flow_matrix[cbg_origin][cbg_dest]
    return alt_flows_dict

### Calculate modularity for each gdf
# def initialize_algo(input_list):
    # cbg_flow_matrix,df,variable,q = input_list
def initialize_algo(input_list):
    cbg_flow_matrix,df,i = input_list
    # Initialize intra flows
    intra_flows = {0:0,1:0,2:0,3:0,4:0,5:0,6:0,7:0}
    inter_flows = {0:0,1:0,2:0,3:0,4:0,5:0,6:0,7:0}
    # Calculate initial flow matrices
    intra_flows_dict = district_within_flows_return(df, cbg_flow_matrix)
    inter_flows_dict = district_between_flows_return(df, cbg_flow_matrix)
    interaction_ratio = sum(intra_flows_dict.values())/sum(inter_flows_dict.values())
    # print(f'i in initialize_algo() = {i}')
    # print(f'interaction ratio for the {i}th iteration = {interaction_ratio}')
    # variable.value = interaction_ratio
    # q.put(interaction_ratio)
    return (interaction_ratio,i)


def calcFlows(var_list):
    cp, recomSteps, the_date, sd, bs, results_path_i, general_output_name = var_list
    ppEG_df = pd.read_csv(results_path_i+"/"+general_output_name+".csv")
    assignment_df = pd.read_csv(results_path_i+"/"+general_output_name+"_assignments.csv")
    interaction_ratios = []
    
    # process columns in parallel
    # this would be a good spot to drop some initial number of iterations from the chain (to not keep stuff similar to the seed)
    # from multiprocessing import Pool, cpu_count
    print(f'starting computations on {cpu_count()} cores')
    # Create manager
# specify pool size; otherwise, will use total number of vCPUs    
    # pool = Pool(10) 
    # https://towardsdatascience.com/pool-limited-queue-processing-in-python-2d02555b57dc
    imap_list = []
    for i in range(recomSteps):
        # create shared variable
        # variable = Value('f', 0.0)
        df = assignment_df.filter([f'assignment_{i}','cbg'], axis=1)
        df[['assignment','cbg']] = df
    #     Process(target=initialize_algo, args=(cbg_flow_matrix,df,variable,q))
        imap_list.append([cbg_flow_matrix,df,i])
    
    
    pool = Pool()
    # results = pool.imap(initialize_algo, imap_list)
    # https://superfastpython.com/multiprocessing-pool-map_async/
    # confirmed with the above link and printouts that map_async() and get() DO return results in the same order we send them in
    result = pool.map_async(initialize_algo, imap_list)
    pool.close()
    pool.join()
    interaction_ratios = result.get()
    print(type(interaction_ratios), interaction_ratios)
    # print("interaction_ratios = ",interaction_ratios)    
    interaction_ratios = [i[0] for i in interaction_ratios]
    ppEG_df['interaction_ratio'] = interaction_ratios
    # print(results_path_i+"/"general_output_name+"_interaction_ratios.csv")
    ppEG_df.to_csv(results_path_i+"/"+general_output_name+"_interaction_ratios.csv")
    



start = time.time()
print('------------------------ STARTING FLOWS CALCULATION SCRIPT------------------------------')
# Take in arguments from shell script
# parser = argparse.ArgumentParser()
# parser.add_argument('--flows_matrix_path',help='Full path for flows matrix location. .npy file type')
# args = parser.parse_args()

# Read in flow data 
flows_matrix_path = os.environ.get("FLOWS_MATRIX_PATH", "data/synthetic_flows.npy")
cbg_flow_matrix = np.load(flows_matrix_path)
# Copy loop from RunGerryChain.py file to get it to read through all of the necessary experiments

results_path_i = "./output"

the_date = 221129
biases = [-99,1]
seeds = [2018,1776,1993]
recomSteps = 1000
comp_values = [1,3,5]
# var_list=[comp_values[0], recomSteps, the_date, seeds[0], biases[0], results_path_i]
# runChain(var_list)

for bs in biases:
    for sd in seeds:
        for cp in comp_values:
            general_output_name = f'{the_date}_{recomSteps}it_{cp}comp_{bs}bias_{sd}seed_wi_2020'           
            var_list=[cp, recomSteps, the_date, sd, bs, results_path_i,general_output_name]
            calcFlows(var_list)
            # prc1 = Process(target=runChain, args=(var_list,))
            # prc1.start()
            
end = time.time()
end-start
timetaken = end - start
# print(f"Total time to run script (recomSteps = {recomSteps}): "+str(timetaken))
print("Total seconds to run script: ",timetaken)
hours = timetaken/60/60
mins = timetaken/60
num_experiments = len(biases)*len(seeds)*len(comp_values)
print(f"Total mins to run script for {num_experiments} experiments: ",mins)
print("Average mins to calc flows for one experiment: ",mins/num_experiments)
print("End of Parallel flows file")