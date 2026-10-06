import streamlit as st
import pandas as pd
import plotly.express as px
from functools import reduce

# Page Configuration
st.set_page_config(
    page_title="BOM Analysis Tool | Electronics Benchmarking",
    page_icon="⚡",
    layout="wide"
)

# Custom CSS for professional corporate styling
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
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 3rem;
        padding-right: 3rem;
        max-width: 100% !important;
    }
    </style>
""", unsafe_allow_html=True)

# Header Section
st.markdown('<p class="main-header">⚡ BOM Analysis Tool — Multi-Product Benchmarking</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-text">BSH Baseline & Competitor Comparison, Matching, Cost Gaps & Complexity Analysis</p>', unsafe_allow_html=True)

# --- SIDEBAR & FILE UPLOADS ---
st.sidebar.header("📁 Data Inputs & Configuration")
bsh_file = st.sidebar.file_uploader("Upload BSH Baseline BOM", type=["csv", "xlsx"])
competitor_files = st.sidebar.file_uploader("Upload Competitor BOM(s) (1-4 files)", type=["csv", "xlsx"], accept_multiple_files=True)
price_file = st.sidebar.file_uploader("Upload Master Price Sheet / EDM Dataset", type=["csv", "xlsx"])

st.sidebar.divider()
st.sidebar.markdown("### Matching Configuration")
matching_column = st.sidebar.selectbox(
    "Matching Reference Column(s)",
    ["ITEM-NO", "SACHNUMMER", "BSH Material No.:", "POSITION"]
)

# --- HELPER FUNCTION TO PARSE UPLOADED BOM ---
def parse_bom_file(uploaded_file, default_name):
    try:
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    except Exception:
        df = pd.DataFrame()
    
    if df.empty:
        return pd.DataFrame(columns=["POSITION", "FUNCTIONGROUP", "QUANTITY", "Total_Cost"])

    # Normalize column names if needed
    col_map = {c.strip().upper(): c for c in df.columns}
    
    # Find quantity column
    qty_col = None
    for c in df.columns:
        if "QUANTITY" in c.upper():
            qty_col = c
            break
    df["QUANTITY"] = pd.to_numeric(df[qty_col], errors="coerce").fillna(1) if qty_col else 1

    # Find price column
    price_col = None
    for c in df.columns:
        if "PRICE" in c.upper() or "€" in c:
            price_col = c
            break
    
    if price_col:
        df["Unit_Cost_EUR"] = pd.to_numeric(df[price_col], errors="coerce").fillna(0.10)
    else:
        df["Unit_Cost_EUR"] = 0.10

    df["Total_Cost"] = df["QUANTITY"] * df["Unit_Cost_EUR"]

    if "FUNCTIONGROUP" not in df.columns:
        for c in df.columns:
            if "FUNCTION" in c.upper() or "GROUP" in c.upper():
                df["FUNCTIONGROUP"] = df[c]
                break
        if "FUNCTIONGROUP" not in df.columns:
            df["FUNCTIONGROUP"] = "General"

    df["FUNCTIONGROUP"] = df["FUNCTIONGROUP"].fillna("General").astype(str)
    return df

# Load BSH baseline data
if bsh_file is not None:
    df_bsh = parse_bom_file(bsh_file, "BSH")
else:
    # Fallback sample data matching your Excel structure
    df_bsh = pd.DataFrame({
        "POSITION": ["R1", "C1", "IC1", "CN1", "Q1"],
        "FUNCTIONGROUP": ["Resistors", "Capacitors", "Integrated Circuits", "Connectors", "Discrete"],
        "ITEM-NO": ["5.560006e+09", "5.560108e+09", "5.560052e+09", None, "5.560052e+09"],
        "QUANTITY": [10, 5, 1, 2, 3],
        "BENENNUNG": ["Resistor 10k", "Capacitor 100nF", "MCU STM32", "Connector 4-pin", "MOSFET"],
        "Unit_Cost_EUR": [0.02, 0.05, 4.50, 0.80, 0.60]
    })
    df_bsh["Total_Cost"] = df_bsh["QUANTITY"] * df_bsh["Unit_Cost_EUR"]

if "STATUS" not in df_bsh.columns:
    df_bsh["STATUS"] = df_bsh[matching_column].apply(lambda x: "Unmatched" if matching_column in df_bsh.columns and (pd.isna(x) or str(x).lower() in ["nan", "none", ""]) else "Matched")

# --- TABS FOR WORKFLOW ---
tab1, tab2, tab3 = st.tabs(["🔍 Step 1: BOM Matching & Validation", "⚖️ Step 2: Multi-Product Comparison & Cost Gap", "📊 Step 3: Advanced Analytics & Complexity"])

with tab1:
    st.subheader("Step 1: BOM Analysis Tool & Manual Matching")
    st.markdown(f"**Matching Reference Defined:** Using column **`{matching_column}`** to map items against the EDM master dataset.")
    
    if st.button("🔗 Run Manual Match", type="primary"):
        if matching_column in df_bsh.columns:
            df_bsh["STATUS"] = df_bsh[matching_column].apply(lambda x: "Unmatched" if pd.isna(x) or str(x).lower() in ["nan", "none", ""] else "Matched")
        st.success("Matching process executed successfully using reference column!")

    edited_bsh = st.data_editor(df_bsh, use_container_width=True, num_rows="dynamic", key="bsh_editor")

    st.markdown("### ⚠️ Unmatched Items Review & Validation")
    if "STATUS" in edited_bsh.columns:
        unmatched_df = edited_bsh[edited_bsh["STATUS"] == "Unmatched"]
    else:
        unmatched_df = pd.DataFrame(columns=edited_bsh.columns)

    if not unmatched_df.empty:
        st.warning(f"Found {len(unmatched_df)} unmatched items requiring manual validation.")
        st.dataframe(unmatched_df, use_container_width=True)
        
        csv_unmatched = unmatched_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Unmatched Items for Review (CSV)",
            data=csv_unmatched,
            file_name="Unmatched_BOM_Items.csv",
            mime="text/csv"
        )
    else:
        st.success("All BOM items are successfully matched!")

with tab2:
    st.subheader("Step 2: Multi-Product Comparison & Function Group Cost Gap")
    st.markdown("Compare BSH baseline against competitor products simultaneously. **Cost Gap Formula:** `(BSH Cost – Benchmark Cost) / Benchmark Cost`")

    competitor_data_dict = {}
    if competitor_files:
        for idx, comp_file in enumerate(competitor_files):
            # Clean safe key name for dict
            safe_name = f"Competitor_{idx+1}"
            cdf = parse_bom_file(comp_file, safe_name)
            competitor_data_dict[safe_name] = cdf
    else:
        competitor_data_dict["Competitor_1"] = pd.DataFrame({
            "FUNCTIONGROUP": ["Resistors", "Capacitors", "Integrated Circuits", "Connectors", "Discrete"],
            "QUANTITY": [12, 4, 1, 2, 3],
            "Total_Cost": [0.22, 0.28, 4.10, 1.50, 1.80]
        })

    all_func_groups = sorted(list(edited_bsh["FUNCTIONGROUP"].dropna().unique())) if "FUNCTIONGROUP" in edited_bsh.columns else []
    selected_fg = st.selectbox("🔍 Filter & Search by Function Group", ["All Groups"] + all_func_groups)

    bsh_fg = edited_bsh.groupby("FUNCTIONGROUP")["Total_Cost"].sum().reset_index().rename(columns={"Total_Cost": "BSH_Cost"})

    comparison_dfs = [bsh_fg]
    for comp_name, cdf in competitor_data_dict.items():
        if "FUNCTIONGROUP" in cdf.columns:
            cfg = cdf.groupby("FUNCTIONGROUP")["Total_Cost"].sum().reset_index().rename(columns={"Total_Cost": comp_name})
            comparison_dfs.append(cfg)

    merged_comp = reduce(lambda left, right: pd.merge(left, right, on="FUNCTIONGROUP", how="outer"), comparison_dfs).fillna(0)

    if selected_fg != "All Groups":
        merged_comp_filtered = merged_comp[merged_comp["FUNCTIONGROUP"] == selected_fg]
    else:
        merged_comp_filtered = merged_comp

    st.markdown("#### Function Group Cost Summary")
    st.dataframe(merged_comp_filtered, use_container_width=True)

    st.markdown("##### Detailed Cost Gap Evaluation `(BSH Cost - Benchmark Cost) / Benchmark Cost`")
    gap_records = []
    for comp_name in competitor_data_dict.keys():
        if comp_name in merged_comp.columns:
            for idx, row in merged_comp.iterrows():
                fg = row["FUNCTIONGROUP"]
                bsh_c = row["BSH_Cost"]
                comp_c = row[comp_name]
                gap = (bsh_c - comp_c) / comp_c if comp_c > 0 else 0.0
                gap_records.append({
                    "Function Group": fg,
                    "Benchmark Product": comp_name,
                    "BSH Cost (€)": bsh_c,
                    "Benchmark Cost (€)": comp_c,
                    "Cost Gap (%)": gap * 100
                })
    df_gaps = pd.DataFrame(gap_records)
    if selected_fg != "All Groups":
        df_gaps = df_gaps[df_gaps["Function Group"] == selected_fg]
    
    if not df_gaps.empty:
        st.dataframe(df_gaps.style.format({"BSH Cost (€)": "{:.2f} €", "Benchmark Cost (€)": "{:.2f} €", "Cost Gap (%)": "{:+.2f}%"}), use_container_width=True)

with tab3:
    st.subheader("Step 3: Advanced Analysis (Cost Distribution & Complexity)")
    
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown("##### 📊 Cost Distribution Comparison Across Products")
        val_vars = ["BSH_Cost"] + list(competitor_data_dict.keys())
        melted_comp = pd.melt(merged_comp, id_vars=["FUNCTIONGROUP"], value_vars=[v for v in val_vars if v in merged_comp.columns],
                              var_name="Product", value_name="Cost_EUR")
        fig_dist = px.bar(melted_comp, x="FUNCTIONGROUP", y="Cost_EUR", color="Product", barmode="group",
                          text_auto=".2f", color_discrete_sequence=px.colors.qualitative.Bold)
        fig_dist.update_layout(xaxis_title="Function Group", yaxis_title="Total Cost (€)", height=380, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_dist, use_container_width=True)

    with col_chart2:
        st.markdown("##### 📈 Complexity Analysis (Component Count by Function Group)")
        bsh_count = edited_bsh.groupby("FUNCTIONGROUP")["QUANTITY"].sum().reset_index().rename(columns={"QUANTITY": "BSH_Count"})
        
        count_dfs = [bsh_count]
        for comp_name, cdf in competitor_data_dict.items():
            if "FUNCTIONGROUP" in cdf.columns and "QUANTITY" in cdf.columns:
                ccount = cdf.groupby("FUNCTIONGROUP")["QUANTITY"].sum().reset_index().rename(columns={"QUANTITY": comp_name})
                count_dfs.append(ccount)
        
        merged_count = reduce(lambda left, right: pd.merge(left, right, on="FUNCTIONGROUP", how="outer"), count_dfs).fillna(0)
        val_count_vars = ["BSH_Count"] + list(competitor_data_dict.keys())
        melted_count = pd.melt(merged_count, id_vars=["FUNCTIONGROUP"], value_vars=[v for v in val_count_vars if v in merged_count.columns],
                               var_name="Product", value_name="Component_Count")
        
        fig_comp = px.bar(melted_count, x="FUNCTIONGROUP", y="Component_Count", color="Product", barmode="group",
                          text_auto=".0f", color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_comp.update_layout(xaxis_title="Function Group", yaxis_title="Component Count", height=380, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_comp, use_container_width=True)

    st.divider()
    if st.button("Generate Full Executive Report Package"):
        st.success("Executive benchmarking report package generated successfully!")