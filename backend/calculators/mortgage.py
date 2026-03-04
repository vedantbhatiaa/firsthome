"""
FirstHome — Mortgage & Amortisation Calculator
Uses numpy_financial for precise PMT, IPMT, PPMT calculations
"""
import numpy_financial as npf
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


def calculate_mortgage(
    home_price: float,
    down_payment: float,
    annual_rate: float,
    term_years: int,
    extra_monthly_payment: float = 0.0
) -> dict:
    """
    Full mortgage calculation with complete amortisation schedule.

    Parameters
    ----------
    home_price             : Purchase price in GBP
    down_payment           : Down payment amount in GBP
    annual_rate            : Annual interest rate as percentage (e.g. 4.5)
    term_years             : Loan term in years
    extra_monthly_payment  : Optional extra principal payment per month

    Returns
    -------
    dict with monthly_emi, total_paid, total_interest, payoff_date,
    int_pct, principal_pct, amortisation_schedule (full), summary_rows
    """
    if home_price <= 0:
        raise ValueError("Home price must be positive")
    if down_payment >= home_price:
        raise ValueError("Down payment cannot exceed home price")
    if annual_rate <= 0:
        raise ValueError("Interest rate must be positive")

    loan_amount = home_price - down_payment
    monthly_rate = annual_rate / 100 / 12
    n_payments = term_years * 12

    # ── Monthly EMI using numpy_financial PMT ──
    monthly_emi = abs(npf.pmt(monthly_rate, n_payments, loan_amount))
    total_payment = monthly_emi + extra_monthly_payment

    # ── Build full amortisation schedule ──
    schedule = []
    balance = loan_amount
    total_interest_paid = 0
    total_principal_paid = 0
    actual_months = 0

    start_date = datetime.now()

    for month in range(1, n_payments + 1):
        if balance <= 0:
            break

        # numpy_financial IPMT/PPMT for precision
        interest_payment = abs(npf.ipmt(monthly_rate, month, n_payments, loan_amount))
        principal_payment = abs(npf.ppmt(monthly_rate, month, n_payments, loan_amount))

        # Apply extra payment to principal
        if extra_monthly_payment > 0:
            extra = min(extra_monthly_payment, balance - principal_payment)
            principal_payment += extra

        principal_payment = min(principal_payment, balance)
        balance = max(0, balance - principal_payment)

        total_interest_paid += interest_payment
        total_principal_paid += principal_payment
        actual_months = month

        payment_date = start_date + relativedelta(months=month)

        schedule.append({
            "month": month,
            "date": payment_date.strftime("%b %Y"),
            "payment": round(monthly_emi + (extra_monthly_payment if extra_monthly_payment > 0 else 0), 2),
            "principal": round(principal_payment, 2),
            "interest": round(interest_payment, 2),
            "balance": round(balance, 2),
            "cumulative_interest": round(total_interest_paid, 2),
            "cumulative_principal": round(total_principal_paid, 2),
        })

        if balance <= 0:
            break

    # ── Summary stats ──
    total_paid = total_interest_paid + loan_amount
    payoff_date = (start_date + relativedelta(months=actual_months)).strftime("%B %Y")

    int_pct = (total_interest_paid / total_paid) * 100 if total_paid > 0 else 0
    principal_pct = 100 - int_pct

    # Interest savings from extra payments
    standard_total = monthly_emi * n_payments
    interest_savings = standard_total - total_paid if extra_monthly_payment > 0 else 0
    months_saved = n_payments - actual_months if extra_monthly_payment > 0 else 0

    # First 12 months for preview table
    preview_rows = schedule[:12]

    # Yearly summary (for charting)
    yearly_summary = []
    for yr in range(1, term_years + 1):
        year_months = schedule[(yr-1)*12 : yr*12]
        if not year_months:
            break
        yearly_summary.append({
            "year": yr,
            "principal_paid": round(sum(m["principal"] for m in year_months), 2),
            "interest_paid": round(sum(m["interest"] for m in year_months), 2),
            "balance": year_months[-1]["balance"],
        })

    return {
        "loan_amount": round(loan_amount, 2),
        "monthly_emi": round(monthly_emi, 2),
        "total_payment_with_extra": round(total_payment, 2),
        "total_paid": round(total_paid, 2),
        "total_interest": round(total_interest_paid, 2),
        "payoff_date": payoff_date,
        "actual_months": actual_months,
        "int_pct": round(int_pct, 2),
        "principal_pct": round(principal_pct, 2),
        "interest_savings": round(interest_savings, 2),
        "months_saved": months_saved,
        "down_payment_pct": round((down_payment / home_price) * 100, 2),
        "preview_rows": preview_rows,
        "yearly_summary": yearly_summary,
        "full_schedule": schedule,
    }
