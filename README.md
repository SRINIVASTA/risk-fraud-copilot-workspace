# 🛡️ Risk & Fraud Copilot Workspace | Team:SnowShield

An AI-native procurement fraud and velocity detection platform built 100% inside the **Snowflake Data Cloud** using a zero-data-movement architecture. Developed natively via **Snowlit**, this solution completely eliminates data exfiltration and leakage vectors by keeping all data parsing, regulatory vector matching, and LLM text generation entirely within your secure database perimeter.

## 🚀 Live Submission Links
* **🎬 Walkthrough Video:** [PASTE YOUR GOOGLE DRIVE/YOUTUBE LINK HERE]
* **❄️ Native App Listing:** [PASTE YOUR SNOWFLAKE DEPLOYED APP LINK HERE]

---

## 🏗️ Technical Architecture & Data Flow

The architecture operates strictly inside the **Snowflake Data Cloud Perimeter** (`RISK_COPILOT_DB`). The frontend interface uses granular role-locking, routing session states through active user master data records before granting analytical or action capabilities.

```mermaid
graph TD
    %% Base Styling
    classDef snowflake fill:#1d94d2,stroke:#0f4c6c,stroke-width:2px,color:#fff;
    classDef security fill:#e056fd,stroke:#68217a,stroke-width:2px,color:#fff;
    classDef app fill:#ff7675,stroke:#b12e2e,stroke-width:2px,color:#fff;
    classDef data fill:#55efc4,stroke:#00b894,stroke-width:2px,color:#333;

    %% Components
    User([👤 User / Compliance Auditor])
    
    subgraph UI [Snowlit Workspace - streamlit_app.py]
        AuthGate[🔒 Identity Authentication Gate]
        Tab1[📊 Tab 1: Operational Dashboard]
        Tab2[💬 Tab 2: Conversational CoCo Copilot]
        Tab3[🔍 Tab 3: Account Directory Lookup]
        Tab4[🎮 Tab 4: Remediation & Actions Console]
        Tab5[🔐 Tab 5: IAM Security & Access Controls]
    end

    subgraph SF [Snowflake Data Cloud Perimeter - RISK_COPILOT_DB]
        direction TB
        subgraph Core [COMPLIANCE_CORE Schema]
            T1[(1. IDENTITY_ACCESS_MASTER)]
            V1{{"👁️ COMPLIANCE_AUDIT_STREAM (View)"}}
            T2[(2. AML_REGULATORY_POLICIES)]
            T3[(3. ACCOUNT_MASTER)]
            T4[(4. TRANSACTION_LEDGER)]
            T5[(5. REMEDIATION_LOG)]
            T6[(6. SANCTIONS_WATCHLIST)]
            T7[(7. TRADE_SHIPMENTS)]
        end
        
        subgraph SnowparkEngine [Snowpark Engine & AI - copilot_engine.py]
            SignalDet[Signal Detection Pipeline]
            VectorSim[Cortex Vector Similarity e5-base-v2]
            CortexLLM[Cortex LLM: llama3.1-70b]
            RuleEng[Automated Enforcement Engine]
        end
    end

    %% Interactions
    User -->|Access System| AuthGate
    AuthGate -->|Validates Active Session| T1
    
    %% Operational Audit Flow
    Tab1 -->|Trigger Pipeline| SignalDet
    SignalDet <-->|Filter Min Amount & Risk Signals| V1
    SignalDet -->|Semantic Context| VectorSim
    VectorSim <-->|Cosine Similarity Search| T2
    VectorSim -->|Augmented Context Payload| CortexLLM
    CortexLLM -->|Generates Markdown STR| Tab1
    
    %% Conversational CoCo Flow
    Tab2 -->|Natural Language Context Lookup| CortexLLM
    CortexLLM <-->|Session Snapshot Data| T3
    
    %% Directory Lookup Flow
    Tab3 -->|Profile Deep Dive| T3
    Tab3 -->|Historical Auditing| T4
    
    %% Remediation Log & Automation Flow
    Tab4 -->|Write Lock Updates & Justifications| T5
    Tab4 -->|Deploy Hardcoded Rules| RuleEng
    RuleEng <-->|Scan Signals & Compute Overrides| T4
    RuleEng <-->|Cross Reference Country Codes| T6

    %% IAM Security Administration Flow
    Tab5 -->|Create Users & Toggle Activity Status| T1

    %% Apply Styles
    class SF,Core,T1,V1,T2,T3,T4,T5,T6,T7 snowflake;
    class AuthGate security;
    class UI,Tab1,Tab2,Tab3,Tab4,Tab5 app;
    class SnowparkEngine,SignalDet,VectorSim,CortexLLM,RuleEng data;
```

