import streamlit as st
import os
import time
import logging
from docx import Document as DocxDocument
import shutil
from io import BytesIO

# Import your backend agents
# Ensure SRS_Agent.py and Analytics_agent.py are in the same folder
try:
    from SRS_Agent import SRSPipeline
    from Analytics_agent import FeasibilityPipeline
except ImportError:
    st.error("Backend scripts not found. Please ensure 'SRS_Agent.py' and 'Analytics_agent.py' are in the directory.")

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Product Architect",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Professional UI ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        font-weight: bold;
    }
    .success-box {
        padding: 1rem;
        border-radius: 5px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .step-container {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e9ecef;
        margin-bottom: 20px;
    }
    /* Dark mode adjustments */
    @media (prefers-color-scheme: dark) {
        .step-container {
            background-color: #262730;
            border: 1px solid #4a4a4a;
        }
        .main-header {
            color: #64B5F6;
        }
        .sub-header {
            color: #ccc;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if 'srs_path' not in st.session_state:
    st.session_state.srs_path = None
if 'feasibility_path' not in st.session_state:
    st.session_state.feasibility_path = None
if 'project_title' not in st.session_state:
    st.session_state.project_title = ""

# --- Helper Functions ---

def read_docx(file_path):
    """Reads a docx file and returns markdown-friendly text."""
    try:
        doc = DocxDocument(file_path)
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip():
                # Bold headings based on style (heuristic)
                if 'Heading' in para.style.name:
                    full_text.append(f"### {para.text}")
                else:
                    full_text.append(para.text)
        return "\n\n".join(full_text)
    except Exception as e:
        return f"Error reading document preview: {str(e)}"

def save_uploaded_file(uploaded_file):
    """Saves uploaded file to temp directory for the agents to access."""
    try:
        os.makedirs("temp_uploads", exist_ok=True)
        file_path = os.path.join("temp_uploads", uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    except Exception as e:
        st.error(f"Error saving file: {e}")
        return None

# --- Sidebar ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/8637/8637107.png", width=50)
    st.title("Settings")
    
    api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")
    
    st.markdown("---")
    st.markdown("### Context Documents")
    uploaded_file = st.file_uploader("Attach PDF or Docx (Optional)", type=['pdf', 'docx'])
    
    st.markdown("---")
    st.info("💡 **Tip:** Provides detailed ideas for better results. The agents perform live web research.")

# --- Main Content ---

st.markdown('<div class="main-header">AI Product Architect</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Automated SRS Generation & Feasibility Analysis Pipeline</div>', unsafe_allow_html=True)

# 1. INPUT SECTION
with st.container():
    st.markdown("### 1. Project Definitions")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        project_title = st.text_input("Project Title", placeholder="e.g. AI Legal Assistant")
    with col2:
        detailed_idea = st.text_area("Detailed Idea / Requirements", height=100, 
                                   placeholder="Describe the problem, target users, key features, and platform requirements...")

    start_srs = st.button("🚀 Generate SRS Document", type="primary")

# 2. SRS GENERATION LOGIC
if start_srs:
    if not api_key:
        st.error("Please provide a Groq API Key in the sidebar.")
    elif not project_title or len(detailed_idea) < 20:
        st.warning("Please provide a project title and a detailed description.")
    else:
        # Set Environment
        os.environ["GROQ_API_KEY"] = api_key
        st.session_state.project_title = project_title
        
        # Handle Attachment
        attachment_path = None
        if uploaded_file:
            attachment_path = save_uploaded_file(uploaded_file)

        # Output Dir
        output_dir = os.path.join(os.getcwd(), "srs_output")
        
        # UI Status
        with st.status("🤖 AI Agent Working...", expanded=True) as status:
            try:
                st.write("Initializing SRS Pipeline...")
                pipeline = SRSPipeline()
                
                st.write("🔍 Parsing inputs and context...")
                time.sleep(1) # UX pause
                
                st.write("🌐 Conducting web research on domain and tech stack...")
                # The agent does this, we just show UI feedback
                
                st.write("📝 Drafting Software Requirements Specification (Llama 3)...")
                
                # Run the actual heavy lifting
                output_file = pipeline.process(
                    project_title=project_title,
                    detailed_idea=detailed_idea,
                    attachment_path=attachment_path,
                    output_dir=output_dir
                )
                
                st.session_state.srs_path = output_file
                status.update(label="✅ SRS Generation Complete!", state="complete", expanded=False)
                st.rerun() # Refresh to show next section
                
            except Exception as e:
                status.update(label="❌ Error Occurred", state="error")
                st.error(f"Process failed: {str(e)}")

# 3. SRS PREVIEW & DOWNLOAD
if st.session_state.srs_path and os.path.exists(st.session_state.srs_path):
    st.divider()
    
    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.markdown(f"### ✅ SRS Ready: *{os.path.basename(st.session_state.srs_path)}*")
    with col_b:
        with open(st.session_state.srs_path, "rb") as file:
            st.download_button(
                label="📥 Download SRS (.docx)",
                data=file,
                file_name=os.path.basename(st.session_state.srs_path),
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

    with st.expander("📄 View Generated SRS Content", expanded=False):
        doc_content = read_docx(st.session_state.srs_path)
        st.markdown(doc_content)

# 4. FEASIBILITY ANALYSIS SECTION
    st.divider()
    st.markdown("### 2. Feasibility & Risk Analysis")
    st.caption("The AI will now analyze the generated SRS for technical feasibility, cost estimation, and risks.")
    
    start_analysis = st.button("📊 Analyze Feasibility", type="primary")

    if start_analysis:
        if not api_key:
            st.error("API Key missing.")
        else:
            os.environ["GROQ_API_KEY"] = api_key
            output_dir = os.path.join(os.getcwd(), "feasibility_output")
            
            with st.status("🕵️‍♀️ Analytics Agent Working...", expanded=True) as status:
                try:
                    st.write("Reading SRS Document...")
                    pipeline = FeasibilityPipeline()
                    
                    st.write("🧠 Extracting functional & non-functional requirements...")
                    time.sleep(0.5)
                    
                    st.write("🌍 Researching tech maturity and market risks...")
                    
                    st.write("📈 Calculating cost estimations and timelines...")
                    
                    st.write("📝 Compiling Feasibility Report...")
                    
                    # Run Analysis Pipeline
                    output_file = pipeline.process(
                        srs_file_path=st.session_state.srs_path,
                        output_dir=output_dir,
                        project_title=st.session_state.project_title
                    )
                    
                    st.session_state.feasibility_path = output_file
                    status.update(label="✅ Analysis Complete!", state="complete", expanded=False)
                    st.rerun()
                    
                except Exception as e:
                    status.update(label="❌ Error Occurred", state="error")
                    st.error(f"Analysis failed: {str(e)}")

# 5. FEASIBILITY PREVIEW & DOWNLOAD
if st.session_state.feasibility_path and os.path.exists(st.session_state.feasibility_path):
    st.success("Feasibility Analysis Report Generated Successfully!")
    
    col_c, col_d = st.columns([3, 1])
    with col_c:
        st.markdown(f"### 📋 Report: *{os.path.basename(st.session_state.feasibility_path)}*")
    with col_d:
        with open(st.session_state.feasibility_path, "rb") as file:
            st.download_button(
                label="📥 Download Report (.docx)",
                data=file,
                file_name=os.path.basename(st.session_state.feasibility_path),
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

    with st.expander("📄 View Feasibility Report", expanded=True):
        report_content = read_docx(st.session_state.feasibility_path)
        st.markdown(report_content)