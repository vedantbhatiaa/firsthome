"""
FirstHome — API Routes
All /api/* endpoints. Each returns a JSON response.
"""
from flask import Blueprint, request, jsonify
from calculators import (
    calculate_affordability,
    calculate_mortgage,
    calculate_rent_vs_buy,
    calculate_savings_goal,
)

api = Blueprint("api", __name__, url_prefix="/api")


def _error(msg: str, code: int = 400):
    return jsonify({"success": False, "error": msg}), code


def _ok(data: dict):
    return jsonify({"success": True, "data": data})


# ─────────────────────────────────────────────
#  POST /api/affordability
# ─────────────────────────────────────────────
@api.route("/affordability", methods=["POST"])
def affordability():
    """
    Body (JSON):
        annual_income   : float  (required)
        monthly_debts   : float  (required)
        deposit         : float  (required)
        annual_rate     : float  (required, e.g. 4.5)
        term_years      : int    (required, e.g. 25)
    """
    body = request.get_json(silent=True)
    if not body:
        return _error("Request body must be JSON")

    required = ["annual_income", "monthly_debts", "deposit", "annual_rate", "term_years"]
    missing = [f for f in required if f not in body]
    if missing:
        return _error(f"Missing fields: {', '.join(missing)}")

    try:
        result = calculate_affordability(
            annual_income=float(body["annual_income"]),
            monthly_debts=float(body["monthly_debts"]),
            deposit=float(body["deposit"]),
            annual_rate=float(body["annual_rate"]),
            term_years=int(body["term_years"]),
        )
        return _ok(result)
    except (ValueError, TypeError) as e:
        return _error(str(e))
    except Exception as e:
        return _error(f"Calculation error: {str(e)}", 500)


# ─────────────────────────────────────────────
#  POST /api/mortgage
# ─────────────────────────────────────────────
@api.route("/mortgage", methods=["POST"])
def mortgage():
    """
    Body (JSON):
        home_price              : float  (required)
        down_payment            : float  (required)
        annual_rate             : float  (required)
        term_years              : int    (required)
        extra_monthly_payment   : float  (optional, default 0)
    """
    body = request.get_json(silent=True)
    if not body:
        return _error("Request body must be JSON")

    required = ["home_price", "down_payment", "annual_rate", "term_years"]
    missing = [f for f in required if f not in body]
    if missing:
        return _error(f"Missing fields: {', '.join(missing)}")

    try:
        result = calculate_mortgage(
            home_price=float(body["home_price"]),
            down_payment=float(body["down_payment"]),
            annual_rate=float(body["annual_rate"]),
            term_years=int(body["term_years"]),
            extra_monthly_payment=float(body.get("extra_monthly_payment", 0)),
        )
        return _ok(result)
    except (ValueError, TypeError) as e:
        return _error(str(e))
    except Exception as e:
        return _error(f"Calculation error: {str(e)}", 500)


# ─────────────────────────────────────────────
#  POST /api/rent-vs-buy
# ─────────────────────────────────────────────
@api.route("/rent-vs-buy", methods=["POST"])
def rent_vs_buy():
    """
    Body (JSON):
        purchase_price             : float  (required)
        down_payment               : float  (required)
        monthly_rent               : float  (required)
        mortgage_rate              : float  (required)
        home_appreciation_rate     : float  (required, e.g. 3.0)
        investment_return_rate     : float  (required, e.g. 7.0)
        time_horizon_years         : int    (required)
        mortgage_term_years        : int    (optional, default 25)
        annual_maintenance_pct     : float  (optional, default 1.0)
        annual_rent_increase_pct   : float  (optional, default 2.5)
    """
    body = request.get_json(silent=True)
    if not body:
        return _error("Request body must be JSON")

    required = [
        "purchase_price", "down_payment", "monthly_rent",
        "mortgage_rate", "home_appreciation_rate",
        "investment_return_rate", "time_horizon_years"
    ]
    missing = [f for f in required if f not in body]
    if missing:
        return _error(f"Missing fields: {', '.join(missing)}")

    try:
        result = calculate_rent_vs_buy(
            purchase_price=float(body["purchase_price"]),
            down_payment=float(body["down_payment"]),
            monthly_rent=float(body["monthly_rent"]),
            mortgage_rate=float(body["mortgage_rate"]),
            home_appreciation_rate=float(body["home_appreciation_rate"]),
            investment_return_rate=float(body["investment_return_rate"]),
            time_horizon_years=int(body["time_horizon_years"]),
            mortgage_term_years=int(body.get("mortgage_term_years", 25)),
            annual_maintenance_pct=float(body.get("annual_maintenance_pct", 1.0)),
            annual_rent_increase_pct=float(body.get("annual_rent_increase_pct", 2.5)),
        )
        return _ok(result)
    except (ValueError, TypeError) as e:
        return _error(str(e))
    except Exception as e:
        return _error(f"Calculation error: {str(e)}", 500)


# ─────────────────────────────────────────────
#  POST /api/savings
# ─────────────────────────────────────────────
@api.route("/savings", methods=["POST"])
def savings():
    """
    Body (JSON):
        target_home_price   : float  (required)
        target_deposit_pct  : float  (required, e.g. 20 for 20%)
        current_savings     : float  (required)
        annual_return       : float  (required, e.g. 4.0)
    """
    body = request.get_json(silent=True)
    if not body:
        return _error("Request body must be JSON")

    required = ["target_home_price", "target_deposit_pct", "current_savings", "annual_return"]
    missing = [f for f in required if f not in body]
    if missing:
        return _error(f"Missing fields: {', '.join(missing)}")

    try:
        result = calculate_savings_goal(
            target_home_price=float(body["target_home_price"]),
            target_deposit_pct=float(body["target_deposit_pct"]),
            current_savings=float(body["current_savings"]),
            annual_return=float(body["annual_return"]),
        )
        return _ok(result)
    except (ValueError, TypeError) as e:
        return _error(str(e))
    except Exception as e:
        return _error(f"Calculation error: {str(e)}", 500)


# ─────────────────────────────────────────────
#  GET /api/health
# ─────────────────────────────────────────────
@api.route("/health", methods=["GET"])
def health():
    """Simple health check endpoint."""
    return _ok({"status": "healthy", "service": "FirstHome API", "version": "1.0.0"})
