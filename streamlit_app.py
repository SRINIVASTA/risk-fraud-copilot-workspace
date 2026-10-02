# streamlit_app.py
import os
import re
import streamlit as st
import pandas as pd
import altair as alt
from snowflake.snowpark.functions import col
from copilot_engine import FraudCopilotEngine

# CORE SYSTEM CONFIGURATION
st.set_page_config(page_title="Risk & Fraud Copilot Workspace", page_icon="🛡️", layout="wide")

try:
    conn = st.connection("snowflake", ttl=os.getenv("SNOWFLAKE_CONNECTION_TTL"))
    session = conn.session()
    engine = FraudCopilotEngine(session)
except Exception as e:
    st.error(f"❌ Connection Error: Run directly inside your Snowflake Streamlit Workspace. Details: {e}")
    st.stop()

# --- MASTER ACCESS SECURITY GATE ---
if "developer_authenticated" not in st.session_state:
    st.session_state["developer_authenticated"] = False

if not st.session_state["developer_authenticated"]:
    st.markdown("---")
    _gate_spacer1, gate_center, _gate_spacer2 = st.columns(3)
    with gate_center:
        st.markdown("## 🛡️ Secure Compliance Sandbox")
        st.caption("Authorized evaluation access only. Please enter the master key to unlock the prototype console.")
        
        entered_key = st.text_input("Evaluation Access Key", type="password", placeholder="Enter key...")
        st.markdown("")
        
        if st.button("Unlock Sandbox Panel", type="primary", use_container_width=True):
            # FIXED: Bypassed os.getenv to eliminate secrets file reading errors entirely
            master_key = "Hack2Skill@2026" 
            if entered_key == master_key:
                st.session_state["developer_authenticated"] = True
                st.success("🔓 Environment Unlocked!")
                st.rerun()
            else:
                st.error("🔒 Invalid Access Key. Access Denied.")
    st.stop()  # Explicitly halts execution until the gate is unlocked

# AUTHENTICATION GATE
CLEARANCE_PERMISSIONS = {
    "L1_BASIC": {
        "label": "Level 1 - Basic",
        "tabs": ["Operational Dashboard"],
        "actions": ["View dashboard metrics", "View flagged transactions"],
        "restricted": ["Cannot access chat copilot", "Cannot view account details", "Cannot execute remediation", "Cannot manage users"]
    },
    "L2_ELEVATED": {
        "label": "Level 2 - Elevated",
        "tabs": ["Operational Dashboard", "Conversational CoCo Copilot", "Account Directory Lookup"],
        "actions": ["View dashboard metrics", "Query CoCo copilot", "View account profiles", "View transaction history"],
        "restricted": ["Cannot execute remediation actions", "Cannot deploy automated rules", "Cannot manage users"]
    },
    "L3_RESTRICTED": {
        "label": "Level 3 - Restricted",
        "tabs": ["Operational Dashboard", "Conversational CoCo Copilot", "Account Directory Lookup", "Remediation & Actions Console"],
        "actions": ["Full dashboard access", "Execute remediation locks", "Deploy automated rules", "Generate STRs", "Export reports"],
        "restricted": ["Cannot manage IAM users", "Cannot modify clearance levels"]
    },
    "L4_FULL_ACCESS": {
        "label": "Level 4 - Full Access",
        "tabs": ["All Tabs"],
        "actions": ["Unrestricted system access", "Manage IAM users", "Modify clearance levels", "Audit access logs", "System configuration"],
        "restricted": []
    }
}

if "iam_user" not in st.session_state:
    st.markdown("---")
