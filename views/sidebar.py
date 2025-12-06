import streamlit as st
import os
import json
import datetime
import io
from model import BusinessEvent, BASE_REVENUE_MONTHLY, BASE_COGS_PCT

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



    # V2: Events
    if 'events' not in st.session_state: st.session_state['events'] = []
    
    # Phase 16: Date Management
    if 'start_date' not in st.session_state: st.session_state['start_date'] = datetime.date.today()

def _render_file_management():
    with st.sidebar.expander("📂 File Management (Export/Import)", expanded=True):
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
                        'operating_hours', 'manager_salary', 'hourly_wage', 'avg_staff', 
                        'enable_fountain', 'fountain_rev_daily', 'enable_candy', 'candy_rev_daily',
                        'loan_amount', 'interest_rate', 'amortization_years',
                        'rental_income_res', 'rental_income_comm',
                        'seasonality_q1', 'seasonality_q2', 'seasonality_q3', 'seasonality_q4',
                        'rev_growth', 'exp_growth', 'wage_growth', 'rent_escalation',
                        'util_monthly', 'ins_monthly', 'maint_monthly', 'mktg_monthly', 'prof_monthly'
                    ]
                    
                    for k in keys_to_load:
                        if k in imported_data:
                            # Infer type from current state default if possible, else float
                            try:
                                if k in st.session_state and isinstance(st.session_state[k], int):
                                     st.session_state[k] = int(float(imported_data[k]))
                                elif k in st.session_state and isinstance(st.session_state[k], float):
                                     st.session_state[k] = float(imported_data[k])
                                else:
                                     # Fallback try generic
                                     st.session_state[k] = float(imported_data[k])
                            except:
                                pass # Keep default if parse fail

                    # Date
                    if 'start_date' in imported_data:
                         try:
                            st.session_state['start_date'] = datetime.datetime.strptime(imported_data['start_date'], "%Y-%m-%d").date()
                         except:
                            pass
                    
                    # 3. Apply Events
                    if 'events_data' in imported_data:
                        try:
                            # It's a JSON string
                            raw_json = imported_data['events_data']
                            # If it was double quoted in CSV it might have extra quotes? 
                            # Simple split above might be fragile for complex JSON with commas.
                            # Better approach: Use csv module.
                            pass 
                        except:
                            pass

                    # Robust CSV read
                    # Re-reading using csv module to handle the JSON string correctly
                    stringio.seek(0)
                    import csv
                    reader = csv.DictReader(stringio)
                    # This expects Key, Value headers
                    
                    # Manual DictReader doesn't work well with K,V structure vertical.
                    # Actually standard CSV reader is fine.
                    stringio.seek(0)
                    csv_reader = csv.reader(stringio)
                    next(csv_reader, None) # Skip header
                    
                    ev_data_list = []
                    
                    for row in csv_reader:
                        if len(row) < 2: continue
                        k = row[0]
                        v = row[1]
                        
                        if k == 'events_data':
                            # Deserialize
                            try:
                                ev_data_list = json.loads(v)
                            except:
                                st.error("Failed to parse events data.")
                        else:
                             # Already handled scalars above broadly, or we can re-do carefully here.
                             # Let's trust the scalar logic above but update it to use this robust loop?
                             # Actually let's just use this loop for everything.
                             if k in keys_to_load:
                                try:
                                    if k in st.session_state and isinstance(st.session_state[k], int):
                                         st.session_state[k] = int(float(v))
                                    elif k in st.session_state and isinstance(st.session_state[k], float):
                                         st.session_state[k] = float(v)
                                except: pass
                             
                             if k == 'start_date':
                                 try: st.session_state['start_date'] = datetime.datetime.strptime(v, "%Y-%m-%d").date()
                                 except: pass

                    # Restore events
                    if ev_data_list:
                        st.session_state['events_data'] = ev_data_list # Logic for UI list
                        st.session_state['events'] = [] # Logic for engine will rebuild in _render_events
                    
                    st.success("Settings Restored!")
                    st.rerun()

            except Exception as e:
                st.error(f"Error parsing file: {e}")



