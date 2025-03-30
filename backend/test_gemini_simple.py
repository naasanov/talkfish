import os
from dotenv import load_dotenv
import google.generativeai as genai
import json

# Load the environment variables
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '.env')
print(f"Loading .env from: {env_path}")
load_dotenv(env_path)

# Get API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("No Gemini API key found in .env file")

# Configure the API
print("Configuring Gemini API")
genai.configure(api_key=GEMINI_API_KEY)

# System prompt - EXACTLY the same as in nlp_analysis.py
SYSTEM_PROMPT = """
You are an expert interview coach specializing in behavioral interviews. Your task is to analyze interview responses and provide constructive, actionable feedback.

Follow these guidelines:
1. Evaluate responses using the STAR method (Situation, Task, Action, Result)
2. Identify strengths and areas for improvement
3. Check for clarity, conciseness, and relevance
4. Note any overuse of filler words or passive voice
5. Provide specific examples from the transcript to support your feedback
6. Suggest improvements with concrete examples
7. Maintain a supportive, encouraging tone
8. Structure your analysis with clear sections
9. Rate the overall response on a scale of 1-10
10. Keep feedback constructive and actionable
11. Consider the specific type of behavioral question asked
12. Evaluate whether the response actually answers the question being asked

Your output should be a JSON object with the following structure:
{
  "message": "Brief summary of overall feedback (1-2 sentences)",
  "type": "positive | neutral | constructive",
  "details": {
    "question_type": "The detected question type",
    "question_relevance": 1-10, 
    "star_analysis": {
      "situation": {"present": true/false, "strength": 1-10, "feedback": "..."},
      "task": {"present": true/false, "strength": 1-10, "feedback": "..."},
      "action": {"present": true/false, "strength": 1-10, "feedback": "..."},
      "result": {"present": true/false, "strength": 1-10, "feedback": "..."}
    },
    "language_quality": {
      "filler_words": {"frequency": "low|medium|high", "examples": [...]},
      "clarity": 1-10,
      "conciseness": 1-10
    },
    "improvement_suggestions": ["...", "...", "..."],
    "overall_score": 1-10
  }
}
"""

def test_gemini_basic():
    """Test very basic Gemini operation"""
    print("\n1. Testing basic Gemini API call...")
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Say hello if you can read this.")
    print(f"Response: {response.text}")

def test_gemini_with_system_prompt():
    """Test with system prompt and standard content"""
    print("\n2. Testing with combined prompt...")
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Sample interview response
    sample_response = """
    In my previous role, I had to deal with a difficult customer who was unhappy with our service. 
    I listened to their concerns, acknowledged their frustration, and worked with our team to find a solution.
    We ended up not only resolving their immediate issue but also implementing a new process to prevent similar problems.
    The customer became one of our strongest advocates.
    """
    
    # Create combined prompt with instructions and content
    combined_prompt = f"""
    {SYSTEM_PROMPT}
    
    Now analyze this response:
    
    Interview Type: behavioral
    Question Type: conflict
    
    Interviewee Response: "{sample_response}"
    
    Please analyze this interview response and provide detailed feedback following the guidelines.
    """
    
    print("Sending API request with combined prompt...")
    try:
        response = model.generate_content(
            combined_prompt,
            generation_config={
                "temperature": 0.2,
                "top_p": 0.95
            }
        )
        
        print("\nResponse received!")
        print(f"Raw response type: {type(response)}")
        
        if hasattr(response, 'text'):
            print("Response has 'text' attribute")
            raw_text = response.text
        else:
            print("Response has 'parts' attribute")
            raw_text = response.parts[0].text
        
        print(f"\nRaw response: {raw_text}")
        
        # Clean the response text
        cleaned_text = raw_text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        if cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[3:]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
        cleaned_text = cleaned_text.strip()
        
        print(f"\nCleaned text: {cleaned_text}")
        
        # Parse JSON
        try:
            parsed_json = json.loads(cleaned_text)
            print("\nSuccessfully parsed JSON:")
            print(json.dumps(parsed_json, indent=2))
        except json.JSONDecodeError as e:
            print(f"\nJSON parse error: {str(e)}")
            print(f"Problem at character position {e.pos}: {cleaned_text[max(0, e.pos-20):e.pos]}[HERE]{cleaned_text[e.pos:min(len(cleaned_text), e.pos+20)]}")
    
    except Exception as e:
        print(f"\nError during API call: {type(e).__name__}: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    print("\n============ SIMPLE GEMINI API TEST ============")
    
    # First test basic functionality
    test_gemini_basic()
    
    # Then test with the system prompt
    test_gemini_with_system_prompt() 