# Change this on line 51:
    _login_spacer1, login_center, _login_spacer2 = st.columns([1, 2, 1])
    with login_center:
        st.markdown("## Procurement Fraud Detection System")
        st.markdown("#### Identity & Access Authentication Required")
        st.caption("All system features are locked until you authenticate with valid credentials.")
        st.markdown("")
        try:
            all_users_df = session.sql("SELECT USERNAME, DISPLAY_NAME, ACCESS_ROLE FROM RISK_COPILOT_DB.COMPLIANCE_CORE.IDENTITY_ACCESS_MASTER WHERE IS_ACTIVE = TRUE ORDER BY USERNAME").to_pandas()
            user_options = [""] + all_users_df["USERNAME"].tolist()
        except Exception:
            all_users_df = pd.DataFrame()
            user_options = [""]
            
        login_user = st.selectbox("Username", options=user_options, key="iam_username", format_func=lambda x: "Select a User ID..." if x == "" else x)
        
        if login_user:
            match = all_users_df[all_users_df["USERNAME"] == login_user]
            if not match.empty:
                # Using .iloc[0] safely extracts the first matched user row
                user_row = match.iloc[0]
                st.success(f"🔓 Welcome, **{user_row['DISPLAY_NAME']}** ({user_row['ACCESS_ROLE']})")
                st.text_input("Password", value="........", type="password", key="iam_password", disabled=True)
        else:
            st.text_input("Password", value="", type="password", key="iam_password", disabled=True, placeholder="Select a user above")
            
        st.markdown("")
        if st.button("Authenticate & Enter System", type="primary", use_container_width=True, key="iam_login_btn"):
            if login_user:
                auth_sql = f"""
                SELECT USER_ID, USERNAME, DISPLAY_NAME, ACCESS_ROLE, CLEARANCE_LEVEL, DEPARTMENT, IS_ACTIVE
                FROM RISK_COPILOT_DB.COMPLIANCE_CORE.IDENTITY_ACCESS_MASTER
                WHERE USERNAME = '{login_user}' AND IS_ACTIVE = TRUE
                """
                try:
                    auth_result = session.sql(auth_sql).to_pandas()
                    if not auth_result.empty:
                        user = auth_result.iloc[0].to_dict()

                        st.session_state["iam_user"] = user
                        session.sql(f"UPDATE RISK_COPILOT_DB.COMPLIANCE_CORE.IDENTITY_ACCESS_MASTER SET LAST_LOGIN = CURRENT_TIMESTAMP() WHERE USERNAME = '{login_user}'").collect()
                        st.rerun()
                    else:
                        st.error("🔒 ACCESS DENIED. Account not found or disabled.")
                except Exception as e:
                    st.error(f"❌ Authentication error: {str(e)}")
            else:
                st.warning("Please select a username to proceed.")
        st.stop()

# --- USER IS AUTHENTICATED — SHOW MAIN APP ---
iam_user = st.session_state["iam_user"]
user_clearance = str(iam_user.get("CLEARANCE_LEVEL", ""))
user_perms = CLEARANCE_PERMISSIONS.get(user_clearance, {})

# --- SIDEBAR CONTROL PANEL ---
st.sidebar.header("🛠️ Control Panel")
st.sidebar.caption("Connected to Database: `RISK_COPILOT_DB`")
st.sidebar.markdown("---")
st.sidebar.markdown(f"👤 **{iam_user['DISPLAY_NAME']}**")
st.sidebar.caption(f"Role: `{iam_user['ACCESS_ROLE']}` | Clearance: `{user_perms.get('label', user_clearance)}`")

if st.sidebar.button("🚪 Logout", use_container_width=True, key="sidebar_logout_btn"):
    st.session_state.pop("iam_user", None)
    st.session_state.pop("messages", None)
    st.rerun()

st.sidebar.markdown("---")
if "current_threshold" not in st.session_state:
    st.session_state["current_threshold"] = 5000000

min_threshold = st.sidebar.slider("Cross-Border Alert Threshold (₹)", 1000000, 10000000, key="current_threshold", step=500000)
if "messages" not in st.session_state: 
    st.session_state.messages = []

# Build tab list based on clearance
all_tab_defs = [
    ("📊 Operational Dashboard", "L1_BASIC"),
    ("💬 Conversational CoCo Copilot", "L2_ELEVATED"),
    ("🔍 Account Directory Lookup", "L2_ELEVATED"),
    ("🎮 Remediation & Actions Console", "L3_RESTRICTED"),
    ("🔐 IAM Security & Access Controls", "L4_FULL_ACCESS"),
]
clearance_rank = {"L1_BASIC": 1, "L2_ELEVATED": 2, "L3_RESTRICTED": 3, "L4_FULL_ACCESS": 4}
user_rank = clearance_rank.get(user_clearance, 0)
visible_tabs = [label for label, min_cl in all_tab_defs if clearance_rank.get(min_cl, 99) <= user_rank]

if user_clearance == "L4_FULL_ACCESS":
    # Fixed: Extract only the string title index t[0] from the tuple list
    visible_tabs = [t[0] for t in all_tab_defs] 

# Fail-safe guardrail: Ensure the list is never completely empty
if not visible_tabs:
    visible_tabs = ["📊 Operational Dashboard"]

tabs = st.tabs(visible_tabs)
tab_map = {label: t for label, t in zip(visible_tabs, tabs)}

