from dataclasses import dataclass, field
from typing import List, Dict
import pandas as pd
import numpy as np
from datetime import date
from dateutil.relativedelta import relativedelta

# --- Constants ---
# Updated Base Revenue to align with $425k/yr legacy pro forma
BASE_REVENUE_MONTHLY = 425000.0 / 12.0
BASE_COGS_PCT = 0.70
DAYS_IN_MONTH = 30.5

@dataclass
class BusinessEvent:
    name: str
    start_month: int
    end_month: int = 120
    frequency: str = "One-time" # "One-time", "Monthly", "Quarterly", "Annually"
    impact_target: str = "Revenue" # "Revenue", "COGS", "Labor", "Ops (Fixed)", "Rent", "Capex"
    pct_basis: str = "Revenue" # "Revenue", "COGS", "Labor", "Ops (Fixed)", "Rent", "Capex", "NOI"
    value_type: str = "Fixed Amount ($)" # "Fixed Amount ($)", "Percentage (%)"
    value: float = 0.0
    affected_entity: str = "Store" # "Store", "Property", "Both"
    description: str = ""
    is_active: bool = True

def calculate_monthly_payment(principal, annual_rate, years):
    if principal <= 0: return 0.0
    if annual_rate <= 0: return principal / (years * 12)
    r = (annual_rate / 100) / 12
    n = years * 12
    return principal * (r * (1 + r)**n) / ((1 + r)**n - 1)

