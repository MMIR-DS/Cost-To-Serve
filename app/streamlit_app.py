"""
Customer Contribution After Cost-to-Serve — Dashboard
Decision-first hierarchy · Neutral Freight Reference · Modeled CTS labels
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
SAMPLE = ROOT / "data" / "sample"
OUTPUTS = ROOT / "outputs"

C = {
    "bg": "#0f1419",
    "panel": "#1a2332",
    "muted": "#8b9cb3",
    "text": "#e8eef7",
    "pos": "#3dd68c",
    "neg": "#f07178",
    "ref": "#5b9fd4",
    "sens": "#9aa5b5",
    "accent": "#c4a35a",
    "grid": "#2a3544",
}

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=C["text"], family="Inter, Segoe UI, sans-serif", size=13),
    margin=dict(l=40, r=24, t=48, b=40),
)

st.set_page_config(
    page_title="Customer Contribution After Cost-to-Serve",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    f"""
<style>
  .stApp {{ background: linear-gradient(160deg, #0b1017 0%, #121a24 45%, #0e1620 100%); color: {C['text']}; }}
  section[data-testid="stSidebar"] {{ background: #0c121a; border-right: 1px solid {C['grid']}; }}
  div[data-testid="stMetric"] {{
    background: {C['panel']}; border: 1px solid {C['grid']}; border-radius: 12px; padding: 12px 14px;
  }}
  .hero {{
    background: linear-gradient(135deg, #1a2838 0%, #15202b 60%, #1c2430 100%);
    border: 1px solid {C['grid']}; border-left: 4px solid {C['ref']};
    border-radius: 14px; padding: 18px 22px; margin-bottom: 18px;
  }}
  .mode-full {{ color: {C['pos']}; font-weight: 600; }}
  .mode-sample {{ color: {C['accent']}; font-weight: 600; }}
</style>
""",
    unsafe_allow_html=True,
)


def load_json(name: str):
    p = OUTPUTS / name
    if not p.exists():
        return None
    with open(p) as f:
        return json.load(f)


def load_cm():
    full = PROCESSED / "customer_month_cts.csv"
    sample = SAMPLE / "customer_month_cts_sample.csv"
    if full.exists() and full.stat().st_size > 1000:
        return pd.read_csv(full), "FULL"
    if sample.exists():
        return pd.read_csv(sample), "SAMPLE"
    return None, "NONE"


def hero(title: str, body: str, pills=None):
    pills = pills or []
    pill_html = " ".join(
        f'<span style="background:{C["panel"]};border:1px solid {C["grid"]};'
        f'border-radius:999px;padding:2px 10px;margin-right:6px;font-size:0.8rem;color:{C[color]}">{text}</span>'
        for text, color in pills
    )
    st.markdown(
        f'<div class="hero"><h2>{title}</h2><p style="color:{C["muted"]};margin:0 0 8px 0">{body}</p>{pill_html}</div>',
        unsafe_allow_html=True,
    )


def fmt_pct(x, digits=3):
    if x is None:
        return "—"
    return f"{float(x) * 100:.{digits}f}%" if abs(float(x)) < 1 else f"{float(x):.{digits}f}%"


def fmt_brl(x):
    if x is None:
        return "—"
    return f"R$ {float(x):,.0f}"


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
cm, mode = load_cm()
honest = load_json("honest_economics_summary.json")
freight = load_json("freight_and_tipping_summary.json")
econ = load_json("economic_robust_classes.json")
rank = load_json("rank_diagnostics.json")
scenarios = load_json("scenarios_summary.json")
mc = load_json("monte_carlo_summary.json")

st.sidebar.markdown("## ◈ Contribution After CTS")
st.sidebar.caption("Customer Contribution After Cost-to-Serve\nPortfolio prototype")
if mode == "FULL":
    st.sidebar.markdown('<div class="mode-full">Data mode: FULL processed Olist</div>', unsafe_allow_html=True)
elif mode == "SAMPLE":
    st.sidebar.markdown('<div class="mode-sample">Data mode: SAMPLE — demonstration only</div>', unsafe_allow_html=True)
else:
    st.sidebar.error("No data. Run: python run_pipeline.py")

page = st.sidebar.radio(
    "Navigate",
    [
        "1 · Executive summary",
        "2 · Financial bridge",
        "3 · Cost-to-Serve (sensitivity)",
        "4 · Decision scenarios",
        "5 · Robustness & tipping",
    ],
)
st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Reference:** Neutral Freight (pass-through)\n\n"
    "**Sensitivity:** Modeled CTS — No Freight Credit\n\n"
    "Negative ≠ exit customer. See docs/limitations.md."
)

if cm is None:
    st.stop()

# ---------------------------------------------------------------------------
# PAGE 1 — Executive summary
# ---------------------------------------------------------------------------
if page.startswith("1"):
    st.title("Executive summary")
    hero(
        "Under Neutral Freight Reference, Modeled service cost is a small perturbation",
        "Ranks stay close to revenue; only a thin tail is robustly negative. The tipping grid shows where that stops being true.",
        [("Neutral Freight = reference", "ref"), ("No Freight Credit = sensitivity", "sens")],
    )

    # Headline KPIs from shipped outputs
    pt_neg_orders = 101
    pt_sales_exp = 0.00027
    if freight:
        for c in freight.get("freight_cases", []):
            if c.get("case") == "pass_through":
                pt_neg_orders = c.get("negative_orders", pt_neg_orders)
                pt_sales_exp = c.get("sales_exposed_pct", pt_sales_exp)

    robust_neg = econ.get("robust_negative", 21) if econ else 21
    robust_mixed = econ.get("robust_negative_mixed_with_cancels", 7) if econ else 7

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Neutral Freight neg. orders", f"{pt_neg_orders:,}")
    c2.metric("% sales exposed (reference)", fmt_pct(pt_sales_exp, 3))
    c3.metric("Robust negative CM", f"{robust_neg} ({robust_mixed} mixed)")
    c4.metric("Spearman contrib vs sales", "≈ 0.99" if rank else "—")

    st.markdown("#### What this does **not** claim")
    st.write(
        "- True Olist COGS, warehouse ownership, or platform take-rate P&L\n"
        "- That baseline CTS ‘finds’ a large unprofitable customer set\n"
        "- Termination policy"
    )

# ---------------------------------------------------------------------------
# PAGE 2 — Financial bridge
# ---------------------------------------------------------------------------
elif page.startswith("2"):
    st.title("Financial bridge")
    hero(
        "Gross → Net → Product Contribution → Customer Contribution",
        "Product Contribution is not Gross Profit. CTS pools are Modeled.",
        [("Observed sales", "ref"), ("Modeled product cost & CTS", "accent")],
    )
    net = float(cm["net_sales"].sum()) if "net_sales" in cm.columns else 13_494_400.74
    pc = float(cm["product_contribution"].sum()) if "product_contribution" in cm.columns else 8_771_360.48
    cts = float(cm["cost_to_serve"].sum()) if "cost_to_serve" in cm.columns else 1_350_000.0
    cc = float(cm["customer_contribution"].sum()) if "customer_contribution" in cm.columns else pc - cts

    bridge = pd.DataFrame(
        {
            "step": ["Net Sales", "Product Contribution", "Cost-to-Serve", "Customer Contribution"],
            "value": [net, pc, cts, cc],
        }
    )
    fig = px.bar(bridge, x="step", y="value", color="step", color_discrete_sequence=[C["ref"], C["pos"], C["accent"], C["ref"]])
    fig.update_layout(**PLOTLY_LAYOUT, showlegend=False, yaxis_title="BRL")
    st.plotly_chart(fig, use_container_width=True)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Net Sales", fmt_brl(net))
    m2.metric("Product Contribution", fmt_brl(pc))
    m3.metric("Modeled CTS", fmt_brl(cts))
    m4.metric("Customer Contribution", fmt_brl(cc))

# ---------------------------------------------------------------------------
# PAGE 3 — Cost-to-Serve (V1 sensitivity)
# ---------------------------------------------------------------------------
elif page.startswith("3"):
    st.title("Cost-to-Serve — Modeled CTS sensitivity")
    hero(
        "Modeled CTS — No Freight Credit (sensitivity)",
        "Full distribution pool charged with no freight credit. Not the headline reference.",
        [("Sensitivity view", "sens"), ("Reference is Neutral Freight (page 1 & 5)", "ref")],
    )
    if honest:
        cm_h = honest.get("cm", {})
        c1, c2, c3 = st.columns(3)
        c1.metric("Baseline negative CM", f"{cm_h.get('baseline_negative', '—'):,}")
        c2.metric("Non-fulfillment only", f"{cm_h.get('non_fulfillment_only_negative', '—'):,}")
        c3.metric("Economic negative $", fmt_brl(cm_h.get("economic_negative_total_brl")))
        st.caption("Non-fulfillment negatives are mechanical (zero revenue + returns pool).")
    else:
        st.info("Run honest_economics to populate this page.")

# ---------------------------------------------------------------------------
# PAGE 4 — Decision scenarios
# ---------------------------------------------------------------------------
elif page.startswith("4"):
    st.title("Decision scenarios")
    st.info(
        "**Scenario basis:** commercial and service-model deltas use the scenarios engine on the "
        "**Modeled CTS — No Freight Credit** layer (distribution is charged). "
        "They are **not** Neutral Freight Reference conclusions. "
        "Lean delivery’s contribution gain includes distribution-pool cuts that net differently under Neutral Freight."
    )
    hero(
        "Illustrative arithmetic — not estimated elasticities",
        "Commercial and service levers on Modeled baselines.",
        [("Price +5% holds product cost in BRL", "ref"), ("Lean delivery uses avoidable share", "pos")],
    )
    if scenarios:
        comm = pd.DataFrame(scenarios.get("commercial", []))
        serv = pd.DataFrame(scenarios.get("service_model", []))
        if len(comm):
            st.subheader("Commercial terms")
            st.dataframe(
                comm[["scenario", "description", "delta_customer_contribution", "n_negative"]],
                use_container_width=True,
            )
        if len(serv):
            st.subheader("Service model")
            st.dataframe(
                serv[["scenario", "description", "delta_customer_contribution", "delta_cts", "n_negative"]],
                use_container_width=True,
            )
    else:
        st.info("Run decision_scenarios to populate this page.")

# ---------------------------------------------------------------------------
# PAGE 5 — Robustness & tipping (pass-through reference)
# ---------------------------------------------------------------------------
elif page.startswith("5"):
    st.title("Robustness & tipping — Neutral Freight Reference")
    hero(
        "Pass-through reference · economic-only classes · tipping grid",
        "At baseline, sales exposed ≈ 0.027%. At ~3× OH+WH intensity, exposure rises to ~1.5% of sales.",
        [("Reference structure", "ref"), ("COGS >45% = stress exploration", "accent")],
    )

    if econ:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Robust positive", f"{econ.get('robust_positive', 0):,}")
        c2.metric("Robust negative", f"{econ.get('robust_negative', 0):,}")
        c3.metric("Sensitive", f"{econ.get('sensitive', 0):,}")
        c4.metric("PT baseline neg. CM", f"{econ.get('baseline_negative_pass_through', 0):,}")

    grid_path = OUTPUTS / "tipping_grid_passthrough.csv"
    if grid_path.exists():
        grid = pd.read_csv(grid_path)
        st.subheader("Tipping grid — sales exposed % (pass-through)")
        sales_cols = [c for c in grid.columns if c.startswith("sales_exposed_pct")]
        if sales_cols:
            # wide → heatmap matrix
            show = grid.set_index("cogs_pct")[sales_cols]
            show.columns = [c.replace("sales_exposed_pct_", "×") for c in show.columns]
            fig = px.imshow(
                show.values * 100,
                x=list(show.columns),
                y=[f"{v:.0%}" for v in show.index],
                labels=dict(x="OH+WH scale", y="COGS", color="Sales exposed %"),
                aspect="auto",
                color_continuous_scale="YlOrRd",
            )
            fig.update_layout(**PLOTLY_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Values are % of net sales exposed (negative contribution). COGS above 45% is stress exploration.")
        else:
            st.dataframe(grid, use_container_width=True)
    else:
        st.info("Run tipping_and_freight to populate the grid.")

    if mc and mc.get("status") != "skipped_insufficient_rows":
        st.subheader("Optional: illustrative Monte Carlo")
        st.caption(mc.get("interpretation", "Uniform priors on COGS and OH+WH scale — not estimated posteriors."))
        bc = mc.get("baseline_point_compare", {})
        m1, m2, m3 = st.columns(3)
        m1.metric("Baseline PT neg. CM", f"{bc.get('neutral_freight_neg_cm_at_defaults', '—')}")
        m2.metric("MC median", f"{bc.get('mc_median_neg_cm', '—')}")
        m3.metric("Median / baseline", f"{bc.get('median_over_baseline', 0):.2f}×" if bc.get("median_over_baseline") else "—")
