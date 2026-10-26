import streamlit as st
import pandas as pd
from datetime import datetime

# ==========================================
# 1. PAGE CONFIG & THEME
# ==========================================
st.set_page_config(page_title="Khwezi Mining Monitor", page_icon="⛏️", layout="wide")

# Custom CSS for a colorful, mining-themed dashboard
st.markdown("""
    <style>
    /* Main background */
    .stApp {
        background-color: #f4f4f9;
    }
    /* Headers */
    h1, h2, h3 {
        color: #2C3E50;
        font-family: 'Arial', sans-serif;
    }
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #3E2723; /* Dark mining brown */
    }
    [data-testid="stSidebar"] * {
        color: #F5F5F5 !important; /* White text in sidebar */
    }
    /* Custom KPI Cards */
    .kpi-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border-top: 5px solid #D4AF37; /* Gold */
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        text-align: center;
    }
    .kpi-value {
        font-size: 36px;
        font-weight: bold;
        color: #D35400; /* Rust Orange */
        margin: 10px 0;
    }
    .kpi-label {
        font-size: 16px;
        color: #555;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA LOADING & SAVING
# ==========================================
# Ensure files exist before trying to read them
try:
    workers_df = pd.read_csv("workers.csv")
    incidents_df = pd.read_csv("incidents.csv")
    equipment_df = pd.read_csv("equipment.csv")
except FileNotFoundError:
    st.error("Error: CSV files not found. Please ensure workers.csv, incidents.csv, and equipment.csv are in the same folder.")
    st.stop()

# Convert to dictionary records for easy iteration in some parts
workers = workers_df.to_dict("records")
equipment = equipment_df.to_dict("records")

# Reconcile Risk Levels
for w in workers:
    serious = False
    if w["PPE_Compliance_pct"] < 80: serious = True
    if w["FatigueLevel_1to10"] >= 8: serious = True
    if serious:
        w["RiskLevel"] = "High"
    elif w["PPE_Compliance_pct"] < 90 or w["FatigueLevel_1to10"] >= 5:
        w["RiskLevel"] = "Medium"
    else:
        w["RiskLevel"] = "Low"

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def temp_status(t):
    return "NORMAL" if t < 80 else ("WARNING" if t <= 100 else "CRITICAL")

def vib_status(v):
    return "NORMAL" if v < 5 else ("WARNING" if v <= 8 else "CRITICAL")

def maintenance_flags(e):
    flags = []
    if str(e.get("MaintenanceStatus", "")).strip().lower() == "overdue":
        flags.append("OVERDUE")
    if e["Availability_pct"] < 90:
        flags.append(f"LOW AVAIL {e['Availability_pct']}%")
    if e["AlertCount"] > 5:
        flags.append(f"HIGH ALERTS ({e['AlertCount']})")
    return flags

# ==========================================
# 4. SIDEBAR (Login & Navigation)
# ==========================================
st.sidebar.markdown("<h2 style='text-align: center;'>⛏️ Khwezi Mining</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.subheader("Role-Based Access Control")

position = st.sidebar.selectbox(
    "Login as:",
    ["Administrator", "Safety Officer", "Mining Engineer", "Maintenance Engineer", "Manager"]
)

menu_options = ["View Dashboard", "Worker Safety Data", "Safety Incidents", "Equipment Data", "Maintenance Data"]

# Apply RBAC
if position == "Safety Officer": 
    menu_options = [m for m in menu_options if m not in ["Equipment Data", "Maintenance Data"]]
elif position == "Maintenance Engineer":
    menu_options = [m for m in menu_options if m not in ["Worker Safety Data", "Safety Incidents"]]

menu_choice = st.sidebar.radio("Navigate to:", menu_options)

# ==========================================
# 5. MAIN APP PAGES
# ==========================================

# --- DASHBOARD ---
if menu_choice == "View Dashboard":
    st.markdown("<h1 style='text-align: center;'>📊 Monitoring Dashboard</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center;'>Logged in as: <b>{position}</b></p>", unsafe_allow_html=True)
    st.divider()
    
    # Custom Colorful KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f'''
            <div class="kpi-card">
                <div class="kpi-label">Total Workers</div>
                <div class="kpi-value">{len(workers)}</div>
            </div>
        ''', unsafe_allow_html=True)
        
    with col2:
        high_risk_count = sum(1 for w in workers if w["RiskLevel"] == "High")
        st.markdown(f'''
            <div class="kpi-card">
                <div class="kpi-label">High Risk Workers</div>
                <div class="kpi-value" style="color: #C0392B;">{high_risk_count}</div>
            </div>
        ''', unsafe_allow_html=True)
        
    with col3:
        st.markdown(f'''
            <div class="kpi-card">
                <div class="kpi-label">Total Incidents</div>
                <div class="kpi-value">{len(incidents_df)}</div>
            </div>
        ''', unsafe_allow_html=True)
        
    with col4:
        overdue_count = sum(1 for e in equipment if e["MaintenanceStatus"] == "Overdue")
        st.markdown(f'''
            <div class="kpi-card">
                <div class="kpi-label">Equipment Overdue</div>
                <div class="kpi-value" style="color: #E67E22;">{overdue_count}</div>
            </div>
        ''', unsafe_allow_html=True)
    
    st.divider()
    st.subheader("🚨 Quick Alert Summary")
    critical_equip = [e["EquipmentID"] for e in equipment if temp_status(e["Temperature_C"]) == "CRITICAL" or vib_status(e["Vibration_mms"]) == "CRITICAL"]
    if critical_equip:
        st.error(f"*CRITICAL ALERT:* Equipment temperature/vibration out of bounds detected on: {', '.join(critical_equip)}. Inspect immediately.")
    else:
        st.success("✅ All equipment within normal operating limits.")

# --- WORKER SAFETY ---
elif menu_choice == "Worker Safety Data":
    st.title("👷 Worker Safety Data")
    df_workers = pd.DataFrame(workers)
    st.dataframe(df_workers[["WorkerID", "Name", "JobRole", "PPE_Compliance_pct", "FatigueLevel_1to10", "RiskLevel"]], use_container_width=True)
    
    st.subheader("⚠️ High Risk Workers (Require Immediate Action)")
    high_risk = df_workers[df_workers["RiskLevel"] == "High"]
    if not high_risk.empty:
        st.warning(f"Found {len(high_risk)} high-risk workers. Check their PPE and Fatigue levels.")
        st.table(high_risk[["WorkerID", "Name", "PPE_Compliance_pct", "FatigueLevel_1to10"]])

# --- INCIDENTS ---
elif menu_choice == "Safety Incidents":
    st.title("⚠️ Safety Incidents Database")
    
    # KPI Counts for Incidents (Requirement)
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Incidents", len(incidents_df))
    critical_inc = len(incidents_df[incidents_df['SeverityClass'] == 'Critical'])
    c2.metric("Critical Incidents", critical_inc)
    if 'LostTimeInjury' in incidents_df.columns:
        lti_inc = len(incidents_df[incidents_df['LostTimeInjury'] == 'Yes'])
        c3.metric("Lost-Time Injuries", lti_inc)

    st.divider()

    # ADD INCIDENT FORM (Now properly placed inside this page)
    with st.expander("📝 Add New Incident", expanded=False):
        with st.form("add_incident_form"):
            col1, col2 = st.columns(2)
            with col1:
                date = st.date_input("Date")
                time = st.time_input("Time")
                shift = st.selectbox("Shift", ["Day", "Night"])
                location = st.text_input("Location")
                department = st.text_input("Department")
            with col2:
                incident_type = st.text_input("Incident Type")
                severity = st.selectbox("Severity", ["Minor", "Moderate", "LTI"])
                severity_class = st.selectbox("Severity Class", ["Low", "High", "Critical"])
                status = st.selectbox("Status", ["Open", "Under Investigation", "Closed"])
            
            submitted = st.form_submit_button("Save Incident")
            
            if submitted:
                if not location or not incident_type:
                    st.error("Location and Incident Type are required.")
                else:
                    # Auto-generate next ID
                    last_id_num = int(incidents_df['IncidentID'].str.replace('INC', '').astype(int).max())
                    new_id = f"INC{last_id_num + 1:04d}"
                    
                    new_incident = {
                        "IncidentID": new_id,
                        "Date": str(date),
                        "Time": str(time),
                        "Shift": shift,
                        "Location": location,
                        "Department": department,
                        "IncidentType": incident_type,
                        "Severity": severity,
                        "SeverityClass": severity_class,
                        "IncidentStatus": status
                    }
                    
                    # Add to DataFrame and Save to CSV
                    new_row = pd.DataFrame([new_incident])
                    incidents_df = pd.concat([incidents_df, new_row], ignore_index=True)
                    incidents_df.to_csv("incidents.csv", index=False)
                    
                    st.success(f"Incident {new_id} added successfully! Data saved.")
                    st.rerun() # Refresh to show new data instantly

    # DISPLAY & FILTER TABLE
    st.subheader("Filter Incidents")
    f1, f2 = st.columns(2)
    with f1:
        shift_filter = st.selectbox("Filter by Shift", ["All"] + list(incidents_df['Shift'].dropna().unique()))
    with f2:
        severity_filter = st.selectbox("Filter by Severity Class", ["All"] + list(incidents_df['SeverityClass'].dropna().unique()))

    filtered_df = incidents_df.copy()
    if shift_filter != "All":
        filtered_df = filtered_df[filtered_df['Shift'] == shift_filter]
    if severity_filter != "All":
        filtered_df = filtered_df[filtered_df['SeverityClass'] == severity_filter]

    st.write("### Incident Records")
    st.dataframe(filtered_df, use_container_width=True)

# --- EQUIPMENT ---
elif menu_choice == "Equipment Data":
    st.title("🚜 Equipment Condition Monitoring")
    df_eq = pd.DataFrame(equipment)
    
    st.dataframe(df_eq[["EquipmentID", "EquipmentType", "Temperature_C", "Vibration_mms", "Availability_pct", "MaintenanceStatus"]], use_container_width=True)
    
    st.subheader("Live Condition Status")
    for e in equipment:
        t_stat = temp_status(e["Temperature_C"])
        v_stat = vib_status(e["Vibration_mms"])
        
        if t_stat == "CRITICAL" or v_stat == "CRITICAL":
            st.error(f"🔴 *{e['EquipmentID']}* - Temp: {e['Temperature_C']}°C ({t_stat}) | Vib: {e['Vibration_mms']}mm/s ({v_stat}) - *INSPECT IMMEDIATELY*")
        elif t_stat == "WARNING" or v_stat == "WARNING":
            st.warning(f"🟡 *{e['EquipmentID']}* - Temp: {e['Temperature_C']}°C ({t_stat}) | Vib: {e['Vibration_mms']}mm/s ({v_stat})")

# --- MAINTENANCE ---
elif menu_choice == "Maintenance Data":
    st.title("🔧 Maintenance Overview")
    df_eq = pd.DataFrame(equipment)
    
    for index, row in df_eq.iterrows():
        flags = maintenance_flags(row)
        if flags:
            st.warning(f"*{row['EquipmentID']}* ({row['EquipmentType']}): {', '.join(flags)}")
        else:
            st.success(f"*{row['EquipmentID']}* ({row['EquipmentType']}): OK")
