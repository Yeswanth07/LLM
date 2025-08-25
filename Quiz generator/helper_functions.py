import streamlit as st
from model import init_llama, get_mcq_prompt, get_model_response
import datetime
import re
import pandas as pd
import plotly.express as px
from streamlit_extras.badges import badge
import time
import asyncio




def validate_question(q):
    """Enhanced question validation with detailed checks"""
    if not isinstance(q, dict):
        st.error("Invalid question format: Not a dictionary")
        return False
    if not q.get('question', '').strip():
        st.error("Invalid question: Missing question text")
        return False
    if len(q.get('options', [])) != 4:
        st.error(f"Invalid question: Expected 4 options, got {len(q.get('options', []))}")
        return False
    if q.get('correct') is None or not 0 <= q['correct'] < 4:
        st.error(f"Invalid question: Correct answer index out of range (0-3), got {q.get('correct')}")
        return False
    if not q.get('explanation', '').strip():
        st.error("Invalid question: Missing explanation")
        return False
    if any(not opt.strip() for opt in q['options']):
        st.error("Invalid question: Empty option found")
        return False
    return True

def parse_mcqs(text):
    """Robust parser with multiple format support and detailed error handling"""
    mcqs = {
        "Basic Concepts": [],
        "Advanced Concepts": [],
        "Current Trends": []
    }
    
    current_section = None
    current_question = None
    option_letters = ['a', 'b', 'c', 'd']
    
    try:
        # Normalize text
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'`{3}.*?`{3}', '', text, flags=re.DOTALL)
        text = re.sub(r'^\s*-\s*', '', text, flags=re.MULTILINE)
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Add progress tracking for parsing
        progress_bar = st.progress(0)
        status_text = st.empty()
        total_lines = len(lines)
        
        for idx, line in enumerate(lines):
            # Update progress every 50 lines
            if idx % 50 == 0:
                progress = idx / total_lines
                progress_bar.progress(progress)
                status_text.text(f"Processing questions... {int(progress*100)}%")
            
            # Section detection
            section_match = re.match(
                r'^#{1,3}\s*(Basic\s*Concepts|Advanced\s*Concepts|Current\s*Trends)\b', 
                line, re.IGNORECASE
            )
            if section_match:
                current_section = section_match.group(1).title()
                continue
                
            if not current_section:
                continue
                
            # Question detection
            question_match = re.match(
                r'^(?:Q\s*\d+[:.)]|Question\s*\d+:?|\[Q\d+\])\s*(.+)', 
                line, re.IGNORECASE
            )
            if question_match:
                if current_question and validate_question(current_question):
                    mcqs[current_section].append(current_question)
                    
                current_question = {
                    'question': question_match.group(1).strip(),
                    'options': [],
                    'correct': None,
                    'explanation': '',
                    'user_answer': None,
                    'section': current_section
                }
                continue
                
            # Option detection
            option_match = re.match(
                r'^\s*([a-dA-D]|[1-4])[).\s]\s*(.*?)(?:\s*\[?\b(?:CORRECT|RIGHT|ANSWER)\b\]?)?\s*$', 
                line, re.IGNORECASE
            )
            if option_match and current_question and len(current_question['options']) < 4:
                option_text = option_match.group(2).strip()
                is_correct = bool(re.search(r'\[?\b(?:CORRECT|RIGHT|ANSWER)\b\]?', line, re.IGNORECASE))
                
                if option_text:
                    current_question['options'].append(option_text)
                    if is_correct:
                        current_question['correct'] = len(current_question['options']) - 1
                continue
                
            # Explanation detection
            explanation_match = re.match(
                r'^(?:Explanation|Exp|Reason|Answer)[:.]?\s*(.+)', 
                line, re.IGNORECASE
            )
            if explanation_match and current_question:
                current_question['explanation'] = explanation_match.group(1).strip()
                continue
                
            # Append to explanation if we're in a question context
            if current_question and current_question.get('explanation'):
                current_question['explanation'] += '\n' + line
    
        # Add the last question if valid
        if current_question and validate_question(current_question):
            mcqs[current_section].append(current_question)
        
        # Validate all sections have questions
        for section, questions in mcqs.items():
            if not questions:
                st.error(f"Section '{section}' has no valid questions")
                progress_bar.empty()
                status_text.empty()
                return None
                
        progress_bar.progress(1.0)
        status_text.success("Questions parsed successfully!")
        time.sleep(0.5)
        progress_bar.empty()
        status_text.empty()
        
        return mcqs
        
    except Exception as e:
        st.error(f"Parsing error: {str(e)}")
        return None

