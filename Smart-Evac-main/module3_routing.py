import pandas as pd
import networkx as nx
import osmnx as ox
import random

def calculate_evacuation_routes(place_name="Alappuzha, Kerala, India"):
    print("🗺️ Loading data and re-fetching road network graph...")
    try:
        shelters_df = pd.read_csv("shelters.csv")
        evacuees_df = pd.read_csv("evacuees_list.csv")
    except FileNotFoundError:
        print("❌ Error: Missing CSV files.")
        return
        
    G = ox.graph_from_place(place_name, network_type='drive')

    print("🌧️ Simulating flood damage to the road network...")
    edges_to_remove = []

    # Iterate through all roads and randomly flag ~5% of them as "Flooded"
    for u, v, key, data in G.edges(keys=True, data=True):
        if random.random() < 0.05: # 5% chance a road is blocked
            edges_to_remove.append((u, v, key))
            
    # Removing the flooded roads from the graph
    G.remove_edges_from(edges_to_remove)
    print(f"🚧 {len(edges_to_remove)} road segments are flooded and impassable!")
    # -----------------------------------------------
    
    # --- INITIALIZE DYNAMIC TRAFFIC WEIGHTS ---
    # Set the baseline travel weight to the physical length of the road
    for u, v, key, data in G.edges(keys=True, data=True):
        data['travel_weight'] = data.get('length', 1.0)
    # ---------------------------------------------------------

    # 2. Initialize Shelter Occupancy Tracker
    shelter_status = {}
    for _, row in shelters_df.iterrows():
        shelter_status[int(row['Shelter_Node_ID'])] = {
            'capacity': int(row['Max_Capacity']),
            'current_occupancy': 0
        }
        
    # Sort evacuees: Families with most elderly and children get priority routing!
    evacuees_df['Dependents_Total'] = evacuees_df['Num_Elderly'] + evacuees_df['Num_Children']
    evacuees_df = evacuees_df.sort_values(by=['Num_Elderly', 'Dependents_Total'], ascending=[False, False])
    
    final_routes = []
    unassigned = []

    print(f"🚗 Routing {len(evacuees_df)} evacuee households with DYNAMIC TRAFFIC SIMULATION...")

    # 3. The Routing Loop
    for index, evacuee in evacuees_df.iterrows():
        evac_node = int(evacuee['Node_ID'])
        family_size = int(evacuee['Family_Size']) 
        
        distances = []
        for shelter_node in shelter_status.keys():
            try:
                # Using the dynamic 'travel_weight' (which includes traffic) to find the fastest path
                dist = nx.shortest_path_length(G, source=evac_node, target=shelter_node, weight='travel_weight')
                distances.append((shelter_node, dist))
            except nx.NetworkXNoPath:
                continue 

        distances.sort(key=lambda x: x[1])
        assigned = False
        
        for shelter_node, dist in distances:
            available_space = shelter_status[shelter_node]['capacity'] - shelter_status[shelter_node]['current_occupancy']
            
            # Check if the whole family fits
            if available_space >= family_size:
                # Assign them!
                shelter_status[shelter_node]['current_occupancy'] += family_size
                
                # Fetch the exact sequence of intersections for this path
                path_nodes = nx.shortest_path(G, source=evac_node, target=shelter_node, weight='travel_weight')
                
                # --- 3: APPLY TRAFFIC CONGESTION PENALTY ---
                # Looping through the exact roads this family is taking and increase their traffic weight
                for i in range(len(path_nodes) - 1):
                    u = path_nodes[i]
                    v = path_nodes[i+1]
                    if G.has_edge(u, v, 0):
                        # Increase the weight by 5% per family member taking up space in the car/bus
                        G[u][v][0]['travel_weight'] *= (1.0 + (0.05 * family_size))
                # -------------------------------------------------------
                
                final_routes.append({
                    'Evacuee_Node': evac_node,
                    'Assigned_Shelter': shelter_node,
                    'Family_Size': family_size,
                    'Effective_Weight': round(dist, 2), 
                    'Path_Nodes': path_nodes
                })
                assigned = True
                break 
                
        if not assigned:
            unassigned.append((evac_node, family_size))

    # 4. Saving the Results
    routes_df = pd.DataFrame(final_routes)
    routes_df.to_csv("evacuation_routes.csv", index=False)
    
    print("\n✅ Routing Complete!")
    print(f"💾 Saved {len(routes_df)} successful household routes to 'evacuation_routes.csv'")
    
    if unassigned:
        unassigned_df = pd.DataFrame(unassigned, columns=['Node_ID', 'Family_Size'])
        unassigned_df.to_csv("airlift_targets.csv", index=False)
        total_unassigned = unassigned_df['Family_Size'].sum()
        print(f"⚠️ Warning: {len(unassigned)} households ({total_unassigned} people) are completely cut off!")
        print("💾 Saved stranded households to 'airlift_targets.csv'")
    else:
        pd.DataFrame(columns=['Node_ID', 'Family_Size']).to_csv("airlift_targets.csv", index=False)
    # -----------------------------------------------
    print("\n--- Final Shelter Occupancy (Individuals) ---")
    for s_id, status in shelter_status.items():
        print(f"Shelter {s_id}: {status['current_occupancy']} / {status['capacity']} full")

# ==========================================
# Execution / Testing the Module
# ==========================================
if __name__ == "__main__":
    calculate_evacuation_routes()