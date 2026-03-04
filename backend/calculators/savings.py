"""
FirstHome — Savings Goal & Down Payment Planner
Uses numpy_financial PMT/FV to reverse-engineer monthly savings requirements
"""
import numpy_financial as npf
import math


def calculate_savings_goal(
    target_home_price: float,
    target_deposit_pct: float,
    current_savings: float,
    annual_return: float,
) -> dict:
    """
    Calculates required monthly savings to hit a deposit goal
    across multiple time horizons.

    Uses PMT to reverse-engineer the required contribution, accounting for
    compounding returns on both existing savings and new contributions.

    Parameters
    ----------
    target_home_price   : Target property price in GBP
    target_deposit_pct  : Target deposit as percentage (e.g. 20 for 20%)
    current_savings     : Already saved amount in GBP
    annual_return       : Expected annual return on savings (%)

    Returns
    -------
    dict with deposit_target, remaining_needed, progress_pct,
    scenarios (1yr, 2yr, 3yr, 5yr), milestones, monthly_breakdown
    """
    if target_home_price <= 0:
        raise ValueError("Home price must be positive")
    if not 1 <= target_deposit_pct <= 100:
        raise ValueError("Deposit percentage must be between 1 and 100")
    if current_savings < 0:
        raise ValueError("Current savings cannot be negative")

    deposit_target = target_home_price * (target_deposit_pct / 100)
    remaining = max(0, deposit_target - current_savings)
    progress_pct = min(100, (current_savings / deposit_target) * 100) if deposit_target > 0 else 100

    monthly_rate = annual_return / 100 / 12

    def required_pmt(months: int) -> float:
        """
        Calculate monthly savings needed using PMT.
        Accounts for future value of existing savings.
        FV of current savings after N months:
            fv_current = current_savings * (1 + r)^n
        Remaining gap to fill via PMT:
            gap = deposit_target - fv_current
        Monthly payment = PMT(r, n, 0, gap)  [saving toward future value]
        """
        if months <= 0:
            return float('inf')

        # Future value of current savings
        fv_current = current_savings * ((1 + monthly_rate) ** months)
        gap = deposit_target - fv_current

        if gap <= 0:
            return 0.0  # already on track

        # PMT needed to accumulate 'gap' in 'months' months
        # npf.pmt(rate, nper, pv=0, fv=-gap) → payment needed
        monthly_payment = abs(npf.pmt(monthly_rate, months, 0, -gap))
        return round(monthly_payment, 2)

    scenarios = {
        "1yr":  {"months": 12,  "label": "Aggressive (1 year)",  "icon": "⚡"},
        "2yr":  {"months": 24,  "label": "Balanced (2 years)",   "icon": "🎯"},
        "3yr":  {"months": 36,  "label": "Patient (3 years)",    "icon": "🌱"},
        "5yr":  {"months": 60,  "label": "Relaxed (5 years)",    "icon": "🕰️"},
    }

    for key, s in scenarios.items():
        pmt = required_pmt(s["months"])
        fv_at_horizon = abs(npf.fv(monthly_rate, s["months"], -pmt, -current_savings))

        s["monthly_payment"] = pmt
        s["already_achieved"] = pmt == 0
        s["total_contributions"] = round(pmt * s["months"], 2)
        s["interest_earned"] = round(fv_at_horizon - current_savings - (pmt * s["months"]), 2)
        s["final_value"] = round(fv_at_horizon, 2)
        s["affordability_pct_income"] = None  # set by frontend if income known

    # ── Milestone projections ──
    milestones = []
    check_amounts = [
        deposit_target * 0.25,
        deposit_target * 0.5,
        deposit_target * 0.75,
        deposit_target,
    ]
    milestone_labels = ["25% of deposit", "50% of deposit", "75% of deposit", "Full deposit reached! 🎉"]

    # Use 2-year scenario monthly payment as reference
    ref_pmt = scenarios["2yr"]["monthly_payment"]

    for amount, label in zip(check_amounts, milestone_labels):
        if amount <= current_savings:
            milestones.append({
                "label": label,
                "amount": round(amount, 2),
                "months_to_reach": 0,
                "date": "Already achieved",
                "achieved": True,
            })
            continue

        # Solve for when savings hit this amount
        # FV = current*(1+r)^n + pmt*((1+r)^n - 1)/r = amount
        # Solve numerically
        months_needed = _months_to_reach(current_savings, ref_pmt, monthly_rate, amount)
        milestones.append({
            "label": label,
            "amount": round(amount, 2),
            "months_to_reach": months_needed,
            "date": _months_to_date_str(months_needed),
            "achieved": False,
        })

    # ── Monthly savings breakdown for first 12 months (2yr scenario) ──
    monthly_breakdown = []
    balance = current_savings
    ref_payment = scenarios["2yr"]["monthly_payment"]

    for m in range(1, 13):
        interest = balance * monthly_rate
        balance = balance + interest + ref_payment
        monthly_breakdown.append({
            "month": m,
            "contribution": round(ref_payment, 2),
            "interest_earned": round(interest, 2),
            "balance": round(balance, 2),
            "progress_pct": round(min(100, (balance / deposit_target) * 100), 1),
        })

    # ── What it unlocks ──
    # First-time buyer schemes comparison (UK)
    ltv_at_target = 100 - target_deposit_pct
    schemes_unlocked = []
    if target_deposit_pct >= 5:
        schemes_unlocked.append("95% LTV Mortgage (Help to Buy eligible)")
    if target_deposit_pct >= 10:
        schemes_unlocked.append("Better rate band: 90% LTV mortgages")
    if target_deposit_pct >= 15:
        schemes_unlocked.append("85% LTV — mid-tier rates unlocked")
    if target_deposit_pct >= 20:
        schemes_unlocked.append("Best rates: 80% LTV + no LMI required")
    if target_deposit_pct >= 25:
        schemes_unlocked.append("Premium rates: 75% LTV — lender sweet spot")

    return {
        "deposit_target": round(deposit_target, 2),
        "remaining_needed": round(remaining, 2),
        "current_savings": round(current_savings, 2),
        "progress_pct": round(progress_pct, 2),
        "target_home_price": round(target_home_price, 2),
        "target_deposit_pct": target_deposit_pct,
        "ltv_at_target": round(ltv_at_target, 2),
        "scenarios": scenarios,
        "milestones": milestones,
        "monthly_breakdown": monthly_breakdown,
        "schemes_unlocked": schemes_unlocked,
    }


def _months_to_reach(current: float, monthly_pmt: float, rate: float, target: float) -> int:
    """Numerically find how many months until balance hits target."""
    balance = current
    for m in range(1, 1201):  # cap at 100 years
        balance = balance * (1 + rate) + monthly_pmt
        if balance >= target:
            return m
    return 1200


def _months_to_date_str(months: int) -> str:
    """Convert months from now to a readable date string."""
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    future = datetime.now() + relativedelta(months=months)
    return future.strftime("%B %Y")
