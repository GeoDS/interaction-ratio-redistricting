#!/usr/bin/env python
# coding: utf-8
import argparse
import multiprocessing
from multiprocessing import Process
import time
import timeit
import sys, importlib, os
from multiprocessing import Pool, cpu_count, Process, Queue, Pool, Manager, Value
from copy import deepcopy

def loadData(args, np, gpd, Graph):
    # ### Merge voting data and shapefile
    cbg_flow_matrix = np.load(args.flows_matrix_path)
    merged = gpd.read_file(args.geojson_file_path)
    # gdf = deepcopy(merged)
    # dic = args.matrix_index_geoid_dict
    print('Loaded data. Producing graph...')
    merged.loc[3424,'geometry'] = deepcopy(merged.loc[3424,'geometry'].buffer(0)) # fix broken geometry
    merged = merged.to_crs('EPSG:3071')
    graph = Graph.from_geodataframe(merged, adjacency='queen')
    
    return cbg_flow_matrix, merged,graph

def find_node_by_geoid(geoid, graph):
         for node in graph:
            if graph.nodes[node]["geoid"] == geoid:
                return node
            
def fixIslands(merged,graph,connected_components):
    # https://gerrychain.readthedocs.io/en/latest/user/islands.html?highlight=islands#figuring-out-what-is-going-on
    components = list(connected_components(graph))
    [len(c) for c in components]
    biggest_component_size = max(len(c) for c in components)
    problem_components = [c for c in components if len(c) != biggest_component_size]
    print(biggest_component_size), print(problem_components)
    problem_nodes = [node for component in problem_components for node in component]
    problem_geoids = [graph.nodes[node]["geoid"] for node in problem_nodes]
    is_a_problem = merged["geoid"].isin(problem_geoids)
    purple_geoid = 550291001002
    yellow_geoid = problem_geoids[0]
    purple_node = find_node_by_geoid(purple_geoid, graph)
    yellow_node = find_node_by_geoid(yellow_geoid, graph)
    graph.add_edge(purple_node, yellow_node)

    return graph

def chooseElections(Election):
    print('Setting updaters and demographic cols...')
    elections = [
        Election("HOUSE18", {"Democratic": "USHDEM18", "Republican": "USHREP18"}),
        # Election("GOV18", {"Democratic": "GOVDEM18", "Republican": "GOVREP18"}),
    #     Election("SEN10", {"Democratic": "SEN10D", "Republican": "SEN10R"}),
    #     Election("SEN12", {"Democratic": "USS12D", "Republican": "USS12R"}),
    #     Election("SEN16", {"Democratic": "T16SEND", "Republican": "T16SENR"}),
    #     Election("PRES12", {"Democratic": "PRES12D", "Republican": "PRES12R"}),
    #     Election("PRES16", {"Democratic": "T16PRESD", "Republican": "T16PRESR"})
    #     USHDEM12
    ]
    election_updaters = {election.name: election for election in elections}
    return election_updaters

def setUpdaters(updaters,demo_cols,election_updaters):
    # Population updater, for computing how close to equality the district
    # populations are. "TOTPOP" is the population column from our shapefile.
    # my_updaters = {"population": updaters.Tally("POPULATION", alias="population")}
    my_updaters = {"population": updaters.Tally("Population",alias='population')}
    # Election updaters, for computing election results using the vote totals
    # from our shapefile.
    my_updaters.update(election_updaters)
    
    for col in demo_cols:
        if col.startswith('Pop'):
            continue
        else:
            my_updaters.update({col:updaters.Tally(col)})
    
    return my_updaters

def makeGeoidNodeDicts(graph):
    geoid_node_dict = {}
    node_geoid_dict = {}
    for node in graph:
        geoid_node_dict[graph.nodes[node]["geoid"]] = node
        node_geoid_dict[node] = graph.nodes[node]["geoid"]
        
    return geoid_node_dict, node_geoid_dict

def returnMatrixIndexDict(dic, json):
    with open(dic,'r') as fp:
        geoid_dict = json.load(fp)
    geoid_dict = {int(v):int(k) for k,v in geoid_dict.items()}    
    geoid_dict_rev = {v:k for k,v in geoid_dict.items()}
    
    return geoid_dict,geoid_dict_rev

