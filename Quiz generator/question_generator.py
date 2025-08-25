import streamlit as st
from model import init_llama, get_mcq_prompt, get_model_response
import datetime
import re
import pandas as pd
import plotly.express as px
from streamlit_extras.badges import badge
import time
import asyncio


from helper_functions import *

# Initialize the model with enhanced caching and loading feedback
@st.cache_resource(ttl="12h", show_spinner=False)
def load_model():
    try:
        # Create a dedicated container for model loading messages
        loading_container = st.empty()
        with loading_container.container():
            st.markdown("""
            <style>
                .model-loading {
                    padding: 20px;
                    border-radius: 10px;
                    background-color: #f8f9fa;
                    margin-bottom: 20px;
                }
                .loading-spinner {
                    border: 5px solid #f3f3f3;
                    border-top: 5px solid #4CAF50;
                    border-radius: 50%;
                    width: 50px;
                    height: 50px;
                    animation: spin 1s linear infinite;
                    margin: 20px auto;
                }
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            </style>
            <div class="model-loading">
                <h3>Initializing AI Model</h3>
                <div class="loading-spinner"></div>
                <p>This may take 2-3 minutes on first run...</p>
                <p><i>The model will remain cached for subsequent runs</i></p>
            </div>
            """, unsafe_allow_html=True)
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("Loading model weights (30%)...")
            time.sleep(1)  # Simulate loading delay
            
            progress_bar.progress(30)
            status_text.text("Initializing neural layers (60%)...")
            model = init_llama()  # Your original model initialization
            
            progress_bar.progress(90)
            status_text.text("Finalizing setup (100%)...")
            time.sleep(0.5)
            
            progress_bar.progress(100)
            status_text.success("Model ready!")
            time.sleep(1)
        
        # Clear the loading container after completion
        loading_container.empty()
        
        return model
    except Exception as e:
        st.error(f"Failed to load model: {str(e)}")
        return None


# ----------------------
# ALL ORIGINAL HELPER FUNCTIONS PRESERVED EXACTLY
# ----------------------

