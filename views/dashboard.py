import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date
from dateutil.relativedelta import relativedelta
from services.ai_service import ask_ai

def render_dashboard(df_projection, model_events, ai_config, inputs_summary, start_date=None):
    
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
    aggregation = c_proj2.selectbox("Aggregation", ["Monthly", "Quarterly", "Annual"], index=2)

    # Filter Data based on controls
    df_view = df_projection[df_projection['Year'] <= time_horizon].copy()

    # Define aggregation dict for all potential columns
    agg_dict = {
        'Year': 'first',
        'Quarter': 'first',
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
        'Owner_Cum': 'last'
    }

    if aggregation == "Quarterly":
        # Group by quarters (custom accumulation)
        df_view['Abs_Quarter'] = ((df_view['Year'] - 1) * 4) + df_view['Quarter']
        df_view = df_view.groupby('Abs_Quarter').agg(agg_dict).reset_index()
        x_axis = df_view['Abs_Quarter'].apply(lambda x: f"Q{x}")
    elif aggregation == "Annual":
        agg_dict.pop('Quarter', None)
        agg_dict.pop('Year', None) # Remove Year from agg since it's the grouper
        df_view = df_view.groupby('Year').agg(agg_dict).reset_index()
        x_axis = df_view['Year']
    else:
        x_axis = df_view['Month']

    # Calculate Total Cash Flow (Global Scope for AI)
    total_cf = df_view['Owner_Cash_Flow'].sum()

    if view_mode == "Consolidated (Owner)":
        # Owner View
        st.header(f"Consolidated Snapshot ({time_horizon}-Year)")
        
        avg_cf_per_period = total_cf / len(df_view)
        
        c1, c2, c3 = st.columns(3)
        c1.metric(f"Total Owner Cash Flow ({time_horizon}y)", f"${total_cf:,.0f}")
        c2.metric(f"Avg Cash Flow (Per {aggregation[:-2]})", f"${avg_cf_per_period:,.0f}")
        
        # Detail Toggle
        show_detail = st.checkbox("Show Detailed Breakdown (P&L)", value=False)

        with st.expander("View Data Detail", expanded=True):
            if show_detail:
                # Detailed Column Order
                # Detailed Column Order & MultiIndex Mapping
                # 1. Prepare Base Data
                cols = [
                    "Year", 
                    # Store Operations Group
                    "Store_Revenue", "Store_COGS", "Store_Labor", "Store_Bonus", "Store_Rent_Ex", "Store_Ops_Ex",
                    # Detailed Expenses Group
                    "Ex_Util", "Ex_Ins", "Ex_Maint", "Ex_Mktg", "Ex_Prof",
                    # Investment
                    "Capex",
                    # Bottom Line
                    "Store_Net", "Prop_Net", "Owner_Cash_Flow"
                ]
                
                df_display = df_view.copy()

                if aggregation == "Monthly":
                    # Calculator helper
                    def get_display_date(m_idx, y_idx):
                        # m_idx is 1-based total month? No, Month column resets?
                        # Wait, df_projection has 'Month' 1-12 usually.
                        # Actually 'Month' is 1-based relative to Year usually?
                        # Let's check model.py logic:
                        # "Month": m (1 to 120)
                        # So 'Month' in input df is Cumulative Month (1-120).
                        # Perfect.
                        if 'Month' in x:
                             # Use cumulative month if available or calculate from Year/Month
                             pass
                             
                    # The 'Month' column in df_display comes from df_view which has 'Month' and 'Year'.
                    # In monthly view, 'Month' is 1-12 relative to year? Or 1-120?
                    # model.py: projection.append({"Month": m, "Year": current_year ...})
                    # m is 1 to 120. So Month is cumulative.
                    
                    df_display["Display_Date"] = df_display.apply(
                        lambda x: (start_date + relativedelta(months=int(x['Month'])-1)).strftime("%b %Y"), 
                        axis=1
                    )
                    cols.insert(1, "Display_Date")
                elif aggregation == "Quarterly":
                    # Quarter is 1-4. Year is 1-10.
                    # We need start of quarter date.
                    # Month index approx: (Year-1)*12 + (Quarter-1)*3
                    df_display["Display_Date"] = df_display.apply(
                        lambda x: (start_date + relativedelta(months=((int(x['Year'])-1)*12 + (int(x['Quarter'])-1)*3))).strftime("Q%q %Y"),
                        axis=1
                    )
                    # Actually strftime %q is not standard.
                    # Let's stick to "Q1 2026"
                    df_display["Display_Date"] = df_display.apply(
                        lambda row: f"Q{int(row['Quarter'])} " + (start_date + relativedelta(years=int(row['Year'])-1)).strftime("%Y"),
                        axis=1
                    )
                    cols.insert(1, "Display_Date")
                else:
                    # Annual
                    pass
                
                # Filter to final list (ensure Display_Date is picked up)
                # But wait, cols has 'Year' at 0.
                # If Monthly: [Year, Display_Date, Store_Rev...] -> (Time, Year), (Time, Date), (Store, Rev) -> Good.
                # If Quarterly: [Year, Display_Date, Store_Rev...] -> Good.
                
                df_display = df_display[cols].copy()
                
                # 2. Rename Columns for Friendliness
                rename_map = {
                    "Year": ("Time", "Year"),
                    "Display_Date": ("Time", "Date"),
                    "Month": ("Time", "Month"),
                    "Quarter": ("Time", "Quarter"),
                    "Store_Revenue": ("Store Operations", "Revenue"),
                    "Store_COGS": ("Store Operations", "COGS"),
                    "Store_Labor": ("Store Operations", "Total Labor"),
                    "Store_Bonus": ("Store Operations", "Manager Bonus"),
                    "Store_Ops_Ex": ("Store Operations", "Total OpEx"),
                    "Ex_Util": ("Detailed Expenses", "Utilities"),
                    "Ex_Ins": ("Detailed Expenses", "Insurance"),
                    "Ex_Maint": ("Detailed Expenses", "Maintenance"),
                    "Ex_Mktg": ("Detailed Expenses", "Marketing"),
                    "Ex_Prof": ("Detailed Expenses", "Professional"),
                    "Store_Rent_Ex": ("Store Operations", "Rent Paid"),
                    "Capex": ("Investment", "Capex"),
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
                # Exclude Time-based columns explicitly in case they are detected as int/float
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
                if aggregation == "Quarterly": cols.insert(2, "Quarter")
                
                st.dataframe(
                    df_view[cols].style.format("${:,.0f}"),
                    width="stretch"
                )

        st.subheader("Visual Explanation: Year 1 Profit Waterfall")
        # Waterfall for Year 1 (Standardized View)
        y1_data = df_projection[df_projection['Year']==1].sum()
        
        fig_water = go.Figure(go.Waterfall(
            name = "20", orientation = "v",
            measure = ["relative", "relative", "relative", "relative", "relative", "relative", "total", "relative", "total"],
            x = ["Revenue", "COGS", "Labor", "Ops", "Rent", "Capex", "Store Net", "+ Prop Net", "Owner CF"],
            textposition = "outside",
            y = [
                y1_data['Store_Revenue'], 
                -y1_data['Store_COGS'], 
                -y1_data['Store_Labor'], 
                -y1_data['Store_Ops_Ex'], 
                -y1_data['Store_Rent_Ex'], 
                -y1_data['Capex'], 
                None, # Store Net Calc
                y1_data['Prop_Net'],
                None  # Owner CF Calc
            ],
            connector = {"line":{"color":"rgb(63, 63, 63)"}},
        ))
        
        fig_water.update_layout(
                title = "Year 1 Profit Flow (Waterfall)",
                showlegend = True
        )
        st.plotly_chart(fig_water, width="stretch")
            
        st.subheader(f"{time_horizon}-Year Consolidated Projection")
        fig_owner = go.Figure()
        # Bar for periodic flow
        fig_owner.add_trace(go.Bar(x=x_axis, y=df_view['Owner_Cash_Flow'], name='Periodic CF', marker_color='lightgreen'))
        # Line for cumulative
        fig_owner.add_trace(go.Scatter(x=x_axis, y=df_view['Owner_Cum'], mode='lines', name='Cumulative', line=dict(color='darkgreen', width=3), yaxis='y2'))
        
        fig_owner.update_layout(
            yaxis=dict(title="Periodic Cash Flow"),
            yaxis2=dict(title="Cumulative Cash Flow", overlaying='y', side='right'),
            title=f"Owner Cash Flow: Periodic vs Cumulative ({aggregation})",
            hovermode="x unified"
        )
        st.plotly_chart(fig_owner, width="stretch")

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

    col_ai_1, col_ai_2 = st.columns([3, 1])

    with col_ai_1:
        user_question = st.text_input("Ask a question about your financial scenario:", placeholder="e.g. Should I increase Commercial Rent to shift profit to the Holding Co?")

    with col_ai_2:
        st.write("") # Spacer
        st.write("") 
        
        # Build Context for AI
        # Need year 1 summary from inputs?
        # Re-calc year 1 summary from projection for accuracy
        df_y1 = df_projection[df_projection['Year'] == 1]
        summary_y1 = {
             "Owner_Cash_Flow": df_y1['Owner_Cash_Flow'].sum(),
             "Store_Net_Income": df_y1['Store_Net'].sum(),
             "Property_Net_Income": df_y1['Prop_Net'].sum()
        }
        
        current_context = {
            "year_1_summary": summary_y1,
            "assumptions": inputs_summary,
            "events": len(model_events)
        }
        
        analysis_prompt = f"""
        Analyze this 10-year projection for a general store:
        - Annual Owner Cash Flow (avg): ${total_cf/time_horizon:,.0f}
        - Total 10y Cash Flow: ${total_cf:,.0f}
        
        Provide 3 strategic recommendations.
        """
        if st.button("Generate AI Executive Summary"):
            with st.spinner("Analyzing financials..."):
                summary_10y = df_projection.groupby('Year')[['Owner_Cash_Flow', 'Store_Net', 'Prop_Net']].sum().to_dict()
                full_context = {
                    "Input_Parameters": current_context,
                    "10_Year_Summary": summary_10y,
                    "Events": [e.__dict__ for e in model_events]
                }
                summary = ask_ai(analysis_prompt, full_context, provider=ai_config['provider'], api_key=ai_config['api_key'], model_id=ai_config['model_id'])
                st.info(summary)

    if user_question:
        with st.spinner(f"Consulting {ai_config['provider']}..."):
            
            # Recalc context again? Or just use what we built.
            df_y1 = df_projection[df_projection['Year'] == 1]
            summary_y1 = {
                 "Owner_Cash_Flow": df_y1['Owner_Cash_Flow'].sum(),
                 "Store_Net_Income": df_y1['Store_Net'].sum(),
                 "Property_Net_Income": df_y1['Prop_Net'].sum()
            }
            context_data = {
                "year_1_summary": summary_y1,
                "assumptions": inputs_summary,
                "events_count": len(model_events)
            }
            
            response = ask_ai(user_question, context_data, provider=ai_config['provider'], api_key=ai_config['api_key'], model_id=ai_config['model_id'])
            st.info(response)
