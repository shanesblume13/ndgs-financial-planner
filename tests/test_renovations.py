
from model import FinancialModel
from datetime import date

# Mock config
config = {
    'seasonality': [0.8, 1.0, 1.3, 1.1],
    'revenue_growth_rate': 3.5,
    'expense_growth_rate': 2.5,
    'wage_growth_rate': 3.0,
    'rent_escalation_rate': 4.0,
    'base_revenue': 425000.0 / 12,
    'gross_margin_pct': 30.0,
    'operating_hours': 14,
    'manager_weekly_hours': 40,
    'manager_wage_hourly': 20,
    'hourly_wage': 12,
    'avg_staff': 1.0,
    'utilities': 1200,
    'insurance': 400,
    'maintenance': 300,
    'marketing': 200,
    'professional_fees': 150,
    'loan_amount': 320000,
    'interest_rate': 8.0,
    'amortization_years': 25,
    'initial_inventory': 30000,
    'initial_renovations': 20000, # KEY TEST INPUT
    'initial_equity': 150000,
    'intangible_assets': 150000,
    'initial_property_value': 250000,
    'closing_costs': 10000,
    'commercial_rent_income': 1500,
    'residential_rent_income': 1550,
    'property_tax_annual': 6000,
    'property_appreciation_rate': 2.0
}

print("--- TESTING MODEL INITIALIZATION ---")
model = FinancialModel(**config)
df = model.calculate_projection(date(2025, 1, 1), 12)

# Check Cash Balance Month 1
# Sources: Equity(150k) + Loan(320k) = 470k
# Uses: Prop(250k) + Intang(150k) + Inv(30k) + Reno(20k) + Close(10k) = 460k
# Expected Start Cash: 10k
# Month 1 adds OCF.

# Let's check the first row's cash balance logic implicitly.
# Base Cash = 10,000.
# + Owner_Cash_Flow (Month 1).

first_cf = df.iloc[0]['Owner_Cash_Flow']
first_bal = df.iloc[0]['Cash_Balance']
derived_start_cash = first_bal - first_cf

print(f"Sources: {150000 + 320000}")
print(f"Uses: {250000 + 150000 + 30000 + 20000 + 10000}")
print(f"Expected Start Cash: {470000 - 460000}")
print(f"Actual Start Cash (Derived): {derived_start_cash}")

if abs(derived_start_cash - 10000) < 1.0:
    print("✅ SUCCESS: Initial Renovations correctly deducted from Starting Cash.")
else:
    print(f"❌ FAILURE: Expected 10000, got {derived_start_cash}")

# Check Asset Value (Cumulative Capex)
# Should start with Inventory(30k) + Reno(20k) = 50k.
# Plus any month 1 capex (assumed 0).
first_capex_cum = df.iloc[0]['Cum_Capex']
print(f"Cumulative Capex (Month 1): {first_capex_cum}")

if abs(first_capex_cum - 50000) < 1.0:
    print("✅ SUCCESS: Initial Renovations capitalized into Cumulative Capex.")
else:
    print(f"❌ FAILURE: Expected 50000, got {first_capex_cum}")
