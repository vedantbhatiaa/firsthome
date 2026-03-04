/**
 * FirstHome — API Client
 * Connects the frontend to the Flask backend.
 * Falls back to local JS calculations if API is unavailable.
 */

const API_BASE = "http://localhost:5000/api";
let apiOnline = false;

// ─── Health Check ───────────────────────────────────────────────────────────
async function checkApiHealth() {
  const dot = document.getElementById("api-dot");
  const label = document.getElementById("api-label");
  if (dot) dot.className = "api-dot checking";
  if (label) label.textContent = "Connecting...";

  try {
    const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(3000) });
    const json = await res.json();
    apiOnline = json.success;
    if (dot) dot.className = `api-dot ${apiOnline ? "online" : "offline"}`;
    if (label) label.textContent = apiOnline ? "API Connected" : "Offline Mode";
  } catch {
    apiOnline = false;
    if (dot) dot.className = "api-dot offline";
    if (label) label.textContent = "Offline (local calc)";
  }
}

// ─── Generic POST helper ─────────────────────────────────────────────────────
async function apiPost(endpoint, body) {
  const res = await fetch(`${API_BASE}/${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(8000),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const json = await res.json();
  if (!json.success) throw new Error(json.error || "Unknown error");
  return json.data;
}

// ─── Affordability API ───────────────────────────────────────────────────────
async function fetchAffordability(params) {
  if (!apiOnline) return localAffordability(params);
  try {
    return await apiPost("affordability", params);
  } catch (e) {
    console.warn("API error, falling back to local:", e);
    return localAffordability(params);
  }
}

// ─── Mortgage API ────────────────────────────────────────────────────────────
async function fetchMortgage(params) {
  if (!apiOnline) return localMortgage(params);
  try {
    return await apiPost("mortgage", params);
  } catch (e) {
    console.warn("API error, falling back to local:", e);
    return localMortgage(params);
  }
}

// ─── Rent vs Buy API ─────────────────────────────────────────────────────────
async function fetchRentVsBuy(params) {
  if (!apiOnline) return localRentVsBuy(params);
  try {
    return await apiPost("rent-vs-buy", params);
  } catch (e) {
    console.warn("API error, falling back to local:", e);
    return localRentVsBuy(params);
  }
}

// ─── Savings API ─────────────────────────────────────────────────────────────
async function fetchSavings(params) {
  if (!apiOnline) return localSavings(params);
  try {
    return await apiPost("savings", params);
  } catch (e) {
    console.warn("API error, falling back to local:", e);
    return localSavings(params);
  }
}

// ─── LOCAL FALLBACK CALCULATIONS ─────────────────────────────────────────────
// Mirror of the Python numpy_financial logic in vanilla JS

function localPMT(rate, nper, pv) {
  if (rate === 0) return -pv / nper;
  const pvif = Math.pow(1 + rate, nper);
  return -(rate * pv * pvif) / (pvif - 1);
}

function localFV(rate, nper, pmt, pv = 0) {
  const pvif = Math.pow(1 + rate, nper);
  return -(pv * pvif + pmt * ((pvif - 1) / rate));
}

function localAffordability({ annual_income, monthly_debts, deposit, annual_rate, term_years }) {
  const r = annual_rate / 100 / 12;
  const n = term_years * 12;
  const maxPrice = annual_income * 4.5 + deposit;
  const loan = maxPrice - deposit;
  const emi = Math.abs(localPMT(r, n, loan));
  const dti = ((emi + monthly_debts) / (annual_income / 12)) * 100;
  const depPct = (deposit / maxPrice) * 100;
  const ltv = 100 - depPct;
  const health = dti < 28 ? 90 : dti < 36 ? 70 : dti < 43 ? 50 : 20;
  const healthLabel = dti < 28 ? "Excellent" : dti < 36 ? "Good" : dti < 43 ? "Stretching" : "Over-extended";
  const totalPaid = emi * n;
  const totalInterest = totalPaid - loan;

  return {
    max_price: maxPrice,
    loan_amount: loan,
    monthly_emi: emi,
    dti_ratio: dti,
    deposit_pct: depPct,
    ltv,
    health_score: health,
    health_label: healthLabel,
    total_interest: totalInterest,
    total_paid: totalPaid,
  };
}

function localMortgage({ home_price, down_payment, annual_rate, term_years }) {
  const loan = home_price - down_payment;
  const r = annual_rate / 100 / 12;
  const n = term_years * 12;
  const emi = Math.abs(localPMT(r, n, loan));
  const totalPaid = emi * n;
  const totalInterest = totalPaid - loan;
  const intPct = (totalInterest / totalPaid) * 100;

  // Build first 12 rows
  let bal = loan;
  const previewRows = [];
  const yearlySum = [];

  for (let m = 1; m <= n; m++) {
    const intPay = bal * r;
    const prinPay = emi - intPay;
    bal = Math.max(0, bal - prinPay);

    if (m <= 12) {
      const d = new Date();
      d.setMonth(d.getMonth() + m);
      previewRows.push({
        month: m,
        date: d.toLocaleDateString("en-GB", { month: "short", year: "numeric" }),
        payment: emi,
        principal: prinPay,
        interest: intPay,
        balance: bal,
      });
    }

    if (m % 12 === 0) {
      const yr = m / 12;
      yearlySum.push({ year: yr, balance: bal });
    }
  }

  const payoffDate = new Date();
  payoffDate.setMonth(payoffDate.getMonth() + n);

  return {
    loan_amount: loan,
    monthly_emi: emi,
    total_paid: totalPaid,
    total_interest: totalInterest,
    int_pct: intPct,
    principal_pct: 100 - intPct,
    payoff_date: payoffDate.toLocaleDateString("en-GB", { month: "long", year: "numeric" }),
    preview_rows: previewRows,
    yearly_summary: yearlySum,
  };
}

function localRentVsBuy({ purchase_price, down_payment, monthly_rent, mortgage_rate, home_appreciation_rate, investment_return_rate, time_horizon_years }) {
  const loan = purchase_price - down_payment;
  const r = mortgage_rate / 100 / 12;
  const n = 25 * 12;
  const emi = Math.abs(localPMT(r, n, loan));
  const horizonMonths = time_horizon_years * 12;

  const homeFV = purchase_price * Math.pow(1 + home_appreciation_rate / 100, time_horizon_years);
  const remainingN = n - horizonMonths;
  const remainingBal = remainingN > 0 ? Math.abs(localPMT(r, remainingN, loan) * (Math.pow(1 + r, remainingN) - 1) / r) : 0;

  const totalMortgagePaid = emi * Math.min(horizonMonths, n);
  const totalMaintenance = purchase_price * 0.01 * time_horizon_years;
  const buyNetWealth = (homeFV - remainingBal) - (totalMortgagePaid + totalMaintenance);

  const investedDeposit = down_payment * Math.pow(1 + investment_return_rate / 100, time_horizon_years);
  const totalRentPaid = monthly_rent * 12 * time_horizon_years;
  const rentNetWealth = investedDeposit - totalRentPaid;

  const diff = buyNetWealth - rentNetWealth;
  const verdict = Math.abs(diff) < purchase_price * 0.02 ? "neutral" : diff > 0 ? "buy" : "rent";
  const recommendation = verdict === "neutral"
    ? `It's essentially a tie over ${time_horizon_years} years. Your lifestyle should decide.`
    : verdict === "buy"
    ? `Buying builds £${Math.abs(Math.round(diff)).toLocaleString()} more wealth over ${time_horizon_years} years.`
    : `Renting and investing generates £${Math.abs(Math.round(diff)).toLocaleString()} more over ${time_horizon_years} years.`;

  return {
    buy_net_wealth: buyNetWealth,
    home_future_value: homeFV,
    total_mortgage_paid: totalMortgagePaid,
    rent_net_wealth: rentNetWealth,
    total_rent_paid: totalRentPaid,
    invested_deposit_value: investedDeposit,
    monthly_emi: emi,
    wealth_difference: diff,
    verdict,
    recommendation,
  };
}

function localSavings({ target_home_price, target_deposit_pct, current_savings, annual_return }) {
  const target = target_home_price * (target_deposit_pct / 100);
  const remaining = Math.max(0, target - current_savings);
  const progress = Math.min(100, (current_savings / target) * 100);
  const r = annual_return / 100 / 12;

  function pmt(months) {
    const fvCurr = current_savings * Math.pow(1 + r, months);
    const gap = target - fvCurr;
    if (gap <= 0) return 0;
    return Math.abs(localPMT(r, months, 0) * gap / (Math.pow(1 + r, months) - 1)) || gap / months;
  }

  const scenarios = {
    "1yr": { months: 12, label: "Aggressive (1 year)", icon: "⚡" },
    "2yr": { months: 24, label: "Balanced (2 years)", icon: "🎯" },
    "3yr": { months: 36, label: "Patient (3 years)", icon: "🌱" },
    "5yr": { months: 60, label: "Relaxed (5 years)", icon: "🕰️" },
  };

  for (const key in scenarios) {
    const s = scenarios[key];
    const payment = pmt(s.months);
    s.monthly_payment = payment;
    s.already_achieved = payment === 0;
    s.total_contributions = payment * s.months;
  }

  return {
    deposit_target: target,
    remaining_needed: remaining,
    progress_pct: progress,
    scenarios,
  };
}