---

## 👥 Role Matrix & Access Hierarchy

## 🔓 Passwordless Single Sign-On (SSO) Simulation Guide
For quick judging evaluation, the system features a passwordless, biometric-style IAM mapping lookup. 

**Instructions for Judges:**
1. Simply select any **Username** from the select box dropdown menu.
2. The system will automatically fetch that user's identity matrix. Leave the masked password as-is.
3. Click the primary **🔓 Authenticate & Enter System ** button to enter the workspace!

The application maps specific interfaces dynamically based on the verified `CLEARANCE_LEVEL` row entry assigned to the user inside `IDENTITY_ACCESS_MASTER`:

| Role | Clearance Level | Permitted Views & Actions | System Restrictions |
| :--- | :--- | :--- | :--- |
| **JUNIOR_CLERK** | `L1_BASIC` | View basic operational dashboard metrics & active anomalies. | Cannot query CoCo, view detailed profiles, lock accounts, or manage users. |
| **COMPLIANCE_OFFICER** | `L2_ELEVATED` | Operational Dashboard + Conversational CoCo room chat + Customer 360 lookup. | Blocked from executing manual remediations, auto-rules, or IAM adjustments. |
| **PRINCIPAL_PCO** | `L3_RESTRICTED` | All functional views + Execute manual containment protocols + Deploy automated rules. | Restricted from adding/managing system users or altering system clearancies. |
| **SYSTEM_ADMIN** | `L4_FULL_ACCESS` | Complete system access. Manage IAM table, append records, toggle user activity statuses. | *None — Unrestricted Account Administrator Access*. |
---

## ⚙️ Core Workspace Modules

### 📊 Tab 1: Operational Dashboard
Runs a multi-tier risk calculation pipeline powered by Snowpark analytics:
1. **Signal Detection:** Filters out anomalies from `COMPLIANCE_AUDIT_STREAM` (View) based on an interactive cross-border amount slider, matching high-impact criteria (`IS_PEP`, suspended flags, velocity warnings). 
2. **Dynamic Risk Scoring:** Programmatically builds a real-time risk profile using geographic target parameters (e.g., scoring adjustments for tax havens like `CH` or `KY`).
3. **Semantic Policy Extraction:** Executes a native Snowflake `VECTOR_COSINE_SIMILARITY` search querying `AML_REGULATORY_POLICIES` using the `e5-base-v2` embedding engine to surface matching legal context.
4. **Automated STR Assembly:** Pipelines structured data and unstructured legal fragments directly into Cortex `llama3.1-70b` to build a production-grade markdown Suspicious Transaction Report (STR) complete with metric summary cards and charts.

### 💬 Tab 2: Conversational CoCo Copilot
An interactive natural language compliance assistant. CoCo matches account mentions (e.g., searching for numeric patterns or strings like `ACC_101`) to parse details out of the `ACCOUNT_MASTER` layout instantly. If specific key phrases regarding "status" or "locks" are queried, CoCo references active states from the remediation log; general compliance prompts route out to a context-augmented Cortex LLM engine.

### 🔍 Tab 3: Account Directory Lookup
Exposes a comprehensive Customer 360 profile registry using data from `ACCOUNT_MASTER`. System users can browse demographic parameters, PAN numbers, Import Export Code (IEC) fields, GSTIN registrations, and historical transactional logs from the `TRANSACTION_LEDGER`. *Security Guard: If an account is currently marked with an `ACTIVE_LOCK` inside `REMEDIATION_LOG`, transaction histories are automatically masked to preserve audit integrity.*

### 🎮 Tab 4: Remediation & Actions Console
Allows direct database containment enforcement. Modifying an active account protocol to an unlocked state requires a mandatory compliance rationale and file upload attachment (PDF/images), appending audit traces directly to `REMEDIATION_LOG`. Includes the **Automated Data Engine Rules** runner which programmatically audits the workspace and processes system locks for high-risk targets:
* **Rule 1 (Sanctioned Country Auto-Freeze):** Immediate account lockdown if capital routes to countries flagged inside the `SANCTIONS_WATCHLIST` (`KP`, `IR`, `SY`, or `MM`).
* **Rule 2 (PEP Tax Haven Lock):** Immediate lockdown and `ENHANCED_EDD` escalation if a Politically Exposed Person transfers funds to designated tax havens.

### 🔐 Tab 5: IAM Security & Access Controls
A secure simulator panel displaying active clearance configurations. When accessed by an `L4_FULL_ACCESS` administrator, it unlocks database insertion wrappers to register new users with `SHA2` password hashes or toggle live operational access statuses inside `IDENTITY_ACCESS_MASTER`.
