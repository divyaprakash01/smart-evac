import streamlit as st
import pandas as pd
import folium
import ast
import osmnx as ox
import plotly.express as px
from streamlit_folium import st_folium

# --- PAGE SETUP & CUSTOM CSS ---
st.set_page_config(page_title="NDRF Command Portal", layout="wide", page_icon="🚁")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    h1, h2, h3 { color: #00FF41 !important; font-family: 'Courier New', Courier, monospace; }
    .stMetric { background-color: #1E2127; padding: 15px; border-left: 5px solid #00FF41; border-radius: 5px; }
    .stSlider > div > div > div { background-color: #00FF41 !important; }
    </style>
""", unsafe_allow_html=True)

# --- LOAD DATA ---
@st.cache_data
def load_data():
    households_df = pd.read_csv("synthetic_households.csv")
    shelters_df = pd.read_csv("shelters.csv")
    evacuees_df = pd.read_csv("evacuees_list.csv")
    routes_df = pd.read_csv("evacuation_routes.csv")
    try:
        airlift_df = pd.read_csv("airlift_targets.csv")
    except FileNotFoundError:
        airlift_df = pd.DataFrame(columns=['Node_ID', 'Family_Size'])
    return households_df, shelters_df, evacuees_df, routes_df, airlift_df

@st.cache_resource
def load_graph():
    return ox.graph_from_place("Alappuzha, Kerala, India", network_type='drive')

households_df, shelters_df, evacuees_df, routes_df, airlift_df = load_data()
G = load_graph()
occupancy_data = routes_df.groupby('Assigned_Shelter')['Family_Size'].sum().to_dict()

# --- HEADER ---
st.title("🚁 NDRF TACTICAL EVACUATION COMMAND")
st.markdown("_Live Flood Routing & Asset Deployment System_")
st.divider()

# --- INTERACTIVE CONTROLS ---
st.sidebar.title("⚙️ Tactical Controls")
risk_threshold = st.sidebar.slider(
    "Evacuation Risk Threshold", 
    min_value=0.20, max_value=0.90, value=0.55, step=0.05,
    help="Lowering this will flag more households for evacuation."
)

dynamic_evacuees = households_df[households_df['Exact_Risk_Score'] >= risk_threshold]
evacuee_ids = set(dynamic_evacuees['Node_ID'])

stranded_ids = set(airlift_df['Node_ID']) if not airlift_df.empty else set()
routed_evacuees = dynamic_evacuees[~dynamic_evacuees['Node_ID'].isin(stranded_ids)]

route_options = ["Show All Routes"] + list(routes_df['Evacuee_Node'].unique())
selected_route = st.sidebar.selectbox("Inspect Specific Route:", route_options)

st.sidebar.divider()
st.sidebar.subheader("Active Shelters")
for _, row in shelters_df.iterrows():
    s_id = int(row['Shelter_Node_ID'])
    cap = int(row['Max_Capacity'])
    occ = occupancy_data.get(s_id, 0)
    status = "🔴 FULL" if occ >= cap else "🟢 OPEN"
    st.sidebar.text(f"Shelter {str(s_id)[-4:]}: {occ}/{cap} {status}")

# --- HUD METRICS ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Safe", len(households_df) - len(dynamic_evacuees))
col2.metric("Ground Evacuations", len(routed_evacuees))
col3.metric("Airlifts Required", len(airlift_df), delta="Critical", delta_color="inverse")
col4.metric("Shelters Online", len(shelters_df))

st.write("") 

# --- MAIN DASHBOARD SPLIT ---
map_col, stats_col = st.columns([2.5, 1])

with map_col:
    first_shelter = shelters_df.iloc[0]['Shelter_Node_ID']
    m = folium.Map(location=[G.nodes[first_shelter]['y'], G.nodes[first_shelter]['x']], zoom_start=14, tiles="CartoDB dark_matter")

    for _, row in households_df.iterrows():
        n_id = int(row['Node_ID'])
        if n_id not in evacuee_ids:
            folium.CircleMarker(location=[G.nodes[n_id]['y'], G.nodes[n_id]['x']], radius=2, color='#1f77b4', fill=True, fill_opacity=0.3).add_to(m)

    # Plot Routed Evacuees (Red)
    for _, row in routed_evacuees.iterrows():
        n_id = int(row['Node_ID'])
        f_size = int(row['Family_Size']) 
        risk = row.get('Exact_Risk_Score', 'N/A')
        
        # Format the binary data into readable text
        n_elderly = int(row.get('Num_Elderly', 0))
        n_children = int(row.get('Num_Children', 0))
        b_type = "Kutcha/Weak" if row.get('Building_Type') == 1 else "Pucca/Concrete"
        tooltip = f"""
        <b>Ground Evac ID:</b> {n_id}<br>
        <b>Family Size:</b> {f_size} members<br>
        <b>Elderly/Children:</b> {n_elderly} / {n_children}<br>
        <b>Risk Score:</b> {risk}<br>
        <b>Building Type:</b> {b_type}
        """
        folium.CircleMarker(location=[G.nodes[n_id]['y'], G.nodes[n_id]['x']], radius=5, color='#FF003C', fill=True, fill_opacity=0.9, tooltip=tooltip).add_to(m)

    # Plot Stranded Evacuees (Purple for Airlift)
    for _, row in airlift_df.iterrows():
        n_id = int(row['Node_ID'])
        f_size = int(row['Family_Size']) 
        original_stats = households_df[households_df['Node_ID'] == n_id].iloc[0]
        risk = original_stats['Exact_Risk_Score']
        n_elderly = int(original_stats.get('Num_Elderly', 0))
        n_children = int(original_stats.get('Num_Children', 0))
        b_type = "Kutcha/Weak" if original_stats['Building_Type'] == 1 else "Pucca/Concrete"
        
        tooltip = f"""
        <b>🚨 AIRLIFT REQUIRED</b><br>
        <b>ID:</b> {n_id}<br>
        <b>Family Size:</b> {f_size} members<br>
        <b>Elderly/Children:</b> {n_elderly} / {n_children}<br>
        <b>Risk Score:</b> {risk}<br>
        <b>Building Type:</b> {b_type}
        """

        folium.CircleMarker(location=[G.nodes[n_id]['y'], G.nodes[n_id]['x']], radius=8, color='#9D00FF', fill=True, fill_opacity=0.9, tooltip=tooltip).add_to(m)

    # Plot Shelters
    for _, row in shelters_df.iterrows():
        s_id = int(row['Shelter_Node_ID'])
        cap = int(row['Max_Capacity'])
        occ = occupancy_data.get(s_id, 0)
        color = 'darkred' if occ >= cap else 'green'
        folium.Marker(location=[G.nodes[s_id]['y'], G.nodes[s_id]['x']], icon=folium.Icon(color=color, icon='tower', prefix='fa'), tooltip=f"Shelter {s_id}: {occ}/{cap}").add_to(m)

    # Plot Routes 
    for _, row in routes_df.iterrows():
        evac_node = row['Evacuee_Node']

        if evac_node in evacuee_ids:
            # If "Show All Routes" is selected OR this specific node is selected in the dropdown
            if selected_route == "Show All Routes" or selected_route == evac_node:
                path_nodes = ast.literal_eval(row['Path_Nodes'])
                path_coords = [[G.nodes[n]['y'], G.nodes[n]['x']] for n in path_nodes]
                
                # If it's a specifically selected route, make it thicker and brighter!
                line_weight = 6 if selected_route == evac_node else 3
                line_color = '#00FFFF' if selected_route == evac_node else '#FFD700'
                
                folium.PolyLine(locations=path_coords, color=line_color, weight=line_weight, opacity=0.8, dash_array='7, 7').add_to(m)

    st_folium(m, width=1000, height=650, returned_objects=[])

with stats_col:
    st.subheader("📊 Live Shelter Capacity")

    chart_data = []
    for _, row in shelters_df.iterrows():
        s_id = str(row['Shelter_Node_ID'])[-4:] 
        cap = int(row['Max_Capacity'])
        occ = occupancy_data.get(int(row['Shelter_Node_ID']), 0)
        chart_data.append({"Shelter": f"ID-{s_id}", "Occupancy": occ, "Capacity": cap, "Available": cap - occ})
    
    df_chart = pd.DataFrame(chart_data)
    
    fig = px.bar(df_chart, x="Shelter", y=["Occupancy", "Available"], 
                 title="Current Fill Status",
                 color_discrete_map={"Occupancy": "#FF003C", "Available": "#00FF41"})
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white", legend_title_text="Status")
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()

    # --- QUEUE 1: STRANDED (AIRLIFT) ---
    st.subheader("🚁 Aerial Rescue Queue")
    if not airlift_df.empty:
        st.error("Road access cut off. Immediate aerial evac required:")
        for _, target in airlift_df.head(5).iterrows(): # Show top 5
            st.markdown(f"**ID:** {int(target['Node_ID'])} | **Family:** {int(target['Family_Size'])}")
    else:
        st.success("No households currently stranded.")

    st.divider()

    # --- QUEUE 2: HIGH RISK (GROUND) ---
    st.subheader("⚠️ Top Priority Ground Queue")
    st.warning("Highest risk scores. Dispatch ground units immediately:")
    
    # Sort ground evacuees by Risk Score
    top_targets = routed_evacuees.sort_values(by='Exact_Risk_Score', ascending=False).head(5)
    for _, target in top_targets.iterrows():
        st.markdown(f"**ID:** {int(target['Node_ID'])} | **Risk:** {target['Exact_Risk_Score']} | **Family:** {int(target['Family_Size'])}")