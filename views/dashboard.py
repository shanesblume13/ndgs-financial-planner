import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date
from dateutil.relativedelta import relativedelta

# --- CONFIGURATION ---
COLUMN_DISPLAY_MAP = {
    'Store_Revenue': 'Revenue',
    'Store_COGS': 'Cost of Goods Sold',
    'Store_Labor': 'Labor Costs',
    'Store_Ops_Ex': 'Operating Expenses',
    'Ex_Util': 'Utilities',
    'Ex_Ins': 'Insurance',
    'Ex_Maint': 'Maintenance',
    'Ex_Mktg': 'Marketing',
    'Ex_Prof': 'Professional Fees',
    'Store_Rent_Ex': 'Rent Expense',
    'Prop_Debt': 'Debt Service',
    'Prop_Tax': 'Property Tax',
    'Store_Net': 'Net Operating Profit',
    'Prop_Revenue': 'Total Property Revenue',
    'Prop_Net': 'Net Property Income',
    'Owner_Cash_Flow': 'Net Cash Flow',
    'Cash_Balance': 'Cash on Hand',
    'Cum_Capex': 'Cumulative Capex',
    'Property_Value': 'Property Value',
    'Loan_Balance': 'Loan Balance',
    'Property_Equity': 'Property Equity',
    'Intangible_Assets': 'Intangible Assets',
    'Store_Cum': 'Cumulative Store Profit',
    'Prop_Cum': 'Cumulative Property Profit',
    'Year': 'Year',
    'Quarter': 'Quarter',
    'Month': 'Month'
}

