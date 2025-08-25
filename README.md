# 🧠 Smart MCQ Quiz Generator  

An **AI-powered interactive quiz application** built with **Streamlit**, designed to generate **topic-specific MCQs** with detailed explanations, performance tracking, and personalized study recommendations. This project integrates **Llama 3 (via Ollama)** and **Google Gemini** for quiz generation, making it a powerful tool for adaptive learning and self-assessment.  

---

## ✨ Features  

- **⚡ Dynamic Quiz Generation**  
  - Generate quizzes on any topic/domain.  
  - Questions categorized into *Basic Concepts*, *Advanced Concepts*, and *Current Trends*.  
  - Customizable difficulty (Beginner → Advanced), style (Conceptual, Scenario-based, Mixed), and diagram-based options.  

- **📝 Smart Question Parsing & Validation**  
  - Ensures exactly 4 options per question.  
  - Marks correct answers with explanations.  
  - Robust error handling and format consistency.  

- **📊 Performance Analytics**  
  - Section-wise scoring with accuracy tracking.  
  - Interactive visualizations powered by **Plotly**.  
  - Historical performance trends and progress monitoring.  

- **🎯 Personalized Feedback**  
  - AI-driven analysis of incorrect answers.  
  - Identifies weak areas and knowledge gaps.  
  - Provides study material recommendations.  

- **🤖 Multi-Model Support**  
  - **Llama 3 (Ollama)** for structured quiz generation.  
  - **Gemini (Google Generative AI)** for flexible content creation.  

---

## 🛠️ Tech Stack  

- **Frontend:** Streamlit  
- **Backend / AI Models:** Llama 3 (Ollama), Google Gemini  
- **Data Handling & Visualization:** Pandas, Plotly  
- **Other Tools:** Streamlit Extras, AsyncIO  

---

## 📂 Project Structure  

```
├── helper_functions.py   # Validation, parsing, quiz display & analytics  
├── model.py              # Model initialization & response handling (Llama 3 & Gemini)  
├── question_generator.py # Main Streamlit app (quiz generation & UI)  
├── requirements.txt      # Dependencies  
```

---

## 🚀 Getting Started  

### 1. Clone the Repository  
```bash
git clone https://github.com/yourusername/smart-mcq-quiz.git
cd smart-mcq-quiz
```

### 2. Install Dependencies  
```bash
pip install -r requirements.txt
```

### 3. Run the Application  
```bash
streamlit run question_generator.py
```

---

## 📌 Usage  

1. Enter a **topic/domain** (e.g., *Machine Learning, Database Design*).  
2. Select **model** (Llama 3 or Gemini), difficulty, style, and number of questions.  
3. Generate the quiz and attempt the MCQs.  
4. View **real-time performance analytics** and **personalized recommendations**.  

---

## 🎯 Future Enhancements  

- Support for **multi-language quiz generation**.  
- Integration with **learning platforms (Coursera, Udemy, etc.)**.  
- Export quizzes to **PDF/CSV**.  
- Adaptive quizzes that change difficulty based on performance.  

---

## 📜 License  

This project is licensed under the MIT License.  
