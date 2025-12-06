from dataclasses import dataclass, field
from typing import List, Dict
import pandas as pd
import numpy as np

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
    value_type: str = "Fixed Amount ($)" # "Fixed Amount ($)", "% of Revenue", "% of Cost", "% of Net (NOI) - Prev Quarter"
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
    manager_salary: float
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
    commercial_rent_income: float
    residential_rent_income: float
    

    
    # Dynamic Events
    events: List[BusinessEvent] = field(default_factory=list)

    def calculate_projection(self, months=120) -> pd.DataFrame:
        """
        Generates a 120-month (10-year) projection dataframe.
        """
        projection = []
        
        # Initial Calculations
        monthly_debt_service = calculate_monthly_payment(
            self.loan_amount, self.interest_rate, self.amortization_years
        )
        
        # Initial Capex
        initial_capex = 0.0

        cumulative_cash_owner = -initial_capex
        cumulative_cash_store = -initial_capex 
        cumulative_cash_prop = 0.0
        


        for m in range(1, months + 1):
            year_idx = (m - 1) // 12
            month_in_year = (m - 1) % 12
            quarter_idx = month_in_year // 3
            
            # --- Growth Factors ---
            rev_growth_factor = (1 + self.revenue_growth_rate / 100.0) ** year_idx
            exp_growth_factor = (1 + self.expense_growth_rate / 100.0) ** year_idx
            wage_growth_factor = (1 + self.wage_growth_rate / 100.0) ** year_idx
            rent_growth_factor = (1 + self.rent_escalation_rate / 100.0) ** year_idx
            
            seasonality_factor = self.seasonality[quarter_idx]

            # --- STORE OPERATION ---
            # 1. Revenue
            monthly_base_rev = self.base_revenue * rev_growth_factor * seasonality_factor
            
            # 2. COGS (Base)
            cogs_base_amt = (self.base_revenue * self.base_cogs_pct) * rev_growth_factor * seasonality_factor
            
            # 3. Labor (Base)
            manager_mo = (self.manager_salary / 12.0) * wage_growth_factor
            current_hourly_wage = self.hourly_wage * wage_growth_factor
            staff_base_mo = current_hourly_wage * self.avg_staff * self.operating_hours * DAYS_IN_MONTH
            labor_seasonality = 1 + (seasonality_factor - 1) * 0.5
            store_labor = manager_mo + (staff_base_mo * labor_seasonality)

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

            for e in self.events:
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
                if e.value_type == "Fixed Amount ($)":
                    val = e.value
                elif e.value_type == "% of Revenue":
                    val = monthly_base_rev * (e.value / 100.0)
                elif e.value_type == "% of COGS":
                    val = cogs_base_amt * (e.value / 100.0)
                elif e.value_type == "% of Ops":
                     val = store_ops_expenses * (e.value / 100.0)
                elif e.value_type == "% of Previous Quarter NOI":
                    # Sum NOI from previous 3 months (m-1, m-2, m-3)
                    # Indices in projection list: m-2, m-3, m-4
                    # Only valid if m > 3
                    if m > 3:
                        prev_q_noi = 0.0
                        for i in range(1, 4):
                             # Check existence
                             if (m - i - 1) >= 0:
                                 prev_data = projection[m - i - 1]
                                 prev_q_noi += prev_data.get("Store_NOI_Pre", 0.0)
                        
                        # Only apply bonus if NOI is positive? Yes, standard practice.
                        if prev_q_noi > 0:
                             val = prev_q_noi * (e.value / 100.0)
                
                # 4. Apply to Target
                # Note: We iterate all events. Order doesn't matter as we base % on Base amounts (safe).
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

            projection.append({
                "Month": m,
                "Year": year_idx + 1, # Reverted to original as current_year was not defined
                "Quarter": quarter_idx + 1, # Reverted to original as current_quarter was not defined
                
                "Store_Revenue": store_total_revenue,
                "Store_COGS": store_cogs,
                "Store_Labor": store_labor,
                "Store_Ops_Ex": store_ops_expenses,
                "Store_Rent_Ex": store_rent_expense,
                
                # Detailed Expenses (Approximate breakdown if needed or just total)
                "Ex_Util": ex_util, # Reverted to original variable names
                "Ex_Ins": ex_ins, # Reverted to original variable names
                "Ex_Maint": ex_maint, # Reverted to original variable names
                "Ex_Mktg": ex_mktg, # Reverted to original variable names
                "Ex_Prof": ex_prof, # Reverted to original variable names
                
                "Store_Bonus": bonus_payout,
                "Capex": event_capex_store + event_capex_prop,
                
                "Store_NOI_Pre": store_noi_pre_bonus, # Stored for lookback
                "Store_Net": store_net_cash,
                
                "Prop_Debt": prop_debt,
                "Prop_Net": prop_net_cash,
                
                "Owner_Cash_Flow": consolidated_cash,
                "Store_Cum": cumulative_cash_store, # Reverted to original
                "Prop_Cum": cumulative_cash_prop, # Reverted to original
                "Owner_Cum": cumulative_cash_owner, # Reverted to original
                
                "Net_Event_Impact": net_event_impact
            })
            
        return pd.DataFrame(projection)

