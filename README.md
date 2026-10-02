# 🛡️ Risk & Fraud Copilot Workspace | Team SnowShield

An AI-native procurement fraud and velocity detection platform built 100% inside the Snowflake Data Cloud using a zero-data-movement architecture. Developed natively via Snowlit, it eliminates data leakage risks by keeping all financial processing within the secure database perimeter.

## 🚀 Live Submission Links
* **🎬 Walkthrough Video:** [PASTE YOUR GOOGLE DRIVE/YOUTUBE LINK HERE]
* **❄️ Native App Listing:** [PASTE YOUR SNOWFLAKE DEPLOYED APP LINK HERE]

## 🏗️ Technical Architecture
* **🔒 Tab 1: Identity Gate:** Dynamic Level 1–4 role-locking matching live `IDENTITY_ACCESS_MASTER` database rows.
* **📊 Tab 2: Audit Dashboard:** Fault-tolerant Snowpark analytics with typecast fallback guards for 100% uptime.
* **💬 Tab 3: Conversational CoCo:** RAG engine using `VECTOR_COSINE_SIMILARITY` and `llama3.1-70b` for instant markdown STR reports.
* **🔍 Tab 4 & 🔐 5: Admin Desk:** Account lookup and real-time status overrides.

graph TD
    %% Base Styling
    classDef snowflake fill:#1d94d2,stroke:#0f4c6c,stroke-width:2px,color:#fff;
    classDef security fill:#e056fd,stroke:#68217a,stroke-width:2px,color:#fff;
    classDef app fill:#ff7675,stroke:#b12e2e,stroke-width:2px,color:#fff;
    classDef data fill:#55efc4,stroke:#00b894,stroke-width:2px,color:#333;

    %% Components
    User([👤 User / Auditor])
    
    subgraph UI [Snowlit Streamlit App - streamlit_app.py]
        Tab1[🔒 Tab 1: Identity Gate]
        Tab2[📊 Tab 2: Audit Dashboard]
        Tab3[💬 Tab 3: Conversational CoCo]
        Tab4[🔍 Tabs 4 & 5: Admin Desk]
    end

    subgraph SF [Snowflake Data Cloud Perimeter]
        direction TB
        DB[(Master Data)]
        IAM[(IDENTITY_ACCESS_MASTER)]
        
        subgraph Snowpark [Snowpark Engine & AI - copilot_engine.py]
            Analytics[Fault-Tolerant Analytics]
            Vector[Vector Similarity Search]
            LLM[Cortex LLM: llama3.1-70b]
        end
    end

    %% Interactions
    User --> UI
    
    %% Security Validation
    Tab1 -->|Validates Active Session| IAM
    
    %% Core App Flows
    Tab2 -->|Executes Queries| Analytics
    Analytics <-->|Zero Data Movement| DB
    
    %% AI Flows
    Tab3 -->|Natural Language Prompt| Vector
    Vector -->|Context Retrieval| DB
    Vector -->|Augmented Context| LLM
    LLM -->|Generates Markdown| Tab3
    
    %% Admin Flows
    Tab4 -->|Lookups & Status Overrides| DB

    %% Apply Styles
    class SF,DB,IAM,Snowpark snowflake;
    class Tab1 security;
    class UI,Tab2,Tab3,Tab4 app;
    class Analytics,Vector,LLM data;