def _render_acquisition():
    with st.sidebar.expander("🏦 Acquisition & Rent"):
        st.caption("Loan Parameters")
        
        # Date Input
        st.session_state['start_date'] = st.date_input("Project Acquisition Date", value=st.session_state['start_date'])
        
        # New: Initial Capex
        st.number_input("Initial Capex / Startup Costs ($)", value=50000.0, step=1000.0, key='initial_capex')

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
        idx_basis = 0 # Default to Revenue

        # Basis options
        basis_options = ["Revenue", "COGS", "Labor", "Ops (Fixed)", "Rent", "Capex", "NOI"]


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
                    
                    # Determine Value Type and Basis from potential legacy data
                    raw_type = ev.get('value_type', "Fixed Amount ($)")
                    
                    if "Fixed" in raw_type:
                        idx_val_type = 0 # Fixed
                    elif "%" in raw_type or "Percent" in raw_type:
                        idx_val_type = 1 # Percentage (%)
                        # Try to find basis in stored 'pct_basis' OR infer from old string
                        stored_basis = ev.get('pct_basis', None)
                        if stored_basis == "Previous Quarter NOI": stored_basis = "NOI" # Migration
                        
                        if stored_basis and stored_basis in basis_options:
                             idx_basis = basis_options.index(stored_basis)
                        else:
                            # Infer from legacy string (e.g. "% of Revenue")
                            if "Revenue" in raw_type: idx_basis = basis_options.index("Revenue")
                            elif "COGS" in raw_type: idx_basis = basis_options.index("COGS")
                            elif "Ops" in raw_type: idx_basis = basis_options.index("Ops (Fixed)")
                            elif "NOI" in raw_type: idx_basis = basis_options.index("NOI")

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
        
        # New split UI for Value Type + Basis
        e_val_type_main = st.selectbox("Value Type", ["Fixed Amount ($)", "Percentage (%)"], index=idx_val_type)
        
        e_basis = "Revenue"
        if e_val_type_main == "Percentage (%)":
             e_basis = st.selectbox("Percentage Basis", basis_options, index=idx_basis)
        
        val_label = "Amount ($)" if e_val_type_main == "Fixed Amount ($)" else f"Percent (%) of {e_basis}" 
        val_step = 100.0 if e_val_type_main == "Fixed Amount ($)" else 0.5
        
        e_val = st.number_input(val_label, value=float(default_val), step=val_step)
        
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
                        "value_type": e_val_type_main,
                        "pct_basis": e_basis, # New field
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
                        "value_type": e_val_type_main,
                        "pct_basis": e_basis, # New field
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
                basis_info = ""
                if "Percent" in v_type or "%" in v_type:
                     # Check separate basis field or infer from old string type
                     b = e.get('pct_basis', '')
                     if not b: 
                         # Fallback display for legacy
                         b = v_type 
                     basis_info = f"({b})"

                c_info.text(f"{name_str}")
                c_info.caption(f"{target} | {e.get('frequency')}")
                c_info.caption(f"{val} {v_type} {basis_info}")

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
                 pct_basis=ed.get('pct_basis', 'Revenue'), # Default if missing
                 value=ed.get('value', 0.0),
                 affected_entity=ed.get('affected_entity', 'Store'),
                 is_active=ed.get('is_active', True)
            ))
            events_objects.append(st.session_state['events'][-1])
    return events_objects

def render_sidebar():
    initialize_session_state()
    
    _render_file_management()
    
    _render_acquisition()
    _render_ops()
    seasonality, rev_growth, exp_growth, wage_growth, rent_escalation = _render_growth_and_expenses()
    events_objects = _render_event_management()

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
        
        
        "initial_capex": st.session_state['initial_capex'],

        "start_date": st.session_state['start_date'],
        
        "events": events_objects
    }
