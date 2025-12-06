import streamlit as st
import os
import json
import datetime
from model import BusinessEvent, BASE_REVENUE_MONTHLY, BASE_COGS_PCT
from utils.storage import load_scenarios, save_scenario

def initialize_session_state():
    # Core V1
    if 'operating_hours' not in st.session_state: st.session_state['operating_hours'] = 14
    if 'manager_salary' not in st.session_state: st.session_state['manager_salary'] = 32000
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

    # V2: Incentives (New)
    if 'inc_on' not in st.session_state: st.session_state['inc_on'] = False
    if 'inc_metric' not in st.session_state: st.session_state['inc_metric'] = "Net (NOI)"
    if 'inc_pct' not in st.session_state: st.session_state['inc_pct'] = 5.0
    if 'inc_freq' not in st.session_state: st.session_state['inc_freq'] = "Annual"

    # V2: Events
    if 'events' not in st.session_state: st.session_state['events'] = []
    
    # Phase 16: Date Management
    if 'start_date' not in st.session_state: st.session_state['start_date'] = datetime.date.today()

def _render_scenario_management():
    with st.sidebar.expander("📂 Scenario Management", expanded=True):
        scenarios = load_scenarios()
        scenario_names = ["Current Custom"] + list(scenarios.keys())
        selected_scenario = st.selectbox("Load Scenario", scenario_names)

        if st.button("Load Scenario"):
            if selected_scenario != "Current Custom":
                data = scenarios[selected_scenario]
                # V1
                for k in ['operating_hours', 'manager_salary', 'hourly_wage', 'avg_staff', 
                          'enable_fountain', 'fountain_rev_daily', 'enable_candy', 'candy_rev_daily',
                          'loan_amount', 'interest_rate', 'amortization_years']:
                    if k in data: st.session_state[k] = data[k]
                
                # Helper for Rent Migration
                if 'rental_income' in data: # Legacy single field
                    st.session_state['rental_income_res'] = data['rental_income']
                    st.session_state['rental_income_comm'] = 0.0
                else:
                    if 'rental_income_res' in data: st.session_state['rental_income_res'] = data['rental_income_res']
                    if 'rental_income_comm' in data: st.session_state['rental_income_comm'] = data['rental_income_comm']

                # V2
                for k in ['seasonality_q1', 'seasonality_q2', 'seasonality_q3', 'seasonality_q4',
                          'rev_growth', 'exp_growth',
                          'util_monthly', 'ins_monthly', 'maint_monthly', 'mktg_monthly', 'prof_monthly']:
                    if k in data: st.session_state[k] = data[k]
                    
                # Events (V2 Robust)
                if 'events_data' in data:
                    st.session_state['events'] = []
                    for ed in data['events_data']:
                        # Handle legacy events (migration)
                        if 'one_time_cost' in ed:
                            # Convert legacy to new format
                            val = 0.0
                            target = "Capex"
                            if ed.get('one_time_cost', 0) > 0:
                                val = ed['one_time_cost']
                                target = "Capex"
                            elif ed.get('recurring_cost_change', 0) > 0:
                                val = ed['recurring_cost_change']
                                target = "Ops (Fixed)"
                            elif ed.get('revenue_change', 0) > 0:
                                val = ed['revenue_change']
                                target = "Revenue"
                                
                            st.session_state['events'].append(BusinessEvent(
                                name=ed['name'],
                                start_month=ed['start_month'],
                                end_month=120,
                                frequency="One-time" if target=="Capex" else "Monthly",
                                impact_target=target,
                                value_type="Fixed Amount ($)",
                                value=val,
                                affected_entity="Store" # Default
                            ))
                        else:
                            # New format
                            st.session_state['events'].append(BusinessEvent(
                                name=ed['name'],
                                start_month=ed['start_month'],
                                end_month=ed.get('end_month', 120),
                                frequency=ed.get('frequency', 'One-time'),
                                impact_target=ed.get('impact_target', 'Revenue'),
                                value_type=ed.get('value_type', 'Fixed Amount ($)'),
                                value=ed.get('value', 0.0),
                                affected_entity=ed.get('affected_entity', 'Store')
                            ))
                else:
                     st.session_state['events'] = [] # Clear if no events
                
                if 'start_date' in data:
                    try:
                        st.session_state['start_date'] = datetime.datetime.strptime(data['start_date'], "%Y-%m-%d").date()
                    except:
                        st.session_state['start_date'] = datetime.date.today()

                st.rerun()

        st.info("Note: Scenarios are saved temporarily to disk. On cloud deployments, they may be lost on restart.")
        new_scenario_name = st.text_input("Save Current as New Scenario")
        if st.button("Save Scenario"):
            if new_scenario_name:
                # Save V2 state
                current_state = {k: st.session_state[k] for k in st.session_state.keys() if k not in ['events', 'events_data']}
                # Serialize events manually
                events_data = []
                for e in st.session_state['events']:
                    events_data.append({
                        "name": e.name, 
                        "start_month": e.start_month, 
                        "end_month": e.end_month,
                        "frequency": e.frequency,
                        "impact_target": e.impact_target,
                        "value_type": e.value_type,
                        "value": e.value,
                        "affected_entity": e.affected_entity,
                        "is_active": e.is_active
                    })
                current_state['events_data'] = events_data
                current_state['start_date'] = st.session_state['start_date'].strftime("%Y-%m-%d")
                save_scenario(new_scenario_name, current_state)
                st.success(f"Saved scenario: {new_scenario_name}")

