import re

import streamlit as st
import pandas as pd
import plotly.express as px

# ======================
# CONFIG
# ======================
st.set_page_config(layout="wide")

# ======================
# UI STYLE
# ======================
st.markdown("""
<style>

/* FORCE TEXT WHITE FOR STREAMLIT UI */
* {
    color: white !important;
}

/* APP BACKGROUND */
.stApp {
    background-color: #0e1117 !important;
}

/* SIDEBAR BACKGROUND */
[data-testid="stSidebar"] {
    background-color: #111827 !important;
}

/* TITLES GOLD */
h1, h2, h3 {
    color: #FFD700 !important;
}

/* ROW CARD STYLE - COMPACT */
.row-card {
    border: 1px solid #2f333a;
    border-radius: 6px;
    padding: 3px 8px;
    margin-bottom: 3px;
    background-color: #1c1f26;
}

/* REDUCE SPACE BETWEEN COLUMNS */
[data-testid="stHorizontalBlock"] {
    gap: 0.4rem;
}

[data-testid="column"] {
    padding: 0px 4px !important;
}

/* REDUCE DEFAULT MARKDOWN MARGINS */
p {
    margin-bottom: 0.2rem !important;
}

/* HORIZONTAL LINE */
hr {
    margin-top: 0.5rem !important;
    margin-bottom: 0.5rem !important;
}

/* DEFAULT BUTTONS - KEEP YELLOW FOR BACK BUTTON */
button {
    background-color: #FFD700 !important;
    color: black !important;
    border-radius: 8px !important;
    font-weight: bold !important;
    padding: 4px 10px !important;
}

/* DEFAULT BUTTON TEXT BLACK */
button * {
    color: black !important;
}

/* ACTION ICON BUTTONS: DETAILS + CLEAR FILTER */
button[kind="tertiary"] {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 2px 6px !important;
    min-width: 34px !important;
    height: 34px !important;
    border-radius: 8px !important;
}

button[kind="tertiary"] * {
    color: #38BDF8 !important;
    font-size: 22px !important;
}

button[kind="tertiary"]:hover {
    background-color: rgba(56, 189, 248, 0.14) !important;
}

/* CLEAR FILTER ICON POSITION */
.clear-filter-button button {
    margin-top: 8px !important;
}

/* DATAFRAME TEXT FIX */
[data-testid="stDataFrame"] * {
    color: white !important;
}

/* KPI CARDS */
.kpi-card {
    border: 1px solid #9aa8b5;
    border-radius: 6px;
    padding: 8px;
    background-color: rgba(229, 236, 246, 0.95);
    text-align: center;
    height: 82px;
    margin-bottom: 8px;
}

.kpi-title {
    color: #1f3b63 !important;
    font-size: 13px;
    font-weight: bold;
}

.kpi-value {
    color: black !important;
    font-size: 26px;
    font-weight: bold;
    margin-top: 8px;
}

/* ========================= */
/* SIDEBAR FILTERS FIX */
/* Make multiselect/search values visible */
/* ========================= */

[data-baseweb="input"] input,
[data-baseweb="select"] input,
[data-baseweb="select"] div,
[data-baseweb="select"] span {
    color: #111827 !important;
}

[data-baseweb="input"] input::placeholder {
    color: #6b7280 !important;
}

[data-baseweb="popover"] {
    background-color: white !important;
}

[data-baseweb="popover"] *,
[role="listbox"] *,
li[role="option"] * {
    color: #111827 !important;
}

li[role="option"]:hover,
[role="option"]:hover {
    background-color: #E5ECF6 !important;
}

[aria-selected="true"] {
    background-color: #E5ECF6 !important;
}

[data-baseweb="tag"] {
    background-color: #FFD700 !important;
}

[data-baseweb="tag"] span {
    color: black !important;
}

[data-baseweb="input"] input {
    color: #111827 !important;
}

[data-testid="stSidebar"] label,
[data-testid="stSidebar"] label * {
    color: white !important;
}

</style>
""", unsafe_allow_html=True)