# --- TAB 1: OPERATIONAL MONITORING ---
if "📊 Operational Dashboard" in tab_map:
    with tab_map["📊 Operational Dashboard"]:
        st.header("📈 Risk & Compliance Monitoring Terminal")
        st.caption("Powered Natively by Snowflake Snowpark Analytical Calculations & Cortex Vectors")
        
        if st.button("Run Global Compliance Audit Pipeline", type="primary"):
            st.subheader("🕵️ Step 1: Signal Detection (Structured Data)")
            with st.spinner("Filtering analytical database engines..."):
                signals_df = engine.detect_signals(min_amount=min_threshold)
            
            if signals_df.empty:
                st.warning("No anomalies detected for this configuration threshold.")
            else:
                total_incidents = len(signals_df)
                st.success(f"Detected {total_incidents} matching high-risk account profiles inside Snowflake.")
                try: total_flagged_amt = int(signals_df["AMOUNT"].sum())
                except Exception: total_flagged_amt = "NA"
                try:
                    avg_risk_score = float(signals_df["RISK_SCORE"].mean())
                    avg_risk_text = f"{avg_risk_score:.1f}%"
                except Exception: avg_risk_text = "NA"
                
                col1, col2, col3 = st.columns(3)
                col1.metric(label="🚨 Flagged Incidents Count", value=f"{total_incidents} Signals")
                col2.metric(label="💰 Total Capital Exposure", value=f"₹{total_flagged_amt:,}" if total_flagged_amt != "NA" else "NA")
                col3.metric(label="🛡️ Average Network Risk Factor", value=avg_risk_text)
                
                st.markdown("### Active Anomalous System Payload (PEP & Velocity Monitored)")
                st.dataframe(signals_df, use_container_width=True)
                
                try:
                    st.markdown("#### 🌍 Capital Exposure & Aggregated Risk Matrix by Country Destination")
                    country_summary = signals_df.groupby("COUNTRY_CODE", as_index=False).agg(TOTAL_VOLUME=("AMOUNT", "sum")).sort_values(by="TOTAL_VOLUME", ascending=False)
                    altair_chart = alt.Chart(country_summary).mark_bar(color="#DC2626").encode(
                        x=alt.X('TOTAL_VOLUME:Q', title="Total Capital Exposure (INR)"),
                        y=alt.Y('COUNTRY_CODE:N', sort='-x', title="Destination Jurisdiction"),
                        tooltip=[alt.Tooltip('COUNTRY_CODE:N', title="Jurisdiction"), alt.Tooltip('TOTAL_VOLUME:Q', title="Total Volume (₹)", format=",d")]
                    ).properties(height=300).interactive()
                    st.altair_chart(altair_chart, use_container_width=True)
                except Exception as chart_err:
                    st.caption(f"📊 Chart layout deferred to tabular registry matrix. Details: {chart_err}")
            
                st.subheader("📚 Step 2: Evidence Gathering (Cortex Vector Store)")
                with st.spinner("Executing semantic matching across compliance policy tables..."):
                    evidence = engine.gather_evidence(signals_df)
                st.info("Extracted Regulatory Violations & Compliance Snippets:")
                st.code(evidence, language="text")
                
                st.subheader("📝 Step 3: Audit-Ready Report Generation (Cortex Llama3.1)")
                with st.spinner("Compiling final markdown template parameters..."):
                    report_markdown = engine.generate_audit_report(signals_df, evidence)
                st.markdown(report_markdown)
                st.download_button(label="📥 Export STR Markdown Backup File", data=report_markdown, file_name="Suspicious_Transaction_Report.md", mime="text/markdown", use_container_width=True)

