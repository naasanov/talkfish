import os
from dotenv import load_dotenv
import google.generativeai as genai
import json

def test_gemini_connection():
    """Test basic Gemini API connectivity"""
    print("\n1. Testing environment setup...")
    
    # Get the current file's directory and find .env
    current_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(current_dir, '.env')
    print(f"Looking for .env at: {env_path}")
    print(f"File exists: {os.path.exists(env_path)}")
    
    # Load environment variables
    load_dotenv(env_path)
    api_key = os.getenv("GEMINI_API_KEY")
    print(f"API key loaded: {'Yes' if api_key else 'No'}")
    
    print("\n2. Testing Gemini API configuration...")
    try:
        genai.configure(api_key=api_key)
        print("Gemini API configured successfully")
    except Exception as e:
        print(f"Error configuring Gemini API: {str(e)}")
        return
    
    print("\n3. Testing model initialization...")
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("Model initialized successfully")
    except Exception as e:
        print(f"Error initializing model: {str(e)}")
        return
    
    print("\n4. Testing simple API call...")
    try:
        response = model.generate_content("Say 'Hello, testing!' if you can read this.")
        print(f"Response received: {response.text}")
    except Exception as e:
        print(f"Error making API call: {str(e)}")
        return
    
    print("\n5. Testing structured output...")
    try:
        prompt = """
        Please respond with this exact JSON structure:
        {
            "message": "Test successful",
            "status": "ok"
        }
        """
        response = model.generate_content(prompt)
        raw_text = response.text
        print(f"Raw response: {raw_text}")
        
        # Clean the response text
        cleaned_text = raw_text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]  # Remove ```json
        if cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[3:]  # Remove ```
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]  # Remove trailing ```
        cleaned_text = cleaned_text.strip()
        
        print(f"Cleaned text: {cleaned_text}")
        
        # Try to parse as JSON
        try:
            json_response = json.loads(cleaned_text)
            print(f"Parsed JSON: {json.dumps(json_response, indent=2)}")
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {str(e)}")
            print(f"Characters at error position: {cleaned_text[max(0, e.pos-10):min(len(cleaned_text), e.pos+10)]}")
    except Exception as e:
        print(f"Error testing structured output: {str(e)}")

if __name__ == "__main__":
    test_gemini_connection() 