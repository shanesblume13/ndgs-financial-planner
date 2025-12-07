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
        
        # Uses: Total Acquisition (RE + Intangibles) + Inventory + Closing Costs
        tot_uses = st.session_state['acquisition_price'] + st.session_state['initial_inventory'] + st.session_state['closing_costs']
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
        time_horizon = st.selectbox("Time Horizon", [1, 3, 5, 10], index=3, format_func=lambda x: f"{x} Years", key="time_horizon_select")
    
    with c_proj2:
        if 'view_agg' not in st.session_state: st.session_state['view_agg'] = "Annual"
        b1, b2, b3 = st.columns(3)
        if b1.button("Annual", use_container_width=True): st.session_state['view_agg'] = "Annual"
        if b2.button("Quarterly", use_container_width=True): st.session_state['view_agg'] = "Quarterly"
        if b3.button("Monthly", use_container_width=True): st.session_state['view_agg'] = "Monthly"
        aggregation = st.session_state['view_agg']

    # 2. Data Preparation
    df_view = df_projection[df_projection['Project_Year'] <= time_horizon].copy()
    
    # Calculate EBITDA (Before aggregation)
    df_view['EBITDA'] = df_view['Store_Revenue'] + df_view['Store_COGS'] + df_view['Store_Labor'] + df_view['Store_Ops_Ex']

    # Aggregation Logic
    agg_dict = {
        'Store_Revenue': 'sum', 'Store_COGS': 'sum', 'Store_Labor': 'sum', 'Store_Ops_Ex': 'sum', 'Store_Net': 'sum',
        'Prop_Net': 'sum', 'Owner_Cash_Flow': 'sum', 'Owner_Cum': 'last', 'EBITDA': 'sum',
        'Prop_Debt': 'sum', 'Prop_Tax': 'sum',
        'Cash_Balance': 'last', 'Cum_Capex': 'last',
        'Property_Value': 'last', 'Property_Equity': 'last', 'Intangible_Assets': 'last',
        'Loan_Balance': 'last'
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

    # 3. Pro Forma Financial Statements (Table First)
    st.subheader("Pro Forma Financial Statements")
    df_pro_forma = _generate_pro_forma(df_display, x_axis)
    st.dataframe(df_pro_forma, use_container_width=True)

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

    # Chart 4: Income & Expense Breakdown
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
    # Initialize dictionary for rows
    data = {}
    
    # 1. Income
    # Store Revenue + Rental Income (Rental income is inside Prop_Net usually, but we need gross)
    # The model outputs 'Prop_Net' which is Rent - Tax - Debt. 
    # To get Gross Rent, we might need to back it out or check if we aggregated it.
    # checking agg_dict... we didn't agg 'Gross_Rent' explicitly.
    # However, 'Prop_Net' = Gross_Rent - Tax - Debt.
    # So Gross_Rent = Prop_Net + Tax + Debt.
    
    # Note: df_agg values are sums (negative for expenses).
    # Prop_Debt and Prop_Tax are negative numbers in the model output.
    # So: Prop_Net = Gross_Rent + (Prop_Tax) + (Prop_Debt).
    # Gross_Rent = Prop_Net - Prop_Tax - Prop_Debt.
    
    revenue_store = df_agg['Store_Revenue']
    prop_net = df_agg['Prop_Net']
    prop_tax = df_agg['Prop_Tax']
    prop_debt = df_agg['Prop_Debt']
    
    revenue_rent = prop_net - prop_tax - prop_debt
    
    total_rev = revenue_store + revenue_rent
    
    data['Revenue (Operations)'] = revenue_store
    data['Revenue (Real Estate)'] = revenue_rent
    data['Total Revenue'] = total_rev
    
    # 2. COGS
    # Store_COGS is negative
    cogs = df_agg['Store_COGS']
    data['COGS'] = cogs
    
    # 3. Gross Profit
    # Rev + COGS (since COGS is neg)
    gross_profit = total_rev + cogs
    data['Gross Profit'] = gross_profit
    
    # 4. Operating Expenses
    # Store Labor + Store Ops + Prop Tax
    labor = df_agg['Store_Labor']
    ops = df_agg['Store_Ops_Ex']
    # Prop Tax
    
    total_opex = labor + ops + prop_tax
    
    data['Labor'] = labor
    data['OpEx (Store)'] = ops
    data['Property Tax'] = prop_tax
    data['Total OpEx'] = total_opex
    
    # 5. NOI / EBITDA
    noi = gross_profit + total_opex # (opex is neg)
    data['Net Operating Income (NOI)'] = noi
    
    # 6. Debt Service
    data['Debt Service'] = prop_debt
    
    # 7. Net Cash Flow
    # NOI + Debt 
    # (Capex is asset/equity move, usually below line for cash flow, but for Income Statement 'Net Income'...)
    # Let's show Net Cash Flow (Pre-Tax)
    ncf = noi + prop_debt
    data['Net Cash Flow'] = ncf
    
    # Construct DF
    df = pd.DataFrame(data)
    
    # Transpose: Rows = Metrics, Cols = Periods
    df_t = df.T
    df_t.columns = periods
    
    # Formatting helper
    def fmt(x):
        try:
            return f"${x:,.0f}"
        except:
            return x
            
    return df_t.applymap(fmt)



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
