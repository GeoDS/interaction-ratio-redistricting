# This module takes the output csv assignments of cbgs to districts for a recom chain, and returns a csv of interaction ratio values for eahc map in the chain.
# MOST importantly, this is done SERIALLY, where the interaction ratio for each map is calculated by adjusting flows from the previous map. This is faster for a single machine.


    def move_flow_cell(cbg_dis_dict, old_cbg_dis_dict, inter_flows_dict,intra_flows_dict,item):
        origin_cbg, dest_dict = item
        for dest_cbg_flow_pair in dest_dict.items():
            dest_cbg, flow = dest_cbg_flow_pair
            if flow == 0:
                continue
            old_dest_dis_id = old_cbg_dis_dict[dest_cbg]
            new_dest_dis_id = cbg_dis_dict[dest_cbg]
            old_origin_dis_id = old_cbg_dis_dict[origin_cbg]
            new_origin_dis_id = cbg_dis_dict[origin_cbg]

            if (new_origin_dis_id != new_dest_dis_id) & (old_origin_dis_id == old_dest_dis_id): # Now not in same dis; now is inter
                # now goes here
                inter_flows_dict[new_origin_dis_id] += flow
                # used to go here
                intra_flows_dict[old_origin_dis_id] -= flow

            elif (new_origin_dis_id == new_dest_dis_id) & ( old_origin_dis_id!= old_dest_dis_id): # if now is intra
                # used to go to here
                inter_flows_dict[old_origin_dis_id] -= flow
                # now goes to here
                intra_flows_dict[new_origin_dis_id] += flow

            # intra moved to a new dis
            elif (new_origin_dis_id == new_dest_dis_id) & (old_origin_dis_id == old_dest_dis_id):
                # used to go to here
                intra_flows_dict[old_origin_dis_id] -= flow
                # now goes to here
                intra_flows_dict[new_origin_dis_id] += flow            

            # inter moved to a new dis - both origin and dest districts changed
            elif (new_origin_dis_id != new_dest_dis_id) & (old_origin_dis_id != old_dest_dis_id): # leave out new_origin_dis_id !=old_dest_dis_id...it will move the flow but it won't change the sum
                # used to go to here
                inter_flows_dict[old_origin_dis_id] -= flow
                # now goes to here
                inter_flows_dict[new_origin_dis_id] += flow
            else:
                print(f'This did NOT trigger any of the checks:')
                print(f'     Flow from cbg={origin_cbg} to cbg={dest_cbg} is {flow}')
        return inter_flows_dict, intra_flows_dict


    # ### Calculate modularity for each gdf
    def initialize_algo(cbg_flow_matrix,gdf):
        # Initialize intra flows
        intra_flows = {0:0,1:0,2:0,3:0,4:0,5:0,6:0,7:0}
        inter_flows = {0:0,1:0,2:0,3:0,4:0,5:0,6:0,7:0}
        # Calculate initial flow matrices
        intra_flows_dict = district_within_flows_return(gdf, cbg_flow_matrix)
        inter_flows_dict = district_between_flows_return(gdf, cbg_flow_matrix)
        summ = sum(intra_flows_dict.values())/sum(inter_flows_dict.values())
        return summ, inter_flows_dict, intra_flows_dict 

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

    def find_changed_cells(gdf_flows,cbg_dis_dict,old_cbg_dis_dict,cbg_flow_matrix):
        changed_cbgs = []
        for cbg in gdf_flows.cbg.tolist():
            if cbg_dis_dict[cbg] != old_cbg_dis_dict[cbg]:
                changed_cbgs.append(cbg)          
        changed_cells = {x:{} for x in range(len(cbg_flow_matrix))}
        for cbg in changed_cbgs:
            for y in range(len(cbg_flow_matrix)):
                changed_cells[cbg][y] = cbg_flow_matrix[cbg][y]
                changed_cells[y][cbg] = cbg_flow_matrix[y][cbg]
        return changed_cells, changed_cbgs

    ##########################################################
    print('Calculating flows')

    flow_sums = []
    flow_sums_true = []
    flow_dicts = []
    flow_dicts_true = []
    full_time = []
    cell_time = []
    inters_same = []
    intras_same = []

    inter_flows_dict_all = {}
    intra_flows_dict_all = {}
    inter_flows_dict_true_all = {}
    intra_flows_dict_true_all = {}
    # don't add this first one to list here - do so in the loop
    i = 0

    print('Sum of flow matrix= ',sum(map(sum,cbg_flow_matrix)))
    # print('cell count in flow matrix= ',len(cbg_flow_matrix)*len(cbg_flow_matrix))

    general_output_name = f'{args.todays_date}_{args.recom_steps}it_{args.compactness_multiplier}comp_{args.bias}bias_{args.seed}seed_{args.state}_{args.year}'
    save_dfs(gdfs, cbg_flow_matrix,args,general_output_name)

    summ, inter_flows_dict, intra_flows_dict = initialize_algo(cbg_flow_matrix,gdfs[0])
    # sum0 = sum(intra_flows_dict.values())+sum(inter_flows_dict.values())
    # print(f'First initial sum = {sum0}')
    first = True
    i=0
    for gdf_flows in gdfs:
        # print(f'\n##################### {i}th iteration##################################\n')
        # gdf_flows.plot('assignment')
        if i % 1000 == 0:
            print('Flow calc iteration = ',i)
        cbg_dis_dict = pd.Series(gdf_flows.assignment.values,index=gdf_flows.cbg).to_dict()
        if first:
            old_cbg_dis_dict = deepcopy(cbg_dis_dict)
        first = False

        ################ Run faster version, where individual, changed flows are adjusted
        cell_start_time = timeit.default_timer()
        changed_cells, changed_cbgs = find_changed_cells(gdf_flows,cbg_dis_dict,old_cbg_dis_dict,cbg_flow_matrix)
        for item in changed_cells.items():
                inter_flows_dict, intra_flows_dict = move_flow_cell(cbg_dis_dict, old_cbg_dis_dict, inter_flows_dict,intra_flows_dict,item)
        sum_calc = sum(inter_flows_dict.values())+sum(intra_flows_dict.values())
        # print(f'move_flow_cell for {i}th iteration: sum= {sum_calc}')
        # 0th iteration will append the dictionaries pertaining to the initial parition with the code below
        flow_sums.append(deepcopy(sum(intra_flows_dict.values())/sum(inter_flows_dict.values())))
    #     flow_dicts.append((deepcopy(intra_flows_dict), deepcopy(inter_flows_dict)))
    #     ### timer
        cell_end_time = timeit.default_timer()
        cell_timetaken = cell_end_time - cell_start_time
        cell_time.append(cell_timetaken)
        # print(f'cell_timetaken = {cell_timetaken}')

    #     ########## run full calc for time and accuracy comparison
    #     full_start_time = timeit.default_timer()
    #     # print('initialize_algo')
    #     summ_true, inter_flows_dict_true, intra_flows_dict_true = initialize_algo(cbg_flow_matrix,gdf_flows)
    #     sumi = sum(intra_flows_dict_true.values())+sum(inter_flows_dict_true.values())
    #     print(f'initialize_algo {i}th sum= {sumi}')

    #     flow_sums_true.append(deepcopy(sum(intra_flows_dict_true.values())/sum(inter_flows_dict_true.values())))
    #     flow_dicts_true.append((deepcopy(intra_flows_dict_true), deepcopy(inter_flows_dict_true)))
    #     full_end_time = timeit.default_timer()
    #     full_timetaken = full_end_time - full_start_time
    #     full_time.append(full_timetaken)
    #     print(f'full_timetaken = {full_timetaken}')

        # interbool = inter_flows_dict == inter_flows_dict_true
    #     all_same_inters = []
    #     all_same_intras = []
    #     for dis in range(8):
    #         calc_val_inter = inter_flows_dict[dis]
    #         true_val_inter = inter_flows_dict_true[dis]

    #         if abs(calc_val_inter-true_val_inter) < 5:
    #             all_same_inters.append(1)
    #         else:
    #             all_same_inters.append(0)            

    #         calc_val_intra = intra_flows_dict[dis]
    #         true_val_intra = intra_flows_dict_true[dis]
    #         if abs(calc_val_intra-true_val_intra) < 5:
    #             all_same_intras.append(1)
    #         else:
    #             all_same_intras.append(0)

    #     if sum(all_same_inters) == 8:
    #         inters_same.append(1)
    #     else:
    #         inters_same.append(0)
    #     if sum(all_same_intras) == 8:
    #         intras_same.append(1)
    #     else:
    #         intras_same.append(0)

        old_cbg_dis_dict = deepcopy(cbg_dis_dict)
        # inter_flows_dict_true_all[i] = deepcopy(inter_flows_dict_true)
        # intra_flows_dict_true_all[i] = deepcopy(intra_flows_dict_true)
        inter_flows_dict_all[i] = deepcopy(inter_flows_dict)
        intra_flows_dict_all[i] = deepcopy(intra_flows_dict)
        # print(f'inter_flows_dict_true =\n{inter_flows_dict_true}')
        # print(f'inter_flows_dict =\n{inter_flows_dict}')
        # print('\n')
        # print(f'intra_flows_dict_true =\n{intra_flows_dict_true}')
        # print(f'intra_flows_dict =\n{intra_flows_dict}')
        i+=1