@dataclass
class FinancialModel:
    # --- Inputs ---
    # Global Assumptions
    seasonality: List[float]  
    revenue_growth_rate: float 
    expense_growth_rate: float
    wage_growth_rate: float # New: Specific for Labor
    rent_escalation_rate: float # New: Specific for Commercial Rent
    
    # Base Operations
    base_revenue: float
    base_cogs_pct: float
    operating_hours: int
    
    # Staffing
    manager_weekly_hours: float
    manager_wage_hourly: float
    hourly_wage: float
    avg_staff: float

    # Fixed Expenses
    utilities: float
    insurance: float
    maintenance: float
    marketing: float
    professional_fees: float

    # Acquisition
    loan_amount: float
    interest_rate: float
    amortization_years: int
    initial_capex: float # New field
    commercial_rent_income: float
    residential_rent_income: float
    
    
    
    # Dynamic Events
    events: List[BusinessEvent] = field(default_factory=list)

    def calculate_projection(self, start_date: date, months=120) -> pd.DataFrame:
        """
        Generates a 120-month (10-year) projection dataframe.
        """
        projection = []
        
        # Initial Calculations
        monthly_debt_service = calculate_monthly_payment(
            self.loan_amount, self.interest_rate, self.amortization_years
        )
        
        # Initial Capex
        initial_capex_cost = self.initial_capex

        cumulative_cash_owner = -initial_capex_cost
        cumulative_cash_store = -initial_capex_cost
        cumulative_cash_prop = 0.0
        

        for m in range(1, months + 1):
            # Calendar Calculations
            current_date = start_date + relativedelta(months=m-1)
            cal_year = current_date.year
            cal_month = current_date.month
            cal_quarter_idx = (cal_month - 1) // 3 # 0-3 index
            
            # Growth Factors (Compounded Annually based on PROJECT year index)
            # We keep growth tied to project longevity (Year 1 vs Year 2 of ownership), not calendar year.
            project_year_idx = (m - 1) // 12
            
            # --- Growth Factors ---
            rev_growth_factor = (1 + self.revenue_growth_rate / 100.0) ** project_year_idx
            exp_growth_factor = (1 + self.expense_growth_rate / 100.0) ** project_year_idx
            wage_growth_factor = (1 + self.wage_growth_rate / 100.0) ** project_year_idx
            rent_growth_factor = (1 + self.rent_escalation_rate / 100.0) ** project_year_idx
            
            # Use Calendar Seasonality
            seasonality_factor = self.seasonality[cal_quarter_idx]

            # --- STORE OPERATION ---
            # 1. Revenue
            monthly_base_rev = self.base_revenue * rev_growth_factor * seasonality_factor
            
            # 2. COGS (Base)
            cogs_base_amt = (self.base_revenue * self.base_cogs_pct) * rev_growth_factor * seasonality_factor
            
            # 3. Labor (Base)
            # Manager Cost
            current_manager_wage = self.manager_wage_hourly * wage_growth_factor
            manager_hours_mo = self.manager_weekly_hours * 52.0 / 12.0
            manager_mo_cost = current_manager_wage * manager_hours_mo
            
            # Hourly Staff Cost (With Offset)
            current_hourly_wage = self.hourly_wage * wage_growth_factor
            
            # Total Man-Hours Required
            total_required_hours = self.avg_staff * self.operating_hours * DAYS_IN_MONTH
            
            # Offset Logic: Subtract Manager Hours from Required Hours
            # Assuming Manager counts as 1.0 staff when on floor
            required_hourly_staff_hours = max(0.0, total_required_hours - manager_hours_mo)
            
            staff_cost_mo = current_hourly_wage * required_hourly_staff_hours
            
            # Apply Seasonality to Hourly Staff only (Managers are usually fixed/stable presence)
            labor_seasonality = 1 + (seasonality_factor - 1) * 0.5
            store_labor = manager_mo_cost + (staff_cost_mo * labor_seasonality)

            # 4. Store Ops Expenses (Base)
            # 4. Store Ops Expenses (Detailed)
            ex_util = self.utilities * exp_growth_factor
            ex_ins = self.insurance * exp_growth_factor
            ex_maint = self.maintenance * exp_growth_factor
            ex_mktg = self.marketing * exp_growth_factor
            ex_prof = self.professional_fees * exp_growth_factor
            
            store_ops_expenses = ex_util + ex_ins + ex_maint + ex_mktg + ex_prof
            
            # 5. Rent (Base)
            store_rent_expense = self.commercial_rent_income * rent_growth_factor

            # --- DYNAMIC EVENTS APPLICATION ---
            event_rev_impact = 0.0
            event_cogs_impact = 0.0
            event_labor_impact = 0.0
            event_ops_impact = 0.0
            event_rent_impact = 0.0
            event_capex_store = 0.0
            event_capex_prop = 0.0
            event_prop_ops_impact = 0.0
            
            # Track individual event impacts for the dataframe
            monthly_event_breakdown = {}

            for e in self.events:
                # Initialize column with 0 for every event to ensure consistent schema
                if f"Event: {e.name}" not in monthly_event_breakdown:
                     monthly_event_breakdown[f"Event: {e.name}"] = 0.0

                # 0. Active Check
                if not e.is_active:
                    continue

                # 1. Time Window Check
                if not (e.start_month <= m <= e.end_month):
                    continue
                
                # 2. Frequency Check
                applies = False
                month_delta = m - e.start_month
                if e.frequency == "One-time":
                    if m == e.start_month: applies = True
                elif e.frequency == "Monthly":
                    applies = True
                elif e.frequency == "Quarterly":
                    if month_delta % 3 == 0: applies = True
                elif e.frequency == "Annually":
                    if month_delta % 12 == 0: applies = True
                
                if not applies: continue

                # 3. Calculate Value
                val = 0.0
                model_base_val = 0.0
                
                if e.value_type == "Fixed Amount ($)":
                    val = e.value
                elif "Percent" in e.value_type or "%" in e.value_type: # Handle "Percentage (%)" or legacy strings
                    # Detemine Basis
                    # Check explicit basis first
                    basis_to_use = e.pct_basis
                    
                    # Fallback for legacy "Value Type" strings that were like "% of Revenue"
                    if "Revenue" in e.value_type: basis_to_use = "Revenue"
                    elif "COGS" in e.value_type: basis_to_use = "COGS"
                    elif "Ops" in e.value_type: basis_to_use = "Ops (Fixed)"
                    elif "NOI" in e.value_type: basis_to_use = "NOI"
                    elif "Previous Quarter" in e.value_type: basis_to_use = "NOI"

                    if basis_to_use == "Revenue":
                        model_base_val = monthly_base_rev
                    elif basis_to_use == "COGS":
                        model_base_val = cogs_base_amt
                    elif basis_to_use == "Labor":
                        model_base_val = store_labor
                    elif basis_to_use == "Ops (Fixed)":
                        model_base_val = store_ops_expenses
                    elif basis_to_use == "Rent":
                        model_base_val = store_rent_expense
                    elif basis_to_use == "Capex":
                        model_base_val = 0.0 
                    elif basis_to_use == "NOI":
                         # Determine lookback window based on frequency
                         window = 1
                         if e.frequency == "Quarterly": window = 3
                         elif e.frequency == "Annually": window = 12
                         
                         if m > window:
                            noi_sum = 0.0
                            for i in range(1, window + 1):
                                 if (m - i - 1) >= 0:
                                     prev_data = projection[m - i - 1]
                                     noi_sum += prev_data.get("Store_NOI_Pre", 0.0)
                            model_base_val = noi_sum if noi_sum > 0 else 0.0

                    val = model_base_val * (e.value / 100.0)
                
                # Store breakdown
                monthly_event_breakdown[f"Event: {e.name}"] += val

                # 4. Apply to Target
                if e.impact_target == "Revenue":
                    event_rev_impact += val
                elif e.impact_target == "COGS":
                    event_cogs_impact += val
                elif e.impact_target == "Labor":
                    event_labor_impact += val
                elif e.impact_target == "Ops (Fixed)":
                    if e.affected_entity == "Property": 
                        event_prop_ops_impact += val
                    else:
                        event_ops_impact += val
                elif e.impact_target == "Rent":
                    event_rent_impact += val
                elif e.impact_target == "Capex":
                    if e.affected_entity == "Property": event_capex_prop += val
                    else: event_capex_store += val

            # Apply Accumulated Impacts
            # Revenue
            store_total_revenue = monthly_base_rev + event_rev_impact

            # Expenses
            store_cogs = cogs_base_amt + event_cogs_impact
            store_labor += event_labor_impact
            store_ops_expenses += event_ops_impact
            store_rent_expense += event_rent_impact
            
            # Prop Ops
            prop_ops_expenses = event_prop_ops_impact
            
            # --- PRE-BONUS NOI ---
            store_total_outflow_pre_bonus = store_cogs + store_labor + store_ops_expenses + store_rent_expense
            store_noi_pre_bonus = store_total_revenue - store_total_outflow_pre_bonus
            
            # --- INCENTIVE CALCULATION ---
            
            bonus_payout = 0.0

            # Final Store Net
            store_net_cash = store_noi_pre_bonus - bonus_payout - event_capex_store

            # --- PROPERTY OPERATION ---
            # Income
            prop_comm_rent = store_rent_expense # Linked
            prop_res_rent = self.residential_rent_income * rent_growth_factor 
            
            prop_total_income = prop_comm_rent + prop_res_rent
            
            # Expenses
            # Debt Service
            prop_debt = monthly_debt_service
            
            # Prop Ops (calculated above from events)
            
            prop_net_cash = prop_total_income - prop_debt - prop_ops_expenses - event_capex_prop

            # --- CONSOLIDATED OWNER VIEW ---
            consolidated_cash = store_net_cash + prop_net_cash 
            
            cumulative_cash_store += store_net_cash
            cumulative_cash_prop += prop_net_cash
            cumulative_cash_owner += consolidated_cash
            
            # Net Event Impact (Cash basis)
            # Revenue Impact - (Expense Impacts) - (Capex)
            total_event_expense_impact = event_cogs_impact + event_labor_impact + event_ops_impact + event_rent_impact + event_prop_ops_impact
            total_event_capex = event_capex_store + event_capex_prop
            net_event_impact = event_rev_impact - total_event_expense_impact - total_event_capex

            row_data = {
                "Year": cal_year,
                "Month": cal_month,
                "Quarter": cal_quarter_idx + 1,
                "Project_Month": m,
                "Project_Year": project_year_idx + 1,
                
                "Store_Revenue": store_total_revenue,
                "Store_COGS": -store_cogs,
                "Store_Labor": -store_labor,
                "Store_Bonus": -bonus_payout,
                "Store_Ops_Ex": -store_ops_expenses,
                "Ex_Util": -ex_util,
                "Ex_Ins": -ex_ins,
                "Ex_Maint": -ex_maint,
                "Ex_Mktg": -ex_mktg,
                "Ex_Prof": -ex_prof,
                "Store_Rent_Ex": -store_rent_expense,
                
                "Prop_Debt": -prop_debt,
                
                "Store_Net": store_net_cash,
                "Prop_Net": prop_net_cash,
                
                "Store_Cum": cumulative_cash_store,
                "Prop_Cum": cumulative_cash_prop,
                "Owner_Cum": cumulative_cash_owner,
                "Owner_Cash_Flow": consolidated_cash,
                
                "Capex": -(initial_capex_cost if m == 1 else total_event_capex),
                "Net_Event_Impact": net_event_impact,
                "Store_NOI_Pre": store_noi_pre_bonus
            }
            
            # Merge event columns
            row_data.update(monthly_event_breakdown)
            
            projection.append(row_data)
            
        return pd.DataFrame(projection)