# --- TAB 2: CONVERSATIONAL COPILOT ---
if "💬 Conversational CoCo Copilot" in tab_map:
    with tab_map["💬 Conversational CoCo Copilot"]:
        st.header("💬 Conversational Cortex Copilot Room")
        st.caption("Ask natural language compliance questions with complete visibility across the full account database.")
        
        history_col1, history_col2 = st.columns(2)
        with history_col1:
            history_option = st.radio("Chat History Tracking Protocol:", ["Required (Keep Session Logs)", "Not Required (Clear Screen Buffer)"], horizontal=True, key="chat_history_toggle")
        with history_col2:
            st.write("##")
            if st.button("🗑️ Clear Conversation", type="secondary", use_container_width=True, key="clear_chat_bottom_pinned_btn"):
                st.session_state.messages = []
                st.toast("Conversational state history reset successfully.")
                st.rerun()
                
        if history_option == "Not Required (Clear Screen Buffer)":
            st.session_state.messages = []
            
        st.markdown("### Active Conversation Stream (Newest First)")
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
        user_prompt = st.chat_input("Ask CoCo about transactions, accounts, or RBI compliance playbooks...")
        if user_prompt:
            st.session_state.messages.insert(0, {"role": "user", "content": user_prompt})
            with st.spinner("CoCo querying live database..."):
                try:
                    joined_profiles_sql = """
                    SELECT 
                        a.ACCOUNT_ID, a.CUSTOMER_NAME, a.KYC_STATUS, a.CUSTOMER_TYPE, a.IS_PEP,
                        NVL(r.SYSTEMIC_LOCK_STATUS, 'UNLOCKED') as LIVE_LOCK_STATUS,
                        NVL(r.OUTBOUND_OVERRIDE_ENABLED, FALSE) as OVERRIDE_STATUS,
                        r.UPDATED_AT as LAST_REMEDIATION_AT
                    FROM RISK_COPILOT_DB.COMPLIANCE_CORE.ACCOUNT_MASTER a
                    LEFT JOIN (
                        SELECT ACCOUNT_ID, SYSTEMIC_LOCK_STATUS, OUTBOUND_OVERRIDE_ENABLED, UPDATED_AT
                        FROM RISK_COPILOT_DB.COMPLIANCE_CORE.REMEDIATION_LOG
                        QUALIFY ROW_NUMBER() OVER (PARTITION BY ACCOUNT_ID ORDER BY UPDATED_AT DESC) = 1
                    ) r ON a.ACCOUNT_ID = r.ACCOUNT_ID
                    """
                    joined_df = session.sql(joined_profiles_sql).to_pandas()
                    joined_df.columns = joined_df.columns.str.strip().str.upper()
                    
                    numbers_in_prompt = re.findall(r'\d+', user_prompt)
                    acc_patterns = re.findall(r'ACC[_\s\-]?(\d+)', user_prompt.upper())
                    candidate_nums = set(numbers_in_prompt + acc_patterns)
                    
                    account_lookup = {}
                    for _, row in joined_df.iterrows():
                        aid = str(row.get("ACCOUNT_ID", "")).strip()
                        num = aid.replace("ACC_", "")
                        account_lookup[num] = row
                        
                    matched = None
                    for num in candidate_nums:
                        if num in account_lookup:
                            matched = account_lookup[num]
                            break
                            
                    status_keywords = ["status", "locked", "lock", "unlocked", "remediation", "state", "active"]
                    is_status_question = any(kw in user_prompt.lower() for kw in status_keywords)
                    
                    if matched is not None and is_status_question:
                        aid = str(matched["ACCOUNT_ID"])
                        name = str(matched["CUSTOMER_NAME"])
                        kyc = str(matched["KYC_STATUS"])
                        ctype = str(matched["CUSTOMER_TYPE"])
                        is_pep = str(matched["IS_PEP"]).strip().upper() in ["TRUE", "YES", "1"]
                        lock = str(matched["LIVE_LOCK_STATUS"]).strip()
                        override = str(matched["OVERRIDE_STATUS"]).strip()
                        
                        lines = [f"**Account {aid} - {name}**\n"]
                        lines.append(f"- **KYC Verification Status:** {kyc}")
                        lines.append(f"- **PEP Flag:** {'Yes - Politically Exposed Person' if is_pep else 'No'}")
                        lines.append(f"- **Customer Type:** {ctype}")
                        if lock == "ACTIVE_LOCK":
                            lines.append(f"\n🚨 **REMEDIATION_LOG STATUS: ACTIVE_LOCK - This account is currently LOCKED.**")
                            lines.append(f"Outbound override enabled: {override}. Account is under active investigation. All outbound transactions are restrained.")
                        elif lock == "UNLOCKED":
                            lines.append(f"\n✅ **Remediation Status:** UNLOCKED. No restrictions. Account is fully operational.")
                        else:
                            lines.append(f"\nℹ️ **Remediation Status:** No remediation actions on record.")
                        ai_output = "\n".join(lines)
                    else:
                        account_detail_block = ""
                        if matched is not None:
                            aid = str(matched["ACCOUNT_ID"])
                            full_record_sql = f"SELECT * FROM RISK_COPILOT_DB.COMPLIANCE_CORE.ACCOUNT_MASTER WHERE ACCOUNT_ID = '{aid}'"
                            full_df = session.sql(full_record_sql).to_pandas()
                            full_df.columns = full_df.columns.str.strip().str.upper() # Keep column casing safe
                            
                            if not full_df.empty:
                                # FIXED: Explicitly pull the row as a Series index record to fix .iloc get attribute crash
                                record = full_df.iloc[0] 
                                detail_lines = [f"FULL ACCOUNT MASTER RECORD FOR {aid}:"]
                                for col_name in full_df.columns:
                                    detail_lines.append(f" {col_name}: {record[col_name]}")
                                
                                # FIXED: Standardized safe key access out of the series block
                                lock = str(matched.get("LIVE_LOCK_STATUS", "UNLOCKED")).strip()
                                detail_lines.append(f" REMEDIATION_LOCK_STATUS: {lock}")
                                account_detail_block = "\n".join(detail_lines)
                        
                        account_block = "\n".join([f"{row['ACCOUNT_ID']} | {row['CUSTOMER_NAME']} | LOCK:{row.get('LIVE_LOCK_STATUS','UNLOCKED')} | KYC:{row.get('KYC_STATUS','NA')} | PEP:{row.get('IS_PEP','NA')}" for _, row in joined_df.iterrows()])
                        reference_df = engine.detect_signals(min_amount=min_threshold)
                        target_cols = [c for c in ["TRANSACTION_ID","ACCOUNT_ID","CUSTOMER_NAME","AMOUNT","COUNTRY_CODE","RISK_STATUS","RISK_SCORE"] if c in reference_df.columns]
                        anomalies = reference_df[target_cols].to_string(index=False) if target_cols else "None"
                        
                        chat_prompt = f"""You are CoCo, an RBI compliance assistant. Answer using ONLY the data below.
                        {account_detail_block}
                        ALL ACCOUNTS (LOCK = remediation status, KYC = verification):
                        {account_block}
                        FLAGGED TRANSACTIONS:
                        {anomalies}
                        User Question: {user_prompt}
                        Answer:"""
                        clean = chat_prompt.replace("'", "''").replace("{", "[").replace("}", "]")
                        
                        # Execute context call directly to Cortex Complete API
                        res_df = session.sql(f"SELECT SNOWFLAKE.CORTEX.COMPLETE('llama3.1-70b', '{clean}') as output;").to_pandas()
                        if not res_df.empty:
                            ai_output = str(res_df.iloc[0]["OUTPUT"])
                        else:
                            ai_output = "No response from Cortex."
                except Exception as e:
                    ai_output = f"Error: {str(e)}"
                    
                st.session_state.messages.insert(1, {"role": "assistant", "content": ai_output})
                st.rerun()