# ======================
# HEADER
# ======================
st.markdown(
    "<h1 style='text-align:center;'>🚨 Smart Alert System</h1>",
    unsafe_allow_html=True
)

# ======================
# LOAD DATA
# ======================
df_day = pd.read_csv("./data/daily_alerts.csv")
df_detail = pd.read_csv("./data/production_anomaly_alerts.csv")
df_noprod = pd.read_csv("./data/non_efficient_alerts.csv")

# ======================
# LEGACY NAMING COMPATIBILITY
# ======================
_LEGACY_NAME_PATTERN = re.compile("egauge", re.IGNORECASE)

def _legacy_name_repl(match):
    old = match.group(0)
    if old.isupper():
        return "SENSOR"
    if old[0].isupper():
        return "Sensor"
    return "sensor"

def to_sensor_naming(text):
    return _LEGACY_NAME_PATTERN.sub(_legacy_name_repl, text)

def normalize_sensor_naming(df):
    df = df.rename(columns={col: to_sensor_naming(str(col)) for col in df.columns})

    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].map(
                lambda v: to_sensor_naming(v) if isinstance(v, str) else v
            )

    return df

df_day = normalize_sensor_naming(df_day)
df_detail = normalize_sensor_naming(df_detail)
df_noprod = normalize_sensor_naming(df_noprod)

df_detail["alert_start"] = pd.to_datetime(df_detail["alert_start"])

if "alert_start" in df_noprod.columns:
    df_noprod["alert_start"] = pd.to_datetime(df_noprod["alert_start"])

if "alert_end" in df_noprod.columns:
    df_noprod["alert_end"] = pd.to_datetime(df_noprod["alert_end"])

# Convert dates
df_day["date_dt"] = pd.to_datetime(df_day["date"]).dt.date

if "date" in df_detail.columns:
    df_detail["date_dt"] = pd.to_datetime(df_detail["date"]).dt.date
else:
    df_detail["date_dt"] = df_detail["alert_start"].dt.date

if "date" in df_noprod.columns:
    df_noprod["date_dt"] = pd.to_datetime(df_noprod["date"]).dt.date
elif "alert_start" in df_noprod.columns:
    df_noprod["date_dt"] = df_noprod["alert_start"].dt.date

# ======================
# MACHINE MAPPING
# Derived automatically from sensor + register
# ======================
MACHINE_MAPPING = {
    ("egauge90773", "i11"): "Injection Molding 1",
    ("egauge90773", "i21"): "Injection Molding 3",
    ("egauge90773", "i31"): "Injection Molding 6",
    ("egauge90773", "i41"): "Injection Molding 2",
    ("egauge90773", "i51"): "Injection Molding 5",
    ("egauge113530", "i11"): "Blow Molding 11",
    ("egauge113530", "i21"): "Blow Molding 6",
    ("egauge113530", "i31"): "Blow Molding 5",
    ("egauge113530", "i41"): "Blow Molding 8",
    ("egauge113530", "i51"): "Blow Molding 9",
    ("egauge113526", "i11"): "Injection Molding 6",
    ("egauge113526", "i21"): "Injection Molding 17",
    ("egauge113526", "i31"): "Injection Molding 15",
}

def get_machine(sensor, register):
    return MACHINE_MAPPING.get(
        (str(sensor).strip(), str(register).strip()),
        "not defined"
    )

def add_machine_column(df):
    if "sensor" in df.columns and "register" in df.columns:
        df["machine"] = df.apply(
            lambda r: get_machine(r["sensor"], r["register"]),
            axis=1
        )
    else:
        df["machine"] = "not defined"
    return df

df_day = add_machine_column(df_day)
df_detail = add_machine_column(df_detail)
df_noprod = add_machine_column(df_noprod)

# Normalize useful columns
if "severity" in df_day.columns:
    df_day["severity"] = df_day["severity"].astype(str).str.upper()

