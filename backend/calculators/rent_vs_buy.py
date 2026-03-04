"""
FirstHome — Rent vs Buy NPV Analysis
Uses numpy_financial NPV/PV to compute true net cost comparison
"""
import numpy_financial as npf
import numpy as np


def calculate_rent_vs_buy(
    purchase_price: float,
    down_payment: float,
    monthly_rent: float,
    mortgage_rate: float,
    home_appreciation_rate: float,
    investment_return_rate: float,
    time_horizon_years: int,
    mortgage_term_years: int = 25,
    annual_maintenance_pct: float = 1.0,
    annual_rent_increase_pct: float = 2.5,
) -> dict:
    """
    True NPV-based rent vs buy comparison.

    The analysis computes net wealth position after N years for each path:

    BUYING PATH:
      - Down payment (opportunity cost)
      - Monthly mortgage payments
      - Annual maintenance costs
      - Property taxes (estimated)
      - Net equity gain from appreciation
      → Net Wealth = Home Value - Remaining Mortgage - Total Costs Paid

    RENTING PATH:
      - Down payment invested at investment_return_rate
      - Monthly rent (escalating annually)
      - Monthly rent savings vs mortgage → invested
      → Net Wealth = Investment Portfolio Value - Total Rent Paid

    Parameters
    ----------
    purchase_price           : Home price in GBP
    down_payment             : Initial deposit in GBP
    monthly_rent             : Current monthly rent in GBP
    mortgage_rate            : Annual mortgage interest rate (%)
    home_appreciation_rate   : Expected annual home appreciation (%)
    investment_return_rate   : Expected annual return if renting and investing (%)
    time_horizon_years       : Analysis period in years
    mortgage_term_years      : Full mortgage term (default 25 years)
    annual_maintenance_pct   : Home maintenance as % of value per year (default 1%)
    annual_rent_increase_pct : Annual rent inflation (default 2.5%)

    Returns
    -------
    dict with buy_net_wealth, rent_net_wealth, wealth_difference,
    verdict, recommendation, year_by_year breakdown
    """
    loan = purchase_price - down_payment
    monthly_rate = mortgage_rate / 100 / 12
    n_total = mortgage_term_years * 12
    horizon_months = time_horizon_years * 12

    # ── BUYING PATH ──

    # Monthly EMI
    monthly_emi = abs(npf.pmt(monthly_rate, n_total, loan))

    # Future home value after appreciation
    home_future_value = purchase_price * ((1 + home_appreciation_rate / 100) ** time_horizon_years)

    # Remaining mortgage balance at horizon
    if time_horizon_years < mortgage_term_years:
        # PV of remaining payments
        remaining_payments = n_total - horizon_months
        remaining_balance = abs(npf.pv(monthly_rate, remaining_payments, monthly_emi))
    else:
        remaining_balance = 0.0

    # Total mortgage paid out of pocket over horizon
    total_mortgage_paid = monthly_emi * min(horizon_months, n_total)

    # Maintenance costs (% of home value, growing with appreciation)
    total_maintenance = 0
    for yr in range(time_horizon_years):
        home_val_yr = purchase_price * ((1 + home_appreciation_rate / 100) ** yr)
        total_maintenance += home_val_yr * (annual_maintenance_pct / 100)

    # Stamp duty (UK: simplified estimate)
    stamp_duty = _estimate_stamp_duty(purchase_price)

    # Buy Net Wealth = Home value - remaining mortgage - all cash outlaid
    total_buy_outlay = down_payment + total_mortgage_paid + total_maintenance + stamp_duty
    buy_equity = home_future_value - remaining_balance
    buy_net_wealth = buy_equity - (total_mortgage_paid + total_maintenance + stamp_duty)

    # ── RENTING PATH ──

    # Invest the down payment
    invested_deposit = down_payment * ((1 + investment_return_rate / 100) ** time_horizon_years)

    # Monthly difference: if rent < EMI, invest the surplus each month
    # If rent > EMI, renter has higher costs — negative surplus
    monthly_inv_rate = investment_return_rate / 100 / 12
    total_rent_paid = 0
    investment_portfolio = invested_deposit  # starts with the deposit

    for month in range(1, horizon_months + 1):
        yr = (month - 1) // 12
        # Rent escalates annually
        current_rent = monthly_rent * ((1 + annual_rent_increase_pct / 100) ** yr)
        total_rent_paid += current_rent

        # Surplus = EMI - rent (if positive, renter invests it; if negative, renter has extra cost)
        monthly_surplus = monthly_emi - current_rent
        if monthly_surplus > 0:
            investment_portfolio += monthly_surplus

        # Monthly portfolio growth
        investment_portfolio *= (1 + monthly_inv_rate)

    rent_net_wealth = investment_portfolio - total_rent_paid

    # ── NPV comparison using numpy npv ──
    # Build annual cash flow arrays for NPV
    discount_rate = 0.05  # 5% discount rate for NPV

    buy_cashflows = [-down_payment - stamp_duty]
    rent_cashflows = [-down_payment]  # invested instead

    for yr in range(1, time_horizon_years + 1):
        # Buy: -EMI*12 - maintenance
        home_val_yr = purchase_price * ((1 + home_appreciation_rate / 100) ** yr)
        maint = home_val_yr * (annual_maintenance_pct / 100)
        buy_cf = -(monthly_emi * 12) - maint
        if yr == time_horizon_years:
            buy_cf += home_future_value - remaining_balance  # proceeds from sale
        buy_cashflows.append(buy_cf)

        # Rent: -rent*12
        yr_rent = monthly_rent * 12 * ((1 + annual_rent_increase_pct / 100) ** (yr - 1))
        rent_cf = -yr_rent
        if yr == time_horizon_years:
            rent_cf += invested_deposit  # liquidate portfolio
        rent_cashflows.append(rent_cf)

    buy_npv = npf.npv(discount_rate, buy_cashflows)
    rent_npv = npf.npv(discount_rate, rent_cashflows)

    # ── Breakeven year ──
    breakeven_year = None
    cumulative_buy_cost = down_payment + stamp_duty
    cumulative_rent_cost = 0
    cumulative_buy_equity = 0

    breakeven_data = []
    for yr in range(1, time_horizon_years + 1):
        yr_maint = purchase_price * ((1 + home_appreciation_rate / 100) ** yr) * (annual_maintenance_pct / 100)
        cumulative_buy_cost += (monthly_emi * 12) + yr_maint
        cumulative_buy_equity = purchase_price * ((1 + home_appreciation_rate / 100) ** yr)
        buy_position = cumulative_buy_equity - cumulative_buy_cost

        yr_rent = monthly_rent * 12 * ((1 + annual_rent_increase_pct / 100) ** (yr - 1))
        cumulative_rent_cost += yr_rent
        rent_deposit_value = down_payment * ((1 + investment_return_rate / 100) ** yr)
        rent_position = rent_deposit_value - cumulative_rent_cost

        if buy_position > rent_position and breakeven_year is None:
            breakeven_year = yr

        breakeven_data.append({
            "year": yr,
            "buy_net_position": round(buy_position, 0),
            "rent_net_position": round(rent_position, 0),
        })

    # ── Verdict ──
    wealth_diff = buy_net_wealth - rent_net_wealth
    if abs(wealth_diff) < purchase_price * 0.02:
        verdict = "neutral"
        recommendation = f"It's essentially a tie over {time_horizon_years} years. Your lifestyle preference should decide."
    elif wealth_diff > 0:
        verdict = "buy"
        recommendation = f"Buying builds £{abs(round(wealth_diff)):,} more wealth over {time_horizon_years} years, driven by {home_appreciation_rate}% p.a. appreciation."
    else:
        verdict = "rent"
        recommendation = f"Renting and investing your deposit generates £{abs(round(wealth_diff)):,} more over {time_horizon_years} years at {investment_return_rate}% returns."

    return {
        # Buying path
        "buy_net_wealth": round(buy_net_wealth, 2),
        "home_future_value": round(home_future_value, 2),
        "remaining_balance": round(remaining_balance, 2),
        "total_mortgage_paid": round(total_mortgage_paid, 2),
        "total_maintenance": round(total_maintenance, 2),
        "stamp_duty": round(stamp_duty, 2),
        "monthly_emi": round(monthly_emi, 2),

        # Renting path
        "rent_net_wealth": round(rent_net_wealth, 2),
        "total_rent_paid": round(total_rent_paid, 2),
        "invested_deposit_value": round(invested_deposit, 2),

        # NPV comparison
        "buy_npv": round(float(buy_npv), 2),
        "rent_npv": round(float(rent_npv), 2),

        # Summary
        "wealth_difference": round(wealth_diff, 2),
        "verdict": verdict,
        "recommendation": recommendation,
        "breakeven_year": breakeven_year,
        "year_by_year": breakeven_data,
    }


def _estimate_stamp_duty(price: float) -> float:
    """
    UK Stamp Duty Land Tax (SDLT) for first-time buyers.
    Thresholds as of 2024 (standard rates).
    """
    if price <= 250_000:
        return 0
    elif price <= 925_000:
        return (price - 250_000) * 0.05
    elif price <= 1_500_000:
        return 33_750 + (price - 925_000) * 0.10
    else:
        return 91_250 + (price - 1_500_000) * 0.12
