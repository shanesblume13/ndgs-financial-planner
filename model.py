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
    value_type: str = "Fixed Amount ($)" # "Fixed Amount ($)", "% of Revenue", "% of COGS", "% of Ops"
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
    
    # Incentives (Defaults)
    incentive_pct: float = 0.0 # 0-100
    incentive_metric: str = "None" # "Revenue", "Net (NOI)"
    incentive_freq: str = "Annual" # "Annual", "Quarterly"
    
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
        
        # Incentive Accumulators
        acc_rev_period = 0.0
        acc_noi_period = 0.0

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
            acc_rev_period += store_total_revenue
            acc_noi_period += store_noi_pre_bonus
            
            bonus_payout = 0.0
            payout_due = False
            
            if self.incentive_pct > 0 and self.incentive_metric != "None":
                if self.incentive_freq == "Annual":
                    if month_in_year == 11: # Dec
                        payout_due = True
                elif self.incentive_freq == "Quarterly":
                    if (m % 3) == 0: # Mar, Jun, Sep, Dec
                        payout_due = True
                        
                if payout_due:
                    basis = acc_rev_period if self.incentive_metric == "Revenue" else acc_noi_period
                    # If basis < 0 (negative NOI), assume no bonus? Yes.
                    if basis > 0:
                        bonus_payout = basis * (self.incentive_pct / 100.0)
                    
                    # Reset accumulators after payout period ends
                    acc_rev_period = 0.0
                    acc_noi_period = 0.0

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
            
            projection.append({
                "Month": m,
                "Year": year_idx + 1,
                "Quarter": quarter_idx + 1,
                # Store
                "Store_Revenue": store_total_revenue,
                "Store_COGS": store_cogs,
                "Store_Labor": store_labor + bonus_payout, 
                "Store_Bonus": bonus_payout,
                "Store_Ops_Ex": store_ops_expenses,
                "Ex_Util": ex_util,
                "Ex_Ins": ex_ins,
                "Ex_Maint": ex_maint,
                "Ex_Mktg": ex_mktg,
                "Ex_Prof": ex_prof,
                "Store_Rent_Ex": store_rent_expense,
                "Store_Net": store_net_cash,
                "Store_Cum": cumulative_cash_store,
                # Property
                "Prop_Inc_Comm": prop_comm_rent,
                "Prop_Inc_Res": prop_res_rent,
                "Prop_Debt": prop_debt,
                "Prop_Net": prop_net_cash,
                "Prop_Cum": cumulative_cash_prop,
                # Consolidated
                "Owner_Cash_Flow": consolidated_cash,
                "Owner_Cum": cumulative_cash_owner,
                "Capex": event_capex_store + event_capex_prop
            })
            
        return pd.DataFrame(projection)