if "severity" in df_detail.columns:
    df_detail["severity"] = df_detail["severity"].astype(str).str.upper()

# ======================
# STATE
# ======================
if "selected_date" not in st.session_state:
    st.session_state.selected_date = None

if "selected_context" not in st.session_state:
    st.session_state.selected_context = {}

if "page" not in st.session_state:
    st.session_state.page = "overview"

# ======================
# SIDEBAR FILTERS
# ======================
df_day_filtered = df_day.copy()

# Default dates
min_date = df_day["date_dt"].min()
max_date = df_day["date_dt"].max()

# ======================
# INIT FILTER STATES
# ======================
if "search_filter" not in st.session_state:
    st.session_state.search_filter = ""

if "sensor_filter" not in st.session_state:
    st.session_state.sensor_filter = []

if "register_filter" not in st.session_state:
    st.session_state.register_filter = []

if "date_filter" not in st.session_state:
    st.session_state.date_filter = (min_date, max_date)

if "severity_filter" not in st.session_state:
    st.session_state.severity_filter = []

if "alert_type_filter" not in st.session_state:
    st.session_state.alert_type_filter = []

# Clear filters function
def clear_filters():
    st.session_state.search_filter = ""
    st.session_state.sensor_filter = []
    st.session_state.register_filter = []
    st.session_state.date_filter = (min_date, max_date)
    st.session_state.severity_filter = []
    st.session_state.alert_type_filter = []

# Sidebar title + clear button
side_col1, side_col2 = st.sidebar.columns([3, 1])

side_col1.markdown("## 🔎 Filters")

with side_col2:
    st.markdown('<div class="clear-filter-button">', unsafe_allow_html=True)
    st.button(
        "",
        icon=":material/filter_alt_off:",
        help="Clear all filters",
        on_click=clear_filters,
        type="tertiary"
    )
    st.markdown("</div>", unsafe_allow_html=True)

# Search bar
search_query = st.sidebar.text_input(
    "Search",
    placeholder="Search sensor, register, alert type...",
    key="search_filter"
)

# Sensor filter
sensor_options = (
    sorted(df_day["sensor"].dropna().astype(str).unique())
    if "sensor" in df_day.columns
    else []
)

selected_sensors = st.sidebar.multiselect(
    "Sensor",
    sensor_options,
    key="sensor_filter"
)

# Register filter
register_options = (
    sorted(df_day["register"].dropna().astype(str).unique())
    if "register" in df_day.columns
    else []
)

selected_registers = st.sidebar.multiselect(
    "Register",
    register_options,
    key="register_filter"
)

# Date filter
selected_date_range = st.sidebar.date_input(
    "Date",
    min_value=min_date,
    max_value=max_date,
    key="date_filter"
)

# Severity filter
severity_options = (
    sorted(df_day["severity"].dropna().astype(str).unique())
    if "severity" in df_day.columns
    else []
)

selected_severities = st.sidebar.multiselect(
    "Severity",
    severity_options,
    key="severity_filter"
)

# Alert Type filter
alert_type_options = (
    sorted(df_day["alert_type"].dropna().astype(str).unique())
    if "alert_type" in df_day.columns
    else []
)

selected_alert_types = st.sidebar.multiselect(
    "Alert Type",
    alert_type_options,
    key="alert_type_filter"
)

# ======================
# APPLY SIDEBAR FILTERS
# ======================

# Search filter
if search_query:
    search_cols = [
        col for col in [
            "date",
            "sensor",
            "register",
            "machine",
            "alert_type",
            "status",
            "severity",
            "created_by"
        ]
        if col in df_day_filtered.columns
    ]

    if search_cols:
        df_day_filtered = df_day_filtered[
            df_day_filtered[search_cols]
            .astype(str)
            .apply(
                lambda row: row.str.contains(search_query, case=False, na=False).any(),
                axis=1
            )
        ]

