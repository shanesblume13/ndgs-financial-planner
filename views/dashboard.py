import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date
from dateutil.relativedelta import relativedelta

def render_dashboard(df_projection, model_events, inputs_summary, start_date=None):
    
    # Defaults
    if start_date is None: start_date = date.today()

    st.header("Financial Performance Dashboard")
    
    # --- TABS: INPUTS & DATA ---
    tab_ops, tab_staff, tab_growth, tab_re, tab_events = st.tabs([
        "⚙️ Operations", "👥 Staffing", "📈 Growth", "🏢 Real Estate", "✨ Events"
    ])
    
    # 1. Operations Tab
    with tab_ops:
        st.caption("Operating Expenses & Fixed Costs")
        c1, c2 = st.columns(2)
        with c1:
            st.slider("Daily Operating Hours", 6, 24, key='operating_hours')
            st.number_input("Utilities ($/mo)", step=50.0, key='util_monthly')
            st.number_input("Insurance ($/mo)", step=50.0, key='ins_monthly')
        with c2:
            st.number_input("Maintenance ($/mo)", step=50.0, key='maint_monthly')
            st.number_input("Marketing ($/mo)", step=50.0, key='mktg_monthly')
            st.number_input("Professional Fees ($/mo)", step=50.0, key='prof_monthly')
            
        with st.expander("📄 Operating Data", expanded=True):
             # Filter cols for Ops
             ops_cols = ['Year', 'Store_Ops_Ex', 'Ex_Util', 'Ex_Ins', 'Ex_Maint', 'Ex_Mktg', 'Ex_Prof']
             # Aggregate annual for readability in this context
             df_ops = df_projection.groupby('Year')[ops_cols[1:]].sum().reset_index()
             st.dataframe(df_ops.style.format("${:,.2f}", subset=ops_cols[1:]), use_container_width=True)

    # 2. Staffing Tab
    with tab_staff:
        st.caption("Labor, Wages & Management")
        c1, c2 = st.columns(2)
        with c1:
             st.slider("Avg Staff on Shift", 1.0, 5.0, 1.0, step=0.5, key='avg_staff')
             st.slider("Hourly Staff Wage ($/hr)", 10, 30, key='hourly_wage')
             st.slider("Wage Growth (%)", 0.0, 10.0, key='wage_growth')
        with c2:
             st.slider("Manager Hourly Wage ($/hr)", 12.0, 50.0, 0.5, key='manager_wage_hourly')
             st.slider("Manager Weekly Hours", 0, 60, 1, key='manager_weekly_hours')
             mgr_annual = st.session_state['manager_wage_hourly'] * st.session_state['manager_weekly_hours'] * 52
             st.caption(f"Est. Manager Annual: ${mgr_annual:,.2f}")
             
        with st.expander("📄 Staffing Data", expanded=True):
             lab_cols = ['Year', 'Store_Labor']
             df_lab = df_projection.groupby('Year')[lab_cols[1:]].sum().reset_index()
             st.dataframe(df_lab.style.format("${:,.2f}", subset=lab_cols[1:]), use_container_width=True)

    # 3. Growth Tab
    with tab_growth:
         st.caption("Revenue Growth, Inflation & Seasonality")
         c1, c2 = st.columns(2)
         with c1:
            st.slider("Revenue Growth (%)", -5.0, 10.0, key='rev_growth')
            st.slider("Expense Inflation (%)", -5.0, 10.0, key='exp_growth')
            st.slider("Rent Escalation (%)", 0.0, 10.0, key='rent_escalation')
         with c2:
            st.markdown("##### Seasonality Factors")
            st.slider("Q1 (Winter)", 0.5, 1.5, key='seasonality_q1')
            st.slider("Q2 (Spring)", 0.5, 1.5, key='seasonality_q2')
            st.slider("Q3 (Summer)", 0.5, 1.5, key='seasonality_q3')
            st.slider("Q4 (Fall)", 0.5, 1.5, key='seasonality_q4')
            
         with st.expander("📄 Growth Data", expanded=True):
             growth_cols = ['Year', 'Store_Revenue', 'Store_COGS']
             df_growth = df_projection.groupby('Year')[growth_cols[1:]].sum().reset_index()
             st.dataframe(df_growth.style.format("${:,.2f}", subset=growth_cols[1:]), use_container_width=True)

    # 4. Real Estate Tab
    with tab_re:
        st.caption("Acquisition, Loans & Rent")
        c1, c2 = st.columns(2)
        with c1:
             st.date_input("Acquisition Date", key='start_date')
             st.number_input("Initial Capex ($)", step=1000.0, key='initial_capex')
             st.number_input("Loan Amount ($)", step=1000.0, key='loan_amount')
        with c2:
             st.number_input("Interest Rate (%)", step=0.1, format="%.2f", key='interest_rate')
             st.number_input("Amortization (Years)", step=1, key='amortization_years')
             st.number_input("Comm. Rent ($/mo)", step=100.0, key='rental_income_comm')
             st.number_input("Residential Rent ($/mo)", step=100.0, key='rental_income_res')
             
        with st.expander("📄 Property Data", expanded=True):
             prop_cols = ['Year', 'Prop_Net', 'Prop_Debt', 'Prop_Cum']
             df_prop = df_projection.groupby('Year')[prop_cols[1:]].sum().reset_index()
             st.dataframe(df_prop.style.format("${:,.2f}", subset=prop_cols[1:]), use_container_width=True)

    # 5. Events Tab
    with tab_events:
        st.caption("One-time or recurring events affecting the model")
        _render_event_manager_ui()
        # Table of active events is handled inside the UI render helper or can be added here
        
    st.divider()

    # --- GLOBAL VISUALIZATIONS ---
    st.subheader("Global Financial Analysis")
    
    # Global Controls
    c_proj1, c_proj2 = st.columns(2)
    time_horizon = c_proj1.selectbox("Time Horizon", [1, 3, 5, 10], index=3, format_func=lambda x: f"{x} Years")
    
    if 'view_agg' not in st.session_state: st.session_state['view_agg'] = "Annual"
    b1, b2, b3 = c_proj2.columns(3)
    if b1.button("Annual", use_container_width=True): st.session_state['view_agg'] = "Annual"
    if b2.button("Quarterly", use_container_width=True): st.session_state['view_agg'] = "Quarterly"
    if b3.button("Monthly", use_container_width=True): st.session_state['view_agg'] = "Monthly"
    aggregation = st.session_state['view_agg']

    # Prep Data
    df_view = df_projection[df_projection['Project_Year'] <= time_horizon].copy()
    
    # Calculate EBITDA (Before aggregation)
    # EBITDA = Rev + (COGS + Labor + Ops_Ex). Note: Expenses are negative in DF.
    df_view['EBITDA'] = df_view['Store_Revenue'] + df_view['Store_COGS'] + df_view['Store_Labor'] + df_view['Store_Ops_Ex']

    # Aggregation Logic (Shared)
    agg_dict = {
        'Store_Revenue': 'sum', 'Store_COGS': 'sum', 'Store_Labor': 'sum', 'Store_Ops_Ex': 'sum', 'Store_Net': 'sum',
        'Prop_Net': 'sum', 'Owner_Cash_Flow': 'sum', 'Owner_Cum': 'last', 'EBITDA': 'sum'
    }
    
    if aggregation == "Quarterly":
        df_display = df_view.groupby(['Year', 'Quarter']).agg(agg_dict).reset_index()
        x_axis = df_display.apply(lambda row: f"Q{int(row['Quarter'])} {int(row['Year'])}", axis=1)
    elif aggregation == "Annual":
        agg_dict.pop('Quarter', None)
        df_display = df_view.groupby('Year').agg(agg_dict).reset_index()
        x_axis = df_display['Year']
    else:
         x_axis = df_view.apply(lambda row: f"{date(int(row['Year']), int(row['Month']), 1).strftime('%b %Y')}", axis=1)
         df_display = df_view # Monthly is default granularity

    # 1. Main Cash Flow Chart
    total_cf = df_display['Owner_Cash_Flow'].sum()
    st.metric(f"Total Owner Cash Flow ({time_horizon}y)", f"${total_cf:,.2f}")
    
    fig_owner = go.Figure()
    fig_owner.add_trace(go.Bar(
        x=x_axis, y=df_display['Owner_Cash_Flow'], name='Periodic CF', 
        marker_color='lightgreen', hovertemplate='$%{y:,.2f}<extra></extra>'
    ))
    fig_owner.add_trace(go.Scatter(
        x=x_axis, y=df_display['Owner_Cum'], mode='lines', name='Cumulative', 
        line=dict(color='darkgreen', width=3), yaxis='y2', 
        hovertemplate='$%{y:,.2f}<extra></extra>'
    ))
    
    if model_events:
         _add_event_markers(fig_owner, model_events, aggregation, x_axis, start_date, time_horizon)

    # Calculate aligned ranges for dual axis
    y1_data = df_display['Owner_Cash_Flow']
    y2_data = df_display['Owner_Cum']
    
    # Defaults
    y1_min, y1_max = y1_data.min(), y1_data.max()
    y2_min, y2_max = y2_data.min(), y2_data.max()
    
    # Add headroom
    y1_max = max(0, y1_max * 1.1)
    y1_min = min(0, y1_min * 1.1)
    y2_max = max(0, y2_max * 1.1)
    y2_min = min(0, y2_min * 1.1)

    # Calculate ratios (Top / Bottom)
    # Avoid div by zero
    y1_top = y1_max
    y1_bot = abs(y1_min) if y1_min < 0 else 0
    
    y2_top = y2_max
    y2_bot = abs(y2_min) if y2_min < 0 else 0
    
    # Determine the dominating ratio to fit both
    # We want Top/Bot to be the same K for both.
    # K must be >= max(K1, K2) to fit data.
    
    # Logic: 
    # If both are all positive: Min is 0. Easy.
    # If mixed:
    # K1 = Top1 / Bot1
    # K2 = Top2 / Bot2
    # Target K = max(K1, K2)
    # Then adjust the non-binding axis bounds.
    
    range1 = [y1_min, y1_max]
    range2 = [y2_min, y2_max]
    
    if y1_bot > 0 and y2_bot > 0:
        k1 = y1_top / y1_bot
        k2 = y2_top / y2_bot
        target_k = max(k1, k2)
        
        # Adjust Y1
        if k1 < target_k:
            # Need more top space
            y1_max_new = y1_bot * target_k
            range1 = [y1_min, y1_max_new]
        
        # Adjust Y2
        if k2 < target_k:
             y2_max_new = y2_bot * target_k
             range2 = [y2_min, y2_max_new]
             
    elif y1_bot == 0 and y2_bot > 0:
        # Y1 is all positive, Y2 is mixed.
        # Zero line for Y2 is somewhere in middle.
        # Zero line for Y1 is at bottom.
        # To align, Y1 must extend down to match Y2's ratio.
        # K2 = Top2 / Bot2.
        # Y1 needs Bot1 such that Top1 / Bot1 = K2.
        # Bot1 = Top1 / K2.
        range1 = [-y1_top / (y2_top/y2_bot), y1_top]
        
    elif y1_bot > 0 and y2_bot == 0:
        # Y2 all positive, Y1 mixed.
        # Y2 needs space below.
        range2 = [-y2_top / (y1_top/y1_bot), y2_top]

    fig_owner.update_layout(
        yaxis=dict(title="Periodic Cash Flow", range=range1),
        yaxis2=dict(title="Cumulative Cash Flow", overlaying='y', side='right', range=range2),
        title=f"Owner Cash Flow: Periodic vs Cumulative ({aggregation})",
        hovermode="x unified",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_owner, width="stretch", key="glob_chart_cf")

    # 2. Profitability Analysis (EBITDA vs Net)
    st.subheader("Profitability Trends")
    fig_ebitda = go.Figure()
    fig_ebitda.add_trace(go.Scatter(
        x=x_axis, y=df_display['EBITDA'], name='EBITDA', 
        line=dict(color='purple', width=3, dash='dash'), 
        hovertemplate='$%{y:,.2f}<extra></extra>'
    ))
    fig_ebitda.add_trace(go.Bar(
        x=x_axis, y=df_display['Store_Net'], name='Net Profit (Post-Rent/Capex)', 
        marker_color='blue', 
        hovertemplate='$%{y:,.2f}<extra></extra>'
    ))
    
    fig_ebitda.update_layout(title="EBITDA vs Net Profit", hovermode="x unified", legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig_ebitda, width="stretch", key="glob_chart_ebitda")

    # 3. Expense Stack & Profit
    c_chart1, c_chart2 = st.columns(2)
    
    with c_chart1:
        fig_stack = go.Figure()
        fig_stack.add_trace(go.Bar(x=x_axis, y=df_display['Store_COGS'], name='COGS', hovertemplate='$%{y:,.2f}<extra></extra>'))
        fig_stack.add_trace(go.Bar(x=x_axis, y=df_display['Store_Labor'], name='Labor', hovertemplate='$%{y:,.2f}<extra></extra>'))
        fig_stack.add_trace(go.Bar(x=x_axis, y=df_display['Store_Ops_Ex'], name='Ops Expenses', hovertemplate='$%{y:,.2f}<extra></extra>'))
        fig_stack.update_layout(barmode='stack', title="Expense Structure", legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig_stack, use_container_width=True)
        
    with c_chart2:
        fig_prof = go.Figure()
        fig_prof.add_trace(go.Scatter(x=x_axis, y=df_display['Store_Net'], name='Store Net', line=dict(color='blue'), hovertemplate='$%{y:,.2f}<extra></extra>'))
        fig_prof.add_trace(go.Scatter(x=x_axis, y=df_display['Prop_Net'], name='Prop Net', line=dict(color='orange'), hovertemplate='$%{y:,.2f}<extra></extra>'))
        fig_prof.update_layout(title="Net Profit by Entity", legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig_prof, use_container_width=True)
        
    # 4. Detailed Table (Restored)
    st.divider()
    with st.expander("📄 Financial Model Source Data (Detailed)", expanded=False):
        # Format all float columns
        float_cols = [c for c in df_projection.columns if df_projection[c].dtype == 'float64']
        st.dataframe(df_projection.style.format("${:,.2f}", subset=float_cols), width="stretch")