def _render_ai_config():
    ai_config = {}
    with st.sidebar.expander("🤖 AI Configuration"):
        ai_provider = st.selectbox("AI Provider", ["Google (Gemini)", "OpenAI", "Anthropic"], index=0, key="ai_provider")
        
        user_api_key = ""
        ai_model = ""
        
        if ai_provider == "Google (Gemini)":
            user_api_key = st.text_input("Gemini API Key", type="password", key="google_key", help="Leave blank to use GOOGLE_API_KEY environment variable.")
            ai_model = st.selectbox("Model", ["gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"], index=0, key="google_model")
            
        elif ai_provider == "OpenAI":
            user_api_key = st.text_input("OpenAI API Key", type="password", key="openai_key", help="Leave blank to use OPENAI_API_KEY environment variable.")
            ai_model = st.selectbox("Model", ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"], index=0, key="openai_model")
            
        elif ai_provider == "Anthropic":
            user_api_key = st.text_input("Anthropic API Key", type="password", key="anthropic_key", help="Leave blank to use ANTHROPIC_API_KEY environment variable.")
            ai_model = st.selectbox("Model", ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229", "claude-3-haiku-20240307"], index=0, key="anthropic_model")
        
        ai_config = {
            "provider": ai_provider,
            "api_key": user_api_key,
            "model_id": ai_model
        }
    return ai_config

def _render_acquisition():
    with st.sidebar.expander("🏦 Acquisition & Rent"):
        st.caption("Loan Parameters")
        
        # Date Input
        st.session_state['start_date'] = st.date_input("Project Acquisition Date", value=st.session_state['start_date'])
        
        st.number_input("Loan Amount ($)", step=1000.0, key='loan_amount')
        st.number_input("Interest Rate (%)", step=0.1, format="%.2f", key='interest_rate')
        st.number_input("Amortization (Years)", step=1, key='amortization_years')
        
        st.divider()
        st.caption("Rental Income")
        st.number_input("Commercial Rent ($/mo)", value=st.session_state['rental_income_comm'], step=100.0, key='rental_income_comm')
        st.number_input("Residential Rent ($/mo)", value=st.session_state['rental_income_res'], step=100.0, key='rental_income_res')

def _render_ops():
    with st.sidebar.expander("👥 Operations & Staffing"):
        st.slider(
            "Daily Operating Hours",
            min_value=6, max_value=24,
            key='operating_hours',
            help="Daily open hours. Direct multiplier for Staff Labor cost."
        )
        
        st.number_input(
            "Manager Annual Salary ($)",
            min_value=0, step=1000,
            key='manager_salary',
            help="Fixed yearly cost (divided by 12). Industry Avg: $45k-$60k for small retail."
        )
        
        st.slider(
            "Hourly Staff Wage ($/hr)",
            min_value=10, max_value=30,
            key='hourly_wage',
            help="Variable cost. Impacted by inflation/growth. Avg: $15-$20."
        )
        
        st.slider(
            "Avg Staff on Shift",
            min_value=1.0, max_value=5.0, step=0.5,
            key='avg_staff',
            help="Staff count per hour. 1.5 = One full timer + one part timer overlap."
        )

def _render_growth_and_expenses():
    with st.sidebar.expander("📈 Growth, Expenses & Seasonality"):
        st.subheader("Seasonality (Q1-Q4 Multipliers)")
        s_q1 = st.slider("Q1 (Winter)", 0.5, 1.5, key='seasonality_q1')
        s_q2 = st.slider("Q2 (Spring)", 0.5, 1.5, key='seasonality_q2')
        s_q3 = st.slider("Q3 (Summer)", 0.5, 1.5, key='seasonality_q3')
        s_q4 = st.slider("Q4 (Fall/Holiday)", 0.5, 1.5, key='seasonality_q4')
        
        st.subheader("Annual Growth Rates")
        rev_growth = st.slider("Revenue Growth (%)", -5.0, 10.0, st.session_state['rev_growth'], key='rev_growth')
        exp_growth = st.slider("General Expense Inflation (%)", -5.0, 10.0, st.session_state['exp_growth'], key='exp_growth')
        wage_growth = st.slider("Wage Growth (%)", 0.0, 10.0, key='wage_growth', help="Annual increase in hourly wages/salaries.")
        rent_escalation = st.slider("Rent Escalation (%)", 0.0, 10.0, key='rent_escalation', help="Annual increase in Commercial Rent paid by Store.")
        
        st.subheader("Monthly Expenses Breakdown")
        st.number_input("Utilities", step=50.0, key='util_monthly')
        st.number_input("Insurance & Licenses", step=50.0, key='ins_monthly')
        st.number_input("Maintenance", step=50.0, key='maint_monthly')
        st.number_input("Marketing", step=50.0, key='mktg_monthly')
        st.number_input("Professional Fees", step=50.0, key='prof_monthly')
        
        return [s_q1, s_q2, s_q3, s_q4], rev_growth, exp_growth, wage_growth, rent_escalation

def _render_incentives():
    with st.sidebar.expander("💰 Manager Incentives"):
        inc_on = st.checkbox("Enable Performance Bonus", key="inc_on")
        inc_metric = "None"
        inc_pct = 0.0
        inc_freq = "Annual"
        if inc_on:
            inc_metric = st.selectbox("Bonus Metric", ["Net (NOI)", "Revenue"], key="inc_metric")
            inc_pct = st.number_input("Bonus %", 0.0, 50.0, step=0.5, key="inc_pct", help="Percentage of Metric paid as bonus.")
            inc_freq = st.selectbox("Payout Frequency", ["Annual", "Quarterly"], key="inc_freq")
        return inc_pct, inc_metric, inc_freq

def _render_event_management():
    # --- Edit Logic state management ---
    if 'edit_event_idx' not in st.session_state:
        st.session_state['edit_event_idx'] = None

    # --- Events Form (Add/Edit) ---
    form_expander = st.sidebar.expander("✨ Manage Events", expanded=True)
    with form_expander:
        is_edit_mode = st.session_state['edit_event_idx'] is not None
        edit_idx = st.session_state['edit_event_idx']
        
        # Load values if editing
        default_name = ""
        default_start = 12
        default_end = 120
        default_val = 0.0
        
        # Default Indices for Selectboxes
        idx_freq = 0
        idx_entity = 0 
        idx_target = 0
        idx_val_type = 0

        if is_edit_mode and 'events_data' in st.session_state:
            try:
                # Safety check
                if edit_idx < len(st.session_state['events_data']):
                    ev = st.session_state['events_data'][edit_idx]
                    default_name = ev.get('name', '')
                    default_start = ev.get('start_month', 12)
                    default_end = ev.get('end_month', 120)
                    default_val = ev.get('value', 0.0)
                    
                    freqs = ["One-time", "Monthly", "Quarterly", "Annually"]
                    if ev.get('frequency') in freqs: idx_freq = freqs.index(ev.get('frequency'))
                    
                    entities = ["Store", "Property"]
                    if ev.get('affected_entity') in entities: idx_entity = entities.index(ev.get('affected_entity'))

                    targets = ["Revenue", "COGS", "Labor", "Ops (Fixed)", "Rent", "Capex"]
                    if ev.get('impact_target') in targets: idx_target = targets.index(ev.get('impact_target'))
                    
                    vtypes = ["Fixed Amount ($)", "% of Revenue", "% of COGS", "% of Ops"]
                    if ev.get('value_type') in vtypes: idx_val_type = vtypes.index(ev.get('value_type'))
            except Exception:
                st.session_state['edit_event_idx'] = None # Reset on error
                st.rerun()

        form_title = f"Edit Event #{edit_idx+1}" if is_edit_mode else "Add New Event"
        st.caption(form_title)

        e_name = st.text_input("Event Name", value=default_name, placeholder="e.g. Renovation, Rent Hike")
        
        c1, c2 = st.columns(2)
        e_start = c1.number_input("Start Month", 1, 120, default_start)
        e_end = c2.number_input("End Month", 1, 120, default_end, help="Event stops after this month.")
        
        e_freq = st.selectbox("Frequency", ["One-time", "Monthly", "Quarterly", "Annually"], index=idx_freq)
        
        c3, c4 = st.columns(2)
        e_entity = c3.selectbox("Entity", ["Store", "Property"], index=idx_entity)
        e_target = c4.selectbox("Target", ["Revenue", "COGS", "Labor", "Ops (Fixed)", "Rent", "Capex"], index=idx_target)
        
        e_val_type = st.selectbox("Value Type", ["Fixed Amount ($)", "% of Revenue", "% of COGS", "% of Ops"], index=idx_val_type)
        
        val_help = "Enter absolute dollar amount" if "Fixed" in e_val_type else "Enter percentage (e.g. 5.0 for 5%)"
        e_val = st.number_input("Value", value=float(default_val), step=10.0 if "Fixed" in e_val_type else 0.5, help=val_help)
        
        c_act1, c_act2 = st.columns(2)
        
        if is_edit_mode:
            if c_act1.button("💾 Update Event"):
                if e_name:
                    # Update existing
                    new_event_dict = {
                        "name": e_name,
                        "start_month": int(e_start),
                        "end_month": int(e_end),
                        "frequency": e_freq,
                        "impact_target": e_target,
                        "value_type": e_val_type,
                        "value": float(e_val),
                        "affected_entity": e_entity,
                        "is_active": st.session_state['events_data'][edit_idx].get('is_active', True) # Preserve active state
                    }
                    st.session_state['events_data'][edit_idx] = new_event_dict
                    st.session_state['edit_event_idx'] = None
                    st.success("Updated!")
                    st.rerun()
            
            if c_act2.button("❌ Cancel"):
                st.session_state['edit_event_idx'] = None
                st.rerun()

        else:
            if st.button("➕ Add Event"):
                if e_name:
                    new_event_dict = {
                        "name": e_name,
                        "start_month": int(e_start),
                        "end_month": int(e_end),
                        "frequency": e_freq,
                        "impact_target": e_target,
                        "value_type": e_val_type,
                        "value": float(e_val),
                        "affected_entity": e_entity,
                        "is_active": True
                    }
                    if 'events_data' not in st.session_state: st.session_state['events_data'] = []
                    st.session_state['events_data'].append(new_event_dict)
                    st.success(f"Added {e_name}!")
                    st.rerun()

    # List active events with Actions
    if 'events_data' in st.session_state and st.session_state['events_data']:
        with st.sidebar.expander("📅 Passive Events List", expanded=False):
            st.warning("Use the form above to add events.")
        
        st.markdown("### Active Events")
        for i, e in enumerate(st.session_state['events_data']):
            with st.container():
                c_info, c_acts = st.columns([0.7, 0.3])
                
                # Info Column
                e_active = e.get('is_active', True)
                name_str = e.get('name')
                if not e_active: name_str += " (Inactive)"
                
                target = e.get('impact_target', '?')
                val = e.get('value', 0)
                v_type = e.get('value_type', '$')
                
                c_info.text(f"{name_str}")
                c_info.caption(f"{target} | {e.get('frequency')} | {val}")

                # Toggle
                is_on = c_info.checkbox("Active", value=e_active, key=f"active_{i}")
                if is_on != e_active:
                    st.session_state['events_data'][i]['is_active'] = is_on
                    st.rerun()

                # Actions Column
                if c_acts.button("✏️", key=f"edit_{i}", help="Edit this event"):
                    st.session_state['edit_event_idx'] = i
                    st.rerun()
                
                if c_acts.button("🗑️", key=f"del_{i}", help="Delete this event"):
                    st.session_state['events_data'].pop(i)
                    # If we deleted the one being edited, clear edit mode
                    if st.session_state['edit_event_idx'] == i:
                         st.session_state['edit_event_idx'] = None
                    st.rerun()
                    
                st.divider()

    # Reconstruct objects from dicts for the Engine
    events_objects = []
    if 'events_data' in st.session_state:
        st.session_state['events'] = []
        for ed in st.session_state['events_data']:
            # Double check for migration if needed, but UI adds new format
            st.session_state['events'].append(BusinessEvent(
                 name=ed.get('name', 'Unnamed Event'),
                 start_month=ed.get('start_month', 1),
                 end_month=ed.get('end_month', 120),
                 frequency=ed.get('frequency', 'One-time'),
                 impact_target=ed.get('impact_target', 'Revenue'),
                 value_type=ed.get('value_type', 'Fixed Amount ($)'),
                 value=ed.get('value', 0.0),
                 affected_entity=ed.get('affected_entity', 'Store'),
                 is_active=ed.get('is_active', True)
            ))
            events_objects.append(st.session_state['events'][-1])
    return events_objects

def render_sidebar():
    initialize_session_state()
    
    _render_scenario_management()
    ai_config = _render_ai_config()
    _render_acquisition()
    _render_ops()
    seasonality, rev_growth, exp_growth, wage_growth, rent_escalation = _render_growth_and_expenses()
    inc_pct, inc_metric, inc_freq = _render_incentives()
    events_objects = _render_event_management()

    # Return Config Dict
    return {
        "seasonality": seasonality,
        "revenue_growth_rate": rev_growth,
        "expense_growth_rate": exp_growth,
        "wage_growth_rate": wage_growth,
        "rent_escalation_rate": rent_escalation,
        "base_revenue": BASE_REVENUE_MONTHLY,
        "base_cogs_pct": BASE_COGS_PCT,
        
        "operating_hours": st.session_state['operating_hours'],
        "manager_salary": st.session_state['manager_salary'],
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
        
        "incentive_pct": inc_pct,
        "incentive_metric": inc_metric,
        "incentive_freq": inc_freq,
        
        "start_date": st.session_state['start_date'],
        
        "events": events_objects
    }, ai_config
