/**
 * FirstHome — UI & Calculator Controller
 * Handles all DOM updates, animations, and tab management.
 */

// ─── FORMAT HELPERS ──────────────────────────────────────────────────────────
const fmt = (n) => "£" + Math.round(n).toLocaleString("en-GB");
const fmtPct = (n) => Number(n).toFixed(1) + "%";
const fmtShort = (n) => {
  if (Math.abs(n) >= 1_000_000) return "£" + (n / 1_000_000).toFixed(2) + "M";
  if (Math.abs(n) >= 1_000) return "£" + (n / 1_000).toFixed(1) + "K";
  return fmt(n);
};

// ─── ANIMATED VALUE ──────────────────────────────────────────────────────────
function animVal(el, val, formatter = fmt) {
  if (!el) return;
  const old = parseFloat(el.textContent.replace(/[£,K M%]/g, "")) || 0;
  const steps = 20;
  let i = 0;
  const prev = setInterval(() => {
    i++;
    const v = old + (val - old) * (i / steps);
    el.textContent = formatter(v);
    if (i >= steps) { el.textContent = formatter(val); clearInterval(prev); }
  }, 16);
}

// ─── DONUT CHART ─────────────────────────────────────────────────────────────
function setDonut(pct) {
  const circumference = 402;
  const offset = circumference - (Math.min(pct, 100) / 100) * circumference;
  const fill = document.getElementById("donut-fill");
  if (!fill) return;
  fill.style.strokeDashoffset = offset;
  fill.style.stroke = pct < 30 ? "var(--green)" : pct < 50 ? "var(--accent)" : "var(--red)";
  const lbl = document.getElementById("dti-pct");
  if (lbl) lbl.textContent = pct.toFixed(0) + "%";
}

// ─── RANGE SLIDER FILL ───────────────────────────────────────────────────────
function updateSliderFill(input) {
  const min = +input.min, max = +input.max, val = +input.value;
  const pct = ((val - min) / (max - min)) * 100;
  input.style.background = `linear-gradient(to right, var(--accent) ${pct}%, var(--surface2) ${pct}%)`;
}

function initSliders() {
  document.querySelectorAll('input[type="range"]').forEach(input => {
    updateSliderFill(input);
    input.addEventListener("input", () => updateSliderFill(input));
  });
}

// ─── TABS ────────────────────────────────────────────────────────────────────
function switchTab(id) {
  const ids = ["affordability", "mortgage", "rentvsbuy", "savings"];
  document.querySelectorAll(".tab-btn").forEach((b, i) => b.classList.toggle("active", ids[i] === id));
  document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
  const panel = document.getElementById("tab-" + id);
  if (panel) panel.classList.add("active");
  const fn = { affordability: updateAffordability, mortgage: updateMortgage, rentvsbuy: updateRentVsBuy, savings: updateSavings };
  if (fn[id]) fn[id]();
}

// ─── TOAST ───────────────────────────────────────────────────────────────────
let toastTimer;
function showToast(msg = "✨ Updated") {
  const t = document.getElementById("toast");
  if (!t) return;
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove("show"), 2000);
}

// ─── SCROLL REVEAL ───────────────────────────────────────────────────────────
function initReveal() {
  const obs = new IntersectionObserver(
    entries => entries.forEach(e => { if (e.isIntersecting) e.target.classList.add("visible"); }),
    { threshold: 0.1 }
  );
  document.querySelectorAll(".reveal").forEach(el => obs.observe(el));
}

// ─── COUNTER ANIMATION ───────────────────────────────────────────────────────
function initCounters() {
  document.querySelectorAll("[data-count]").forEach(el => {
    const target = +el.dataset.count;
    let current = 0;
    const step = () => {
      current = Math.min(current + Math.ceil(target / 30), target);
      el.textContent = current + (target === 4 ? "" : "+");
      if (current < target) requestAnimationFrame(step);
    };
    setTimeout(step, 1200);
  });
}

// ─── CURSOR ──────────────────────────────────────────────────────────────────
function initCursor() {
  const cursor = document.getElementById("cursor");
  const ring = document.getElementById("cursorRing");
  if (!cursor || !ring) return;
  let mouseX = 0, mouseY = 0, ringX = 0, ringY = 0;
  document.addEventListener("mousemove", e => {
    mouseX = e.clientX; mouseY = e.clientY;
    cursor.style.left = mouseX + "px"; cursor.style.top = mouseY + "px";
  });
  (function animateRing() {
    ringX += (mouseX - ringX) * 0.12;
    ringY += (mouseY - ringY) * 0.12;
    ring.style.left = ringX + "px"; ring.style.top = ringY + "px";
    requestAnimationFrame(animateRing);
  })();
  document.querySelectorAll("a,button,input,[onclick]").forEach(el => {
    el.addEventListener("mouseenter", () => {
      cursor.style.transform = "translate(-50%,-50%) scale(2)";
      ring.style.transform = "translate(-50%,-50%) scale(1.5)";
    });
    el.addEventListener("mouseleave", () => {
      cursor.style.transform = "translate(-50%,-50%) scale(1)";
      ring.style.transform = "translate(-50%,-50%) scale(1)";
    });
  });
}

