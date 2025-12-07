import unittest
import sys
import os
import datetime
import pandas as pd

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model import FinancialModel, BusinessEvent, calculate_monthly_payment, BASE_REVENUE_MONTHLY

class TestFinancialLogic(unittest.TestCase):

    def setUp(self):
        # Default Inputs for a clean baseline test
        self.default_inputs = {
            "seasonality": [1.0, 1.0, 1.0, 1.0],
            "revenue_growth_rate": 0.0,
            "expense_growth_rate": 0.0,
            "wage_growth_rate": 0.0,
            "rent_escalation_rate": 0.0,
            "base_revenue": 10000.0, # Simple number
            "gross_margin_pct": 50.0, # 50% Margin -> 50% COGS
            "operating_hours": 10,
            "manager_wage_hourly": 20.0, # 20/hr
            "manager_weekly_hours": 10.0, # 10 hrs/week -> ~43.33 hrs/mo -> Cost: 866.66
            "hourly_wage": 10.0,  
            "avg_staff": 1.0, # 10hrs * 10/hr * 30.5 = 3050.0
            "utilities": 100.0,
            "insurance": 100.0,
            "maintenance": 100.0,
            "marketing": 100.0,
            "professional_fees": 100.0,
            # Acquisition
            "loan_amount": 100000.0,
            "interest_rate": 0.0, # Simplify Debt
            "amortization_years": 10,
            "initial_inventory": 0.0,
            "initial_equity": 200000.0,
            
            "intangible_assets": 200000.0,
            "initial_property_value": 100000.0, # Match loan for simplicity in base test
            "closing_costs": 0.0, # Default for tests
            
            "commercial_rent_income": 1000.0,
            "residential_rent_income": 500.0,
            
            "property_tax_annual": 0.0, # Simplify base test
            "property_appreciation_rate": 0.0,
            # Events
            "events": []
        }

    def test_loan_calculation(self):
        # Case 1: 0 Interest
        # 120k principal, 10 years = 1k/mo
        pmt = calculate_monthly_payment(120000, 0, 10)
        self.assertAlmostEqual(pmt, 1000.0, places=2)
        
        # Case 2: Standard Mortgage
        # 100k, 5%, 30 years. 
        # r = 0.0041666. n = 360.
        # P = 100000 * (r(1+r)^n)/((1+r)^n - 1)
        # Online calc suggests ~536.82
        pmt_std = calculate_monthly_payment(100000, 5.0, 30)
        self.assertAlmostEqual(pmt_std, 536.82, places=1)

    def test_base_projection(self):
        """Verify Year 1 Month 1 calculations with no growth/seasonality"""
        model = FinancialModel(**self.default_inputs)
        df = model.calculate_projection(start_date=datetime.date(2024, 1, 1), months=1)
        row = df.iloc[0]
        
        # Revenue: 10,000 (Base)
        self.assertEqual(row['Store_Revenue'], 10000.0)
        
        # COGS: 50% of 10,000 = 5,000 (Negative)
        self.assertEqual(row['Store_COGS'], -5000.0)
        
        # Labor Calculation Update:
        # Manager: 20/hr * 10 hrs/wk * (52/12) = 20 * 43.333 = 866.666
        mgr_monthly_hours = 10.0 * 52.0 / 12.0
        mgr_cost = 20.0 * mgr_monthly_hours
        
        # Staff Requirement: 1.0 (Avg Staff) * 10 (Op Hours) * 30.5 (Days) = 305.0 Hours Total
        total_req_hours = 1.0 * 10 * 30.5
        
        # Offset: 305.0 - 43.333 = 261.666 Hours needed from Hourly Staff
        hourly_needed = total_req_hours - mgr_monthly_hours
        staff_cost = hourly_needed * 10.0
        
        expected_labor = mgr_cost + staff_cost
        
        # Expect Negative
        self.assertAlmostEqual(row['Store_Labor'], -expected_labor, places=2)
        
        # Ops Expenses: 500 (Base fixed) -> Negative
        self.assertEqual(row['Store_Ops_Ex'], -500.0)
        
        # Rent Expense: 1000 -> Negative
        self.assertEqual(row['Store_Rent_Ex'], -1000.0)
        
        # Store Net: 10000 - 5000 - labor - 500 - 1000
        # Formula uses the signed values (Revenue + COGS + ...)? 
        # Model: store_net_cash = store_noi_pre_bonus - bonus - capex
        # store_noi_pre_bonus = store_total_revenue - store_total_outflow
        # store_total_outflow = cogs + labor + ops + rent (all positive magnitudes)
        expected_net_store = 10000.0 - 5000.0 - expected_labor - 500.0 - 1000.0
        self.assertAlmostEqual(row['Store_Net'], expected_net_store, places=2)
        
        # Property Net: Rent(1000) + Res(500) - Debt(100k/10y/0% = 833.33)
        # 1500 - 833.33 = 666.67
        # Debt in output is negative?
        # Row 319: "Prop_Debt": -prop_debt,
        self.assertEqual(row['Prop_Debt'], -1000.0 * (100.0/120.0)) # 833.333
        
        expected_debt = 100000.0 / (10 * 12)
        expected_net_prop = 1500.0 - expected_debt
        self.assertAlmostEqual(row['Prop_Net'], expected_net_prop, places=2)
        
        # Consolidated: StoreNet + PropNet 
        # (-550) + (666.67) = 116.67
        # Also: (StoreRev + ResRent) - (StoreExp_ExclRent + PropExp + Debt)
        # (10000 + 500) - (5000 + 4050 + 500 + 0 + 833.33) = 10500 - 10383.33 = 116.67
        self.assertAlmostEqual(row['Owner_Cash_Flow'], expected_net_store + expected_net_prop, places=2)

    def test_seasonality(self):
        """Verify Q1 vs Q3 revenue impact"""
        inputs = self.default_inputs.copy()
        inputs['seasonality'] = [0.5, 1.0, 1.5, 1.0] # Q1 half, Q3 1.5x
        model = FinancialModel(**inputs)
        df = model.calculate_projection(start_date=datetime.date(2024, 1, 1), months=12)
        
        # Month 1 (Q1): Factor 0.5. Rev should be 5000.
        self.assertEqual(df.iloc[0]['Store_Revenue'], 5000.0)
        
        # Month 7 (Q3): Factor 1.5. Rev should be 15000.
        self.assertEqual(df.iloc[6]['Store_Revenue'], 15000.0)
        
        # Verify Labor Seasonality (Partial Flex)
        # Logic: 1 + (Seasonality-1)*0.5
        # Q1 Labor Factor: 1 + (0.5-1)*0.5 = 0.75
        
        # Re-calc Base Labor Parts from setup (same as test_base_projection logic)
        mgr_monthly_hours = 10.0 * 52.0 / 12.0
        mgr_cost = 20.0 * mgr_monthly_hours  # Fixed, not seasonal
        
        total_req_hours = 1.0 * 10 * 30.5
        hourly_needed = total_req_hours - mgr_monthly_hours
        staff_base_cost = hourly_needed * 10.0
        
        # Apply Seasonality to Staff Cost Only
        expected_q1_labor = mgr_cost + (staff_base_cost * 0.75)
        # Expect negative
        self.assertAlmostEqual(df.iloc[0]['Store_Labor'], -expected_q1_labor, places=2)

    def test_growth_rates(self):
        """Verify Year 2 Compounding"""
        inputs = self.default_inputs.copy()
        inputs['revenue_growth_rate'] = 10.0 # 10%
        inputs['expense_growth_rate'] = 5.0 # 5%
        inputs['rent_escalation_rate'] = 2.0 # 2%
        
        model = FinancialModel(**inputs)
        df = model.calculate_projection(start_date=datetime.date(2024, 1, 1), months=13)
        
        # M1 (Year 1): Base values
        m1 = df.iloc[0]
        # M13 (Year 2): Growth values
        m13 = df.iloc[12]
        
        # Revenue: 10000 -> 11000
        self.assertAlmostEqual(m13['Store_Revenue'], m1['Store_Revenue'] * 1.10)
        
        # Rent Expense: 1000 -> 1020 (Negative)
        self.assertAlmostEqual(m13['Store_Rent_Ex'], -1020.0)
        
        # Ops Expense: 500 -> 525 (Negative)
        self.assertAlmostEqual(m13['Store_Ops_Ex'], -525.0)

    def test_events_and_entity_attribution(self):
        inputs = self.default_inputs.copy()
        # Add Events
        e_store_rev = BusinessEvent("New Product Rev", start_month=6, impact_target="Revenue", value_type="Fixed Amount ($)", value=1000, affected_entity="Store", frequency="Monthly")
        e_store_ops = BusinessEvent("New Product Cost", start_month=6, impact_target="Ops (Fixed)", value_type="Fixed Amount ($)", value=500, affected_entity="Store", frequency="Monthly")
        e_prop = BusinessEvent("Roof Repair", start_month=6, impact_target="Ops (Fixed)", value_type="Fixed Amount ($)", value=100, affected_entity="Property", frequency="Monthly")
        
        inputs['events'] = [e_store_rev, e_store_ops, e_prop]
        model = FinancialModel(**inputs)
        df = model.calculate_projection(start_date=datetime.date(2024, 1, 1), months=6)
        
        m5 = df.iloc[4] # Month 5 (Before)
        m6 = df.iloc[5] # Month 6 (Start)
        
        # Store Check:
        # Rev increases by 1000
        self.assertEqual(m6['Store_Revenue'], m5['Store_Revenue'] + 1000.0)
        # Ops Ex increases by 500 (Store event only) -> Becomes MORE negative
        # Prop event (100) should NOT be in Store Ops
        # m5 ops is -500. m6 ops should be -1000.
        self.assertEqual(m6['Store_Ops_Ex'], m5['Store_Ops_Ex'] - 500.0)
        
        # Property Check:
        # Prop Net should decrease by 100 (Expense)
        # Store event should NOT affect Prop Net directly
        self.assertEqual(m6['Prop_Net'], m5['Prop_Net'] - 100.0)


        
    def test_robust_event_features(self):
        """Test %-based events, duration windows, and dynamic targets"""
        inputs = self.default_inputs.copy()
        inputs['base_revenue'] = 10000.0
        
        # Event 1: +5% Revenue boost for Summer (Month 7-9)
        e1 = BusinessEvent(
            name="Summer Promo",
            start_month=7,
            end_month=9,
            impact_target="Revenue",
            value_type="% of Revenue",
            value=5.0, # 5%
            frequency="Monthly"
        )
        
        # Event 2: Fixed $500 Rent Increase starting Month 6
        e2 = BusinessEvent(
            name="Rent Hike",
            start_month=6,
            end_month=120,
            impact_target="Rent",
            value_type="Fixed Amount ($)",
            value=500.0,
            frequency="Monthly"
        )
        
        inputs['events'] = [e1, e2]
        model = FinancialModel(**inputs)
        df = model.calculate_projection(start_date=datetime.date(2024, 1, 1), months=12)
        
        m5 = df.iloc[4] # May
        m6 = df.iloc[5] # Jun (Rent hike starts)
        m7 = df.iloc[6] # Jul (Rev boost starts)
        m10 = df.iloc[9] # Oct (Rev boost ends)
        
        # 1. Rent Check
        # M5 Rent = -1000 (Base)
        # M6 Rent = -1000 - 500 = -1500
        self.assertEqual(m5['Store_Rent_Ex'], -1000.0)
        self.assertEqual(m6['Store_Rent_Ex'], -1500.0)
        
        # 2. Revenue Check
        # M6 Rev = 10000 (Base)
        # M7 Rev = 10000 + (5% of 10000) = 10500
        self.assertEqual(m6['Store_Revenue'], 10000.0)
        self.assertEqual(m7['Store_Revenue'], 10500.0)
        
        # 3. Duration Check
        # M10 (Oct) should be back to base Revenue (10000)
        self.assertEqual(m10['Store_Revenue'], 10000.0)
        # Rent should still be high (end_month=120)
        self.assertEqual(m10['Store_Rent_Ex'], -1500.0)


    def test_is_active_toggle(self):
        inputs = self.default_inputs.copy()
        
        # Two identical events, one Active, one Inactive
        e_active = BusinessEvent("Active Event", start_month=1, value=1000, value_type="Fixed Amount ($)", impact_target="Revenue", is_active=True)
        e_inactive = BusinessEvent("Inactive Event", start_month=1, value=1000, value_type="Fixed Amount ($)", impact_target="Revenue", is_active=False)
        
        inputs['events'] = [e_active, e_inactive]
        model = FinancialModel(**inputs)
        df = model.calculate_projection(start_date=datetime.date(2024, 1, 1), months=1)
        row = df.iloc[0]
        
        # Base Rev = 10,000
        # Expected = 10,000 + 1000 (Active) = 11,000
        # Inactive should be ignored.
        self.assertEqual(row['Store_Revenue'], 11000.0)

    def test_prev_quarter_noi_event(self):
        """Test the Lookback Logic for NOI Events"""
        inputs = self.default_inputs.copy()
        inputs['base_revenue'] = 10000.0
        inputs['seasonality'] = [1.0] * 4 # Flat seasonality
        
        # Scenario:
        # M1-M3: Base Rev 10k. 
        # Expenses: COGS 5k, Labor ~3k, Rent 1k, Ops 500.
        # Approx NOI per month = 10k - 5k - 3k - 1k - 500 = 500.
        # Q1 Total NOI = 1500.
        
        # Event: +10% of Previous Quarter NOI starting Month 4 (April)
        # Target: Labor (Bonus)
        e_bonus = BusinessEvent(
            name="Quarterly Bonus",
            start_month=4,
            frequency="Quarterly",
            impact_target="Labor", # Bonuses are usually labor cost
            value_type="% of Previous Quarter NOI",
            value=10.0, # 10%
        )
        
        inputs['events'] = [e_bonus]
        model = FinancialModel(**inputs)
        df = model.calculate_projection(start_date=datetime.date(2024, 1, 1), months=6)
        
        m1 = df.iloc[0]
        m4 = df.iloc[3] # April (Bonus Month)
        
        # M1 Labor should be base. Recalculate what base is for assert.
        # Mgr: 20*43.33 = 866.66
        # Staff: 1.0 * 10 * 30.5 = 305 hours. Offset = 305 - 43.33 = 261.66
        # Staff Cost: 261.66 * 10 = 2616.66
        # Total ~ 3483.33
        base_labor_expected = (20.0 * (10*52/12)) + (10.0 * ((1.0*10*30.5) - (10*52/12)))
        self.assertAlmostEqual(m1['Store_Labor'], -base_labor_expected, places=1)
        
        # Calculate expected NOI for Q1
        # Each month M1-M3 is identical.
        # Rev: 10000
        # Outflow: 5000(COGS) + 4050(Labor) + 500(Ops) + 1000(Rent) = 10550
        # Net Pre-Bonus = 10000 - 10550 = -550.
        # Wait, my mental math in test_base_projection said -550.
        # If NOI is negative, bonus should be 0.
        
        # Let's boost revenue to make it positive.
        inputs['base_revenue'] = 12000.0
        # Rev 12000. COGS 6000. Labor 4050. Ops 500. Rent 1000.
        # Outflow = 11550.
        # Net = 450.
        # Q1 Total = 450 * 3 = 1350.
        # Bonus = 10% of 1350 = 135.
        
        model_pos = FinancialModel(**inputs)
        df_pos = model_pos.calculate_projection(start_date=datetime.date(2024, 1, 1), months=6)
        
        m4_pos = df_pos.iloc[3] # April
        
        # Base Labor M4 is same as M1.
        # Total M4 Labor = base_labor_expected + 305 = 3788.33.
        # Expect MORE negative
        self.assertAlmostEqual(m4_pos['Store_Labor'], -(base_labor_expected + 305.0), places=1)
        
        # Verify Month 5 (May) has no bonus (Quarterly freq)
        m5_pos = df_pos.iloc[4]
        self.assertAlmostEqual(m5_pos['Store_Labor'], -base_labor_expected, places=1)

    def test_property_metrics(self):
        """Verify Property Tax, Equity, and Appreciation logic"""
        inputs = self.default_inputs.copy()
        inputs['property_tax_annual'] = 1200.0 # 100/mo
        inputs['initial_property_value'] = 200000.0
        inputs['loan_amount'] = 150000.0
        inputs['initial_equity'] = 100000.0 # Cash
        inputs['property_appreciation_rate'] = 10.0 # 10% annual
        inputs['intangible_assets'] = 10000.0
        inputs['initial_inventory'] = 5000.0
        
        # Start:
        # Downpayment = 200k - 150k = 50k.
        # Startup Uses = 5k(Inv) + 10k(Intangible) + 50k(Down) = 65k.
        # Initial Cash Balance = 100k - 65k = 35k.
        
        model = FinancialModel(**inputs)
        df = model.calculate_projection(start_date=datetime.date(2024, 1, 1), months=13)
        
        m1 = df.iloc[0]
        m13 = df.iloc[12] # Year 2 Month 1
        
        # 1. Cash Balance check
        # M1 Cash Balance = Initial(25k) + M1_Cash_Flow
        # We need to calc M1 Cash Flow roughly.
        # Store Net approx: 10k(Rev) - 5k(COGS) - ~3k(Labor) - 500(Ops) - 1000(Rent) = 500.
        # Prop Net: 1000+500 - Debt(150k/10y/0int = 1250) - Tax(100) = 150.
        # Consolidated = 650.
        # Balance ~ 35000 + 650 = 35650.
        self.assertAlmostEqual(m1['Cash_Balance'], 35000.0 + m1['Owner_Cash_Flow'], places=1)
        
        # 2. Property Tax
        self.assertEqual(m1['Prop_Tax'], -100.0)
        
        # 3. Equity
        # M1: Prop Value = 200,000 (Growth applied at YEAR index, so Year 1 is 1.0)
        # Loan Balance: 150,000 - Principal Payment (1250).
        # Equity = 200,000 - 148,750 = 51,250.
        principal_pay = 150000.0 / 120.0
        self.assertAlmostEqual(m1['Loan_Balance'], 150000.0 - principal_pay, places=2)
        self.assertAlmostEqual(m1['Property_Equity'], 200000.0 - (150000.0 - principal_pay), places=2)
        
        # 4. Appreciation (Year 2)
        # Year 2 Index = 1.
        # Factor = (1.10)^1 = 1.10.
        # Value = 220,000.
        self.assertAlmostEqual(m13['Property_Value'], 220000.0, places=1)
        
        # 5. Intangibles
        self.assertEqual(m1['Intangible_Assets'], 10000.0)

if __name__ == '__main__':
    unittest.main()
