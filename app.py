import streamlit as st
import pandas as pd
from model import FinancialModel
import views.styles as styles
import views.sidebar as sidebar
import views.dashboard as dashboard

# --- Page Configuration ---
st.set_page_config(page_title="North Dorr General Store - Financial Scenarios", layout="wide")

# --- Styles ---
styles.apply_custom_css()

# --- Header ---
st.title("North Dorr General Store: Financial Scenario Generator (V2.1)")
st.markdown("Dynamic acquisition modeling with Seasonality, Growth, and Event Planning.")

# --- Controller Logic ---

# 1. Get Inputs (View)
# render_sidebar returns (config_dict, ai_config_dict)
config, ai_config = sidebar.render_sidebar() 

# 2. Run Model (Logic)
# Unpack config directly into Model
# Extract start_date first as it's not a model field
start_date = config.pop('start_date', None) 
model = FinancialModel(**config)
df_projection = model.calculate_projection(months=120)

# 3. Render Output (View)
# Pass results, metadata, and AI config to Dashboard
# Create a summary of key inputs for the Dashboard/AI context display
inputs_summary = {
    "rev_growth": config['revenue_growth_rate'],
    "operating_hours": config['operating_hours'],
    "loan_amount": config['loan_amount']
}

dashboard.render_dashboard(
    df_projection=df_projection, 
    model_events=model.events, 
    ai_config=ai_config, 
    inputs_summary=inputs_summary,
    start_date=start_date
)
