import unittest
import sys
import os
import pandas as pd

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model import FinancialModel, BusinessEvent, calculate_monthly_payment, BASE_REVENUE_MONTHLY, BASE_COGS_PCT

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
            "base_cogs_pct": 0.50,
            "operating_hours": 10,
            "manager_salary": 12000.0, # 1k/mo
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
            "commercial_rent_income": 1000.0,
            "residential_rent_income": 500.0,
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
        df = model.calculate_projection(months=1)
        row = df.iloc[0]
        
        # Revenue: 10,000 (Base)
        self.assertEqual(row['Store_Revenue'], 10000.0)
        
        # COGS: 50% of 10,000 = 5,000
        self.assertEqual(row['Store_COGS'], 5000.0)
        
        # Labor: Manager(1k) + Staff(10 * 10 * 1 * 30.5 = 3050) = 4050
        # Wait, app.py uses DAYS_IN_MONTH = 30.5 global constant
        expected_staff = 10.0 * 1.0 * 10 * 30.5
        expected_labor = 1000.0 + expected_staff
        self.assertEqual(row['Store_Labor'], expected_labor)
        
        # Ops Expenses: 500 (Base fixed)
        self.assertEqual(row['Store_Ops_Ex'], 500.0)
        
        # Rent Expense: 1000
        self.assertEqual(row['Store_Rent_Ex'], 1000.0)
        
        # Store Net: 10000 - 5000 - 4050 - 500 - 1000 = -550
        expected_net_store = 10000.0 - 5000.0 - expected_labor - 500.0 - 1000.0
        self.assertAlmostEqual(row['Store_Net'], expected_net_store, places=2)
        
        # Property Net: Rent(1000) + Res(500) - Debt(100k/10y/0% = 833.33)
        # 1500 - 833.33 = 666.67
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
        df = model.calculate_projection(months=12)
        
        # Month 1 (Q1): Factor 0.5. Rev should be 5000.
        self.assertEqual(df.iloc[0]['Store_Revenue'], 5000.0)
        
        # Month 7 (Q3): Factor 1.5. Rev should be 15000.
        self.assertEqual(df.iloc[6]['Store_Revenue'], 15000.0)
        
        # Verify Labor Seasonality (Partial Flex)
        # Logic: 1 + (Seasonality-1)*0.5
        # Q1 Labor Factor: 1 + (0.5-1)*0.5 = 0.75
        # Base Staff Labor 3050 -> 2287.5
        # Manager Fixed 1000
        # Total M1 Labor = 3287.5
        base_staff = 3050.0
        expected_q1_labor = 1000.0 + (base_staff * 0.75)
        self.assertEqual(df.iloc[0]['Store_Labor'], expected_q1_labor)

    def test_growth_rates(self):
        """Verify Year 2 Compounding"""
        inputs = self.default_inputs.copy()
        inputs['revenue_growth_rate'] = 10.0 # 10%
        inputs['expense_growth_rate'] = 5.0 # 5%
        inputs['rent_escalation_rate'] = 2.0 # 2%
        
        model = FinancialModel(**inputs)
        df = model.calculate_projection(months=13)
        
        # M1 (Year 1): Base values
        m1 = df.iloc[0]
        # M13 (Year 2): Growth values
        m13 = df.iloc[12]
        
        # Revenue: 10000 -> 11000
        self.assertAlmostEqual(m13['Store_Revenue'], m1['Store_Revenue'] * 1.10)
        
        # Rent Expense: 1000 -> 1020
        self.assertAlmostEqual(m13['Store_Rent_Ex'], 1000.0 * 1.02)
        
        # Ops Expense: 500 -> 525
        self.assertAlmostEqual(m13['Store_Ops_Ex'], 500.0 * 1.05)

    def test_events_and_entity_attribution(self):
        inputs = self.default_inputs.copy()
        # Add Events
        e_store_rev = BusinessEvent("New Product Rev", start_month=6, impact_target="Revenue", value_type="Fixed Amount ($)", value=1000, affected_entity="Store", frequency="Monthly")
        e_store_ops = BusinessEvent("New Product Cost", start_month=6, impact_target="Ops (Fixed)", value_type="Fixed Amount ($)", value=500, affected_entity="Store", frequency="Monthly")
        e_prop = BusinessEvent("Roof Repair", start_month=6, impact_target="Ops (Fixed)", value_type="Fixed Amount ($)", value=100, affected_entity="Property", frequency="Monthly")
        
        inputs['events'] = [e_store_rev, e_store_ops, e_prop]
        model = FinancialModel(**inputs)
        df = model.calculate_projection(months=6)
        
        m5 = df.iloc[4] # Month 5 (Before)
        m6 = df.iloc[5] # Month 6 (Start)
        
        # Store Check:
        # Rev increases by 1000
        self.assertEqual(m6['Store_Revenue'], m5['Store_Revenue'] + 1000.0)
        # Ops Ex increases by 500 (Store event only)
        # Prop event (100) should NOT be in Store Ops
        self.assertEqual(m6['Store_Ops_Ex'], m5['Store_Ops_Ex'] + 500.0)
        
        # Property Check:
        # Prop Net should decrease by 100 (Expense)
        # Store event should NOT affect Prop Net directly
        self.assertEqual(m6['Prop_Net'], m5['Prop_Net'] - 100.0)

    def test_manager_incentives(self):
        inputs = self.default_inputs.copy()
        # Case A: 10% of Revenue, Quarterly
        inputs['incentive_metric'] = "Revenue"
        inputs['incentive_pct'] = 10.0
        inputs['incentive_freq'] = "Quarterly"
        
        # Base rev is 10k/mo. 
        # Q1 Rev = 30k. Used flat seasonality for simplify.
        # Bonus should be 10% of 30k = 3000.
        
        model = FinancialModel(**inputs)
        df = model.calculate_projection(months=4)
        
        m1 = df.iloc[0]
        m3 = df.iloc[2] # Q1 End
        m4 = df.iloc[3] # New Quarter
        
        self.assertEqual(m1['Store_Bonus'], 0.0) # No payout M1
        self.assertEqual(m3['Store_Bonus'], 3000.0) # Payout M3
        # Ensure Store Net is reduced
        # Net = Rev(10k) - COGS(5k) - Labor(4k) - Ops(500) - Rent(1k) = -550 approx (with slight labor diff)
        # Bonus reduces it further by 3k.
        # We can just check the Bonus column is correct (3000) and that Net is roughly Revenue - Expenses - 3000
        # But simpler to just verify the bonus amount is as expected, which we did above.
        self.assertEqual(m3['Store_Bonus'], 3000.0) 

        
        # Case B: 5% of NOI, Annual
        inputs['incentive_metric'] = "Net (NOI)"
        inputs['incentive_pct'] = 5.0
        inputs['incentive_freq'] = "Annual"
        
        # Make profitable so positive NOI
        inputs['base_revenue'] = 50000.0 
        
        model2 = FinancialModel(**inputs)
        df2 = model2.calculate_projection(months=12)
        
        m11 = df2.iloc[10] # Nov
        m12 = df2.iloc[11] # Dec
        self.assertEqual(m11['Store_Bonus'], 0.0)
        self.assertTrue(m12['Store_Bonus'] > 0.0)
        # Verify accumulator reset? Implicit if Year 2 starts clean.
        
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
        df = model.calculate_projection(months=12)
        
        m5 = df.iloc[4] # May
        m6 = df.iloc[5] # Jun (Rent hike starts)
        m7 = df.iloc[6] # Jul (Rev boost starts)
        m10 = df.iloc[9] # Oct (Rev boost ends)
        
        # 1. Rent Check
        # M5 Rent = 1000 (Base)
        # M6 Rent = 1000 + 500 = 1500
        self.assertEqual(m5['Store_Rent_Ex'], 1000.0)
        self.assertEqual(m6['Store_Rent_Ex'], 1500.0)
        
        # 2. Revenue Check
        # M6 Rev = 10000 (Base)
        # M7 Rev = 10000 + (5% of 10000) = 10500
        self.assertEqual(m6['Store_Revenue'], 10000.0)
        self.assertEqual(m7['Store_Revenue'], 10500.0)
        
        # 3. Duration Check
        # M10 (Oct) should be back to base Revenue (10000)
        self.assertEqual(m10['Store_Revenue'], 10000.0)
        # Rent should still be high (end_month=120)
        self.assertEqual(m10['Store_Rent_Ex'], 1500.0)


    def test_is_active_toggle(self):
        inputs = self.default_inputs.copy()
        
        # Two identical events, one Active, one Inactive
        e_active = BusinessEvent("Active Event", start_month=1, value=1000, value_type="Fixed Amount ($)", impact_target="Revenue", is_active=True)
        e_inactive = BusinessEvent("Inactive Event", start_month=1, value=1000, value_type="Fixed Amount ($)", impact_target="Revenue", is_active=False)
        
        inputs['events'] = [e_active, e_inactive]
        model = FinancialModel(**inputs)
        df = model.calculate_projection(months=1)
        row = df.iloc[0]
        
        # Base Rev = 10,000
        # Expected = 10,000 + 1000 (Active) = 11,000
        # Inactive should be ignored.
        self.assertEqual(row['Store_Revenue'], 11000.0)

if __name__ == '__main__':
    unittest.main()
