import osmnx as ox
import networkx as nx
import pandas as pd
import numpy as np
import requests
import random
from sklearn.cluster import KMeans

def get_real_elevations(G, node_ids):
    """
    Hits the Open-Elevation API to get real-world topographical data 
    for the exact street coordinates of our households.
    """
    print("⛰️ Fetching real topographical data from Open-Elevation API...")
    elevations = {}
    locations = [{"latitude": G.nodes[n]['y'], "longitude": G.nodes[n]['x']} for n in node_ids]
    
    url = "https://api.open-elevation.com/api/v1/lookup"
    payload = {"locations": locations}
    
    try:
        # We use a 15-second timeout. Free APIs can be slow.
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            results = response.json()['results']
            for i, res in enumerate(results):
                elevations[node_ids[i]] = res['elevation']
            print("✅ Successfully fetched real-world elevations!")
            return elevations
        else:
            print(f"⚠️ API Error {response.status_code}. Falling back to synthetic elevations.")
    except Exception as e:
        print(f"⚠️ API Timeout or Connection Error. Falling back to synthetic elevations.")
        
    # Fallback Mechanism: If the API is down, generate random realistic elevations
    for n in node_ids:
        elevations[n] = random.uniform(0.0, 50.0)
    return elevations

def setup_geospatial_data(place_name="Alappuzha, Kerala, India", num_shelters=5, num_households=200):
    print(f"🌍 Fetching drivable road network for: {place_name}...")
    G = ox.graph_from_place(place_name, network_type='drive')
    all_nodes = list(G.nodes)
    print(f"✅ Graph downloaded successfully. Total nodes found: {len(all_nodes)}")
    
    print("🎯 Optimizing shelter locations using K-Means Spatial Clustering...")
    
    # Extract the exact X (Longitude) and Y (Latitude) for every node in the graph
    node_data = [{'id': n, 'x': data['x'], 'y': data['y']} for n, data in G.nodes(data=True)]
    df_nodes = pd.DataFrame(node_data)
    
    # Run the K-Means algorithm to find 5 optimal geographic centers
    kmeans = KMeans(n_clusters=num_shelters, random_state=42, n_init=10)
    kmeans.fit(df_nodes[['x', 'y']])
    
    shelter_nodes = []
    for centroid in kmeans.cluster_centers_:
        # GIS TRICK: Snap the mathematical centroid to the nearest actual road intersection
        closest_real_node = ox.distance.nearest_nodes(G, X=centroid[0], Y=centroid[1])
        shelter_nodes.append(closest_real_node)
        
    # Ensuring all selected shelters are unique (in case clusters are extremely close)
    shelter_nodes = list(set(shelter_nodes))
    shelters_data = []
    for node in shelter_nodes:
        shelters_data.append({
            'Shelter_Node_ID': node,
            'Max_Capacity': random.randint(55, 110) 
        })
    shelters_df = pd.DataFrame(shelters_data)
    print("✅ Shelters perfectly distributed across the region!")
    
    # Defining Households & Fetching Real Elevations
    available_household_nodes = list(set(all_nodes) - set(shelter_nodes))
    household_nodes = random.sample(available_household_nodes, num_households)

    real_elevations = get_real_elevations(G, household_nodes)
    
    # Generating Advanced Synthetic Features
    households_data = []
    for node in household_nodes:
        dist_to_hazard = random.uniform(0.0, 1000.0)
        elevation = real_elevations[node]
        building_type = random.choice([0, 1])
        num_adults = max(1, np.random.poisson(2)) # At least 1 adult
        num_elderly = np.random.poisson(1)      # Averages 1 elderly
        num_children = np.random.poisson(1.0)     # Averages 1 child
        family_size = num_adults + num_elderly + num_children

        dependents_ratio = (num_elderly + num_children) / family_size
        dependents_penalty = 0.2 * dependents_ratio
        
        
        # --- NEW: EXPONENTIAL CONTINUOUS RISK LOGIC ---
        # Distance: e^(-0.005 * dist) -> 0m = 1.0 risk, drops quickly after 200m
        # Elevation: e^(-0.15 * elev) -> 0m = 1.0 risk, drops quickly after 10m
        dist_factor = np.exp(-0.005 * dist_to_hazard)
        elev_factor = np.exp(-0.15 * elevation)

        building_penalty = 0.3 if building_type == 1 else 0.0
        
        # Calculate Final Weighted Risk Score
        total_risk_score = (dist_factor * 0.4) + (elev_factor * 0.4) + building_penalty + dependents_penalty
        
        # Threshold for Evacuation (If total risk > 0.4, they need evacuation)
        risk_label = 1 if total_risk_score >= 0.4 else 0
        # ----------------------------------------------
        
        households_data.append({
            'Node_ID': node,
            'Distance_to_Hazard': round(dist_to_hazard, 2),
            'Elevation': round(elevation, 2),
            'Building_Type': building_type,
            'Num_Elderly': num_elderly,
            'Num_Children': num_children,
            'Family_Size': family_size,
            'Risk_Label': risk_label,
            'Exact_Risk_Score': round(total_risk_score, 3) 
        })
        
    households_df = pd.DataFrame(households_data)
    print(f"✅ {num_households} Synthetic Households generated.")
    return G, shelters_df, households_df

if __name__ == "__main__":
    G, df_shelters, df_households = setup_geospatial_data()
    df_households.to_csv("synthetic_households.csv", index=False)
    df_shelters.to_csv("shelters.csv", index=False)
    print("💾 Files saved successfully!")
    
    print("\n--- Sample of Advanced Generated Data ---")
    print(df_households[['Distance_to_Hazard', 'Elevation', 'Family_Size', 'Exact_Risk_Score', 'Risk_Label']].head(10).to_string(index=False))