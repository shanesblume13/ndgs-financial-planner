import streamlit as st
import os
import json
import datetime
import io
from model import BusinessEvent, BASE_REVENUE_MONTHLY, BASE_COGS_PCT
from services.ai_service import ask_ai

def initialize_session_state():
    # Core V1
    if 'operating_hours' not in st.session_state: st.session_state['operating_hours'] = 14
    if 'manager_wage_hourly' not in st.session_state: st.session_state['manager_wage_hourly'] = 20.0
    if 'manager_weekly_hours' not in st.session_state: st.session_state['manager_weekly_hours'] = 40.0
    if 'hourly_wage' not in st.session_state: st.session_state['hourly_wage'] = 12
    if 'avg_staff' not in st.session_state: st.session_state['avg_staff'] = 1.0
    if 'enable_fountain' not in st.session_state: st.session_state['enable_fountain'] = False
    if 'fountain_rev_daily' not in st.session_state: st.session_state['fountain_rev_daily'] = 150.0
    if 'enable_candy' not in st.session_state: st.session_state['enable_candy'] = False
    if 'candy_rev_daily' not in st.session_state: st.session_state['candy_rev_daily'] = 80.0

    # Acquisition Defaults
    if 'loan_amount' not in st.session_state: st.session_state['loan_amount'] = 320000.0
    if 'interest_rate' not in st.session_state: st.session_state['interest_rate'] = 7.0
    if 'amortization_years' not in st.session_state: st.session_state['amortization_years'] = 25
    if 'rental_income_comm' not in st.session_state: st.session_state['rental_income_comm'] = 2000.0 # Split
    if 'rental_income_res' not in st.session_state: st.session_state['rental_income_res'] = 1550.0 # Split

    # V2: Seasonality (Q1-Q4)
    if 'seasonality_q1' not in st.session_state: st.session_state['seasonality_q1'] = 0.8  # Winter slow
    if 'seasonality_q2' not in st.session_state: st.session_state['seasonality_q2'] = 1.0  # Spring avg
    if 'seasonality_q3' not in st.session_state: st.session_state['seasonality_q3'] = 1.3  # Summer peak
    if 'seasonality_q4' not in st.session_state: st.session_state['seasonality_q4'] = 1.1  # Holiday bump

    # V2: Growth
    if 'rev_growth' not in st.session_state: st.session_state['rev_growth'] = 3.0 # 3% annual
    if 'exp_growth' not in st.session_state: st.session_state['exp_growth'] = 2.0 # 2% annual

    # V2: Granular Expenses
    if 'util_monthly' not in st.session_state: st.session_state['util_monthly'] = 1200.0
    if 'ins_monthly' not in st.session_state: st.session_state['ins_monthly'] = 400.0
    if 'maint_monthly' not in st.session_state: st.session_state['maint_monthly'] = 300.0
    if 'mktg_monthly' not in st.session_state: st.session_state['mktg_monthly'] = 200.0
    if 'prof_monthly' not in st.session_state: st.session_state['prof_monthly'] = 150.0

    # V2: Growth Extras (New)
    if 'wage_growth' not in st.session_state: st.session_state['wage_growth'] = 3.0
    if 'rent_escalation' not in st.session_state: st.session_state['rent_escalation'] = 2.0

    # New: Initial Capex
    if 'initial_capex' not in st.session_state: st.session_state['initial_capex'] = 50000.0

    # V2: Events
    if 'events' not in st.session_state: st.session_state['events'] = []
    
    # Phase 16: Date Management
    if 'start_date' not in st.session_state: st.session_state['start_date'] = datetime.date.today()