// ─── SCROLL NAV ──────────────────────────────────────────────────────────────
function initNav() {
  window.addEventListener("scroll", () => {
    document.getElementById("navbar")?.classList.toggle("scrolled", window.scrollY > 80);
  });
}

// ─────────────────────────────────────────────────────────────────────────────
//  TAB 1 — AFFORDABILITY
// ─────────────────────────────────────────────────────────────────────────────
async function updateAffordability() {
  const income = +document.getElementById("af-income").value;
  const debt = +document.getElementById("af-debt").value;
  const deposit = +document.getElementById("af-deposit").value;
  const rate = +document.getElementById("af-rate").value;
  const term = +document.getElementById("af-term").value;

  document.getElementById("af-income-val").textContent = fmt(income);
  document.getElementById("af-debt-val").textContent = fmt(debt);
  document.getElementById("af-deposit-val").textContent = fmt(deposit);
  document.getElementById("af-rate-val").textContent = fmtPct(rate);

  const data = await fetchAffordability({ annual_income: income, monthly_debts: debt, deposit, annual_rate: rate, term_years: term });

  animVal(document.getElementById("af-max-price"), data.max_price);
  animVal(document.getElementById("af-loan"), data.loan_amount);
  animVal(document.getElementById("af-emi"), data.monthly_emi);
  document.getElementById("af-dep-pct").textContent = data.deposit_pct.toFixed(0) + "%";
  document.getElementById("af-ltv").textContent = data.ltv.toFixed(0) + "%";

  setDonut(data.dti_ratio);

  const health = Math.max(0, Math.min(100, 100 - data.dti_ratio));
  document.getElementById("af-health-bar").style.width = health + "%";
  document.getElementById("af-health-label").textContent = data.health_label;

  showToast("Affordability updated");
}

// ─────────────────────────────────────────────────────────────────────────────
//  TAB 2 — MORTGAGE & EMI
// ─────────────────────────────────────────────────────────────────────────────
async function updateMortgage() {
  const price = +document.getElementById("mo-price").value;
  const down = +document.getElementById("mo-down").value;
  const rate = +document.getElementById("mo-rate").value;
  const term = +document.getElementById("mo-term").value;

  document.getElementById("mo-price-val").textContent = fmt(price);
  document.getElementById("mo-down-val").textContent = fmt(down);
  document.getElementById("mo-rate-val").textContent = fmtPct(rate);

  const data = await fetchMortgage({ home_price: price, down_payment: down, annual_rate: rate, term_years: term });

  animVal(document.getElementById("mo-emi"), data.monthly_emi);
  animVal(document.getElementById("mo-total"), data.total_paid);
  animVal(document.getElementById("mo-total-int"), data.total_interest);

  document.getElementById("mo-payoff").textContent = "Payoff: " + data.payoff_date;
  document.getElementById("mo-int-pct").textContent = fmtPct(data.int_pct);
  document.getElementById("mo-prin-pct").textContent = fmtPct(data.principal_pct);
  document.getElementById("mo-int-bar").style.width = data.int_pct + "%";
  document.getElementById("mo-prin-bar").style.width = data.principal_pct + "%";

  // Amortisation preview rows
  const rows = (data.preview_rows || []).slice(0, 6);
  document.getElementById("amort-rows").innerHTML = rows.map(r => `
    <div class="amort-row">
      <span style="color:var(--text3)">${r.month}</span>
      <span>${fmt(r.payment)}</span>
      <span style="color:var(--green)">${fmt(r.principal)}</span>
      <span style="color:var(--red)">${fmt(r.interest)}</span>
    </div>`).join("");

  showToast("Mortgage recalculated");
}