# --- HELPER FUNCTIONS ---
def _add_event_markers(fig, model_events, aggregation, x_axis, start_date, time_horizon):
    """Helper to add vertical event lines to a Plotly figure."""
    for e in model_events:
        if e.is_active:
            event_date = start_date + relativedelta(months=e.start_month - 1)
            e_year = event_date.year
            e_q = (event_date.month - 1) // 3 + 1
            
            x_loc = None
            if aggregation == "Monthly":
                label = event_date.strftime('%b %Y')
                if label in x_axis.values: x_loc = label
            elif aggregation == "Annual":
                if e_year in x_axis.values: x_loc = e_year
            elif aggregation == "Quarterly":
                    label = f"Q{e_q} {e_year}"
                    if label in x_axis.values: x_loc = label
            
            if x_loc:
                fig.add_vline(x=x_loc, line_width=1, line_dash="dash", line_color="red", opacity=0.5)

def _render_event_manager_ui():
    """Renders the Event CRUD UI"""
    if 'edit_event_idx' not in st.session_state:
        st.session_state['edit_event_idx'] = None

    c_form, c_list = st.columns([1, 1])
    
    with c_form:
        st.markdown("#### Add / Edit Event")
        is_edit_mode = st.session_state['edit_event_idx'] is not None
        edit_idx = st.session_state['edit_event_idx']
        
        # Load values
        default_name = ""
        default_start = 12
        default_end = 120
        default_val = 0.0
        idx_freq = 0
        idx_entity = 0 
        idx_target = 0
        idx_val_type = 0
        idx_basis = 0
        
        basis_options = ["Revenue", "COGS", "Labor", "Ops (Fixed)", "Rent", "Capex", "NOI"]

        if is_edit_mode and 'events_data' in st.session_state:
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
                
                raw_type = ev.get('value_type', "Fixed Amount ($)")
                if "Fixed" in raw_type: idx_val_type = 0 
                elif "Percent" in raw_type: idx_val_type = 1
                
                stored_basis = ev.get('pct_basis', 'Revenue')
                if stored_basis in basis_options: idx_basis = basis_options.index(stored_basis)

        e_name = st.text_input("Event Name", value=default_name, placeholder="e.g. Renovation")
        
        c1, c2 = st.columns(2)
        e_start = c1.number_input("Start Month", 1, 120, default_start)
        e_end = c2.number_input("End Month", 1, 120, default_end)
        
        e_freq = st.selectbox("Frequency", ["One-time", "Monthly", "Quarterly", "Annually"], index=idx_freq)
        
        c3, c4 = st.columns(2)
        e_entity = c3.selectbox("Entity", ["Store", "Property"], index=idx_entity)
        e_target = c4.selectbox("Target", ["Revenue", "COGS", "Labor", "Ops (Fixed)", "Rent", "Capex"], index=idx_target)
        
        e_val_type_main = st.selectbox("Value Type", ["Fixed Amount ($)", "Percentage (%)"], index=idx_val_type)
        e_basis = "Revenue"
        if e_val_type_main == "Percentage (%)":
             e_basis = st.selectbox("Basis", basis_options, index=idx_basis)
        
        val_step = 100.0 if e_val_type_main == "Fixed Amount ($)" else 0.5
        e_val = st.number_input("Value", value=float(default_val), step=val_step)
        
        if is_edit_mode:
            if st.button("💾 Update Event"):
                if e_name:
                    new_event_dict = {
                        "name": e_name, "start_month": int(e_start), "end_month": int(e_end),
                        "frequency": e_freq, "impact_target": e_target, "value_type": e_val_type_main,
                        "pct_basis": e_basis, "value": float(e_val), "affected_entity": e_entity,
                        "is_active": st.session_state['events_data'][edit_idx].get('is_active', True)
                    }
                    st.session_state['events_data'][edit_idx] = new_event_dict
                    st.session_state['edit_event_idx'] = None
                    st.rerun()
            if st.button("❌ Cancel"):
                st.session_state['edit_event_idx'] = None
                st.rerun()
        else:
            if st.button("➕ Add Event"):
                if e_name:
                    new_event_dict = {
                        "name": e_name, "start_month": int(e_start), "end_month": int(e_end),
                        "frequency": e_freq, "impact_target": e_target, "value_type": e_val_type_main,
                        "pct_basis": e_basis, "value": float(e_val), "affected_entity": e_entity,
                        "is_active": True
                    }
                    if 'events_data' not in st.session_state: st.session_state['events_data'] = []
                    st.session_state['events_data'].append(new_event_dict)
                    st.rerun()

    with c_list:
        st.markdown("#### Active Events")
        if 'events_data' in st.session_state and st.session_state['events_data']:
            for i, e in enumerate(st.session_state['events_data']):
                with st.container():
                     c_txt, c_btn = st.columns([0.8, 0.2])
                     c_txt.text(f"{e['name']} ({e['value']})")
                     if c_btn.button("✏️", key=f"tbl_edit_{i}"):
                         st.session_state['edit_event_idx'] = i
                         st.rerun()
                     if c_btn.button("🗑️", key=f"tbl_del_{i}"):
                         st.session_state['events_data'].pop(i)
                         if st.session_state['edit_event_idx'] == i: st.session_state['edit_event_idx'] = None
                         st.rerun()
