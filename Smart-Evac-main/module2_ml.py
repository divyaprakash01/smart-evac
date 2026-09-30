import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

def train_and_predict_risk(data_path="synthetic_households.csv"):
    """
    Module 2: Loads household data, trains a Random Forest model to predict flood risk,
    and isolates the high-risk households that require evacuation.
    """
    print("🧠 Loading data and preparing Machine Learning model...")
    
    # 1. Loading the Data
    try:
        df = pd.read_csv(data_path)
    except FileNotFoundError:
        print(f"❌ Error: Could not find {data_path}. Did you run Module 1?")
        return None

    features = ['Distance_to_Hazard', 'Elevation', 'Building_Type', 'Num_Elderly', 'Num_Children', 'Family_Size']
    X = df[features]
    y = df['Risk_Label']
    
    # 2. Pre-processing: 80/20 Train-Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 3. Model Training
    # Initialize and train the Random Forest Classifier
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)
    
    # Evaluate the model on the 20% test data
    predictions = rf_model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    print(f"✅ Model trained successfully! Accuracy: {accuracy * 100:.2f}%")
    
    # 4. Inference: Predict on all households
    df['Predicted_Risk'] = rf_model.predict(X)
    
    # 5. Filtering: Isolate Evacuees
    evacuees_df = df[df['Predicted_Risk'] == 1].copy()
    
    print(f"🚨 Filtering complete: Identified {len(evacuees_df)} households requiring immediate evacuation.")
    
    return df, evacuees_df

# ==========================================
# Execution / Testing the Module
# ==========================================
if __name__ == "__main__":
    results = train_and_predict_risk()
    
    if results:
        all_households_df, evacuees_df = results

        evacuees_df.to_csv("evacuees_list.csv", index=False)
        print("💾 Saved high-risk households to 'evacuees_list.csv'")
        
        print("\n--- Sample of Evacuees ---")
        print(evacuees_df[['Node_ID', 'Distance_to_Hazard', 'Elevation', 'Predicted_Risk']].head().to_string(index=False))