// ─────────────────────────────────────────────────────────────────────────────
//  TAB 3 — RENT vs BUY
// ─────────────────────────────────────────────────────────────────────────────
async function updateRentVsBuy() {
  const price = +document.getElementById("rvb-price").value;
  const down = +document.getElementById("rvb-down").value;
  const rent = +document.getElementById("rvb-rent").value;
  const rate = +document.getElementById("rvb-rate").value;
  const appr = +document.getElementById("rvb-appr").value;
  const inv = +document.getElementById("rvb-inv").value;
  const years = +document.getElementById("rvb-years").value;

  document.getElementById("rvb-price-val").textContent = fmt(price);
  document.getElementById("rvb-down-val").textContent = fmt(down);
  document.getElementById("rvb-rent-val").textContent = fmt(rent);
  document.getElementById("rvb-rate-val").textContent = fmtPct(rate);
  document.getElementById("rvb-appr-val").textContent = fmtPct(appr);
  document.getElementById("rvb-inv-val").textContent = fmtPct(inv);

  const data = await fetchRentVsBuy({
    purchase_price: price, down_payment: down, monthly_rent: rent,
    mortgage_rate: rate, home_appreciation_rate: appr,
    investment_return_rate: inv, time_horizon_years: years,
  });

  animVal(document.getElementById("rvb-buy-cost"), Math.max(0, data.total_mortgage_paid || 0));
  animVal(document.getElementById("rvb-rent-cost"), Math.max(0, data.total_rent_paid || 0));
  animVal(document.getElementById("rvb-diff"), Math.abs(data.wealth_difference));

  const buyWins = data.verdict === "buy";
  document.getElementById("rvb-diff-sub").textContent = data.recommendation;

  const verdict = document.getElementById("rvb-verdict");
  verdict.className = `verdict ${data.verdict}`;
  document.getElementById("rvb-icon").textContent = buyWins ? "🏠" : data.verdict === "rent" ? "🏢" : "⚖️";
  document.getElementById("rvb-title").textContent = buyWins
    ? "Buying is the better financial move"
    : data.verdict === "rent"
    ? "Renting + investing beats buying here"
    : "It's too close to call";
  document.getElementById("rvb-explanation").textContent = data.recommendation;

  const buyPct = Math.max(10, Math.min(90, 50 + (data.wealth_difference / (price + 1)) * 50));
  document.getElementById("rvb-bar").style.width = buyPct + "%";
  document.getElementById("rvb-buy-pct").textContent = buyWins ? "Advantage: Buy" : "Advantage: Rent";

  showToast("Analysis complete");
}

// ─────────────────────────────────────────────────────────────────────────────
//  TAB 4 — SAVINGS GOAL
// ─────────────────────────────────────────────────────────────────────────────
async function updateSavings() {
  const price = +document.getElementById("sv-price").value;
  const depPct = +document.getElementById("sv-dep").value;
  const curr = +document.getElementById("sv-curr").value;
  const ret = +document.getElementById("sv-ret").value;

  document.getElementById("sv-price-val").textContent = fmt(price);
  document.getElementById("sv-dep-val").textContent = depPct + "%";
  document.getElementById("sv-curr-val").textContent = fmt(curr);
  document.getElementById("sv-ret-val").textContent = fmtPct(ret);

  const data = await fetchSavings({
    target_home_price: price, target_deposit_pct: depPct,
    current_savings: curr, annual_return: ret,
  });

  animVal(document.getElementById("sv-target"), data.deposit_target);
  document.getElementById("sv-remain").textContent = "Still needed: " + fmt(data.remaining_needed);

  const progress = data.progress_pct;
  document.getElementById("sv-progress-bar").style.width = progress + "%";
  document.getElementById("sv-progress-pct").textContent = progress.toFixed(0) + "%";

  const scenarios = data.scenarios || {};
  const scKeys = ["1yr", "2yr", "3yr", "5yr"];
  const icons = { "1yr": "⚡", "2yr": "🎯", "3yr": "🌱", "5yr": "🕰️" };
  const colors = {
    "1yr": "rgba(200,169,110,0.15)", "2yr": "rgba(94,158,126,0.15)",
    "3yr": "rgba(94,94,180,0.15)", "5yr": "rgba(192,96,96,0.15)"
  };

  scKeys.forEach(key => {
    const s = scenarios[key];
    if (!s) return;
    const el = document.getElementById(`sv-${key}`);
    const detailEl = document.getElementById(`sv-${key}-detail`);
    if (el) el.textContent = s.already_achieved ? "Already there! 🎉" : fmt(s.monthly_payment) + "/mo";
    const months = key === "1yr" ? 12 : key === "2yr" ? 24 : key === "3yr" ? 36 : 60;
    const yrs = months / 12;
    if (detailEl) detailEl.textContent = s.already_achieved ? "Your savings cover this" : `Save for ${yrs} year${yrs > 1 ? "s" : ""}`;
  });

  showToast("Savings plan updated");
}

// ─── INIT ────────────────────────────────────────────────────────────────────
async function init() {
  initCursor();
  initNav();
  initReveal();
  initCounters();
  initSliders();
  await checkApiHealth();
  await updateAffordability();
}

document.addEventListener("DOMContentLoaded", init);
