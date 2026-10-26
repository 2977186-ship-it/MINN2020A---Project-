import streamlit as st
import pandas as pd
from datetime import datetime

# ==========================================
# 1. PAGE CONFIG & SETUP
# ==========================================
st.set_page_config(page_title="Khwezi Mining Monitor", page_icon="⛏️", layout="wide")

st.markdown(
    "<h2 style='text-align: center; color: #D4AF37; font-style: italic;'>"
    '"If it can\'t be grown, it must be mined."'
    "</h2>",
    unsafe_allow_html=True
)
st.divider()

# Load Data
@st.cache_data
def load_data():
    workers = pd.read_csv("workers.csv").to_dict("records")
    incidents = pd.read_csv("incidents.csv").to_dict("records")
    equipment = pd.read_csv("equipment.csv").to_dict("records")
    
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
            
    return workers, incidents, equipment

workers, incidents, equipment = load_data()

# ==========================================
# 2. HELPER FUNCTIONS
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
# 3. SIDEBAR (Login & Navigation)
# ==========================================
st.sidebar.title("⛏️ Khwezi Mining")
st.sidebar.subheader("Role-Based Access Control")

position = st.sidebar.selectbox(
    "Login as:",
    ["Administrator", "Safety Officer", "Mining Engineer", "Maintenance Engineer", "Manager"]
)

menu_options = ["View Dashboard", "Worker Safety Data", "Safety Incidents", "Equipment Data", "Maintenance Data"]
if position == "Safety Officer": 
    menu_options = [m for m in menu_options if m not in ["Equipment Data", "Maintenance Data"]]
elif position == "Maintenance Engineer":
    menu_options = [m for m in menu_options if m not in ["Worker Safety Data", "Safety Incidents"]]

menu_choice = st.sidebar.radio("Navigate to:", menu_options)

# ==========================================
# 4. MAIN APP PAGES
# ==========================================

# --- DASHBOARD ---
if menu_choice == "View Dashboard":
    st.title("📊 Monitoring Dashboard")
    st.markdown(f"Logged in as: **{position}**")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Workers", len(workers))
    col2.metric("High Risk Workers", sum(1 for w in workers if w["RiskLevel"] == "High"))
    col3.metric("Total Incidents", len(incidents))
    col4.metric("Equipment Overdue", sum(1 for e in equipment if e["MaintenanceStatus"] == "Overdue"))
    
    st.divider()
    st.subheader("Quick Alert Summary")
    critical_equip = [e["EquipmentID"] for e in equipment if temp_status(e["Temperature_C"]) == "CRITICAL" or vib_status(e["Vibration_mms"]) == "CRITICAL"]
    if critical_equip:
        st.error(f"🚨 CRITICAL equipment temperature/vibration detected on: {', '.join(critical_equip)}")
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
with st.expander("📝 Add New Incident"):
    with st.form("add_incident_form"):
        date = st.date_input("Date")
        time = st.time_input("Time")
        shift = st.selectbox("Shift", ["Day", "Night"])
        location = st.text_input("Location")
        department = st.text_input("Department")
        incident_type = st.text_input("Incident Type")
        severity = st.selectbox("Severity", ["Minor", "Moderate", "LTI"])
        severity_class = st.selectbox("Severity Class", ["Low", "High", "Critical"])
        status = st.selectbox("Status", ["Open", "Under Investigation", "Closed"])
        
        # Submit button
        submitted = st.form_submit_button("Save Incident")
        
        if submitted:
            # Basic validation
            if not location or not department or not incident_type:
                st.error("Please fill in all required text fields.")
            else:
                # Create new incident dictionary
                new_incident = {
                    "IncidentID": f"INC{incident_id_counter:04d}",
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
                
                # Add to dataframe (and ideally save to CSV)
                new_row = pd.DataFrame([new_incident])
                st.session_state['incidents_df'] = pd.concat([st.session_state['incidents_df'], new_row], ignore_index=True)
                
                st.success(f"Incident {new_incident['IncidentID']} added successfully!")
                st.rerun() # Refresh the page to show the new data

# --- DISPLAY TABLE SECTION ---
# Your existing filter code goes here...
st.write("### Current Incidents")
# st.dataframe(filtered_df) ...

# 3. Filters
st.write("### Filter Incidents")
f1, f2 = st.columns(2)
with f1:
    shift_filter = st.selectbox("Filter by Shift", ["All"] + list(incidents_df['Shift'].unique()))
with f2:
    severity_filter = st.selectbox("Filter by Severity Class", ["All"] + list(incidents_df['SeverityClass'].unique()))

# Apply filters
filtered_df = incidents_df.copy()
if shift_filter != "All":
    filtered_df = filtered_df[filtered_df['Shift'] == shift_filter]
if severity_filter != "All":
    filtered_df = filtered_df[filtered_df['SeverityClass'] == severity_filter]

# 4. Display Table
st.write("### Incident Records")
st.dataframe(filtered_df, use_container_width=True)
# --- EQUIPMENT ---
menu_choice == "Equipment Data"
st.title("🚜 Equipment Condition Monitoring")
df_eq = pd.DataFrame(equipment)
st.dataframe(df_eq[["EquipmentID", "EquipmentType", "Temperature_C", "Vibration_mms", "Availability_pct", "MaintenanceStatus"]], use_container_width=True)
st.subheader("Live Condition Status")
for e in equipment:
        t_stat = temp_status(e["Temperature_C"])
        v_stat = vib_status(e["Vibration_mms"])
        
        if t_stat == "CRITICAL" or v_stat == "CRITICAL":
            st.error(f"🔴 **{e['EquipmentID']}** - Temp: {e['Temperature_C']}°C ({t_stat}) | Vib: {e['Vibration_mms']}mm/s ({v_stat}) - **INSPECT IMMEDIATELY**")
        elif t_stat == "WARNING" or v_stat == "WARNING":
            st.warning(f"🟡 **{e['EquipmentID']}** - Temp: {e['Temperature_C']}°C ({t_stat}) | Vib: {e['Vibration_mms']}mm/s ({v_stat})")

# --- MAINTENANCE ---
elif menu_choice == "Maintenance Data":
    st.title("🔧 Maintenance Overview")
    df_eq = pd.DataFrame(equipment)
    
    for index, row in df_eq.iterrows():
        flags = maintenance_flags(row)
        if flags:
            st.warning(f"**{row['EquipmentID']}** ({row['EquipmentType']}): {', '.join(flags)}")
        else:
            st.success(f"**{row['EquipmentID']}** ({row['EquipmentType']}): OK")
        
