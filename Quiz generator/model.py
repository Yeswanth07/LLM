
import datetime
import ollama
import os
from google import genai

client = genai.Client(api_key="")


def init_llama():
    """Returns the default model name."""
    return "llama3:instruct"

def get_mcq_prompt(topic, difficulty="Intermediate", count=3, style="Conceptual", include_diagrams=False):
    """Generate a prompt for MCQ generation with customizable parameters"""
    prompt = f"""
    Generate a multiple choice quiz about {topic} with these specifications:
    - Difficulty level: {difficulty}
    - Question style: {style}
    - Questions per section: {count}
    - Include diagram-based questions: {'Yes' if include_diagrams else 'No'}
    
    Create questions in these categories:
    1. Basic Concepts
    2. Advanced Concepts
    3. Current Trends
    
    For each category, provide exactly {count} questions following this exact format:
    
    ### [Category Name]
    Q1: [Question text]?
    a) Option 1
    b) Option 2 [CORRECT]
    c) Option 3
    d) Option 4
    Explanation: [Detailed explanation of the correct answer]
    
    Important requirements:
    - Each question must have exactly 4 options
    - Mark the correct answer with [CORRECT]
    - Provide clear, technical explanations
    - Questions should match the {difficulty} difficulty level
    - Use {style}-style questions
    {'- Include at least one diagram description per section' if include_diagrams else ''}
    
    Example for {topic} ({difficulty} level):
    
    ### Basic Concepts
    Q1: What is the primary purpose of a constructor in OOP?
    a) To destroy objects [CORRECT]
    b) To initialize object properties
    c) To perform arithmetic operations
    d) To handle exceptions
    Explanation: Constructors are special methods called when an object is created...
    """
    return prompt
def get_model_response(model_name: str, prompt: str) -> str:
    print(f"Using model: {model_name}")
    """
    Generates a structured response using the given model and prompt via Ollama.
    """
    
    if model_name == 'llama3:instruct':
        # Use Ollama for the specified model
        print("Using Llama3 model for response generation")
        try:
            start_time = datetime.datetime.now()
            response = ollama.chat(
                model='llama3:instruct',
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert quiz generator who crafts perfect MCQs with clear explanations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            print(f"Response time for {model_name}: {datetime.datetime.now() - start_time}")
            return response['message']['content']
        except Exception as e:
            return f"⚠️ Model generation failed: {str(e)}"
        
    if model_name == 'gemini':
        # Use Ollama for the specified model
        print("Using Gemini model for response generation")
        try:
            start_time = datetime.datetime.now()
            response = client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prompt
            )
            # print(response.text)
            print(f"Response time for {model_name}: {datetime.datetime.now() - start_time}")
            return response.text
        except Exception as e:
            return f"⚠️ Model generation failed: {str(e)}"