# Sensor filter
if selected_sensors and "sensor" in df_day_filtered.columns:
    df_day_filtered = df_day_filtered[
        df_day_filtered["sensor"].astype(str).isin(selected_sensors)
    ]

# Register filter
if selected_registers and "register" in df_day_filtered.columns:
    df_day_filtered = df_day_filtered[
        df_day_filtered["register"].astype(str).isin(selected_registers)
    ]

# Date range filter
if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
    start_date, end_date = selected_date_range

    df_day_filtered = df_day_filtered[
        (df_day_filtered["date_dt"] >= start_date) &
        (df_day_filtered["date_dt"] <= end_date)
    ]

# Severity filter
if selected_severities and "severity" in df_day_filtered.columns:
    df_day_filtered = df_day_filtered[
        df_day_filtered["severity"].astype(str).isin(selected_severities)
    ]

# Alert Type filter
if selected_alert_types and "alert_type" in df_day_filtered.columns:
    df_day_filtered = df_day_filtered[
        df_day_filtered["alert_type"].astype(str).isin(selected_alert_types)
    ]

# ======================
# DEFAULT SORT OVERVIEW
# Sort by date, then alert_type
# ======================
sort_cols = []

if "date_dt" in df_day_filtered.columns:
    sort_cols.append("date_dt")

if "alert_type" in df_day_filtered.columns:
    sort_cols.append("alert_type")

if sort_cols:
    df_day_filtered = df_day_filtered.sort_values(
        by=sort_cols,
        ascending=True
    )

# Sidebar count
st.sidebar.markdown("---")
st.sidebar.metric("Displayed Rows", len(df_day_filtered))

# ======================
# PAGE 1 : OVERVIEW
# ======================
if st.session_state.page == "overview":

    st.markdown("### 📊 Daily Alerts Overview")

    header_cols = st.columns([1.3, 1.6, 1.2, 1.3, 0.9, 1.2, 1.4, 1.0, 1.7, 1.3, 0.7])

    header_cols[0].markdown("**Date**")
    header_cols[1].markdown("**Alert Type**")
    header_cols[2].markdown("**Status**")
    header_cols[3].markdown("**Severity**")
    header_cols[4].markdown("**Alerts**")
    header_cols[5].markdown("**Anomalies**")
    header_cols[6].markdown("**Sensor**")
    header_cols[7].markdown("**Register**")
    header_cols[8].markdown("**Machine**")
    header_cols[9].markdown("**Created By**")
    header_cols[10].markdown("**Details**")

    st.markdown("<hr>", unsafe_allow_html=True)

    if df_day_filtered.empty:
        st.warning("No alerts found for the selected filters.")

    for i, row in df_day_filtered.iterrows():

        st.markdown('<div class="row-card">', unsafe_allow_html=True)

        col1, col2, col3, col4, col5, col6, col7, col8, col9, col10, col11 = st.columns(
            [1.3, 1.6, 1.2, 1.3, 0.9, 1.2, 1.4, 1.0, 1.7, 1.3, 0.7]
        )

        col1.markdown(f"**{row['date']}**")
        col2.markdown(f"**{row['alert_type']}**")
        col3.markdown(f"**{row['status']}**")

        if row["severity"] == "HIGH":
            col4.markdown("🔴 **HIGH**")
        elif row["severity"] == "MEDIUM":
            col4.markdown("🟠 **MEDIUM**")
        else:
            col4.markdown("🟢 **LOW**")

        col5.markdown(f"**{row['total_alerts']}**")
        col6.markdown(f"**{row['total_anomalies']}**")

        row_sensor = row["sensor"] if "sensor" in row.index else "-"
        row_register = row["register"] if "register" in row.index else "-"

        col7.markdown(f"**{row_sensor}**")
        col8.markdown(f"**{row_register}**")
        col9.markdown(f"**{row['machine']}**")
        col10.markdown(f"**{row['created_by']}**")

        if col11.button(
            "",
            icon=":material/search:",
            key=f"btn_{i}",
            help="View details",
            type="tertiary"
        ):

            st.session_state.selected_date = row["date"]

            st.session_state.selected_context = {
                "date": row["date"],
                "date_dt": row["date_dt"],
                "sensor": row["sensor"] if "sensor" in row.index else None,
                "register": row["register"] if "register" in row.index else None,
                "alert_type": row["alert_type"] if "alert_type" in row.index else None,
                "severity": row["severity"] if "severity" in row.index else None
            }

            st.session_state.page = "detail"
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