def render_dashboard(df_projection, model_events, inputs_summary, start_date=None):
    
    # Defaults
    if start_date is None: start_date = date.today()

    st.header("Financial Performance Dashboard")
    
    # --- TABS: INPUTS & DATA ---
    tab_acq, tab_re, tab_rev, tab_opex, tab_staff, tab_events = st.tabs([
        "🤝 Acquisition", "🏢 Real Estate", "📈 Revenue & COGS", "🏢 Overhead & OpEx", "👥 Staffing", "✨ Events"
    ])
    
    # 3. Revenue & COGS Tab
    with tab_rev:
        st.caption("Revenue Configuration, COGS & Growth")
        with st.expander("Settings", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                st.number_input("Base Annual Revenue ($)", min_value=100000.0, step=10000.0, key='base_annual_revenue', help="Starting baseline before growth & seasonality")
                st.slider("Revenue Growth (%)", -5.0, 10.0, key='rev_growth')
            with c2:
                st.slider("Gross Profit Margin (%)", 0, 100, step=5, key='gross_margin_pct')
                st.markdown("##### Seasonality Factors")
                st.slider("Q1 (Winter)", 0.5, 1.5, key='seasonality_q1')
                st.slider("Q2 (Spring)", 0.5, 1.5, key='seasonality_q2')
                st.slider("Q3 (Summer)", 0.5, 1.5, key='seasonality_q3')
                st.slider("Q4 (Fall)", 0.5, 1.5, key='seasonality_q4')
            
        with st.expander("📄 Income Data", expanded=True):
             # Filter cols for Income
             inc_cols = ['Year', 'Store_Revenue', 'Store_COGS']
             df_inc = df_projection.groupby('Year')[inc_cols[1:]].sum().reset_index()
             # RENAMING
             df_inc_display = df_inc.rename(columns=COLUMN_DISPLAY_MAP)
             display_cols = [COLUMN_DISPLAY_MAP.get(c, c) for c in inc_cols[1:]]
             
             st.dataframe(df_inc_display.style.format("${:,.2f}", subset=display_cols), use_container_width=True)

    # 4. Overhead & OpEx Tab
    with tab_opex:
        st.caption("Fixed Operating Expenses & Inflation")
        with st.expander("Settings", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                st.slider("Expense Inflation (%)", -5.0, 10.0, key='exp_growth')
                st.number_input("Utilities ($/mo)", step=50.0, key='util_monthly')
                st.number_input("Insurance ($/mo)", step=50.0, key='ins_monthly')
            with c2:
                st.number_input("Maintenance ($/mo)", step=50.0, key='maint_monthly')
                st.number_input("Marketing ($/mo)", step=50.0, key='mktg_monthly')
                st.number_input("Professional Fees ($/mo)", step=50.0, key='prof_monthly')
            
        with st.expander("📄 Expense Data", expanded=True):
             # Filter cols for Ops
             ops_cols = ['Year', 'Store_Ops_Ex', 'Store_Rent_Ex', 'Ex_Util', 'Ex_Ins', 'Ex_Maint', 'Ex_Mktg', 'Ex_Prof']
             # Aggregate annual for readability in this context
             df_ops = df_projection.groupby('Year')[ops_cols[1:]].sum().reset_index()
             # RENAMING
             df_ops_display = df_ops.rename(columns=COLUMN_DISPLAY_MAP)
             # Get the new column names for formatting subset (minus Year)
             display_cols = [COLUMN_DISPLAY_MAP.get(c, c) for c in ops_cols[1:]]
             
             st.dataframe(df_ops_display.style.format("${:,.2f}", subset=display_cols), use_container_width=True)

    # 2. Staffing Tab
    with tab_staff:
        st.caption("Labor, Wages & Management")
        with st.expander("Settings", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                 st.slider("Daily Operating Hours", 6, 24, key='operating_hours')
                 st.slider("Avg Staff on Shift", 1.0, 5.0, step=0.5, key='avg_staff')
                 st.slider("Hourly Staff Wage ($/hr)", 10, 30, key='hourly_wage')
                 st.slider("Wage Growth (%)", 0.0, 10.0, key='wage_growth')
            with c2:
                 st.slider("Manager Hourly Wage ($/hr)", 12.0, 50.0, step=0.5, key='manager_wage_hourly')
                 st.slider("Manager Weekly Hours", 0, 60, key='manager_weekly_hours')
                 mgr_annual = st.session_state['manager_wage_hourly'] * st.session_state['manager_weekly_hours'] * 52
                 st.caption(f"Est. Manager Annual: ${mgr_annual:,.2f}")
             
        with st.expander("📄 Staffing Data", expanded=True):
             lab_cols = ['Year', 'Store_Labor']
             df_lab = df_projection.groupby('Year')[lab_cols[1:]].sum().reset_index()
             # RENAMING
             df_lab_display = df_lab.rename(columns=COLUMN_DISPLAY_MAP)
             display_cols = [COLUMN_DISPLAY_MAP.get(c, c) for c in lab_cols[1:]]
             
             st.dataframe(df_lab_display.style.format("${:,.2f}", subset=display_cols), use_container_width=True)



    # 4. Acquisition Tab
    with tab_acq:
        st.caption("Startup Costs, Loan & Initial Equity")
        with st.expander("Settings", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                 st.date_input("Acquisition Date", key='start_date')
                 # Refactor: Total Price Input
                 st.number_input("Total Acquisition Price ($)", step=10000.0, key='acquisition_price', help="Total Purchase Price (RE + Assets)")
                 st.number_input("Intangible Asset Allocation ($)", step=5000.0, key='intangible_assets', help="Portion of Price for Licenses, Goodwill, etc.")
                 st.number_input("Closing Costs ($)", step=1000.0, key='closing_costs', help="Legal, Title, Fees (Reduces Cash)")
                 
                 # Feedback on RE Value
                 re_val = st.session_state['acquisition_price'] - st.session_state['intangible_assets']
                 st.caption(f"implied Real Estate Value: ${re_val:,.2f}")
                 
                 st.number_input("Initial Inventory ($)", step=1000.0, key='initial_inventory')
                 st.number_input("Initial Renovations ($)", step=1000.0, key='initial_renovations')
                 
            with c2:
                 st.number_input("Loan Amount ($)", step=1000.0, key='loan_amount')
                 st.number_input("Interest Rate (%)", step=0.1, format="%.2f", key='interest_rate')
                 st.number_input("Amortization (Years)", step=1, key='amortization_years')
                 st.number_input("Startup Capital ($)", step=5000.0, key='initial_equity', help="Cash Injection from Owner")
        
        # Sources & Uses Summary
        st.divider()
        st.markdown("##### 💰 Sources & Uses Analysis")
        
        su_col1, su_col2 = st.columns(2)
        
        # Calculations
        tot_sources = st.session_state['loan_amount'] + st.session_state['initial_equity']
        
        # Uses: Total Acquisition (RE + Intangibles) + Inventory + Renovations + Closing Costs
        tot_uses = st.session_state['acquisition_price'] + st.session_state['initial_inventory'] + st.session_state['initial_renovations'] + st.session_state['closing_costs']
        net_cash = tot_sources - tot_uses
        
        with su_col1:
            st.markdown("**Uses of Funds**")
            # Break down Acquisition
            re_val_display = st.session_state['acquisition_price'] - st.session_state['intangible_assets']
            
            df_uses = pd.DataFrame([
                {"Category": "Acquisition (Real Estate)", "Amount": re_val_display},
                {"Category": "Acquisition (Intangibles)", "Amount": st.session_state['intangible_assets']},
                {"Category": "Closing Costs", "Amount": st.session_state['closing_costs']},
                {"Category": "Initial Inventory", "Amount": st.session_state['initial_inventory']},
                {"Category": "Initial Renovations", "Amount": st.session_state['initial_renovations']},
                {"Category": "TOTAL USES", "Amount": tot_uses}
            ])
            st.dataframe(df_uses.style.format("${:,.2f}", subset="Amount"), use_container_width=True, hide_index=True)
            
        with su_col2:
            st.markdown("**Sources of Funds**")
            df_sources = pd.DataFrame([
                {"Category": "Bank Loan", "Amount": st.session_state['loan_amount']},
                {"Category": "Owner Equity", "Amount": st.session_state['initial_equity']},
                {"Category": "TOTAL SOURCES", "Amount": tot_sources}
            ])
            st.dataframe(df_sources.style.format("${:,.2f}", subset="Amount"), use_container_width=True, hide_index=True)
            
        if net_cash < 0:
            st.error(f"⚠️ Funding Deficit (Negative Starting Cash): ${net_cash:,.2f}")
        else:
            st.success(f"✅ Starting Cash on Hand: ${net_cash:,.2f}")

    # 5. Real Estate Tab
    with tab_re:
        st.caption("Property Operations & Income")
        with st.expander("Settings", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                 st.number_input("Comm. Rent ($/mo)", step=100.0, key='rental_income_comm')
                 st.number_input("Residential Rent ($/mo)", step=100.0, key='rental_income_res')
            with c2:
                 st.number_input("Property Tax (Annual $)", step=500.0, key='property_tax_annual')
                 st.number_input("Appreciation Rate (%)", step=0.5, key='property_appreciation_rate')
                 st.slider("Rent Escalation (%)", 0.0, 10.0, key='rent_escalation')
             
        with st.expander("📄 Property Data", expanded=True):
             # We will update these columns once model is updated
             if 'Property_Equity' in df_projection.columns:
                 prop_agg = {
                     'Prop_Revenue': 'sum',
                     'Prop_Net': 'sum', 'Prop_Debt': 'sum', 
                     'Property_Value': 'last', 'Property_Equity': 'last'
                 }
             else:
                 prop_agg = {
                     'Prop_Net': 'sum', 'Prop_Debt': 'sum', 
                     'Prop_Cum': 'last'
                 }
                 
             df_prop = df_projection.groupby('Year').agg(prop_agg).reset_index()
             
             # RENAMING
             df_prop_display = df_prop.rename(columns=COLUMN_DISPLAY_MAP)
             # Get cols dynamically from the aggregated result
             display_cols = [c for c in df_prop_display.columns if c != 'Year']
             
             st.dataframe(df_prop_display.style.format("${:,.2f}", subset=display_cols), use_container_width=True)

    # 5. Events Tab
    with tab_events:
        st.caption("One-time or recurring events affecting the model")
        _render_event_manager_ui()
        # Table of active events is handled inside the UI render helper or can be added here
        
    st.divider()

    st.divider()

    # --- GLOBAL REPORT & ANALYSIS ---
    st.header("Global Report & Analysis")
    
    # 1. Global Controls
    c_proj1, c_proj2 = st.columns(2)
    with c_proj1:
        time_horizon = st.selectbox("Time Horizon", [1, 3, 5, 10], index=0, format_func=lambda x: f"{x} Years", key="time_horizon_select")
    
    with c_proj2:
        if 'view_agg' not in st.session_state: st.session_state['view_agg'] = "Monthly"
        b1, b2, b3 = st.columns(3)
        if b1.button("Monthly", use_container_width=True): st.session_state['view_agg'] = "Monthly"
        if b2.button("Quarterly", use_container_width=True): st.session_state['view_agg'] = "Quarterly"
        if b3.button("Annual", use_container_width=True): st.session_state['view_agg'] = "Annual"
        aggregation = st.session_state['view_agg']

    # 2. Data Preparation
    df_view = df_projection[df_projection['Project_Year'] <= time_horizon].copy()
    
    # Calculate EBITDA (Before aggregation)
    df_view['EBITDA'] = df_view['Store_Revenue'] + df_view['Store_COGS'] + df_view['Store_Labor'] + df_view['Store_Ops_Ex']

    # Dynamically find Event columns for aggregation
    event_cols = [c for c in df_view.columns if c.startswith("Event: ")]
    
    # Aggregation Logic
    agg_dict = {
        'Store_Revenue': 'sum', 'Store_COGS': 'sum', 'Store_Labor': 'sum', 'Store_Ops_Ex': 'sum', 'Store_Net': 'sum',
        'Prop_Net': 'sum', 'Owner_Cash_Flow': 'sum', 'Owner_Cum': 'last', 'EBITDA': 'sum',
        'Prop_Debt': 'sum', 'Prop_Tax': 'sum',
        'Cash_Balance': 'last', 'Cum_Capex': 'last',
        'Property_Value': 'last', 'Property_Equity': 'last', 'Intangible_Assets': 'last',
        'Loan_Balance': 'last',
        'Net_Event_Impact': 'sum', # Add Net Event Impact
        'Capex': 'sum' # Add Capex for Pro Forma row
    }
    
    # Add dynamic event columns to aggregation
    for ec in event_cols:
        agg_dict[ec] = 'sum'
    
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

    # 3. Pro Forma Financial Statements (Table First)
    st.subheader("Pro Forma Financial Statements")
    df_pro_forma_raw = _generate_pro_forma(df_display, x_axis)
    
    # --- STYLING ---
    # Rows to Bold
    bold_rows = ['Total Revenue', 'Gross Profit', 'Net Operating Income (NOI)', 'Net Cash Flow']
    
    # Helper to apply styles
    def style_pro_forma(row):
        styles = []
        # Bold Logic
        if row.name in bold_rows:
            styles.append('font-weight: bold')
        return styles

    # Helper for formatting values
    def format_values(val):
        if pd.isna(val): return ""
        if isinstance(val, str): return val
        return f"${val:,.0f}"

    # Create Styler
    styler = df_pro_forma_raw.style.apply(lambda x: [f"font-weight: bold" if x.name in bold_rows else "" for _ in x], axis=1)
    
    # Format Numbers
    # Everything is currency except DSCR
    format_dict = {col: "${:,.0f}" for col in df_pro_forma_raw.columns}
    
    # Apply special formatting for DSCR row if it exists
    # Note: Styler.format works on columns, but we have metrics as Index. 
    # We can use a custom formatter function that checks the index for the row being rendered? 
    # Actually, pandas styler format is cell-based or column-based. 
    # To format specific rows differently, we might need a formatter that inspects the index, but standard format() doesn't give index context easily.
    # ALTERNATIVE: Format the data frame as strings BEFORE passing to Styler, but keep the index for style application.
    
    # Let's do the formatting in the dataframe construction but keep numeric where possible for underlying data if needed?
    # No, for display we want precise control. 
    # Let's use the _generate_pro_forma to return a DF where DSCR is float and others are float.
    # Then we use `styler.format` passing a formatter function.
    
    def custom_formatter(x):
        # This function doesn't know which row x belongs to if applied elementwise without context.
        return f"${x:,.0f}"

    # We will iterate and build a formatter dict for specific cells? Too complex.
    # Simpler: We can just use the Styler.format(formatter=...)
    # But wait, Styler.format applies to columns.
    
    # Let's try this: convert the DataFrame to strictly formatted strings in a new DF for display,
    # but use the index of the original/new DF to drive the bolding.
    
    df_display_final = df_pro_forma_raw.copy()
    
    # Format all as currency first
    for col in df_display_final.columns:
        df_display_final[col] = df_display_final[col].apply(lambda x: f"${x:,.0f}" if isinstance(x, (int, float)) else x)
    
    # Fix DSCR row
    if 'DSCR' in df_display_final.index:
        # We need to access the raw values again to format correctly
        dscr_vals = df_pro_forma_raw.loc['DSCR']
        df_display_final.loc['DSCR'] = dscr_vals.apply(lambda x: f"{x:.2f}x")

    # Apply Style to the STRING dataframe
    styler_final = df_display_final.style.apply(lambda x: [f"font-weight: bold" if x.name in bold_rows else "" for _ in x], axis=1)
    
    st.dataframe(styler_final, use_container_width=True)

    # 4. Visualizations
    st.subheader("Financial Visualizations")
    
    # Chart 1: Cash Flow & Assets
    total_cf = df_display['Owner_Cash_Flow'].sum()
    st.metric(f"Total Owner Cash Flow ({time_horizon}y)", f"${total_cf:,.2f}")
    
    fig_owner = go.Figure()
    
    # 1. Bars: Periodic Cash Flow (Left Axis)
    fig_owner.add_trace(go.Bar(
        x=x_axis, y=df_display['Owner_Cash_Flow'], name=COLUMN_DISPLAY_MAP['Owner_Cash_Flow'], 
        marker_color='lightgreen', hovertemplate='$%{y:,.2f}<extra></extra>',
        offsetgroup=0
    ))
    
    # 2. Area: Physical Assets (Right Axis, Stack Group A)
    fig_owner.add_trace(go.Scatter(
        x=x_axis, y=df_display['Cum_Capex'], mode='lines', name=COLUMN_DISPLAY_MAP['Cum_Capex'], 
        line=dict(color='orange', width=0), 
        fill='tozeroy',
        stackgroup='assets', # Stack with Cash
        yaxis='y2',
        hovertemplate='$%{y:,.2f}<extra></extra>'
    ))
    
    # 3. Area: Intangible Assets
    fig_owner.add_trace(go.Scatter(
        x=x_axis, y=df_display['Intangible_Assets'], mode='lines', name=COLUMN_DISPLAY_MAP['Intangible_Assets'], 
        line=dict(color='violet', width=0), 
        fill='tonexty',
        stackgroup='assets', 
        yaxis='y2',
        hovertemplate='$%{y:,.2f}<extra></extra>'
    ))

    # 4. Area: Property Equity
    fig_owner.add_trace(go.Scatter(
        x=x_axis, y=df_display['Property_Equity'], mode='lines', name=COLUMN_DISPLAY_MAP['Property_Equity'], 
        line=dict(color='brown', width=0), 
        fill='tonexty',
        stackgroup='assets', 
        yaxis='y2',
        hovertemplate='$%{y:,.2f}<extra></extra>'
    ))
    
    # 5. Area: Cash on Hand (Right Axis, Stack Group A)
    fig_owner.add_trace(go.Scatter(
        x=x_axis, y=df_display['Cash_Balance'], mode='lines', name=COLUMN_DISPLAY_MAP['Cash_Balance'], 
        line=dict(color='blue', width=0), 
        fill='tonexty',
        stackgroup='assets',
        yaxis='y2', 
        hovertemplate='$%{y:,.2f}<extra></extra>'
    ))
    
    if model_events:
         _add_event_markers(fig_owner, model_events, aggregation, x_axis, start_date, time_horizon)

    # Calculate aligned ranges for dual axis
    y1_data = df_display['Owner_Cash_Flow']
    
    # Total Assets = Sum of all stacked items
    total_assets = df_display['Cash_Balance'] + df_display['Cum_Capex'] + df_display['Property_Equity'] + df_display['Intangible_Assets']
    y2_data = total_assets
    
    # Defaults
    y1_min, y1_max = y1_data.min(), y1_data.max()
    y2_min, y2_max = y2_data.min(), y2_data.max()
    
    # Add headroom
    y1_max = max(0, y1_max * 1.1)
    y1_min = min(0, y1_min * 1.1)
    y2_max = max(0, y2_max * 1.1)
    y2_min = min(0, y2_min * 1.1)

    # Calculate ratios (Top / Bottom) & Align Axes
    range1, range2 = _align_dual_axes(y1_min, y1_max, y2_min, y2_max)

    fig_owner.update_layout(
        yaxis=dict(title=COLUMN_DISPLAY_MAP['Owner_Cash_Flow'], range=range1),
        yaxis2=dict(title="Total Asset Value", overlaying='y', side='right', range=range2),
        title=f"Cash Flow & Asset Value ({aggregation})",
        hovermode="x unified",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_owner, width="stretch", key="glob_chart_cf")

    # Chart 2: Capital Structure (Balance Sheet Visualization)
    # Assets (Positive)
    asset_series = df_display['Cash_Balance'] + df_display['Cum_Capex'] + df_display['Property_Value'] + df_display['Intangible_Assets']
    # Debt (Negative)
    debt_series = -df_display['Loan_Balance']
    # Equity (Net) = Assets + Debt (since debt is negative)
    equity_series = asset_series + debt_series
    
    fig_cap = go.Figure()
    
    # Assets Bar
    fig_cap.add_trace(go.Bar(
        x=x_axis, y=asset_series, 
        name='Total Assets', marker_color='forestgreen',
        hovertemplate='$%{y:,.2f}<extra></extra>'
    ))
    
    # Debt Bar
    fig_cap.add_trace(go.Bar(
        x=x_axis, y=debt_series, 
        name='Total Debt', marker_color='firebrick',
        hovertemplate='$%{y:,.2f}<extra></extra>'
    ))
    
    # Equity Line
    fig_cap.add_trace(go.Scatter(
        x=x_axis, y=equity_series, 
        name='Total Equity (Net Worth)', mode='lines+markers',
        line=dict(color='gold', width=3),
        hovertemplate='$%{y:,.2f}<extra></extra>'
    ))
    
    fig_cap.update_layout(
        title="Balance Sheet: Assets (Pos) + Debt (Neg) = Equity", 
        barmode='relative', # Stacks positive and negative relative to 0
        hovermode="x unified", 
        legend=dict(orientation="h", y=1.1)
    )
    st.plotly_chart(fig_cap, width="stretch", key="glob_chart_cap_struct")

    # Chart 3: Profitability Analysis (EBITDA vs Net)
    fig_ebitda = go.Figure()
    fig_ebitda.add_trace(go.Scatter(
        x=x_axis, y=df_display['EBITDA'], name='EBITDA', 
        line=dict(color='purple', width=3, dash='dash'), 
        hovertemplate='$%{y:,.2f}<extra></extra>'
    ))
    fig_ebitda.add_trace(go.Bar(
        x=x_axis, y=df_display['Store_Net'], name=COLUMN_DISPLAY_MAP['Store_Net'], 
        marker_color='blue', 
        hovertemplate='$%{y:,.2f}<extra></extra>'
    ))
    
    fig_ebitda.update_layout(title=f"EBITDA vs {COLUMN_DISPLAY_MAP['Store_Net']}", hovermode="x unified", legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig_ebitda, width="stretch", key="glob_chart_ebitda")

    # Chart 4: Event Impact Analysis (NEW)
    # Only show if there are active events
    active_event_cols = [c for c in df_display.columns if c.startswith("Event: ") and df_display[c].abs().sum() > 0]
    
    if active_event_cols:
         st.subheader("Event Impact Analysis")
         fig_events = go.Figure()
         
         # 1. Total Net Impact Line
         fig_events.add_trace(go.Scatter(
             x=x_axis, y=df_display['Net_Event_Impact'],
             name='Net Event Impact', mode='lines+markers',
             line=dict(color='red', width=3, dash='dot'),
             hovertemplate='$%{y:,.2f}<extra></extra>'
         ))
         
         # 2. Individual Event Breakdown (Bars)
         # Using a distinct color palette for events
         colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98FB98', '#DDA0DD', '#F0E68C']
         
         for i, col in enumerate(active_event_cols):
             evt_name = col.replace("Event: ", "")
             color = colors[i % len(colors)]
             fig_events.add_trace(go.Bar(
                 x=x_axis, y=df_display[col],
                 name=evt_name,
                 marker_color=color,
                 hovertemplate= f"{evt_name}: $:%" + "{y:,.2f}<extra></extra>"
             ))
             
         fig_events.update_layout(
             title="Financial Impact of Business Events",
             barmode='relative',
             hovermode="x unified",
             legend=dict(orientation="h", y=1.1)
         )
         st.plotly_chart(fig_events, width="stretch", key="glob_chart_events_breakdown")


    # Chart 5: Income & Expense Breakdown
    fig_combo = go.Figure()
    
    # Revenue (Positive)
    fig_combo.add_trace(go.Bar(
        x=x_axis, y=df_display['Store_Revenue'], 
        name=COLUMN_DISPLAY_MAP['Store_Revenue'], marker_color='green',
        hovertemplate='$%{y:,.2f}<extra></extra>'
    ))
    
    # Expenses (Negative)
    fig_combo.add_trace(go.Bar(x=x_axis, y=df_display['Store_COGS'], name=COLUMN_DISPLAY_MAP['Store_COGS'], marker_color='lightblue', hovertemplate='$%{y:,.2f}<extra></extra>'))
    fig_combo.add_trace(go.Bar(x=x_axis, y=df_display['Store_Labor'], name=COLUMN_DISPLAY_MAP['Store_Labor'], marker_color='blue', hovertemplate='$%{y:,.2f}<extra></extra>'))
    fig_combo.add_trace(go.Bar(x=x_axis, y=df_display['Store_Ops_Ex'], name=COLUMN_DISPLAY_MAP['Store_Ops_Ex'], marker_color='pink', hovertemplate='$%{y:,.2f}<extra></extra>'))
    
    # Net Profit Line (Right Axis - y2)
    fig_combo.add_trace(go.Scatter(
        x=x_axis, y=df_display['Store_Net'], 
        name=COLUMN_DISPLAY_MAP['Store_Net'], mode='lines+markers',
        line=dict(color='black', width=3),
        yaxis='y2',
        hovertemplate='$%{y:,.2f}<extra></extra>'
    ))
    
    # Custom Axis Alignment
    max_pos_stack = df_display['Store_Revenue'].max()
    
    df_display['Total_Exp_Stack'] = df_display['Store_COGS'] + df_display['Store_Labor'] + df_display['Store_Ops_Ex']
    min_neg_stack = df_display['Total_Exp_Stack'].min()
    
    y1_range_min = min_neg_stack
    y1_range_max = max_pos_stack
    
    # Axis 2 (Right): Net Profit line
    y2_range_min = df_display['Store_Net'].min()
    y2_range_max = df_display['Store_Net'].max()
    
    range1, range2 = _align_dual_axes(y1_range_min, y1_range_max, y2_range_min, y2_range_max)
    
    fig_combo.update_layout(
        barmode='relative', 
        title=f"Income, Expenses & {COLUMN_DISPLAY_MAP['Store_Net']}", 
        hovermode="x unified",
        legend=dict(orientation="h", y=1.1),
        yaxis=dict(title="Revenue & Expenses", range=range1),
        yaxis2=dict(title=COLUMN_DISPLAY_MAP['Store_Net'], overlaying='y', side='right', range=range2)
    )
    st.plotly_chart(fig_combo, width="stretch", key="glob_chart_income_exp")
    
    # 5. Financial Model Source Data (Detailed)
    with st.expander("📄 Source Data (Raw Model Output)", expanded=False):
        # Format all float columns
        # Rename for display
        df_display_raw = df_projection.rename(columns=COLUMN_DISPLAY_MAP)
        
        # We need to find the NEW names of float columns
        float_cols_raw = [c for c in df_projection.columns if df_projection[c].dtype == 'float64']
        float_cols_display = [COLUMN_DISPLAY_MAP.get(c, c) for c in float_cols_raw]
        
        st.dataframe(df_display_raw.style.format("${:,.2f}", subset=float_cols_display), width="stretch")

def _generate_pro_forma(df_agg, periods):
    """
    Constructs a standard Pro Forma Income Statement from aggregated data.
    Rows: Metrics
    Cols: Periods
    """
    # Reorder keys to match image
    data = {}
    
    # 1. Revenue
    data['Revenue (Operations)'] = df_agg['Store_Revenue']
    revenue_rent = df_agg.get('Prop_Revenue', 0.0) # Using Prop_Revenue which is already calculated as Sum in agg_dict ??
    # Wait, in agg_dict: 'Prop_Revenue': 'sum' is NOT there. Only Prop_Net.
    # Let's fix calculation.
    # Original code: revenue_rent = prop_net - prop_tax - prop_debt. 
    # NOTE: In agg_dict lines 268+, 'Prop_Revenue' is NOT present.
    # But in lines 22-23 'Prop_Revenue' is mapped.
    # In Tab 5 (Real Estate), we do aggregate Prop_Revenue if distinct.
    # Let's re-derive or add 'Prop_Revenue' to agg_dict in future.
    # For now, stick to the derivation used in original function for safety.
    prop_net = df_agg['Prop_Net']
    prop_tax = df_agg['Prop_Tax']
    prop_debt = df_agg['Prop_Debt']
    revenue_rent = prop_net - prop_tax - prop_debt
    
    data['Revenue (Real Estate)'] = revenue_rent
    data['Total Revenue'] = data['Revenue (Operations)'] + data['Revenue (Real Estate)']
    
    # 2. COGS
    data['COGS'] = df_agg['Store_COGS']
    
    # 3. Gross Profit
    data['Gross Profit'] = data['Total Revenue'] + data['COGS'] # COGS is neg
    
    # 4. Expenses
    data['Labor'] = df_agg['Store_Labor']
    data['OpEx (Store)'] = df_agg['Store_Ops_Ex']
    data['Rent (Commercial)'] = df_agg['Store_Rent_Ex']
    data['Property Tax'] = prop_tax
    
    # NOI
    # NOI = Gross Profit + Labor + OpEx + Rent + PropTax (all expenses are negative)
    data['Net Operating Income (NOI)'] = data['Gross Profit'] + data['Labor'] + data['OpEx (Store)'] + data['Rent (Commercial)'] + data['Property Tax']
    
    # Debt
    data['Debt Service (P&I)'] = prop_debt
    
    # Capex (Renamed)
    capex = df_agg.get('Capex', 0.0)
    data['Capital Expenditures (Normalized)'] = capex
    
    # Net Cash Flow
    # NOI + Debt + Capex
    data['Net Cash Flow'] = data['Net Operating Income (NOI)'] + data['Debt Service (P&I)'] + data['Capital Expenditures (Normalized)']
    
    # 5. Balance Sheet (Cash)
    if 'Cash_Balance' in df_agg.columns:
        data['Cash on Hand (End of Period)'] = df_agg['Cash_Balance']
        
    # 6. DSCR
    # NOI / Abs(Debt Service)
    def calc_dscr(n, d):
        if d == 0: return 0.0
        return n / abs(d)
    
    dscr_series = pd.Series([calc_dscr(n, d) for n, d in zip(data['Net Operating Income (NOI)'], data['Debt Service (P&I)'])])
    data['DSCR'] = dscr_series

    # Assemble DataFrame with strict order
    ordered_keys = [
        'Revenue (Operations)', 'Revenue (Real Estate)', 'Total Revenue',
        'COGS', 'Gross Profit',
        'Labor', 'OpEx (Store)', 'Rent (Commercial)', 'Property Tax',
        'Net Operating Income (NOI)',
        'Debt Service (P&I)', 'Capital Expenditures (Normalized)',
        'Net Cash Flow',
        'Cash on Hand (End of Period)',
        'DSCR'
    ]
    
    # Filter data dict to ordered keys ensuring all exist
    final_data = {k: data.get(k, pd.Series(0, index=df_agg.index)) for k in ordered_keys}
    
    df = pd.DataFrame(final_data)
    
    # Transpose
    df_t = df.T
    df_t.columns = periods
    
    # Add TOTALS Column
    # Sum List
    sum_rows = [
        'Revenue (Operations)', 'Revenue (Real Estate)', 'Total Revenue',
        'COGS', 'Gross Profit',
        'Labor', 'OpEx (Store)', 'Rent (Commercial)', 'Property Tax',
        'Net Operating Income (NOI)',
        'Debt Service (P&I)', 'Capital Expenditures (Normalized)',
        'Net Cash Flow'
    ]
    
    last_rows = ['Cash on Hand (End of Period)']
    
    total_series = pd.Series(index=df_t.index)
    
    for row_name in df_t.index:
        if row_name in sum_rows:
            total_series[row_name] = df_t.loc[row_name].sum()
        elif row_name in last_rows:
            # Last period value
            total_series[row_name] = df_t.loc[row_name].iloc[-1]
        elif row_name == 'DSCR':
            # Recalc DSCR on totals
            t_noi = total_series['Net Operating Income (NOI)']
            t_debt = total_series['Debt Service (P&I)']
            total_series[row_name] = calc_dscr(t_noi, t_debt)
        else:
            total_series[row_name] = 0.0
            
    df_t['TOTAL'] = total_series

    return df_t



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

def _align_dual_axes(y1_min, y1_max, y2_min, y2_max):
    """
    Calculates the ranges for two axes such that their zero lines align.
    Returns (range1, range2).
    """
    # 1. Add headroom
    y1_max = max(0, y1_max * 1.1)
    y1_min = min(0, y1_min * 1.1)
    y2_max = max(0, y2_max * 1.1)
    y2_min = min(0, y2_min * 1.1)
    
    # 2. Defaults if no alignment needed (e.g. all positive)
    range1 = [y1_min, y1_max]
    range2 = [y2_min, y2_max]
    
    # 3. Calculate ratios (Top / Bottom)
    y1_top = y1_max
    y1_bot = abs(y1_min) if y1_min < 0 else 0
    
    y2_top = y2_max
    y2_bot = abs(y2_min) if y2_min < 0 else 0
    
    # 4. Alignment Logic
    if y1_bot > 0 and y2_bot > 0:
        # Both have negative and positive
        k1 = y1_top / y1_bot
        k2 = y2_top / y2_bot
        target_k = max(k1, k2)
        
        # Adjust Y1
        if k1 < target_k:
            y1_max_new = y1_bot * target_k
            range1 = [y1_min, y1_max_new]
        
        # Adjust Y2
        if k2 < target_k:
             y2_max_new = y2_bot * target_k
             range2 = [y2_min, y2_max_new]
             
    elif y1_bot == 0 and y2_bot > 0:
        # Y1 all positive, Y2 mixed
        # Scale Y1 down to match Y2's ratio
        # Ratio K2 = Top2 / Bot2
        # Y1 needs Bot1 such that Top1 / Bot1 = K2 => Bot1 = Top1 / K2
        range1 = [-y1_top / (y2_top/y2_bot), y1_top]
        
    elif y1_bot > 0 and y2_bot == 0:
        # Y2 all positive, Y1 mixed
        # Scale Y2 down
        range2 = [-y2_top / (y1_top/y1_bot), y2_top]
        
    return range1, range2