def analyze_wrong_answers(mcqs, user_answers, topic,model_name ):
    """Enhanced analysis of incorrect answers with personalized feedback"""
    wrong_answers = []
    
    # Collect all wrong answers with context
    for section, questions in mcqs.items():
        for i, q in enumerate(questions, 1):
            user_choice = user_answers.get(f"{section}_{i}")
            if user_choice is not None and user_choice != q['correct']:
                wrong_answers.append({
                    'section': section,
                    'question': q['question'],
                    'user_answer': q['options'][user_choice] if user_choice is not None else "Not attempted",
                    'correct_answer': q['options'][q['correct']],
                    'explanation': q['explanation']
                })
    
    if not wrong_answers:
        return {"analysis": "🎉 Excellent! You answered all questions correctly.", "wrong_answers": []}
    
    # Prepare prompt for detailed analysis
    prompt = f"""
    Analyze these incorrect answers from a {topic} quiz:
    {wrong_answers}
    
    Identify 3-5 specific technical areas that need improvement, focusing on:
    - Core concepts that were misunderstood
    - Patterns in the mistakes
    - Fundamental knowledge gaps
    
    For each area provide:
    1. The specific concept/topic
    2. Why it's important for {topic}
    3. Recommended study materials
    4. Related concepts to review
    
    Format your response as follows:
    
    🔍 Detailed Analysis for {topic}:
    
    🎯 Focus Area 1: [Concept Name]
    • Importance: [Why this matters]
    • Resources: [Books/Courses/Articles]
    • Related: [Related topics]
    
    🎯 Focus Area 2: [Concept Name]
    • Importance: [Why this matters]
    • Resources: [Books/Courses/Articles]
    • Related: [Related topics]
    """
    
    try:
        analysis = get_model_response(model_name, prompt)
        return {"analysis": analysis, "wrong_answers": wrong_answers}
    except Exception as e:
        return {"analysis": f"⚠️ Could not generate analysis: {str(e)}", "wrong_answers": wrong_answers}

def identify_common_themes(wrong_answers, topic, model_name):
    """Identify common themes in wrong answers for visualization"""
    if not wrong_answers:
        return {}
    
    prompt = f"""
    Analyze these wrong answers about {topic}:
    {wrong_answers}
    
    Identify the 3-5 most common technical themes/concepts that were misunderstood.
    Return ONLY a Python dictionary with concepts as keys and counts as values.
    Example: {{"Object-oriented programming": 3, "Database normalization": 2}}
    """
    
    try:
        response = get_model_response(model_name, prompt)
        return eval(response)
    except:
        return {}