# ----------------------
# MAIN APP WITH LOADING OPTIMIZATIONS
# ----------------------
def main():
    # Page configuration with light theme
    st.set_page_config(
        page_title="🎯 Smart MCQ Quiz", 
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Light theme CSS
    st.markdown("""
    <style>
        /* Main styles */
        .stApp {
            background-color: #f8f9fa;
        }
        
        /* Text colors */
        body, p, h1, h2, h3, h4, h5, h6, .stMarkdown, .stText, .stRadio, .stSelectbox, .stSlider {
            color: #333333 !important;
        }
        
        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            color: #2c3e50 !important;
        }
        
        /* Input fields */
        .stTextInput>div>div>input, .stSelectbox>div>div>select {
            border: 2px solid #4CAF50 !important;
            border-radius: 8px !important;
            padding: 0.5rem !important;
            background-color: white !important;
        }
        
        /* Buttons */
        .stButton>button {
            background-color: #4CAF50 !important;
            color: white !important;
            border-radius: 8px !important;
            padding: 0.5rem 1rem !important;
            font-weight: bold !important;
        }
        
        .stButton>button:hover {
            background-color: #45a049 !important;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
        }
        
        .stTabs [data-baseweb="tab"] {
            padding: 8px 16px;
            border-radius: 8px;
            background-color: #e9f5ff;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #4CAF50 !important;
            color: white !important;
        }
        
        /* Progress bar */
        [data-testid="stProgress"] > div > div > div > div {
            background-color: #4CAF50 !important;
        }
        
        /* Cards */
        .question-card {
            background-color: white !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state with loading flags
    if 'app_initialized' not in st.session_state:
        st.session_state.app_initialized = False
        st.session_state.model_loaded = False
        st.session_state.show_results = False
        st.session_state.current_mcqs = None
        st.session_state.user_answers = None
        st.session_state.current_topic = None
        st.session_state.model_name = None
        st.session_state.quiz_history = []
    
    # Initial loading screen
    if not st.session_state.app_initialized:
        with st.container():
            st.markdown("""
            <div style="text-align:center; padding:50px;">
                <h1>🧠 Smart MCQ Quiz Generator</h1>
                <div style="margin:30px auto; width:100px; height:100px; border:8px solid #f3f3f3; border-top:8px solid #4CAF50; border-radius:50%; animation:spin 1s linear infinite;"></div>
                <p>Initializing application components...</p>
                <style>@keyframes spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}</style>
            </div>
            """, unsafe_allow_html=True)
            
            # Initialize critical components
            model = load_model()
            if model:
                st.session_state.model_loaded = True
                st.session_state.app_initialized = True
                st.rerun()
            return
    
    # Main app header
    st.title("🧠 Smart MCQ Quiz Generator")
    st.markdown("Generate topic-specific quizzes with detailed performance analysis and personalized recommendations.")
    
    # Show results page if applicable
    if st.session_state.show_results and st.session_state.current_mcqs:
        show_results_page(
            st.session_state.current_mcqs,
            st.session_state.user_answers,
            st.session_state.current_topic,
            st.session_state.model_name
        )
        
        if st.button("🔄 Take Another Quiz", type="primary"):
            st.session_state.show_results = False
            st.rerun()
        return
    
    # Quiz Generation Page with async optimization
    with st.form("generator_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            topic = st.text_input(
                "📌 Enter your topic/domain",
                placeholder="e.g., Machine Learning, Database Design",
                help="Be specific for better results (e.g., 'Python OOP' instead of 'Programming')"
            )
            model_choice = st.selectbox(
                "🤖 Select AI Model",
                options=["llama3:instruct", "gemini"],
                help="Llama3 for complex topics, Mistral for faster generation"
            )
        
        with col2:
            difficulty = st.selectbox(
                "📊 Difficulty Level",
                options=["Beginner", "Intermediate", "Advanced"],
                index=1
            )
            questions_per_section = st.slider(
                "📝 Questions per section",
                min_value=1,
                max_value=10,
                value=3,
                help="Total questions = sections × this value"
            )
        
        # Advanced options
        with st.expander("⚙️ Advanced Options", expanded=False):
            col3, col4 = st.columns(2)
            with col3:
                question_style = st.selectbox(
                    "📝 Question Style",
                    options=["Conceptual", "Application", "Scenario-based", "Mixed"],
                    index=3
                )
            with col4:
                include_diagrams = st.checkbox(
                    "🖼️ Include diagram-based questions",
                    value=False,
                    help="Questions involving visual analysis"
                )
        
        submitted = st.form_submit_button(
            "✨ Generate Quiz",
            type="primary",
            use_container_width=True
        )
    
    if submitted:
        if not topic.strip():
            st.error("Please enter a topic.")
            return
        
        # Prepare prompt
        prompt = get_mcq_prompt(
            topic=topic,
            difficulty=difficulty,
            count=questions_per_section,
            style=question_style,
            include_diagrams=include_diagrams
        )
        
        # Generate with async loading
        with st.spinner(f"Generating {questions_per_section * 3} {difficulty} level questions about {topic}..."):
            try:
                # Show generation progress
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("Preparing question generation...")
                progress_bar.progress(10)
                
                # Async generation
                result = asyncio.run(async_get_model_response(model_choice, prompt))
                print(f"Model response: {result}")
                progress_bar.progress(60)
                status_text.text("Parsing generated questions...")
                
                parsed_mcqs = parse_mcqs(result)
                progress_bar.progress(90)
                
                if not parsed_mcqs:
                    st.error("""
                    ### Couldn't generate valid questions
                    This might be because:
                    - The topic was too broad or unclear
                    - The AI model didn't follow the format
                    - Technical issues with the model
                    
                    **Try:**
                    1. A more specific topic
                    2. Changing the difficulty level
                    3. Using a different AI model
                    """)
                    return
                
                st.session_state.current_mcqs = parsed_mcqs
                st.session_state.current_topic = topic
                st.session_state.model_name = model_choice
                progress_bar.progress(100)
                status_text.success("Questions generated successfully!")
                time.sleep(1)
                progress_bar.empty()
                status_text.empty()
                
                st.success(f"""
                ### ✅ Successfully generated {questions_per_section * 3} questions about:
                **{topic}**  
                **Difficulty:** {difficulty} | **Style:** {question_style}  
                {'**Includes:** Diagram-based questions' if include_diagrams else ''}
                """)
                
            except Exception as e:
                st.error(f"""
                ### Error generating questions
                **Details:** {str(e)}
                
                Please try:
                1. A different topic or more specific wording
                2. Changing the difficulty level
                3. Using a different AI model
                """)
                return
    
    # Display quiz if available
    if st.session_state.current_mcqs:
        display_quiz(st.session_state.current_mcqs)
        
    # Display quiz history if available
    if st.session_state.quiz_history:
        with st.expander("📜 Quiz History", expanded=False):
            history_df = pd.DataFrame(st.session_state.quiz_history)
            st.dataframe(
                history_df.sort_values('date', ascending=False),
                column_config={
                    "date": st.column_config.DatetimeColumn("Date"),
                    "topic": "Topic",
                    "score": "Correct",
                    "total": "Total",
                    "percentage": st.column_config.ProgressColumn(
                        "Accuracy",
                        format="%.0f%%",
                        min_value=0,
                        max_value=1,
                    )
                },
                hide_index=True,
                use_container_width=True
            )
            
            if len(history_df) > 1:
                fig = px.line(
                    history_df.sort_values('date'),
                    x='date',
                    y='percentage',
                    title='Your Accuracy Over Time',
                    labels={'percentage': 'Accuracy', 'date': 'Date'},
                    markers=True
                )
                fig.update_yaxes(tickformat=".0%", range=[0, 1])
                st.plotly_chart(fig, use_container_width=True)

# Async helper function
async def async_get_model_response(model_choice, prompt):
    """Run model response generation in a separate thread"""
    return await asyncio.to_thread(get_model_response, model_choice, prompt)

if __name__ == "__main__":
    main()