# ======================
# PAGE 2 : DETAIL VIEW
# ======================
if st.session_state.page == "detail" and st.session_state.selected_date:

    st.markdown("---")

    if st.button("⬅️ Back to Overview"):
        st.session_state.selected_date = None
        st.session_state.selected_context = {}
        st.session_state.page = "overview"
        st.rerun()

    selected_context = st.session_state.selected_context

    selected_date_label = selected_context.get("date", st.session_state.selected_date)
    selected_date_dt = selected_context.get("date_dt")
    selected_sensor = selected_context.get("sensor")
    selected_register = selected_context.get("register")
    selected_alert_type = selected_context.get("alert_type")

    selected_alert_type_clean = str(selected_alert_type).strip().lower()

    # ======================
    # SPECIAL VIEW FOR NON EFFICIENT
    # ======================
    if selected_alert_type_clean == "non efficient":

        detail_title = f"Non Efficient Alerts for {selected_date_label}"

        st.markdown(
            f"<h2>{detail_title}</h2>",
            unsafe_allow_html=True
        )

        # Filter noprod data
        df_noprod_filtered = df_noprod.copy()

        if selected_date_dt is not None and "date_dt" in df_noprod_filtered.columns:
            df_noprod_filtered = df_noprod_filtered[
                df_noprod_filtered["date_dt"] == selected_date_dt
            ]

        noprod_display_cols = [
            "alert_start",
            "alert_end",
            "duration"
        ]

        existing_noprod_cols = [
            col for col in noprod_display_cols
            if col in df_noprod_filtered.columns
        ]

        if not existing_noprod_cols:
            st.error(
                "Missing columns in non_efficient_alerts.csv. Expected: alert_start, alert_end, duration."
            )
            st.stop()

        if df_noprod_filtered.empty:
            st.warning("No non efficient detailed alerts found for this selection.")

        st.dataframe(
            df_noprod_filtered[existing_noprod_cols],
            use_container_width=True,
            height=520
        )

        st.stop()

    # ======================
    # STANDARD DETAIL VIEW
    # ======================
    detail_title = f"Detailed Alerts for {selected_date_label}"

    if selected_sensor:
        detail_title += f" - {selected_sensor}"

    if selected_register:
        detail_title += f" - {selected_register}"

    if selected_alert_type:
        detail_title += f" - {selected_alert_type}"

    st.markdown(
        f"<h2>{detail_title}</h2>",
        unsafe_allow_html=True
    )

    # ======================
    # FILTER DETAIL DATA
    # ======================
    df_filtered = df_detail[
        df_detail["date_dt"] == selected_date_dt
    ].copy()

    if selected_sensor is not None and "sensor" in df_filtered.columns:
        df_filtered = df_filtered[
            df_filtered["sensor"].astype(str) == str(selected_sensor)
        ]

    if selected_register is not None and "register" in df_filtered.columns:
        df_filtered = df_filtered[
            df_filtered["register"].astype(str) == str(selected_register)
        ]

    if selected_alert_type is not None and "alert_type" in df_filtered.columns:
        df_filtered = df_filtered[
            df_filtered["alert_type"].astype(str) == str(selected_alert_type)
        ]

    if df_filtered.empty:
        st.warning("No detailed alerts found for this selection.")
        st.stop()

    df_filtered["severity_clean"] = df_filtered["severity"].astype(str).str.upper()

    # If start_date column does not exist, create it from alert_start
    if "start_date" not in df_filtered.columns and "alert_start" in df_filtered.columns:
        df_filtered["start_date"] = df_filtered["alert_start"]

    severity_colors = {
        "HIGH": "#EF553B",
        "MEDIUM": "#FFA500",
        "LOW": "#00CC96"
    }

    # ======================
    # COMMON PLOTLY STYLE
    # ======================
    def apply_plotly_reference_style(fig, height=380):
        fig.update_layout(
            template="plotly",
            paper_bgcolor="#E5ECF6",
            plot_bgcolor="#E5ECF6",
            font=dict(color="#1f3b63", size=12),
            title_font=dict(color="#1f3b63", size=14),
            legend=dict(
                bgcolor="rgba(229,236,246,0)",
                font=dict(color="#1f3b63"),
                title_font=dict(color="#1f3b63")
            ),
            margin=dict(l=45, r=25, t=50, b=45),
            height=height
        )

        fig.update_xaxes(
            showgrid=True,
            gridcolor="#FFFFFF",
            gridwidth=1,
            zeroline=False,
            linecolor="#FFFFFF",
            tickfont=dict(color="#1f3b63"),
            title_font=dict(color="#1f3b63", size=12)
        )

        fig.update_yaxes(
            showgrid=True,
            gridcolor="#FFFFFF",
            gridwidth=1,
            zeroline=False,
            linecolor="#FFFFFF",
            tickfont=dict(color="#1f3b63"),
            title_font=dict(color="#1f3b63", size=12)
        )

        return fig

    st.markdown(
        "<h3 style='text-align:center; color:white !important;'>Smart Alerts Monitoring</h3>",
        unsafe_allow_html=True
    )

    top_col1, top_col2, top_col3 = st.columns([1.1, 2.3, 1.1])

    # ======================
    # 1) RADAR - Alert Frequency by Hour
    # ======================
    df_filtered["alert_hour"] = df_filtered["alert_start"].dt.hour

    df_hour = (
        df_filtered
        .groupby("alert_hour")
        .size()
        .reset_index(name="alert_count")
    )

    all_hours = pd.DataFrame({
        "alert_hour": list(range(24))
    })

    df_hour = all_hours.merge(
        df_hour,
        on="alert_hour",
        how="left"
    )

    df_hour["alert_count"] = df_hour["alert_count"].fillna(0)

    df_hour["hour_label"] = df_hour["alert_hour"].apply(
        lambda h: f"{int(h):02d}h00"
    )

    fig_radar = px.line_polar(
        df_hour,
        r="alert_count",
        theta="hour_label",
        line_close=True,
        markers=True,
        title="Alert Frequency by Hour"
    )

    fig_radar.update_traces(
        fill="toself",
        line=dict(color="#C44E52", width=3),
        marker=dict(size=6, color="#C44E52"),
        fillcolor="rgba(196, 78, 82, 0.35)"
    )

    fig_radar.update_layout(
        template="plotly",
        paper_bgcolor="#E5ECF6",
        plot_bgcolor="#E5ECF6",
        polar=dict(
            bgcolor="#E5ECF6",
            radialaxis=dict(
                title="Alerts",
                gridcolor="#FFFFFF",
                gridwidth=1,
                linecolor="#FFFFFF",
                tickfont=dict(color="#1f3b63"),
                title_font=dict(color="#1f3b63"),
                showline=True
            ),
            angularaxis=dict(
                gridcolor="#FFFFFF",
                gridwidth=1,
                linecolor="#FFFFFF",
                tickfont=dict(color="#1f3b63", size=10),
                rotation=90,
                direction="clockwise"
            )
        ),
        font=dict(color="#1f3b63", size=11),
        title_font=dict(color="#1f3b63", size=13),
        margin=dict(l=10, r=10, t=45, b=10),
        height=380
    )

    top_col1.plotly_chart(
        fig_radar,
        use_container_width=True,
        config={
            "displayModeBar": False,
            "responsive": True
        }
    )

    # ======================
    # 2) TIMELINE - NB ANOMALIES OVER TIME
    # ======================
    fig_timeline = px.bar(
        df_filtered,
        x="alert_start",
        y="nb_anomalies",
        color="severity_clean",
        color_discrete_map=severity_colors,
        title="Nb Anomalies Over Time",
        labels={
            "alert_start": "Time",
            "nb_anomalies": "Nb Anomalies",
            "severity_clean": "Severity"
        }
    )

    fig_timeline = apply_plotly_reference_style(fig_timeline, height=380)

    fig_timeline.update_traces(
        width=60 * 60 * 1000,
        opacity=0.95,
        marker_line_width=0
    )

    fig_timeline.update_layout(
        bargap=0.02,
        bargroupgap=0.02
    )

    top_col2.plotly_chart(
        fig_timeline,
        use_container_width=True,
        config={"displayModeBar": False}
    )

    # ======================
    # 3) SCATTER - LOG SCALE ON Y AXIS
    # ======================
    df_scatter = df_filtered[df_filtered["density"] > 0].copy()

    fig_scatter = px.scatter(
        df_scatter,
        x="duration",
        y="density",
        color="severity_clean",
        size="nb_anomalies",
        color_discrete_map=severity_colors,
        log_y=True,
        title="Alert Severity vs. Duration Cluster",
        labels={
            "duration": "Duration",
            "density": "Density",
            "severity_clean": "Severity"
        }
    )

    fig_scatter = apply_plotly_reference_style(fig_scatter, height=380)

    top_col3.plotly_chart(
        fig_scatter,
        use_container_width=True,
        config={"displayModeBar": False}
    )

    # ======================
    # BOTTOM ROW : TABLE + PIE + KPIs
    # ======================
    bottom_col1, bottom_col2, bottom_col3 = st.columns([2.1, 1.3, 1])

    display_cols = [
        "start_date",
        "alert_end",
        "duration",
        "nb_anomalies",
        "severity",
        "severity_score",
        "density"
    ]

    existing_cols = [col for col in display_cols if col in df_filtered.columns]

    bottom_col1.dataframe(
        df_filtered[existing_cols].sort_values(
            "severity_score",
            ascending=False
        ),
        use_container_width=True,
        height=360
    )

    fig_pie = px.pie(
        df_filtered,
        names="severity_clean",
        color="severity_clean",
        color_discrete_map=severity_colors,
        title="Overall Alert Severity Distribution"
    )

    fig_pie.update_layout(
        template="plotly",
        paper_bgcolor="#E5ECF6",
        plot_bgcolor="#E5ECF6",
        font=dict(color="#1f3b63", size=12),
        title_font=dict(color="#1f3b63", size=14),
        legend=dict(
            bgcolor="rgba(229,236,246,0)",
            font=dict(color="#1f3b63"),
            title_font=dict(color="#1f3b63")
        ),
        margin=dict(l=25, r=25, t=50, b=25),
        height=360
    )

    bottom_col2.plotly_chart(
        fig_pie,
        use_container_width=True,
        config={"displayModeBar": False}
    )

    # ======================
    # KPI CARDS
    # ======================
    total_alerts = len(df_filtered)
    avg_duration = df_filtered["duration"].mean()
    total_anomalies = df_filtered["nb_anomalies"].sum()
    high_alerts = len(df_filtered[df_filtered["severity_clean"] == "HIGH"])

    high_alert_rate = (high_alerts / total_alerts * 100) if total_alerts > 0 else 0

    bottom_col3.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">Avg. Duration</div>
            <div class="kpi-value">{avg_duration:.1f}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    bottom_col3.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">Total Anomalies</div>
            <div class="kpi-value">{int(total_anomalies)}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    bottom_col3.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">High Alerts</div>
            <div class="kpi-value">{high_alerts}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    bottom_col3.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">High Alert Rate</div>
            <div class="kpi-value">{high_alert_rate:.1f}%</div>
        </div>
        """,
        unsafe_allow_html=True
    )
