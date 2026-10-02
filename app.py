import streamlit as st
import pandas as pd
import plotly.express as px

# Page Configuration - wide layout
st.set_page_config(
    page_title="BOM Analysis Tool | Electronics Benchmarking",
    page_icon="⚡",
    layout="wide"
)

# Custom CSS for professional corporate look and fixing top header margin
st.markdown("""
    <style>
    .main-header {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0rem;
    }
    .sub-text {
        color: #475569;
        font-size: 0.95rem;
        margin-bottom: 1rem;
    }
    div.stMetric {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 0.8rem 1rem;
        border-radius: 8px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    }
    /* Fix top margin so the header is fully visible and not cut off */
    .block-container {
        padding-top: 2.5rem;
        padding-bottom: 2rem;
        padding-left: 3rem;
        padding-right: 3rem;
        max-width: 100% !important;
    }
    </style>
""", unsafe_allow_html=True)

# Header Section
st.markdown('<p class="main-header">⚡ BOM Analysis Tool</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-text">Electronics Benchmarking & Material Cost (MCC) Evaluation Platform</p>', unsafe_allow_html=True)

# --- FILE UPLOADS ---
col_up1, col_up2 = st.columns(2)
with col_up1:
    uploaded_bom = st.file_uploader("Upload BOM File (CSV / Excel)", type=["csv", "xlsx"])
with col_up2:
    uploaded_price = st.file_uploader("Upload Price Sheet / EDM Dataset (Optional)", type=["csv", "xlsx"])

# Data Loading (Mock data fallback if empty)
if uploaded_bom is not None:
    try:
        if uploaded_bom.name.endswith('.csv'):
            df_bom = pd.read_csv(uploaded_bom)
        else:
            df_bom = pd.read_excel(uploaded_bom)
    except Exception as e:
        st.error(f"Error reading file: {e}")
        df_bom = None
else:
    # Professional mock data
    df_bom = pd.DataFrame({
        "Reference": ["R1", "C1", "IC1", "CN1", "Q1", "R2", "C2", "U1"],
        "Description": ["Resistor 10k 0402", "Capacitor 100nF", "Microcontroller STM32", "Connector 4-pin", "MOSFET N-Channel", "Resistor 1k 0603", "Capacitor 10uF", "EEPROM 32k"],
        "Quantity": [10, 5, 1, 2, 3, 20, 8, 2],
        "Unit_Cost_EUR": [0.02, 0.05, 4.50, 0.80, 0.60, 0.01, 0.12, 1.20]
    })

if df_bom is not None:
    if "Total_Cost" not in df_bom.columns and "Quantity" in df_bom.columns and "Unit_Cost_EUR" in df_bom.columns:
        df_bom["Total_Cost"] = df_bom["Quantity"] * df_bom["Unit_Cost_EUR"]

    def auto_classify(desc):
        d = str(desc).lower()
        if "res" in d: return "Resistors"
        elif "cap" in d: return "Capacitors"
        elif "ic" in d or "micro" in d or "eeprom" in d: return "Integrated Circuits"
        elif "conn" in d: return "Connectors"
        else: return "Discrete & Others"

    if "Category" not in df_bom.columns:
        df_bom["Category"] = df_bom["Description"].apply(auto_classify)
        
    if "EDM_Status" not in df_bom.columns:
        df_bom["EDM_Status"] = "Matched"

    # --- METRICS OVERVIEW ---
    total_components = int(df_bom["Quantity"].sum()) if "Quantity" in df_bom.columns else len(df_bom)
    total_mcc = df_bom["Total_Cost"].sum() if "Total_Cost" in df_bom.columns else 0.0
    
    max_driver = "N/A"
    if "Total_Cost" in df_bom.columns and not df_bom.empty:
        top_row = df_bom.loc[df_bom["Total_Cost"].idxmax()]
        max_driver = f"{top_row.get('Reference', '')} ({top_row.get('Description', '')})"

    m1, m2, m3 = st.columns(3)
    m1.metric(label="Total Components Count", value=total_components)
    m2.metric(label="Total Material Cost (MCC)", value=f"{total_mcc:.2f} €")
    m3.metric(label="Top Cost Driver", value=max_driver)

    st.divider()

    # --- SEARCH & EDITABLE DATAFRAME ---
    st.subheader("BOM Component Breakdown & Classification")
    search_query = st.text_input("🔍 Quick Search Component", "", placeholder="Type reference or description...")
    
    if search_query:
        filtered_df = df_bom[
            df_bom["Reference"].astype(str).str.contains(search_query, case=False, na=False) |
            df_bom["Description"].astype(str).str.contains(search_query, case=False, na=False)
        ]
    else:
        filtered_df = df_bom

    edited_df = st.data_editor(filtered_df, use_container_width=True, num_rows="dynamic")

    if "Quantity" in edited_df.columns and "Unit_Cost_EUR" in edited_df.columns:
        edited_df["Total_Cost"] = edited_df["Quantity"] * edited_df["Unit_Cost_EUR"]

    st.divider()

    # --- ENHANCED PROFESSIONAL PLOTLY CHARTS ---
    st.subheader("Cost Analytics & Insights")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        if "Category" in edited_df.columns and "Total_Cost" in edited_df.columns:
            cat_summary = edited_df.groupby("Category")["Total_Cost"].sum().reset_index()
            cat_summary = cat_summary.sort_values(by="Total_Cost", ascending=False)
            
            fig_cat = px.bar(
                cat_summary, x="Category", y="Total_Cost", 
                text_auto=".2f",
                color_discrete_sequence=["#0284ceter"] if False else ["#0284c7"]
            )
            fig_cat.update_layout(
                title="Cost Distribution by Functional Group",
                xaxis_title="", yaxis_title="Cost (€)",
                xaxis=dict(tickangle=0),
                margin=dict(l=10, r=10, t=40, b=10),
                height=340,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)"
            )
            fig_cat.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
            st.plotly_chart(fig_cat, use_container_width=True)

    with chart_col2:
        if "Total_Cost" in edited_df.columns and not edited_df.empty:
            top5_df = edited_df.nlargest(5, "Total_Cost").copy()
            top5_df["Item"] = top5_df["Reference"].astype(str) + " (" + top5_df["Description"] + ")"
            top5_df = top5_df.sort_values(by="Total_Cost", ascending=False)
            
            fig_top = px.bar(
                top5_df, x="Item", y="Total_Cost", 
                text_auto=".2f",
                color_discrete_sequence=["#f43f5e"]
            )
            fig_top.update_layout(
                title="Top Cost Drivers (Top 5 Items)",
                xaxis_title="", yaxis_title="Cost (€)",
                xaxis=dict(tickangle=0),
                margin=dict(l=10, r=10, t=40, b=10),
                height=340,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)"
            )
            fig_top.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
            st.plotly_chart(fig_top, use_container_width=True)

    st.divider()

    # --- EXPORT REPORT ---
    st.subheader("Export Consolidated Report")
    
    @st.cache_data
    def convert_to_csv(df):
        return df.to_csv(index=False).encode('utf-8')

    st.download_button(
        label="📥 Download Consolidated BOM Report (CSV)",
        data=convert_to_csv(edited_df),
        file_name="BOM_Benchmarking_Report.csv",
        mime="text/csv"
    )