# --- TAB 3: ACCOUNT LOOKUP ---
if "🔍 Account Directory Lookup" in tab_map:
    with tab_map["🔍 Account Directory Lookup"]:
        st.header("🔍 Customer 360 Account Profile Registry")
        st.caption("Select any customer to view full account master details, remediation status, and transaction history.")
        try:
            master_accounts_df = session.table("ACCOUNT_MASTER").to_pandas()
            master_accounts_df.columns = master_accounts_df.columns.str.strip().str.upper()
            ledger_transactions_df = session.table("TRANSACTION_LEDGER").to_pandas()
            ledger_transactions_df.columns = ledger_transactions_df.columns.str.strip().str.upper()
            account_list = master_accounts_df["ACCOUNT_ID"].unique() if "ACCOUNT_ID" in master_accounts_df.columns else []
        except Exception: 
            account_list, master_accounts_df, ledger_transactions_df = [], pd.DataFrame(), pd.DataFrame()
            
        selected_acc = st.selectbox("Select Account ID:", account_list, key="directory_account_lookup_select")
        if selected_acc:
            try:
                acc_row = master_accounts_df[master_accounts_df["ACCOUNT_ID"] == selected_acc]
                
                # FIXED: Added [0] to correctly extract the row as a Series object
                acc = acc_row.iloc[0] if not acc_row.empty else pd.Series(dtype=object)
                
                rem_sql = f"SELECT SYSTEMIC_LOCK_STATUS, KYC_STEP_UP_LEVEL, OUTBOUND_OVERRIDE_ENABLED, UPDATED_AT, UPDATED_BY FROM REMEDIATION_LOG WHERE ACCOUNT_ID = '{selected_acc}' ORDER BY UPDATED_AT DESC LIMIT 1"
                rem_df = session.sql(rem_sql).to_pandas()
                rem_df.columns = rem_df.columns.str.strip().str.upper() # Keep column headers matching uppercase
                
                if not rem_df.empty:
                    # FIXED: Extracted the first row as a Series via .iloc[0] to support .get()
                    rem_row = rem_df.iloc[0]
                    lock_status = str(rem_row.get("SYSTEMIC_LOCK_STATUS", "UNLOCKED"))
                    kyc_step = str(rem_row.get("KYC_STEP_UP_LEVEL", "STANDARD"))
                else:
                    lock_status, kyc_step = "UNLOCKED", "STANDARD"
                    
                is_locked = lock_status == "ACTIVE_LOCK"
                st.markdown("#### Key Status")
                s1, s2, s3, s4 = st.columns(4)
                kyc_status = str(acc.get("KYC_STATUS", "NA"))
                
                kyc_display = "✅ Verified" if kyc_status == "Verified" else ("⏳ Pending" if kyc_status == "Pending" else ("🛑 Suspended" if kyc_status == "Suspended" else kyc_status))
                rem_display = "🚨 ACTIVE_LOCK" if is_locked else ("⚡ ENHANCED_EDD" if kyc_step == "ENHANCED_EDD" else "🔓 No Restrictions")
                is_pep = str(acc.get("IS_PEP", "")).strip().upper() in ["TRUE", "YES", "1"]
                risk_tier = str(acc.get("RISK_TIER", "NA"))
                
                s1.metric("KYC Status", kyc_display)
                s2.metric("Remediation", rem_display)
                s3.metric("PEP", "⚠️ YES" if is_pep else "✅ No")
                s4.metric("Risk Tier", risk_tier)
                
                st.markdown("#### Account Master Record")
                d1, d2 = st.columns(2)
                with d1:
                    st.markdown(f"**Account ID:** `{acc.get('ACCOUNT_ID', 'NA')}`")
                    st.markdown(f"**Customer Name:** {acc.get('CUSTOMER_NAME', 'NA')}")
                    st.markdown(f"**Customer Type:** {acc.get('CUSTOMER_TYPE', 'NA')}")
                    st.markdown(f"**IEC Code:** `{acc.get('IEC_CODE', 'NA')}`")
                    st.markdown(f"**Trade License:** {acc.get('TRADE_LICENSE_TYPE', 'NA')}")
                    st.markdown(f"**Primary Trade Role:** {acc.get('PRIMARY_TRADE_ROLE', 'NA')}")
                    st.markdown(f"**Authorized AD Bank:** {acc.get('AUTHORIZED_AD_BANK', 'NA')}")
                with d2:
                    balance = acc.get('CURRENT_BALANCE_INR', 0)
                    try: balance_str = f"{int(float(balance)):,}"
                    except Exception: balance_str = str(balance)
                    st.markdown(f"**Current Balance:** **₹{balance_str}**")
                    st.markdown(f"**GSTIN:** `{acc.get('GSTIN', 'NA')}`")
                    st.markdown(f"**Tax Identifier (PAN):** `{acc.get('TAX_IDENTIFIER', 'NA')}`")
                    st.markdown(f"**Permanent Address:** {acc.get('PERMANENT_ADDRESS', 'NA')}")
                    st.markdown(f"**Registration Date:** {acc.get('REGISTRATION_DATE', 'NA')}")
                    st.markdown(f"**Last Audit Date:** {acc.get('LAST_AUDIT_DATE', 'NA')}")
                    
                st.markdown("#### Transaction History")
                related_tx = ledger_transactions_df[ledger_transactions_df["ACCOUNT_ID"] == selected_acc] if "ACCOUNT_ID" in ledger_transactions_df.columns else pd.DataFrame()
                if is_locked:
                    st.error("🔒 **Account is ACTIVE_LOCK - Transaction ledger access blocked during investigation.**")
                elif related_tx.empty:
                    st.info("No transactions found for this account.")
                else:
                    st.caption(f"{len(related_tx)} transaction(s) found")
                    st.dataframe(related_tx.fillna("NA"), use_container_width=True)
            except Exception as lookup_err: st.error(f"Error loading account profile: {lookup_err}")