def setGraphWeights(graph, cbg_flow_matrix,node_geoid_dict,geoid_dict_rev,np):  #https://networkx.org/documentation/stable/_modules/networkx/algorithms/tree/mst.html#maximum_spanning_tree
    #         - but, might have already been done elsewhere?

    print('Setting edge weights as sum of DO+OD flows between the two cbgs of interest (flows within cbg ignored)')
    edge_dict = {}
    zero_count = 0
    for edge in graph.edges:
        o_node,d_node = edge
        #get geoid from node attributes, created in dict above
        o_geoid = node_geoid_dict[o_node]
        d_geoid = node_geoid_dict[d_node]
        # get row and col pos for flows matrix from saved dict (reversed) geoid_dict_rev
        o_index = geoid_dict_rev[o_geoid]
        d_index = geoid_dict_rev[d_geoid]
        # we want birdectional flows as edge weight
        od_flows = cbg_flow_matrix[o_index][d_index]
        do_flows = cbg_flow_matrix[d_index][o_index]
        flow_sum = od_flows+do_flows
        edge_dict[edge] = flow_sum
        if flow_sum <1 or flow_sum == None:
    #         print(flow_sum,edge)
            # set to none zero value for later math operations
            edge_dict[edge] = np.float64(1)
    #         print(edge_dict[edge])

    # set as actual edge weight
    for edge in graph.edges:
        graph.edges[edge]["flow_weight"] = edge_dict[edge] # don't use "weight" keyword

    # ### In gerrychain module, use the normalized weight of neighbors in the current partition (graph)
    #     - then let maximum/minimum spanning tree work as normal
    #     - https://gerrychain.readthedocs.io/en/latest/_modules/gerrychain/tree.html
    return graph


def chooseDemoCols():
    demo_cols = ['population','18+_Pop', 'PISLAND18', 'WHITE18', 'BLACK18', 'HISPANIC18', 'ASIAN18', 'AMINDIAN18', 'PISLAND',
                 'White', 'Black', 'HISPANIC', 'Asian', 'AmIndian']
    return demo_cols

def printTimes(start_chain,args, time):
    end_chain = time.time()
    timechain_taken = (end_chain-start_chain)/60
    print(f'Finished running chain! Took {timechain_taken} mins')
    min_per_iteration = timechain_taken/int(args.recom_steps)
    print(f'Mins per iteration = {min_per_iteration}')
    
def makeSaveFig(plt, data,args):
    fig, ax = plt.subplots(figsize=(8, 6))
    # Draw 50% line
    ax.axhline(0.5, color="#cccccc")
    # Draw boxplot
    data.boxplot(ax=ax, positions=range(len(data.columns)))
    # Draw initial plan's Democratic vote %s (.iloc[0] gives the first row)
    plt.plot(data.iloc[0], "ro")
    # Annotate
    ax.set_title("Comparing the 2020 plan to an ensemble")
    ax.set_ylabel(f"Democratic vote % {args.election}")
    ax.set_xlabel("Sorted districts")
    ax.set_ylim(0, 1)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1])
    plt.savefig(f'{args.results_path}/{args.todays_date}_{args.recom_steps}it_{args.compactness_multiplier}comp_{args.bias}bias_{args.seed}seed_{args.state}_{args.year}_{args.election}.jpg') 
    plt.show()
    
    
def save_dfs(gdfs, cbg_flow_matrix,args,general_output_name):
    print('Saving dfs...')
    i=0
    for i in range(len(gdfs)):
        if i % 1000 == 0:
            print(f'{i} dfs saved')
        if i == 0:
            df = gdfs[i][['assignment','cbg','geoid']]
            df = df.rename(columns={'assignment':f'assignment_{i}'})
        else:
            df_dic = gdfs[i][['assignment','cbg']]
            dic = dict(zip(df_dic.cbg, df_dic.assignment))
            df[f'assignment_{i}'] = df['cbg'].map(dic)
        df = df.copy()
    df.to_csv(f'{args.results_path}/{general_output_name}_assignments.csv')
    
