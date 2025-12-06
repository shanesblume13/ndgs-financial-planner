import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date
from dateutil.relativedelta import relativedelta
from services.ai_service import ask_ai

def render_dashboard(df_projection, model_events, inputs_summary, start_date=None):
    
    # Defaults
    if start_date is None: start_date = date.today()

    st.header("Financial Performance Dashboard")
    # --- VIEW TOGGLE ---
    st.markdown("---")
    view_mode = st.radio("Financial View Level", ["Consolidated (Owner)", "Separated (Entities)"], horizontal=True)

    # --- PROJECTION CONTROLS ---
    st.subheader("Projection Settings")
    c_proj1, c_proj2 = st.columns(2)
    time_horizon = c_proj1.selectbox("Time Horizon", [1, 3, 5, 10], index=3, format_func=lambda x: f"{x} Years")
    # Aggregation Controls
    if 'view_agg' not in st.session_state: st.session_state['view_agg'] = "Annual"
    
    st.caption("Data Granularity")
    b1, b2, b3 = c_proj2.columns(3)
    if b1.button("Collapse All (Yearly)", use_container_width=True): st.session_state['view_agg'] = "Annual"
    if b2.button("Expand Quarters", use_container_width=True): st.session_state['view_agg'] = "Quarterly"
    if b3.button("Expand All (Monthly)", use_container_width=True): st.session_state['view_agg'] = "Monthly"
    
    aggregation = st.session_state['view_agg']

    # Filter Data based on controls
    # Use Project_Year for filtering (e.g. 1-10) to match "Time Horizon"
    df_view = df_projection[df_projection['Project_Year'] <= time_horizon].copy()

    # Define aggregation dict for all potential columns
    agg_dict = {
        'Year': 'first', # Calendar Year (e.g. 2026)
        'Quarter': 'first', # Calendar Quarter
        'Month': 'first', # Calendar Month
        'Project_Year': 'first', # Keep track
        # Store Flow
        'Store_Revenue': 'sum', 
        'Store_COGS': 'sum',
        'Store_Labor': 'sum',
        'Store_Ops_Ex': 'sum',
        'Ex_Util': 'sum',
        'Ex_Ins': 'sum',
        'Ex_Maint': 'sum',
        'Ex_Mktg': 'sum',
        'Ex_Prof': 'sum',
        'Store_Rent_Ex': 'sum',
        'Store_Bonus': 'sum',
        'Store_NOI_Pre': 'sum', # New
        'Store_Net': 'sum', 
        # Prop Flow
        'Prop_Debt': 'sum',
        'Prop_Net': 'sum', 
        # Owner Flow
        'Owner_Cash_Flow': 'sum',
        'Capex': 'sum',
        # Cumulative (Last value)
        'Store_Cum': 'last', 
        'Prop_Cum': 'last', 
        'Owner_Cum': 'last',
        'Net_Event_Impact': 'sum'
    }

    if aggregation == "Quarterly":
        # Group by Year+Quarter 
        # Create a transient grouper. "2026-Q2"
        # We can just group by [Year, Quarter]
        df_view = df_view.groupby(['Year', 'Quarter']).agg(agg_dict).reset_index(drop=True)
        # Sort by Year, Quarter just in case
        df_view.sort_values(by=['Year', 'Quarter'], inplace=True)
        x_axis = df_view.apply(lambda row: f"Q{int(row['Quarter'])} {int(row['Year'])}", axis=1)
    elif aggregation == "Annual":
        agg_dict.pop('Quarter', None)
        agg_dict.pop('Month', None)
        agg_dict.pop('Year', None) 
        # Group by Year (Calendar)
        df_view = df_view.groupby('Year').agg(agg_dict).reset_index()
        x_axis = df_view['Year']
    else:
        # Monthly
        x_axis = df_view.apply(lambda row: f"{date(int(row['Year']), int(row['Month']), 1).strftime('%b %Y')}", axis=1)

    # Calculate Total Cash Flow (Global Scope for AI)
    total_cf = df_view['Owner_Cash_Flow'].sum()

    if view_mode == "Consolidated (Owner)":
        # Owner View
        st.header(f"Consolidated Snapshot ({time_horizon}-Year)")
        
        avg_cf_per_period = total_cf / len(df_view)
        
        c1, c2, c3 = st.columns(3)
        c1.metric(f"Total Owner Cash Flow ({time_horizon}y)", f"${total_cf:,.0f}")
        c2.metric(f"Avg Cash Flow (Per {aggregation[:-2]})", f"${avg_cf_per_period:,.0f}")
        
        # KPI Row 2
        # KPI Row 2
        net_margin_agg = (df_view['Store_Net'].sum() / df_view['Store_Revenue'].sum()) * 100.0
        # Prop NOI = Net + Debt Service (add back the negative debt to get pre-debt number)
        # Since Debt is negative, we subtract it to add the magnitude back?
        # Net (8) = NOI (10) + Debt (-2). -> NOI = Net - Debt. (8 - (-2) = 10). Correct.
        prop_noi_agg = df_view['Prop_Net'].sum() - df_view['Prop_Debt'].sum()
        
        # DSCR = NOI / Debt Service (Positive)
        denom = abs(df_view['Prop_Debt'].sum())
        dscr_agg = prop_noi_agg / denom if denom > 0 else 0.0
        
        c3.metric("Avg Net Margin %", f"{net_margin_agg:.1f}%")
        
        c4, c5, c6 = st.columns(3)
        c4.metric("Avg Property DSCR", f"{dscr_agg:.2f}x", help=">1.25x is healthy")
        
        # Detail Toggle
        show_detail = st.checkbox("Show Detailed Breakdown (P&L)", value=False)

        with st.expander("View Data Detail", expanded=True):
            if show_detail:
                # Detailed Column Order
                # 1. Prepare Base Data
                cols = [
                    "Year",
                    "Month", 
                    "Quarter",
                    # Store Operations Group
                    "Store_Revenue", "Store_COGS", "Store_Labor", "Store_Rent_Ex", "Store_Ops_Ex", "Store_NOI_Pre",
                    # Detailed Expenses Group
                    "Ex_Util", "Ex_Ins", "Ex_Maint", "Ex_Mktg", "Ex_Prof",
                    # Investment
                    "Capex",
                    # Bottom Line
                    "Net_Event_Impact", # Add new column
                    "Store_Net", "Prop_Net", "Owner_Cash_Flow"
                ]
                
                df_display = df_view.copy()
                # Ensure all cols exist
                final_cols = [c for c in cols if c in df_display.columns]
                df_display = df_display[final_cols].copy()
                
                # 2. Rename Columns for Friendliness
                rename_map = {
                    "Year": ("Time", "Year"),
                    "Month": ("Time", "Month"),
                    "Quarter": ("Time", "Quarter"),
                    "Store_Revenue": ("Store Operations", "Revenue"),
                    "Store_COGS": ("Store Operations", "COGS"),
                    "Store_Labor": ("Store Operations", "Total Labor"),
                    "Store_Bonus": ("Store Operations", "Manager Bonus"),
                    "Store_Ops_Ex": ("Store Operations", "Total OpEx"),
                    "Store_NOI_Pre": ("Store Operations", "NOI"), # New
                    "Ex_Util": ("Detailed Expenses", "Utilities"),
                    "Ex_Ins": ("Detailed Expenses", "Insurance"),
                    "Ex_Maint": ("Detailed Expenses", "Maintenance"),
                    "Ex_Mktg": ("Detailed Expenses", "Marketing"),
                    "Ex_Prof": ("Detailed Expenses", "Professional"),
                    "Store_Rent_Ex": ("Store Operations", "Rent Paid"),
                    "Capex": ("Investment", "Capex"),
                    "Net_Event_Impact": ("Bottom Line", "Event Adjustments"),
                    "Store_Net": ("Bottom Line", "Store Net"),
                    "Prop_Net": ("Bottom Line", "Property Net"),
                    "Owner_Cash_Flow": ("Bottom Line", "Total Owner CF")
                }
                
                # Check which keys exist (due to dynamic cols)
                final_rename = {k: v for k, v in rename_map.items() if k in df_display.columns}
                df_display.rename(columns=final_rename, inplace=True)
                
                # 3. Create MultiIndex Columns
                df_display.columns = pd.MultiIndex.from_tuples(df_display.columns)
                
                # Apply format only to numeric columns
                numeric_cols = df_display.select_dtypes(include=['float', 'int']).columns
                exclude_cols = [c for c in numeric_cols if c[0] == "Time"] # MultiIndex check
                numeric_cols = [c for c in numeric_cols if c not in exclude_cols]
                
                st.dataframe(
                    df_display.style.format("${:,.0f}", subset=numeric_cols),
                    width="stretch"
                )
                st.caption("Note: 'Detailed Expenses' breaks down the 'Total OpEx' figure.")
            else:
                # Simple Column Order
                cols = ["Year", "Store_Revenue", "Store_Net", "Prop_Net", "Owner_Cash_Flow", "Owner_Cum"]
                if aggregation == "Monthly": cols.insert(1, "Month")
                if aggregation == "Quarterly": cols.insert(1, "Quarter")
                
                # Filter cols
                final_cols = [c for c in cols if c in df_view.columns]
                
                st.dataframe(
                    df_view[final_cols].style.format("${:,.0f}"),
                    width="stretch"
                )

        # Interactive Waterfall Section (Moved up for visibility)
        st.subheader("Profit Anatomy (Waterfall)")
        c_w_sel, _ = st.columns([1, 3])
        # Select Calendar Year not Project Year
        available_years = sorted(df_view['Year'].unique())
        water_year = c_w_sel.selectbox("Select Year for Waterfall", available_years)
        
        y_data = df_projection[df_projection['Year']==water_year].sum()
        
        fig_water = go.Figure(go.Waterfall(
            name = f"Year {water_year}", orientation = "v",
            measure = ["relative", "relative", "relative", "relative", "relative", "relative", "total", "relative", "total"],
            x = ["Revenue", "COGS", "Labor", "Ops", "Rent", "Capex", "Store Net", "+ Prop Net", "Owner CF"],
            textposition = "outside",
            y = [
                y_data['Store_Revenue'], 
                -y_data['Store_COGS'], 
                -y_data['Store_Labor'], 
                -y_data['Store_Ops_Ex'], 
                -y_data['Store_Rent_Ex'], 
                -y_data['Capex'], 
                None, 
                y_data['Prop_Net'],
                None 
            ],
            connector = {"line":{"color":"rgb(63, 63, 63)"}},
        ))
        
        fig_water.update_layout(
                title = f"Year {water_year} Profit Flow",
                showlegend = False,
                height=400
        )
        st.plotly_chart(fig_water, width="stretch", key="chart_waterfall_interactive")


            
        st.subheader(f"{time_horizon}-Year Consolidated Projection")
        fig_owner = go.Figure()
        # Bar for periodic flow
        fig_owner.add_trace(go.Bar(x=x_axis, y=df_view['Owner_Cash_Flow'], name='Periodic CF', marker_color='lightgreen'))
        # Line for cumulative
        fig_owner.add_trace(go.Scatter(x=x_axis, y=df_view['Owner_Cum'], mode='lines', name='Cumulative', line=dict(color='darkgreen', width=3), yaxis='y2'))
        
        # Add Vertical Lines for Events
        if model_events:
            for e in model_events:
                if e.is_active:
                    # Find x-location. 
                    # If Monthly: Month (e.start_month) -> "Jan 20xx" ? x_axis is Month (1-120).
                    # If Annual: Year (e.start_month // 12 + 1) -> x_axis is Year (1-10).
                    # We need to map approx location.
                    
                    x_loc = None
                    if aggregation == "Monthly":
                        if e.start_month <= len(x_axis):
                            x_loc = e.start_month 
                    elif aggregation == "Annual":
                        y_start = (e.start_month - 1) // 12 + 1
                        if y_start <= time_horizon:
                            x_loc = y_start
                    elif aggregation == "Quarterly":
                         # Quarter index (1-40)
                         q_start = (e.start_month - 1) // 3 + 1
                         # x_axis is "Q{abs_quarter}" ? No, x_axis is "Q1", "Q2" .. logic in line 60.
                         # Line 60: x_axis = df_view['Abs_Quarter'].apply(lambda x: f"Q{x}")
                         # Actually Abs_Quarter is int.
                         # Wait, df_view is aggregated. len(df_view) should match len(x_axis).
                         # We need to find the index where 'Abs_Quarter' == q_start
                         if q_start in df_view['Abs_Quarter'].values:
                             x_loc = f"Q{q_start}" 

                    if x_loc:
                        fig_owner.add_vline(x=x_loc, line_width=1, line_dash="dash", line_color="red", opacity=0.5)
                        fig_owner.add_annotation(x=x_loc, y=0, text=e.name, showarrow=False, yref='paper', yanchor='bottom', textangle=-90, font=dict(color="red"))
        
        fig_owner.update_layout(
            yaxis=dict(title="Periodic Cash Flow"),
            yaxis2=dict(title="Cumulative Cash Flow", overlaying='y', side='right'),
            title=f"Owner Cash Flow: Periodic vs Cumulative ({aggregation})",
            hovermode="x unified"
        )
        st.plotly_chart(fig_owner, width="stretch", key="chart_owner_cf")
        
        # --- METRIC EXPLORER ---
        st.subheader("Interactive Metric Explorer")
        st.caption("Select any financial metrics to visualize trends and event correlations.")
        
        # Get all valid numeric columns (excluding metadata)
        all_numeric = [c for c in df_view.columns if c not in ['Year', 'Month', 'Quarter', 'Project_Year', 'Abs_Quarter', 'Display_Date']]
        default_selections = ['Store_Revenue', 'Store_Net']
        
        selected_metrics = st.multiselect("Select Metrics", all_numeric, default=[c for c in default_selections if c in all_numeric])
        
        if selected_metrics:
            fig_explore = go.Figure()
            
            for metric in selected_metrics:
                fig_explore.add_trace(go.Scatter(
                    x=x_axis, 
                    y=df_view[metric], 
                    mode='lines+markers', 
                    name=metric
                ))

            # --- Event Overlay (Reused Logic) ---
            if model_events:
                 for e in model_events:
                    if e.is_active:
                        # Logic matched to Owner Chart above
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
                            fig_explore.add_vline(x=x_loc, line_width=1, line_dash="dash", line_color="orange", opacity=0.5)
                            # Only add annotation if it's the first trace to avoid clutter? Or just add it.
                            # Standard plotly handles annotation overlap poorly, but vertical text is okay.
                            fig_explore.add_annotation(
                                x=x_loc, y=0, text=e.name, 
                                showarrow=False, yref='paper', yanchor='bottom', 
                                textangle=-90, font=dict(color="orange")
                            )

            fig_explore.update_layout(
                title="Metric Trends & Event Impact",
                hovermode="x unified",
                yaxis_title="Amount ($)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_explore, width="stretch", key="chart_explorer")


        # --- NEW VISUALIZATIONS ---
        
        # 1. Expense Breakdown (Stacked)
        st.subheader("Cost Structure Analysis")
        c_exp, c_marg = st.columns(2)
        
        with c_exp:
            st.caption("Expense Breakdown by Category")
            fig_stack = go.Figure()
            # Stacks
            fig_stack.add_trace(go.Bar(x=x_axis, y=df_view['Store_COGS'], name='COGS'))
            fig_stack.add_trace(go.Bar(x=x_axis, y=df_view['Store_Labor'], name='Labor'))
            fig_stack.add_trace(go.Bar(x=x_axis, y=df_view['Store_Rent_Ex'], name='Rent'))
            fig_stack.add_trace(go.Bar(x=x_axis, y=df_view['Store_Ops_Ex'], name='Ops & Fixed'))
            fig_stack.add_trace(go.Bar(x=x_axis, y=df_view['Prop_Debt'], name='Debt Service (Prop)'))
            
            fig_stack.update_layout(barmode='stack', legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig_stack, width="stretch", key="chart_expense_stack")
            
        with c_marg:
            st.caption("Profit Margin Trends")
            # Calculate Margin %
            # Avoid div by zero
            df_view['Net_Margin_Pct'] = (df_view['Store_Net'] / df_view['Store_Revenue'].replace(0, 1)) * 100.0
            
            fig_marg = go.Figure()
            fig_marg.add_trace(go.Scatter(x=x_axis, y=df_view['Net_Margin_Pct'], mode='lines+markers', name='Net Margin %', line=dict(color='purple', width=3)))
            
            # Add Prop DSCR if applicable
            # DSCR = NOI / Debt
            # Prop NOI = Prop Income - Prop Ops. Prop Net = NOI - Debt. So NOI = Prop Net + Debt.
            # Actually Prop Net in model includes debt deduction.
            if df_view['Prop_Debt'].sum() > 0:
                 df_view['Prop_NOI'] = df_view['Prop_Net'] + df_view['Prop_Debt']
                 df_view['DSCR'] = df_view['Prop_NOI'] / df_view['Prop_Debt'].replace(0, 1)
                 fig_marg.add_trace(go.Scatter(x=x_axis, y=df_view['DSCR'], mode='lines', name='Prop DSCR (x)', yaxis='y2', line=dict(dash='dot', color='orange')))
            
            fig_marg.update_layout(
                yaxis=dict(title="Net Margin %"),
                yaxis2=dict(title="DSCR (x)", overlaying='y', side='right'),
                hovermode="x unified",
                legend=dict(orientation="h", y=-0.2)
            )
            st.plotly_chart(fig_marg, width="stretch", key="chart_margin_trend")



    else:
        # Separated View
        st.header(f"Entity Breakdown ({time_horizon}-Year)")
        
        col_store, col_prop = st.columns(2)
        
        store_net_total = df_view['Store_Net'].sum()
        prop_net_total = df_view['Prop_Net'].sum()
        
        with col_store:
            st.subheader("🏬 General Store (OpCo)")
            st.metric(f"Total Net Cash ({time_horizon}y)", f"${store_net_total:,.0f}")
            
            fig_store = go.Figure()
            fig_store.add_trace(go.Bar(x=x_axis, y=df_view['Store_Net'], name='Store Net', marker_color='blue'))
            st.plotly_chart(fig_store, width="stretch", key="chart_store")
            
        with col_prop:
            st.subheader("🏢 Property (Holding Co)")
            st.metric(f"Total Net Cash ({time_horizon}y)", f"${prop_net_total:,.0f}")
            
            fig_prop = go.Figure()
            fig_prop.add_trace(go.Bar(x=x_axis, y=df_view['Prop_Net'], name='Prop Net', marker_color='orange'))
            st.plotly_chart(fig_prop, width="stretch", key="chart_prop")

        st.subheader(f"{time_horizon}-Year Entity Cumulative Growth")
        fig_cum_split = go.Figure()
        fig_cum_split.add_trace(go.Scatter(x=x_axis, y=df_view['Store_Cum'], name='Store Cumulative', line=dict(color='blue')))
        fig_cum_split.add_trace(go.Scatter(x=x_axis, y=df_view['Prop_Cum'], name='Prop Cumulative', line=dict(color='orange')))
        st.plotly_chart(fig_cum_split, width="stretch")

    # --- AI Consultant ---
    st.markdown("---")
    st.subheader("Ask the CFO (AI Consultant)")

    with st.expander("AI Financial Analyst", expanded=True):
        # AI Config Section (Relocated)
        c_ai_conf1, c_ai_conf2, c_ai_conf3 = st.columns([1, 2, 1])
        
        with c_ai_conf1:
            ai_provider = st.selectbox("AI Provider", ["Google (Gemini)", "OpenAI", "Anthropic"], index=0, key="dash_ai_provider")
        
        with c_ai_conf2:
             # Match keys to what logic likely expects or just handle locally
            if ai_provider == "Google (Gemini)":
                user_api_key = st.text_input("Gemini API Key", type="password", key="dash_google_key", help="Leave blank if using Env Var")
                ai_model = "gemini-2.0-flash-exp"
            elif ai_provider == "OpenAI":
                user_api_key = st.text_input("OpenAI API Key", type="password", key="dash_openai_key")
                ai_model = "gpt-4o"
            else:
                user_api_key = st.text_input("Anthropic API Key", type="password", key="dash_anthropic_key")
                ai_model = "claude-3-5-sonnet-20240620"
        
        with c_ai_conf3:
             # Simplified model selection or keep robust? Let's keep it simple for dashboard space
             st.caption(f"Model: {ai_model}")
             
        ai_config = {
            "provider": ai_provider,
            "api_key": user_api_key,
            "model_id": ai_model
        }

        user_q = st.text_area("Ask a question about your scenario:", height=70)
        
        if st.button("Analyze Scenario"):
            if not user_q:
                st.warning("Please type a question.")
            else:
                with st.spinner("Analyzing financial data..."):
                    # Prepare Context
                    context = {
                        "summary": inputs_summary,
                        "data_head": df_projection.head(12).to_dict(), # First year monthly
                        "totals": df_projection[['Store_Revenue', 'Store_Net', 'Prop_Net', 'Owner_Cash_Flow']].sum().to_dict(),
                        "events": [e.__dict__ for e in model_events if e.is_active]
                    }
                    
                    response = ask_ai(ai_config, context, user_q)
                    st.info(response)
