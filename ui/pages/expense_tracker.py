"""
ui/pages/expense_tracker.py
-----------------------------
Streamlit page: Expense Tracker

Lets the user upload UPI screenshots / receipts → OCR → categorise → summarise.
Maintains a session-state list of expenses for the current session.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from tools.expense.ocr_parser import extract_text_from_image, parse_upi_message, save_uploaded_image
from tools.expense.categorizer import categorize_expense, summarise_expenses

DISCLAIMER = "⚠️ *This is for educational analysis, not certified financial advice.*"

CATEGORY_COLORS = {
    "Food":          "#FF6B6B",
    "Transport":     "#4ECDC4",
    "Utilities":     "#45B7D1",
    "Shopping":      "#96CEB4",
    "Healthcare":    "#FFEAA7",
    "Entertainment": "#DDA0DD",
    "Education":     "#98D8C8",
    "Rent":          "#F0A500",
    "Insurance":     "#A8D8EA",
    "Investments":   "#88D498",
    "Other":         "#B2B2B2",
}


def render():
    st.title("💸 Expense Tracker")
    st.caption(DISCLAIMER)

    # ── Session State Initialisation ──────────────────────────────────────────
    if "expenses" not in st.session_state:
        st.session_state.expenses = []  # list of dicts

    # ── Upload Section ────────────────────────────────────────────────────────
    st.subheader("📤 Upload Receipt / UPI Screenshot")

    col_upload, col_manual = st.columns([1, 1])

    with col_upload:
        uploaded_file = st.file_uploader(
            "Upload image (JPG / PNG / WEBP)",
            type=["jpg", "jpeg", "png", "webp"],
            help="Upload a UPI payment screenshot or printed receipt",
        )

        if uploaded_file:
            st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)

            if st.button("🔍 Extract & Categorise", type="primary"):
                with st.spinner("Running OCR…"):
                    try:
                        save_path = save_uploaded_image(
                            uploaded_file.getvalue(), uploaded_file.name
                        )
                        ocr_result  = extract_text_from_image(save_path)
                        upi_data    = parse_upi_message(ocr_result["raw_text"])
                        cat_result  = categorize_expense(
                            vendor=upi_data.get("vendor") or "",
                            upi_id=upi_data.get("upi_id") or "",
                            amount=upi_data.get("amount") or 0.0,
                        )

                        # Store in session
                        st.session_state.expenses.append({
                            "vendor":   upi_data.get("vendor") or "Unknown",
                            "amount":   upi_data.get("amount") or 0.0,
                            "category": cat_result["category"],
                            "date":     upi_data.get("date") or "—",
                            "upi_id":   upi_data.get("upi_id") or "—",
                            "conf_ocr": ocr_result["confidence"],
                            "conf_cat": cat_result["confidence"],
                            "method":   cat_result["method"],
                        })

                        # Show extracted details
                        st.success("✅ Extraction complete!")
                        with st.expander("🔎 OCR Raw Text", expanded=False):
                            st.code(ocr_result["raw_text"])

                        r1, r2, r3 = st.columns(3)
                        r1.metric("Amount",   f"₹{upi_data.get('amount') or 0:.2f}")
                        r2.metric("Category", cat_result["category"])
                        r3.metric("OCR Confidence", f"{ocr_result['confidence']:.0%}")

                    except FileNotFoundError as e:
                        st.error(str(e))
                    except RuntimeError as e:
                        st.error(str(e))
                        st.info(
                            "If Tesseract is not installed:\n"
                            "1. Download from https://github.com/UB-Mannheim/tesseract/wiki\n"
                            "2. Set `TESSERACT_CMD` in your `.env` file."
                        )

    with col_manual:
        st.markdown("**✏️ Or enter manually:**")
        m_vendor   = st.text_input("Vendor / Description", placeholder="Zomato, Uber, Amazon…")
        m_amount   = st.number_input("Amount (₹)", min_value=0.0, step=10.0, format="%.2f")
        m_date     = st.date_input("Date")
        m_upi      = st.text_input("UPI ID (optional)", placeholder="vendor@bank")

        if st.button("➕ Add Expense", type="secondary"):
            if m_vendor and m_amount > 0:
                cat_result = categorize_expense(m_vendor, m_upi, m_amount)
                st.session_state.expenses.append({
                    "vendor":   m_vendor,
                    "amount":   float(m_amount),
                    "category": cat_result["category"],
                    "date":     str(m_date),
                    "upi_id":   m_upi or "—",
                    "conf_ocr": 1.0,
                    "conf_cat": cat_result["confidence"],
                    "method":   cat_result["method"],
                })
                st.success(f"Added: {m_vendor} → {cat_result['category']}")
            else:
                st.warning("Please fill in vendor and amount.")

    st.divider()

    # ── Expense Table & Analytics ─────────────────────────────────────────────
    if not st.session_state.expenses:
        st.info("No expenses yet. Upload a receipt or enter one manually above.")
        return

    st.subheader("📋 Expense Log")

    df = pd.DataFrame(st.session_state.expenses)

    # Editable table
    edited_df = st.data_editor(
        df[["vendor", "amount", "category", "date", "upi_id"]],
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "amount":   st.column_config.NumberColumn("Amount (₹)", format="₹%.2f"),
            "category": st.column_config.SelectboxColumn(
                "Category", options=list(CATEGORY_COLORS.keys())
            ),
        },
    )
    # Sync edits back
    for col in ["vendor", "amount", "category", "date", "upi_id"]:
        if col in edited_df.columns:
            df[col] = edited_df[col]

    total_spend = df["amount"].sum()
    st.metric("💰 Total Spend This Session", f"₹{total_spend:,.2f}")

    if st.button("🗑️ Clear All Expenses", type="secondary"):
        st.session_state.expenses = []
        st.rerun()

    st.divider()

    # ── Charts ────────────────────────────────────────────────────────────────
    st.subheader("📊 Spending Breakdown")
    summary = summarise_expenses(st.session_state.expenses)
    summary_df = pd.DataFrame(list(summary.items()), columns=["Category", "Amount"])
    summary_df = summary_df.sort_values("Amount", ascending=False)

    ch1, ch2 = st.columns(2)

    with ch1:
        fig_pie = px.pie(
            summary_df, names="Category", values="Amount",
            color="Category",
            color_discrete_map=CATEGORY_COLORS,
            title="Spend by Category",
            hole=0.4,
        )
        fig_pie.update_layout(template="plotly_dark", margin=dict(t=40, b=0))
        st.plotly_chart(fig_pie, use_container_width=True)

    with ch2:
        fig_bar = px.bar(
            summary_df, x="Category", y="Amount",
            color="Category",
            color_discrete_map=CATEGORY_COLORS,
            title="Category Totals (₹)",
            text_auto=".0f",
        )
        fig_bar.update_layout(
            template="plotly_dark",
            showlegend=False,
            margin=dict(t=40, b=0),
            xaxis_tickangle=-30,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # ── Model Metrics (for portfolio) ─────────────────────────────────────────
    st.subheader("🏅 System Metrics (for your portfolio)")
    avg_ocr  = df["conf_ocr"].mean()
    avg_cat  = df["conf_cat"].mean()
    rule_pct = (df["method"] == "rule_based").mean()

    m1, m2, m3 = st.columns(3)
    m1.metric("Avg OCR Confidence",        f"{avg_ocr:.1%}")
    m2.metric("Avg Category Confidence",   f"{avg_cat:.1%}")
    m3.metric("Rule-Based Accuracy Rate",  f"{rule_pct:.0%}")

    st.caption(DISCLAIMER)