def render_sidebar():
    initialize_session_state()
    
    # Placeholder for AI (Top of Sidebar)
    ai_container = st.sidebar.container()
    
    with st.sidebar.expander("📂 File Management (Export/Import)", expanded=False):
        st.write("Save your settings to a CSV file or restore from one.")
        
        # --- EXPORT ---
        # 1. Gather Data
        current_state = {k: st.session_state[k] for k in st.session_state.keys() if k not in ['events', 'events_data']}
        # Serialize events
        events_data = []
        if 'events' in st.session_state:
            for e in st.session_state['events']:
                events_data.append({
                    "name": e.name, 
                    "start_month": e.start_month, 
                    "end_month": e.end_month,
                    "frequency": e.frequency,
                    "impact_target": e.impact_target,
                    "pct_basis": e.pct_basis,
                    "value_type": e.value_type,
                    "value": e.value,
                    "affected_entity": e.affected_entity,
                    "is_active": e.is_active
                })
        current_state['events_data'] = json.dumps(events_data) # JSON String for CSV safety
        
        # 2. Convert to CSV
        csv_data = []
        for k, v in current_state.items():
            # Handle date object
            val = v
            if isinstance(v, (datetime.date, datetime.datetime)):
                val = v.strftime("%Y-%m-%d")
            csv_data.append(f"{k},{val}")
        
        csv_string = "Key,Value\n" + "\n".join(csv_data)
        
        # 3. Download Button
        st.download_button(
            label="💾 Download Settings (CSV)",
            data=csv_string,
            file_name="financial_planner_settings.csv",
            mime="text/csv"
        )
        
        st.divider()

        # --- IMPORT ---
        uploaded_file = st.file_uploader("Upload Settings CSV", type=['csv'])
        if uploaded_file is not None:
            try:
                # 1. Parse CSV
                stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
                imported_data = {}
                for line in stringio:
                    if "," not in line or line.startswith("Key,Value"): continue
                    key, val = line.strip().split(",", 1)
                    imported_data[key] = val
                
                if st.button("Apply Uploaded Settings"):
                    # 2. Apply Scalars
                    # V1 & V2 keys
                    keys_to_load = [
                        'operating_hours', 'manager_wage_hourly', 'manager_weekly_hours', 'hourly_wage', 'avg_staff', 
                        'enable_fountain', 'fountain_rev_daily', 'enable_candy', 'candy_rev_daily',
                        'loan_amount', 'interest_rate', 'amortization_years',
                        'rental_income_res', 'rental_income_comm',
                        'seasonality_q1', 'seasonality_q2', 'seasonality_q3', 'seasonality_q4',
                        'rev_growth', 'exp_growth', 'wage_growth', 'rent_escalation',
                        'util_monthly', 'ins_monthly', 'maint_monthly', 'mktg_monthly', 'prof_monthly',
                        'initial_capex'
                    ]
                    
                    for k in keys_to_load:
                        if k in imported_data:
                            try:
                                if k in st.session_state and isinstance(st.session_state[k], int):
                                     st.session_state[k] = int(float(imported_data[k]))
                                elif k in st.session_state and isinstance(st.session_state[k], float):
                                     st.session_state[k] = float(imported_data[k])
                                else:
                                     # Fallback try generic
                                     st.session_state[k] = float(imported_data[k])
                            except:
                                pass 

                    # Date
                    if 'start_date' in imported_data:
                         try:
                            st.session_state['start_date'] = datetime.datetime.strptime(imported_data['start_date'], "%Y-%m-%d").date()
                         except:
                            pass
                    
                    # 3. Apply Events
                    ev_data_list = []
                    
                    if 'events_data' in imported_data:
                        try:
                            ev_data_list = json.loads(imported_data['events_data'])
                        except: pass

                    # Restore events
                    if ev_data_list:
                        st.session_state['events_data'] = ev_data_list # Logic for UI list
                        st.session_state['events'] = [] # Logic for engine will rebuild in _render_events
                    
                    st.success("Settings Restored!")
                    st.rerun()

            except Exception as e:
                st.error(f"Error parsing file: {e}")
                
    return ai_container