# ----------------------
# ALL ORIGINAL DISPLAY FUNCTIONS PRESERVED EXACTLY
# ----------------------
def display_quiz(mcqs):
    """Enhanced quiz display with proper radio buttons and beautiful styling"""
    user_answers = {}
    
    with st.form(key='quiz_form'):
        st.markdown("""
        <style>
            /* Force ALL text to black */
            * {
                color: #000000 !important;
            }
            
            /* Question cards */
            .question-card {
                padding: 1.5rem;
                border-radius: 10px;
                background-color: #ffffff;
                margin-bottom: 1.5rem;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                border-left: 4px solid #4CAF50;
            }
            .question-text {
                font-size: 1.1rem;
                font-weight: 500;
                margin-bottom: 1rem;
            }
            
            /* Custom radio button styling */
            .st-eb {
                padding: 0.5rem;
                border-radius: 5px;
                margin: 0.3rem 0;
                background-color: #f8f9fa;
                transition: all 0.2s;
                border: 1px solid #ddd !important;
            }
            .st-eb:hover {
                background-color: #e9f5ff;
                border-color: #4CAF50 !important;
            }
            .st-eb [data-testid="stMarkdownContainer"] {
                color: #000000 !important;
            }
            
            /* Selected radio button */
            [data-testid="stRadio"] [role="radiogroup"] [aria-checked="true"] {
                background-color: #e1f5fe !important;
                border-color: #4CAF50 !important;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Add section loading progress
        section_count = len(mcqs)
        current_section = 0
        
        for section, questions in mcqs.items():
            current_section += 1
            with st.spinner(f"Loading {section} questions ({current_section}/{section_count})..."):
                if not questions:
                    continue
                    
                st.subheader(f"📘 {section}", divider='rainbow')
                
                for i, q in enumerate(questions, 1):
                    if not validate_question(q):
                        st.error(f"Skipping invalid question {i} in {section}")
                        continue
                        
                    # Question card
                    with st.container():
                        st.markdown(f"""
                        <div class="question-card">
                            <div class="question-text">
                                Q{i}. {q['question']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Radio buttons for options
                        user_choice = st.radio(
                            f"Select an answer for Q{i}",
                            options=q['options'],
                            key=f"{section}_{i}",
                            index=None,
                            format_func=lambda x: x,
                            label_visibility="collapsed"
                        )
                        
                        # Store the index of the selected option
                        if user_choice is not None:
                            user_answers[f"{section}_{i}"] = q['options'].index(user_choice)
                        
                        st.write("")  # Spacing
        
        submitted = st.form_submit_button("✅ Submit Answers", 
                                        use_container_width=True,
                                        type="primary")
    
    if submitted:
        total_questions = sum(len(questions) for questions in mcqs.values())
        if len(user_answers) < total_questions:
            st.warning(f"⚠️ Please answer all {total_questions} questions. You've answered {len(user_answers)}.")
        else:
            st.session_state['show_results'] = True
            st.session_state['user_answers'] = user_answers
            st.rerun()

def show_results_page(mcqs, user_answers, topic, model_name):
    """Enhanced results page with beautiful visualizations and detailed analysis"""
    try:
        # Calculate scores
        section_scores = {}
        for section, questions in mcqs.items():
            correct = sum(1 for i, q in enumerate(questions, 1) 
                     if user_answers.get(f"{section}_{i}") == q['correct'])
            section_scores[section] = {
                'correct': correct,
                'total': len(questions),
                'percentage': correct/len(questions) if len(questions) > 0 else 0
            }
        
        total_correct = sum(s['correct'] for s in section_scores.values())
        total_questions = sum(s['total'] for s in section_scores.values())
        overall_score = total_correct / total_questions if total_questions > 0 else 0
        
        # Performance summary
        st.title("📊 Quiz Results", anchor=False)
        st.subheader(f"Topic: {topic}", divider='rainbow')
        
        # Score cards
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Score", f"{total_correct}/{total_questions}")
        with col2:
            st.metric("Accuracy", f"{overall_score:.0%}")
        with col3:
            performance_level = (
                "Excellent" if overall_score >= 0.8 else
                "Good" if overall_score >= 0.6 else
                "Needs Improvement"
            )
            st.metric("Performance Level", performance_level)
        
        # Performance visualization
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Performance", "🔍 Review Answers", "🎯 Focus Areas", "📚 Recommendations"])
        
        with tab1:
            # Score by section
            st.subheader("Performance by Section")
            df_scores = pd.DataFrame([
                {"Section": s, "Correct": score['correct'], "Incorrect": score['total']-score['correct']}
                for s, score in section_scores.items()
            ])
            fig = px.bar(df_scores, x="Section", y=["Correct", "Incorrect"],
                        title="Score Distribution by Section",
                        labels={"value": "Number of Questions"},
                        color_discrete_map={"Correct": "#4CAF50", "Incorrect": "#F44336"},
                        barmode='group')
            st.plotly_chart(fig, use_container_width=True)
            
            # Time series for historical performance (if available)
            if 'quiz_history' in st.session_state:
                st.subheader("Historical Performance")
                history_df = pd.DataFrame(st.session_state.quiz_history)
                if not history_df.empty:
                    fig = px.line(history_df, x='date', y='percentage', 
                                 title='Your Accuracy Over Time',
                                 labels={'percentage': 'Accuracy', 'date': 'Date'},
                                 markers=True)
                    fig.update_yaxes(tickformat=".0%", range=[0, 1])
                    st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            # Detailed answer review
            st.subheader("Answer Review")
            for section, questions in mcqs.items():
                with st.expander(f"{section} ({section_scores[section]['correct']}/{section_scores[section]['total']} correct)", expanded=True):
                    for i, q in enumerate(questions, 1):
                        user_choice = user_answers.get(f"{section}_{i}")
                        is_correct = user_choice == q['correct']
                        
                        # Question container
                        with st.container():
                            st.markdown(f"**Q{i}. {q['question']}**")
                            
                            # User answer vs correct answer
                            if is_correct:
                                st.success(f"✅ Your answer: {q['options'][user_choice]}")
                            else:
                                st.error(f"❌ Your answer: {q['options'][user_choice] if user_choice is not None else 'Not attempted'}")
                                st.success(f"Correct answer: {q['options'][q['correct']]}")
                            
                            # Explanation with expander
                            with st.expander("📖 Explanation", expanded=False):
                                st.markdown(q['explanation'])
                            
                            st.divider()
        
        with tab3:
            # Weakness analysis
            st.subheader("Focus Areas for Improvement")
            with st.spinner("🔍 Analyzing your performance..."):
                analysis = analyze_wrong_answers(mcqs, user_answers, topic, model_name)
                themes = identify_common_themes(analysis["wrong_answers"], topic, model_name)
            
            if analysis["analysis"].startswith("🔍 Detailed Analysis for"):
                st.markdown(analysis["analysis"])
            else:
                st.warning(analysis["analysis"])
                if analysis["wrong_answers"]:
                    st.subheader("Incorrect Answers")
                    for i, wrong in enumerate(analysis["wrong_answers"], 1):
                        with st.expander(f"Question {i}", expanded=False):
                            st.markdown(f"**Question:** {wrong['question']}")
                            st.markdown(f"**Your answer:** {wrong['user_answer']}")
                            st.markdown(f"**Correct answer:** {wrong['correct_answer']}")
                            st.markdown(f"**Explanation:** {wrong['explanation']}")
            
            # Visualization of weak areas
            if themes:
                st.subheader("Weak Areas Distribution")
                df_themes = pd.DataFrame(themes.items(), columns=["Concept", "Count"])
                
                col1, col2 = st.columns(2)
                with col1:
                    fig = px.bar(df_themes, x="Concept", y="Count", color="Count",
                                title="Most Frequently Missed Concepts",
                                color_continuous_scale="reds")
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = px.pie(df_themes, values='Count', names='Concept',
                                title="Weak Areas Breakdown",
                                hole=0.4)
                    st.plotly_chart(fig, use_container_width=True)
                    
        with tab4:
            # Personalized recommendations
            st.subheader("Personalized Study Recommendations")
            
            if overall_score >= 0.8:
                st.success("🎉 Excellent performance! Here are some advanced resources:")
                st.markdown("""
                - Advanced courses on [Coursera](https://www.coursera.org)
                - Research papers on recent developments
                - Practical projects to apply your knowledge
                """)
            elif overall_score >= 0.6:
                st.info("👍 Good performance! Focus on these areas:")
                st.markdown("""
                - Intermediate courses on [Udemy](https://www.udemy.com)
                - Practice tests to identify remaining gaps
                - Review foundational concepts
                """)
            else:
                st.warning("📚 Needs improvement. Recommended resources:")
                st.markdown("""
                - Beginner courses on [Khan Academy](https://www.khanacademy.org)
                - Foundational textbooks
                - Interactive coding platforms like [Codecademy](https://www.codecademy.com)
                """)
            
            # Badges for learning platforms
            st.markdown("### Recommended Learning Platforms")
            badge(type="coursera", name="deeplearning-ai")
            badge(type="udemy", name="")
            badge(type="kaggle", name="")
            
        # Save to history
        if 'quiz_history' not in st.session_state:
            st.session_state.quiz_history = []
            
        st.session_state.quiz_history.append({
            'topic': topic,
            'date': datetime.datetime.now(),
            'score': total_correct,
            'total': total_questions,
            'percentage': overall_score
        })
        
    except Exception as e:
        st.error(f"Error showing results: {str(e)}")