def calcMetrics(chain, metrics,deepcopy, np):
    # ### Compute Efficiency Gap
    # 1. https://gerrychain.readthedocs.io/en/latest/api.html
    # 2. gerrychain.metrics.efficiency_gap
    # 3. gerrychain.metrics.polsby_popper
    # 4. http://www.math.wsu.edu/faculty/ddeford/GerryChain_Guide.pdf
    # 5. https://github.com/drdeford/VA_Viz/blob/master/VA_Examples.py
    # https://gerrychain.readthedocs.io/en/latest/_modules/gerrychain/partition/partition.html#Partition.plot
    # https://gerrychain.readthedocs.io/en/latest/_modules/gerrychain/updaters/election.html
    # geometries_s = pd.Series(geometries)

    print('Calculating demographic totals, flows, etc, for each partition...')
    # D_wins = []
    # D_votes = []
    # D_percents = []
    # R_wins = []
    # R_votes = []
    # R_percents = []

    EGs = []
    pp = []
    pops = []
    gdfs = []
    # geos = []

    # _18_Pop = []
    # PISLAND18 = []
    # WHITE18 = []
    # BLACK18 = []
    # HISPANIC18 = []
    # ASIAN18 = []
    # AMINDIAN18 = []

    # PISLAND = []
    # White = []
    # Black = []
    # HISPANIC = []
    # Asian = []
    # AmIndian =[]

    # it appears that the first partition in chain IS the initial partition
    for current_partition in chain:
        # votes
    #     D_wins.append(current_partition["HOUSE18"].wins("Democratic"))
    #     D_votes.append(current_partition["HOUSE18"].votes("Democratic"))
    #     D_percents.append(current_partition["HOUSE18"].percents("Democratic"))

    #     R_wins.append(current_partition["HOUSE18"].wins("Republican"))
    #     R_votes.append(current_partition["HOUSE18"].votes("Republican"))
    #     R_percents.append(current_partition["HOUSE18"].percents("Republican"))

        # metrics
        EGs.append(metrics.efficiency_gap(current_partition["HOUSE18"]))
        pp.append(metrics.polsby_popper(current_partition))
        pops.append(current_partition["population"])
        gdf = current_partition.export_to_gdf()
        gdfs.append(gdf)

        # demographic
    #     _18_Pop.append(current_partition["18+_Pop"])
    #     PISLAND18.append(current_partition["PISLAND18"])
    #     WHITE18.append(current_partition["WHITE18"])
    #     BLACK18.append(current_partition["BLACK18"])
    #     HISPANIC18.append(current_partition["HISPANIC18"])
    #     ASIAN18.append(current_partition["ASIAN18"])
    #     AMINDIAN18.append(current_partition["AMINDIAN18"])

    #     PISLAND.append(current_partition["PISLAND"])
    #     White.append(current_partition["White"])
    #     Black.append(current_partition["Black"])
    #     HISPANIC.append(current_partition["HISPANIC"])
    #     Asian.append(current_partition["Asian"])
    #     AmIndian.append(current_partition["AmIndian"])

    # political_names = ['D_votes', 'D_percents', 'R_votes', 'R_percents']    
    # political_list = [D_votes, D_percents, R_votes, R_percents]
    # metric_names = ['EGs','pp']
    # metric_list = [EGs,pp]
    # demo_list = [pops,_18_Pop,PISLAND18,WHITE18,BLACK18,HISPANIC18,ASIAN18,AMINDIAN18,PISLAND,White,Black,HISPANIC,Asian,AmIndian]
    print('Done with calculations!')
    pp_dc = deepcopy(pp)
    ## take the average for each map
    pp_list = []
    for dic in pp_dc:
        ave = np.mean(list(dic.values()))
        pp_list.append(ave)
        
    return gdfs, pp_list, EGs
    
    
    
   ############################################################################################################################################################################################################################################################## 
    
