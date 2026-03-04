"""
FirstHome — Affordability Calculator
Uses numpy_financial for precise PMT calculations
"""
import numpy_financial as npf
import math


def calculate_affordability(
    annual_income: float,
    monthly_debts: float,
    deposit: float,
    annual_rate: float,
    term_years: int
) -> dict:
    """
    Calculate maximum home affordability based on income multiplier
    and debt-to-income ratio stress testing.

    Parameters
    ----------
    annual_income   : Gross annual income in GBP
    monthly_debts   : Existing monthly debt obligations (loans, credit cards, etc.)
    deposit         : Available deposit amount in GBP
    annual_rate     : Annual mortgage interest rate as percentage (e.g. 4.5)
    term_years      : Mortgage term in years

    Returns
    -------
    dict with max_price, loan_amount, monthly_emi, dti_ratio,
    deposit_pct, ltv, affordability_score, health_label
    """
    # Input validation
    if annual_income <= 0:
        raise ValueError("Annual income must be positive")
    if deposit < 0:
        raise ValueError("Deposit cannot be negative")
    if annual_rate <= 0 or annual_rate > 20:
        raise ValueError("Interest rate must be between 0 and 20%")
    if term_years not in [10, 15, 20, 25, 30]:
        raise ValueError("Term must be 10, 15, 20, 25, or 30 years")

    # ── Maximum Price using 4.5× income multiplier (UK standard) ──
    # The 4.5× cap is the standard used by UK mortgage lenders
    # We add deposit to reflect total purchasing power
    income_cap = annual_income * 4.5
    max_price = income_cap + deposit

    # ── Loan amount ──
    loan_amount = max_price - deposit

    # ── Monthly EMI via numpy_financial PMT ──
    # npf.pmt(rate, nper, pv) → negative value (payment outflow)
    monthly_rate = annual_rate / 100 / 12
    n_payments = term_years * 12

    monthly_emi = abs(npf.pmt(monthly_rate, n_payments, loan_amount))

    # ── Debt-to-Income Ratio ──
    monthly_income = annual_income / 12
    total_monthly_obligations = monthly_emi + monthly_debts
    dti_ratio = (total_monthly_obligations / monthly_income) * 100

    # ── Deposit metrics ──
    deposit_pct = (deposit / max_price) * 100
    ltv = 100 - deposit_pct

    # ── Affordability health score (0-100) ──
    # Based on DTI: <28% = excellent, <36% = good, <43% = acceptable, >43% = overstretched
    if dti_ratio < 28:
        health_score = 90 + (28 - dti_ratio) / 28 * 10
        health_label = "Excellent"
    elif dti_ratio < 36:
        health_score = 70 + (36 - dti_ratio) / 8 * 20
        health_label = "Good"
    elif dti_ratio < 43:
        health_score = 40 + (43 - dti_ratio) / 7 * 30
        health_label = "Stretching"
    else:
        health_score = max(0, 40 - (dti_ratio - 43) * 2)
        health_label = "Over-extended"

    health_score = min(100, max(0, health_score))

    # ── Stress-tested EMI at +3% (UK FCA requirement) ──
    stress_rate = (annual_rate + 3) / 100 / 12
    stressed_emi = abs(npf.pmt(stress_rate, n_payments, loan_amount))
    stressed_dti = ((stressed_emi + monthly_debts) / monthly_income) * 100
    passes_stress_test = stressed_dti < 50

    # ── Total interest over term ──
    total_paid = monthly_emi * n_payments
    total_interest = total_paid - loan_amount

    return {
        "max_price": round(max_price, 2),
        "loan_amount": round(loan_amount, 2),
        "monthly_emi": round(monthly_emi, 2),
        "dti_ratio": round(dti_ratio, 2),
        "deposit_pct": round(deposit_pct, 2),
        "ltv": round(ltv, 2),
        "health_score": round(health_score, 1),
        "health_label": health_label,
        "stressed_emi": round(stressed_emi, 2),
        "stressed_dti": round(stressed_dti, 2),
        "passes_stress_test": passes_stress_test,
        "total_interest": round(total_interest, 2),
        "total_paid": round(total_paid, 2),
        "income_multiplier": round((max_price - deposit) / annual_income, 2),
    }