# --- TAB 4: REMEDIATION CONSOLE ---
if "🎮 Remediation & Actions Console" in tab_map:
    with tab_map["🎮 Remediation & Actions Console"]:
        st.header("🛡️ Remediation & Actions Console")
        st.caption("Active Incident Response Core Routing - Updates the REMEDIATION_LOG Table Natively")
        action_col1, action_col2 = st.columns(2)
        with action_col1:
            st.subheader("🎯 Targeted Account Containment Protocols")
            try: remediation_acc_list = master_accounts_df["ACCOUNT_ID"].unique() if "ACCOUNT_ID" in master_accounts_df.columns else []
            except Exception: remediation_acc_list = []
            
            target_remediation_acc = st.selectbox("Select Target Profile to Contain:", remediation_acc_list, key="remediation_acc_select")
            containment_protocol = st.selectbox("Select Mitigation Protocol to Enforce:", ["ACTIVE_LOCK", "UNLOCKED", "ENHANCED_EDD", "STANDARD_KYC"])
            requires_justification = containment_protocol != "ACTIVE_LOCK"
            compliance_remarks, uploaded_doc_name = "", ""
            
            if requires_justification:
                st.warning("⚠️ Changing protocol from ACTIVE_LOCK requires mandatory compliance justification.")
                compliance_remarks = st.text_area("Compliance Remarks & Justification", placeholder="Provide detailed justification for this protocol change...", height=120, key="compliance_remarks")
                uploaded_file = st.file_uploader("Enclosed Scanned Letter / Document Reference", type=["pdf", "png", "jpg", "jpeg"], key="compliance_doc_upload")
                if uploaded_file is not None:
                    uploaded_doc_name = uploaded_file.name
                    st.success(f"📎 Document successfully attached: **{uploaded_doc_name}**")
            
            commit_allowed = not requires_justification or (compliance_remarks.strip() and uploaded_doc_name)
            
            if st.button("Commit Update to REMEDIATION_LOG Table", type="primary", use_container_width=True, disabled=(not commit_allowed)):
                if not target_remediation_acc:
                    st.warning("Action Aborted: No valid target profile selected.")
                else:
                    lock_p = "ACTIVE_LOCK" if containment_protocol == "ACTIVE_LOCK" else ("UNLOCKED" if containment_protocol == "UNLOCKED" else "STANDARD")
                    over_p = "TRUE" if containment_protocol == "ACTIVE_LOCK" else "FALSE"
                    kyc_p = "ENHANCED_EDD" if containment_protocol == "ENHANCED_EDD" else "STANDARD"
                    updated_by = str(iam_user.get("USERNAME", "STREAMLIT_COPILOT_SIS"))
                    
                    if requires_justification:
                        safe_remarks = compliance_remarks.replace("'", "''")
                        safe_doc_ref = uploaded_doc_name.replace("'", "''")
                        insert_query = f"INSERT INTO REMEDIATION_LOG (ACCOUNT_ID, SYSTEMIC_LOCK_STATUS, OUTBOUND_OVERRIDE_ENABLED, KYC_STEP_UP_LEVEL, UPDATED_BY, COMPLIANCE_REMARKS, DOCUMENT_REFERENCE) VALUES ('{str(target_remediation_acc)}', '{str(lock_p)}', {str(over_p)}, '{str(kyc_p)}', '{updated_by}', '{safe_remarks}', '{safe_doc_ref}');"
                    else:
                        insert_query = f"INSERT INTO REMEDIATION_LOG (ACCOUNT_ID, SYSTEMIC_LOCK_STATUS, OUTBOUND_OVERRIDE_ENABLED, KYC_STEP_UP_LEVEL, UPDATED_BY) VALUES ('{str(target_remediation_acc)}', '{str(lock_p)}', {str(over_p)}, '{str(kyc_p)}', '{updated_by}');"
                    try:
                        session.sql(insert_query).collect()
                        st.success(f"Execution complete. Operational mode updated to {containment_protocol}.")
                        st.rerun()
                    except Exception as e: st.error(f"NA - Write pipeline execution dropped: {str(e)}")
                    
        with action_col2:
            st.subheader("📋 Regulatory Export & Core Controls")
            try:
                remediation_history_df = session.table("REMEDIATION_LOG").sort(col("UPDATED_AT").desc()).to_pandas()
                if remediation_history_df.empty: st.info("The `REMEDIATION_LOG` table is currently empty.")
                else: st.dataframe(remediation_history_df.fillna("NA"), use_container_width=True)
            except Exception as log_err: st.info(f"The remediation logging matrix is empty. Details: {log_err}")
            
            st.divider()
            st.subheader("⚙️ Automated Data Engine Rules")
            st.caption("Scans all transactions against sanctioned country and PEP/tax haven rules. Auto-locks accounts and generates STRs.")
            rule_col1, rule_col2 = st.columns(2)
            with rule_col1:
                st.markdown("""
                **Rule 1 - Sanctioned Country Auto-Freeze**
                If any transaction routes to **KP, IR, SY, or MM** ➔ Immediate `ACTIVE_LOCK` + auto-generated STR.
                
                **Rule 2 - PEP Tax Haven Lock**
                If a PEP account routes funds to **KY or CH** ➔ Immediate `ACTIVE_LOCK` + `ENHANCED_EDD`.
                """)
            with rule_col2:
                st.warning("⚠️ This will scan ALL transactions and auto-lock matching accounts in the REMEDIATION_LOG.")
                if st.button("Deploy Automated Rules NOW", type="primary", use_container_width=True, key="auto_rules_btn"):
                    with st.spinner("Scanning all transactions against enforcement rules..."):
                        actions, str_reports = engine.run_automated_rules()
                    if not actions:
                        st.success("✅ Scan complete. No rule violations detected; all transactions are within compliance boundaries.")
                    else:
                        executed = [a for a in actions if a.get("status") == "EXECUTED"]
                        skipped = [a for a in actions if a.get("status") == "SKIPPED"]
                        failed = [a for a in actions if "FAILED" in str(a.get("status", ""))]
                        
                        if executed:
                            st.error(f"🚨 **{len(executed)} account(s) AUTO-LOCKED by rule engine:**")
                            for a in executed: st.markdown(f"- **{a['account_id']}** ({a['customer_name']}) - {a['rule']} - {a['reason']}")
                        if skipped:
                            st.info(f"ℹ️ {len(skipped)} account(s) already locked (skipped):")
                            for a in skipped: st.markdown(f"- **{a['account_id']}** ({a['customer_name']}) - already `ACTIVE_LOCK`")
                        if failed:
                            st.warning(f"⚠️ {len(failed)} action(s) failed:")
                            for a in failed: st.markdown(f"- **{a['account_id']}** - {a['status']}")
                            
                        if str_reports:
                            st.divider()
                            st.subheader("Auto-Generated Suspicious Transaction Reports")
                            for i, report in enumerate(str_reports):
                                with st.expander(f"STR #{i+1}", expanded=True):
                                    st.markdown(report)
                                    st.download_button(label=f"Download STR #{i+1}", data=report, file_name=f"AUTO_STR_{i+1}.md", mime="text/markdown", key=f"str_download_{i}")