def runChain(var_list):
    start = time.time()
    print('------------------------ STARTING NEW SCRIPT------------------------------')
    # https://gerrychain.readthedocs.io/en/latest/topics/reproducibility.html
    os.environ["PYTHONHASHSEED"] = "0"
    # Take in arguments from shell script
    parser = argparse.ArgumentParser()
    parser.add_argument('--py_file',dest='py_file',help='Name of python script for running recomb')
    # parser.add_argument('--flows_matrix_path',help='Full path for flows matrix location. .npy file type')
    parser.add_argument('--geojson_file_path',help='Full path for geojson location. .json file type')
    parser.add_argument('--matrix_index_geoid_dict',help='Full path for geojson location. .json file type')
    parser.add_argument('--recomb_type',help='Specify recom of reversible_recom')
    parser.add_argument('--election',help="e.g. 'HOUSE18'; str type")
    parser.add_argument('--state',help="e.g. 'wi'; str type")
    parser.add_argument('--year',help="e.g. '2018'; str type")

    args = parser.parse_args()
    compactness, recom_steps, todays_date, seed, bias, results_path = var_list
    # overwrite
    args.flows_matrix_path = os.environ.get("FLOWS_MATRIX_PATH", "data/synthetic_flows.npy")
    args.seed = seed
    args.compactness_multiplier = compactness
    args.bias = bias
    args.recom_steps = recom_steps
    args.todays_date = todays_date
    args.results_path = results_path
    dic = args.matrix_index_geoid_dict
    
    print(f'args.seed = {seed}, args.bias = {bias}, args.recom_steps = {recom_steps}, args.todays_date = {todays_date}, args.compactness_multiplier = {compactness}')
    print("ID of process running this particular runChain worker: {}".format(os.getpid()))
    # set seed for gerrychain before importing other packages 
    from gerrychain.random import random
    random.seed(args.seed)
    
    # import other function AFTER setting seed: https://gerrychain.readthedocs.io/en/latest/topics/reproducibility.html
    # https://gerrychain.readthedocs.io/en/latest/user/recom.html#imports
    # https://github.com/mggg-states/WI-shapefiles/blob/master/README.md
    from gerrychain import (GeographicPartition, Partition, Graph, MarkovChain,
                            proposals, updaters, constraints, accept, Election)
    from gerrychain.proposals import recom, reversible_recom
    import gerrychain.metrics as metrics
    import gerrychain
    from functools import partial    
    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np
    import json
    import plotly.express as px
    import plotly.io as pio
    from copy import deepcopy
    import geopandas as gpd
    from networkx import is_connected, connected_components
    import numpy as np
    import networkx as nx
    
    GERRYCHAIN_RANDOM_SEED = os.getenv("GERRYCHAIN_RANDOM_SEED")
    # GERRYCHAIN_RANDOM_SEED =os.environ["GERRYCHAIN_RANDOM_SEED"]
    print(f'Seed value set in ...os.environ["GERRYCHAIN_RANDOM_SEED"] == {GERRYCHAIN_RANDOM_SEED}')
    
    # set up graph and helper data structures
    cbg_flow_matrix, merged,graph = loadData(args, np, gpd, Graph)
    graph = fixIslands(merged,graph,connected_components)

    election_updaters = chooseElections(Election)
    demo_cols = chooseDemoCols() # set in func def
    my_updaters = setUpdaters(updaters,demo_cols,election_updaters)
    geoid_node_dict, node_geoid_dict = makeGeoidNodeDicts(graph)
    geoid_dict,geoid_dict_rev = returnMatrixIndexDict(dic, json)
    
    graph = setGraphWeights(graph, cbg_flow_matrix,node_geoid_dict,geoid_dict_rev,np)
    initial_partition = GeographicPartition(graph, assignment="dis_id", updaters=my_updaters)

    # The ReCom proposal needs to know the ideal population for the districts so that
    # we can improve speed by bailing early on unbalanced partitions.
    ideal_population = sum(initial_partition["population"].values()) / len(initial_partition)
    # We use functools.partial to bind the extra parameters (pop_col, pop_target, epsilon, node_repeats)
    # of the recom proposal.
    # method = 'recursive_tree_part'
    # method = 'bipartition_tree_random'
    # method = 'bipartition_tree'
    # methodd = 'uniform_spanning_tree'
    #     _bipartition_tree_random_all, uniform_spanning_tree,
    #     find_balanced_edge_cuts_memoization
    if args.recomb_type == 'recom':
        proposal = partial(recom,pop_col="population", pop_target=ideal_population,epsilon=0.02,node_repeats=2,bias=args.bias)
        compactness_bound = constraints.UpperBound(lambda p: len(p["cut_edges"]),
                                        int(args.compactness_multiplier)*len(initial_partition["cut_edges"]))

    pop_constraint = constraints.within_percent_of_ideal_population(initial_partition, percent=0.01)

    chain = MarkovChain(proposal=proposal,constraints=[pop_constraint,compactness_bound],
                  accept=accept.always_accept,initial_state=initial_partition, total_steps=int(args.recom_steps)
    )

    print('Running chain...')
    start_chain = time.time()

    data = pd.DataFrame(
        sorted(partition[args.election].percents("Democratic"))
        for partition in chain
    )

    printTimes(start_chain,args,time)
    # makeSaveFig(plt, data,args)

    gdfs, pp_list, EGs = calcMetrics(chain, metrics, deepcopy, np) 
    general_output_name = f'{args.todays_date}_{args.recom_steps}it_{args.compactness_multiplier}comp_{args.bias}bias_{args.seed}seed_{args.state}_{args.year}'

    save_dfs(gdfs, cbg_flow_matrix,args,general_output_name)
    dic = {'compactness': pp_list,'Eff_gap': EGs}  
    df = pd.DataFrame(dic) 
    df.to_csv(f'{args.results_path}/{general_output_name}.csv') 

    print(f'csv path = {args.results_path}.....csv')

    end = time.time()
    timetaken = end - start
    print(f'args.seed = {seed}, args.bias = {bias}, args.recom_steps = {recom_steps}, args.todays_date = {todays_date}, args.compactness_multiplier = {compactness}')
    
    GERRYCHAIN_RANDOM_SEED = os.getenv("GERRYCHAIN_RANDOM_SEED")
    # GERRYCHAIN_RANDOM_SEED =os.environ["GERRYCHAIN_RANDOM_SEED"]
    print(f'Seed value set in ...os.environ["GERRYCHAIN_RANDOM_SEED"] == {GERRYCHAIN_RANDOM_SEED}')    
    print("ID of process running this particular runChain worker: {}".format(os.getpid()))
    
    # GERRYCHAIN_RANDOM_SEED = os.environ["GERRYCHAIN_RANDOM_SEED"]
    # print(f'Seed value set in ...os.environ["GERRYCHAIN_RANDOM_SEED"] == {GERRYCHAIN_RANDOM_SEED}')
    
    # print(f'Seed value set in ...Modularity.py == {random.seed}')
    # if seeds is truly different, than the random number generated will be different for each (which is good)
    print(f'Seed value set in ...Modularity.py == {random.randint(1,1000)}')
    print("Total seconds to run script: ",timetaken)
    hours = timetaken/60/60
    print("Total hours to run script: ",hours)
    hours_per_step = hours/args.recom_steps
    hours_10k = hours_per_step*10000
    print("Total hours to run script for 10,000 steps: ",hours_10k)
    
    
