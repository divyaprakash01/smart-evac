# Smart-Evac: AI-Driven Disaster Routing

Smart-Evac is a data science and geospatial simulation project that models household evacuation during a flood scenario. The system combines synthetic demographic data, machine learning-based risk classification, spatial clustering, road-network analysis, and capacity-aware routing to identify and route households to suitable shelters.

## Overview

The pipeline is organized into four main stages:

1. **Geospatial setup and synthetic data generation**
   - Builds a drivable road network using OpenStreetMap/OSMnx.
   - Generates synthetic household and demographic data to avoid using private household-level information.
   - Uses geographic and demographic attributes to calculate household risk.
   - Uses K-Means clustering to determine candidate shelter locations.

2. **Risk prediction**
   - Trains a Random Forest classifier on household features.
   - Uses a train/test split to evaluate the model.
   - Predicts which households require evacuation.

3. **Evacuation routing**
   - Represents the road system as a graph using NetworkX/OSMnx.
   - Simulates flooded road segments by removing graph edges.
   - Routes households to shelters while considering shelter capacity and keeping families together.
   - Prioritizes households with more dependents.
   - Applies increasing travel weights to simulate congestion as evacuation progresses.
   - Records households that cannot be assigned a reachable shelter for possible airlift support.

4. **Visualization**
   - Provides an interactive dashboard for inspecting evacuation status, shelter occupancy, risk levels, routes, and stranded households.

## Key Features

- Synthetic household and demographic data generation
- Random Forest-based flood-risk classification
- K-Means spatial clustering for shelter placement
- OpenStreetMap road-network integration with OSMnx
- Graph-based shortest-path routing with NetworkX
- Flooded-road / network-failure simulation
- Shelter capacity constraints
- Family-preserving evacuation assignments
- Dependent-aware routing priority
- Dynamic congestion-aware route weighting
- Identification of unreachable households
- Interactive evacuation dashboard

## Tech Stack

**Languages:** Python

**Machine Learning:** Scikit-learn, Random Forest, K-Means

**Data & Numerical Computing:** Pandas, NumPy

**Geospatial & Graph Processing:** OSMnx, NetworkX, GeoPandas, Folium

**Visualization / Dashboard:** Streamlit, Plotly, Folium

## Project Structure

```text
smart-evac/
├── module1_setup.py
├── module2_ml.py
├── module3_routing.py
├── module4_dashboard.py
├── synthetic_households.csv
├── shelters.csv
├── evacuees_list.csv
├── evacuation_routes.csv
├── airlift_targets.csv
├── smart_evac_map.html
└── requirements.txt
```

## How the Pipeline Works

```text
OpenStreetMap Road Network
            │
            ▼
Geospatial + Synthetic Household Data
            │
            ▼
       Risk Prediction
     (Random Forest)
            │
            ▼
   High-Risk Households
            │
            ▼
   Shelter Optimization
      (K-Means)
            │
            ▼
 Flooded Road Simulation
            │
            ▼
 Capacity- and Family-Aware
     Graph Routing
            │
       ┌────┴────┐
       ▼         ▼
 Ground Routes  Airlift Targets
            │
            ▼
     Interactive Dashboard
```

## Why Synthetic Data?

Household-level demographic information can contain sensitive personal information. This project therefore uses synthetic household data while mapping those simulated households onto a real road-network structure. This allows the routing and evacuation algorithms to be tested without relying on private individual-level data.

## Running the Project

Install the dependencies:

```bash
pip install -r requirements.txt
```

Run the modules in order:

```bash
python module1_setup.py
python module2_ml.py
python module3_routing.py
streamlit run module4_dashboard.py
```

The modules generate the intermediate CSV files required by later stages.

> **Note:** The project uses OpenStreetMap-based geospatial data, so the geospatial setup/routing stages require internet access when fetching the road network.

## Team

- Divya Prakash
- Aditya


## Project Context

Academic / course project focused on applying machine learning, geospatial analysis, graph algorithms, and simulation techniques to disaster evacuation planning.
