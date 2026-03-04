# 🏠 FirstHome — First-Time Homebuyer Financial Companion

> A full-stack financial tool that gives first-time homebuyers the clarity they need — no ads, no sign-ups, no fluff.

Built with **Python (Flask + numpy_financial)** backend and a **pure HTML/CSS/JS** frontend.

---

## 📐 Project Structure

```
firsthome/
├── frontend/                   # Static frontend (HTML/CSS/JS)
│   ├── index.html              # Main application page
│   ├── css/
│   │   └── style.css           # All styles (dark theme, animations)
│   └── js/
│       ├── api.js              # API client + local fallback calculators
│       └── ui.js               # UI rendering, tab management, animations
│
├── backend/                    # Flask REST API
│   ├── app.py                  # Application factory + entry point
│   ├── requirements.txt        # Python dependencies
│   ├── calculators/            # numpy_financial calculation modules
│   │   ├── __init__.py
│   │   ├── affordability.py    # Max price, DTI, stress testing
│   │   ├── mortgage.py         # EMI, full amortisation schedule
│   │   ├── rent_vs_buy.py      # NPV-based wealth comparison
│   │   └── savings.py          # PMT savings goal planner
│   └── routes/
│       ├── __init__.py
│       └── api.py              # All /api/* endpoints
│
├── README.md
└── .gitignore
```

---

## 🧮 The Four Calculators

### 1. Affordability Calculator
- **4.5× income multiplier** (UK standard)
- Live **Debt-to-Income (DTI)** ratio via animated donut chart
- **FCA stress test** at rate + 3%
- LTV, deposit percentage, health score

### 2. Mortgage & Amortisation
- Monthly EMI using `numpy_financial.pmt()`
- Full amortisation schedule with `ipmt()` / `ppmt()`
- Principal vs interest breakdown
- Payoff date calculation

### 3. Rent vs Buy NPV Analysis
- True NPV comparison using `numpy_financial.npv()`
- Accounts for: home appreciation, deposit investment returns, rent inflation, maintenance, stamp duty
- Breakeven year calculation
- Green/Red verdict with plain-English recommendation

### 4. Savings Goal Planner
- Reverse PMT: calculates monthly savings to hit a target deposit
- 4 time horizons: 1yr, 2yr, 3yr, 5yr
- Milestone tracker: 25% / 50% / 75% / 100% of deposit
- Future value of existing savings compounded at return rate

---

## 🚀 Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
python app.py
```

The API will start at `http://localhost:5000`

Test it:
```bash
curl http://localhost:5000/api/health
```

### Frontend

Option 1 — Open directly:
```
open frontend/index.html
```

Option 2 — Live Server (VS Code extension) pointing at `frontend/`

Option 3 — Served by Flask (already configured in `app.py`)

---

## 🔌 API Reference

All endpoints accept and return JSON.

### `POST /api/affordability`
```json
{
  "annual_income": 65000,
  "monthly_debts": 400,
  "deposit": 50000,
  "annual_rate": 4.5,
  "term_years": 25
}
```

### `POST /api/mortgage`
```json
{
  "home_price": 450000,
  "down_payment": 90000,
  "annual_rate": 4.5,
  "term_years": 25,
  "extra_monthly_payment": 0
}
```

### `POST /api/rent-vs-buy`
```json
{
  "purchase_price": 400000,
  "down_payment": 80000,
  "monthly_rent": 1800,
  "mortgage_rate": 4.5,
  "home_appreciation_rate": 3.0,
  "investment_return_rate": 7.0,
  "time_horizon_years": 10,
  "mortgage_term_years": 25,
  "annual_maintenance_pct": 1.0,
  "annual_rent_increase_pct": 2.5
}
```

### `POST /api/savings`
```json
{
  "target_home_price": 400000,
  "target_deposit_pct": 20,
  "current_savings": 15000,
  "annual_return": 4.0
}
```

### `GET /api/health`
```json
{ "success": true, "data": { "status": "healthy", "version": "1.0.0" } }
```

---

## 🌐 Offline Mode

The frontend includes **full local fallback calculators** in `api.js`. If the Flask backend is unavailable, all four tools continue to work using JavaScript implementations of the same financial formulas. The API status badge in the nav shows the connection state.

---

## 🎨 Design Principles

- **Dark, warm-gold palette** — premium feel vs. sterile white/blue of competitors
- **Cormorant Garamond** serif for financial figures — gravitas and readability
- **Custom animated cursor** with magnetic ring
- **Live calculations** — every slider drag triggers recalculation
- **No ads, no sign-ups, no third-party trackers**

---

## 🛣️ Roadmap (Next Steps)

- [ ] Chart.js amortisation visualisation (interactive area chart)
- [ ] PDF export of full financial summary report
- [ ] Property-specific stamp duty calculator (UK bands)
- [ ] Historic mortgage rate integration (Bank of England API)
- [ ] Shared results via URL params
- [ ] Dark/light mode toggle

---

## 🏫 Context

Built as part of UCL MSc Business Analytics FinTech module.
Demonstrates: `numpy_financial`, REST API design, full-stack architecture, financial modelling.

---

## 📄 License

MIT — free to use, modify, and deploy.