##### Run the actual functions in parallel
# vars = [compactness, recom_steps, todays_date, seed, bias]
# https://stackoverflow.com/questions/25391025/what-exactly-is-python-multiprocessing-modules-join-method-doing

# https://stackoverflow.com/questions/24642811/set-env-var-in-python-multiprocessing-process
    # - does where the seed is set impact the other processes, using multiprocessing module?
        # - appears that is does NOT impact environment to environment
        
results_path_i = "./output"
os.makedirs(results_path_i, exist_ok=True)

the_date = 221129
biases = [-99,1]
seeds = [2018,1776,1993]
recomSteps = 1000
comp_values = [1,3,5]
# var_list=[comp_values[0], recomSteps, the_date, seeds[0], biases[0], results_path_i]
# runChain(var_list)
var_lists = []
for bs in biases:
    for sd in seeds:
        for cp in comp_values:
            var_lists.append([cp, recomSteps, the_date, sd, bs, results_path_i])
#             print(var_list)
#             prc1 = Process(target=runChain, args=(var_list,))
#             prc1.start()
            
pool = Pool()
# results = pool.imap(initialize_algo, imap_list)
# https://superfastpython.com/multiprocessing-pool-map_async/
# confirmed with the above link and printouts that map_async() and get() DO return results in the same order we send them in
result = pool.map_async(runChain, var_lists)
pool.close()
pool.join()

# results = result.get()
# print(type(results), results)

print('Finished all experiments in this file!')
            