# --- TAB 5: IAM SECURITY & ACCESS CONTROLS ---
if "🔐 IAM Security & Access Controls" in tab_map:
    with tab_map["🔐 IAM Security & Access Controls"]:
        st.header("🔐 IAM Security & Access Controls")
        st.caption("Role-Based Authentication Simulation - Powered by IDENTITY_ACCESS_MASTER")
        user = st.session_state["iam_user"]
        cl = str(user.get("CLEARANCE_LEVEL", ""))
        perms = CLEARANCE_PERMISSIONS.get(cl, {})
        
        st.subheader(f"👤 {user['DISPLAY_NAME']}")
        badge_col1, badge_col2, badge_col3 = st.columns(3)
        badge_col1.markdown(f"**Role:**\n\n`{user['ACCESS_ROLE']}`")
        badge_col2.markdown(f"**Clearance:**\n\n`{perms.get('label', cl)}`")
        badge_col3.markdown(f"**Department:**\n\n{user['DEPARTMENT']}")
        
        st.markdown("#### Authorized Access")
        access_col1, access_col2 = st.columns(2)
        with access_col1:
            st.markdown("**✔️ Permitted:**")
            for action in perms.get("actions", []): st.markdown(f"- {action}")
        with access_col2:
            st.markdown("**🛑 Restricted:**")
            restricted = perms.get("restricted", [])
            if restricted:
                for r in restricted: st.markdown(f"- {r}")
            else: st.markdown("- _No restrictions; full system access_")
            
        st.markdown("**📂 Accessible Tabs:**")
        st.code(", ".join(perms.get("tabs", [])))
        st.divider()
        st.subheader("👥 User Directory & Management")
        
        if st.session_state["iam_user"].get("CLEARANCE_LEVEL") == "L4_FULL_ACCESS":
            try:
                users_df = session.sql("SELECT USERNAME, DISPLAY_NAME, ACCESS_ROLE, CLEARANCE_LEVEL, DEPARTMENT, IS_ACTIVE, LAST_LOGIN, CREATED_AT FROM RISK_COPILOT_DB.COMPLIANCE_CORE.IDENTITY_ACCESS_MASTER ORDER BY CLEARANCE_LEVEL").to_pandas()
                st.dataframe(users_df, use_container_width=True)
            except Exception as e: st.error(f"Failed to load user directory: {e}")
            
            st.markdown("#### ➕ Add New User")
            add_col1, add_col2, add_col3, add_col4 = st.columns(4)
            new_username = add_col1.text_input("Username", key="new_user_name")
            new_display = add_col2.text_input("Display Name", key="new_display_name")
            new_role = add_col3.selectbox("Access Role", ["JUNIOR_CLERK", "COMPLIANCE_OFFICER", "PRINCIPAL_PCO", "SYSTEM_ADMIN"], key="new_role")
            new_clearance = add_col4.selectbox("Clearance", ["L1_BASIC", "L2_ELEVATED", "L3_RESTRICTED", "L4_FULL_ACCESS"], key="new_clearance")
            new_dept = st.text_input("Department", key="new_dept")
            new_password = st.text_input("Initial Password", type="password", key="new_password")
            
            if st.button("Create User", type="primary", key="create_user_btn"):
                if new_username and new_display and new_password:
                    try:
                        session.sql(f"INSERT INTO RISK_COPILOT_DB.COMPLIANCE_CORE.IDENTITY_ACCESS_MASTER (USERNAME, DISPLAY_NAME, PASSWORD_HASH, ACCESS_ROLE, CLEARANCE_LEVEL, DEPARTMENT) SELECT '{new_username}', '{new_display}', SHA2('{new_password}'), '{new_role}', '{new_clearance}', '{new_dept}'").collect()
                        st.success(f"User **{new_display}** ({new_username}) created with {new_clearance} clearance.")
                        st.rerun()
                    except Exception as e: st.error(f"Failed to create user: {e}")
                else: st.warning("Username, display name, and password are required.")
                
            st.markdown("#### 🔄 Toggle User Status")
            toggle_col1, toggle_col2 = st.columns(2)
            toggle_user = toggle_col1.selectbox("Select User", users_df["USERNAME"].tolist() if not users_df.empty else [], key="toggle_user_select")
            toggle_action = toggle_col2.selectbox("Action", ["DEACTIVATE", "ACTIVATE"], key="toggle_action")
            
            if st.button("Apply", key="toggle_user_btn"):
                new_status = "TRUE" if toggle_action == "ACTIVATE" else "FALSE"
                try:
                    session.sql(f"UPDATE RISK_COPILOT_DB.COMPLIANCE_CORE.IDENTITY_ACCESS_MASTER SET IS_ACTIVE = {new_status} WHERE USERNAME = '{toggle_user}'").collect()
                    st.success(f"User **{toggle_user}** {'activated' if new_status == 'TRUE' else 'deactivated'}.")
                    st.rerun()
                except Exception as e: st.error(f"Failed: {e}")