def render_ai_cfo(container, df_projection, model_events, inputs_summary):
    """Renders the AI CFO interface into the provided sidebar container."""
    with container:
        with st.expander("🤖 Ask the CFO (AI)", expanded=True):
            # AI Config
            ai_provider = st.selectbox("AI Provider", ["Google (Gemini)", "OpenAI", "Anthropic"], index=0, key="side_ai_provider")
            
            user_api_key = ""
            if ai_provider == "Google (Gemini)":
                user_api_key = st.text_input("Gemini API Key", type="password", key="side_google_key", help="Leave blank if using Env Var")
                ai_model = "gemini-2.0-flash-exp"
            elif ai_provider == "OpenAI":
                user_api_key = st.text_input("OpenAI API Key", type="password", key="side_openai_key")
                ai_model = "gpt-4o"
            else:
                user_api_key = st.text_input("Anthropic API Key", type="password", key="side_anthropic_key")
                ai_model = "claude-3-5-sonnet-20240620"
                
            st.caption(f"Model: {ai_model}")
            
            ai_config = {"provider": ai_provider, "api_key": user_api_key, "model_id": ai_model}

            user_q = st.text_area("Ask a question:", height=100, placeholder="e.g. How does increasing rent by 10% affect my ROI?")
            
            if st.button("Analyze", use_container_width=True):
                if not user_q:
                    st.warning("Please type a question.")
                else:
                    with st.spinner("Thinking..."):
                        context = {
                            "summary": inputs_summary,
                            "data_head": df_projection.head(12).to_dict(),
                            "totals": df_projection[['Store_Revenue', 'Store_Net', 'Prop_Net', 'Owner_Cash_Flow']].sum().to_dict(),
                            "events": [e.__dict__ for e in model_events if e.is_active]
                        }
                        response = ask_ai(ai_config, context, user_q)
                        st.info(response)

def get_model_config():
    """Constructs the configuration dictionary from session state."""
    
    # Reconstruct Event Objects
    events_objects = []
    if 'events_data' in st.session_state:
        for ed in st.session_state['events_data']:
            events_objects.append(BusinessEvent(
                 name=ed.get('name', 'Unnamed Event'),
                 start_month=ed.get('start_month', 1),
                 end_month=ed.get('end_month', 120),
                 frequency=ed.get('frequency', 'One-time'),
                 impact_target=ed.get('impact_target', 'Revenue'),
                 value_type=ed.get('value_type', 'Fixed Amount ($)'),
                 pct_basis=ed.get('pct_basis', 'Revenue'),
                 value=ed.get('value', 0.0),
                 affected_entity=ed.get('affected_entity', 'Store'),
                 is_active=ed.get('is_active', True)
            ))
    
    return {
        "seasonality": [
            st.session_state['seasonality_q1'],
            st.session_state['seasonality_q2'],
            st.session_state['seasonality_q3'],
            st.session_state['seasonality_q4']
        ],
        "revenue_growth_rate": st.session_state['rev_growth'],
        "expense_growth_rate": st.session_state['exp_growth'],
        "wage_growth_rate": st.session_state['wage_growth'],
        "rent_escalation_rate": st.session_state['rent_escalation'],
        "base_revenue": BASE_REVENUE_MONTHLY,
        "base_cogs_pct": BASE_COGS_PCT,
        
        "operating_hours": st.session_state['operating_hours'],
        "manager_wage_hourly": st.session_state['manager_wage_hourly'],
        "manager_weekly_hours": st.session_state['manager_weekly_hours'],
        "hourly_wage": st.session_state['hourly_wage'],
        "avg_staff": st.session_state['avg_staff'],
        
        "utilities": st.session_state['util_monthly'],
        "insurance": st.session_state['ins_monthly'],
        "maintenance": st.session_state['maint_monthly'],
        "marketing": st.session_state['mktg_monthly'],
        "professional_fees": st.session_state['prof_monthly'],
        
        "loan_amount": st.session_state['loan_amount'],
        "interest_rate": st.session_state['interest_rate'],
        "amortization_years": st.session_state['amortization_years'],
        "commercial_rent_income": st.session_state['rental_income_comm'],
        "residential_rent_income": st.session_state['rental_income_res'],
        
        "initial_capex": st.session_state['initial_capex'],

        "start_date": st.session_state['start_date'],
        
        "events": events_objects
    }
