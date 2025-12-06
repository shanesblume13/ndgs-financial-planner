import streamlit as st
import pandas as pd
from model import FinancialModel
import views.styles as styles
import views.sidebar as sidebar
import views.dashboard as dashboard

# --- Page Configuration ---
st.set_page_config(page_title="NDGS - Mixed Use Financial Planner", layout="wide")

# --- Styles ---
styles.apply_custom_css()

# --- Header ---
st.title("NDGS - Mixed Use Financial Planner")
st.markdown("Dynamic acquisition modeling with Seasonality, Growth, and Event Planning.")

# --- Controller Logic ---

# 1. Initialize State & File Management (Sidebar)
# Returns a container placeholder for the AI component to use later
ai_container = sidebar.render_sidebar() 

# 2. Get Configuration (State -> Dict)
config = sidebar.get_model_config()

# 3. Run Model (Logic)
start_date = config.pop('start_date', None) 
model = FinancialModel(**config)
df_projection = model.calculate_projection(start_date=start_date, months=120)

# 4. Render Output (View)
inputs_summary = {
    "rev_growth": config['revenue_growth_rate'],
    "operating_hours": config['operating_hours'],
    "loan_amount": config['loan_amount'],
    "interest_rate": config['interest_rate'],
    "avg_staff": config['avg_staff'],
    "hourly_wage": config['hourly_wage'],
    "revenue_growth_rate": config['revenue_growth_rate'],
    "commercial_rent_income": config['commercial_rent_income'],
    "residential_rent_income": config['residential_rent_income']
}

# 4a. Render AI CFO in Sidebar (now that we have data)
sidebar.render_ai_cfo(ai_container, df_projection, model.events, inputs_summary)

# 4b. Render Main Dashboard
dashboard.render_dashboard(
    df_projection=df_projection, 
    model_events=model.events, 
    inputs_summary=inputs_summary,
    start_date=start_date
)
