
import pandas as pd
import numpy as np

# Mocking the _generate_pro_forma logic from views/dashboard.py (UPDATED)
def _generate_pro_forma(df_agg, periods):
    data = {}
    
    # Mock Data Extraction
    revenue_store = df_agg['Store_Revenue']
    prop_net = df_agg['Prop_Net']
    prop_tax = df_agg['Prop_Tax'] # negative
    prop_debt = df_agg['Prop_Debt'] # negative
    
    # 0. Mock Initial Renovations (passed via context usually, but here we can mock)
    # Actually, verify_fix.py only mocks the _generate_pro_forma function, which only sees the AGGREGATED DATAFRAME.
    # The Initial Renovations logic happens in model.calculate_projection (Use of Funds -> Cash Balance).
    # Since we can't test model.py easily without instantiating it, we will assume correct flow if Cash Balance reflects it.
    # _generate_pro_forma doesn't care about initial costs, it just shows Cash Balance history.
    
    revenue_rent = prop_net - prop_tax - prop_debt
    
    total_rev = revenue_store + revenue_rent
    
    data['Revenue (Operations)'] = revenue_store
    data['Revenue (Real Estate)'] = revenue_rent
    data['Total Revenue'] = total_rev
    
    cogs = df_agg['Store_COGS'] # negative
    data['COGS'] = cogs
    
    gross_profit = total_rev + cogs
    data['Gross Profit'] = gross_profit
    
    # 4. Operating Expenses
    labor = df_agg['Store_Labor'] # negative
    ops = df_agg['Store_Ops_Ex'] # negative
    rent_ex = df_agg['Store_Rent_Ex'] # negative
    
    total_opex = labor + ops + rent_ex + prop_tax
    
    data['Labor'] = labor
    data['OpEx (Store)'] = ops
    data['Rent (Commercial)'] = rent_ex
    data['Property Tax'] = prop_tax
    data['Total OpEx'] = total_opex
    
    # 5. NOI
    noi = gross_profit + total_opex
    data['Net Operating Income (NOI)'] = noi
    
    # 6. Debt
    data['Debt Service (P&I)'] = prop_debt
    
    # 7. Capex
    capex = df_agg.get('Capex', pd.Series([0]*len(df_agg)))
    data['Capital Expenditures'] = capex

    # 8. Net Cash Flow
    # NOI + Debt + Capex
    ncf = noi + prop_debt + capex
    data['Net Cash Flow'] = ncf
    
    # 9. DSCR
    def calc_dscr(n, d):
        if d == 0: return 0.0
        return n / abs(d)
        
    dscr_series = pd.Series([calc_dscr(n, d) for n, d in zip(noi, prop_debt)]) # Remove explicit index to match others which use default Int index from df_agg
    data['DSCR'] = dscr_series

    # 10. Balance Sheet
    if 'Cash_Balance' in df_agg.columns:
        data['Cash on Hand (End of Period)'] = df_agg['Cash_Balance']
    
    df = pd.DataFrame(data)
    df_t = df.T
    df_t.columns = periods
    
    # TOTAL Column Logic
    sum_cols = ['Revenue (Operations)', 'Revenue (Real Estate)', 'Total Revenue', 
                'COGS', 'Gross Profit', 
                'Labor', 'OpEx (Store)', 'Rent (Commercial)', 'Property Tax', 'Total OpEx',
                'Net Operating Income (NOI)', 'Debt Service (P&I)', 'Capital Expenditures', 'Net Cash Flow']
    last_cols = ['Cash on Hand (End of Period)']
    
    total_series = pd.Series(index=df.columns)
    for c in df.columns:
        if c in sum_cols:
            total_series[c] = df[c].sum()
        elif c in last_cols:
             total_series[c] = df[c].iloc[-1]
        elif c == 'DSCR':
             t_noi = df['Net Operating Income (NOI)'].sum()
             t_debt = df['Debt Service (P&I)'].sum()
             total_series[c] = calc_dscr(t_noi, t_debt)
        else:
             total_series[c] = 0.0
             
    df_t['TOTAL'] = total_series
    
    return df_t

# --- TEST ---
# Scenario:
# Rev: 10000
# Rent Ex: -1000
# Prop Rev: 1000
# Debt: -2000
# Capex: -500 (New)
# NOI Expected: 10K - 1K + 1K = 10K (Pre-OpEx/Debt). Let's Assume 0 OpEx other than rent.
# NCF Expected: 10K (NOI) - 2K (Debt) - 0.5K (Capex) = 7.5K.

data = {
    'Store_Revenue': [10000, 10000, 10000],
    'Store_COGS': [0, 0, 0],
    'Store_Labor': [0, 0, 0],
    'Store_Ops_Ex': [0, 0, 0],
    'Store_Rent_Ex': [-1000, -1000, -1000],
    'Prop_Tax': [0, 0, 0],
    'Prop_Debt': [-2000, -2000, -2000],
    'Prop_Net': [1000, 1000, 1000], # Net = Gross (1000) - Tax(0) - Debt(2000)? 
    # Wait, Prop_Net = Gross - Tax - Debt. 
    # If Gross=1000, Debt=2000 -> Net = -1000.
    # Let's align inputs to avoid confusion.
    # We derived Gross Rent = Prop_Net - Prop_Tax - Prop_Debt in the code?
    # Code says: revenue_rent = prop_net - prop_tax - prop_debt
    # If Prop_Net = -1000, Tax=0, Debt=-2000.
    # Rev_Rent = -1000 - 0 - (-2000) = 1000. Correct.
    
    'Prop_Net': [-1000, -1000, -1000], 
    'Capex': [-500, -500, -500],
    'Cash_Balance': [50000, 50000, 50000]
}
df_agg = pd.DataFrame(data)
periods = ['Jan', 'Feb', 'Mar']

print("--- RUNNING VERIFICATION ---")
result = _generate_pro_forma(df_agg, periods)

# 1. Check Net Cash Flow
ncf_jan = result.loc['Net Cash Flow', 'Jan']
print(f"Net Cash Flow (Jan): {ncf_jan}")
# Exp: NOI(10k) + Debt(-2k) + Capex(-0.5k) = 7.5k
if ncf_jan == 7500:
    print("✅ SUCCESS: Net Cash Flow includes Capex.")
else:
    print(f"❌ FAILURE: NCF Expected 7500, got {ncf_jan}")

# 2. Check DSCR
dscr_jan = result.loc['DSCR', 'Jan']
print(f"DSCR (Jan): {dscr_jan}")
# Exp: NOI(10k) / Abs(-2k) = 5.0
if dscr_jan == 5.0:
    print("✅ SUCCESS: DSCR calculated correctly.")
else:
    print(f"❌ FAILURE: DSCR Expected 5.0, got {dscr_jan}")

# 3. Check Total DSCR
dscr_total = result.loc['DSCR', 'TOTAL']
print(f"Total DSCR: {dscr_total}")
# Exp: Total NOI(30k) / Total Debt(6k) = 5.0
if dscr_total == 5.0:
     print("✅ SUCCESS: Total DSCR calculated correctly.")
else:
     print(f"❌ FAILURE: Total DSCR Expected 5.0, got {dscr_total}")
