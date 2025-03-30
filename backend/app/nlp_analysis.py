import os
import google.generativeai as genai
from dotenv import load_dotenv
import json

# Load environment variables from .env file
# Get the current file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (backend/)
parent_dir = os.path.dirname(current_dir)
env_path = os.path.join(parent_dir, '.env')

print(f"Looking for .env file at: {env_path}")
print(f"Does .env file exist? {os.path.exists(env_path)}")

# Load .env from the parent directory
load_dotenv(env_path)

# Configure the Gemini API with your API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print(f"Loaded API key: {'Found (not showing for security)' if GEMINI_API_KEY else 'Not found'}")

if not GEMINI_API_KEY:
    raise ValueError("No Gemini API key found. Please set GEMINI_API_KEY in your environment variables.")

try:
    genai.configure(api_key=GEMINI_API_KEY)
    print("Successfully configured Gemini API")
except Exception as e:
    print(f"Error configuring Gemini API: {str(e)}")

# Initialize the model
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("Successfully initialized Gemini model")
except Exception as e:
    print(f"Error initializing Gemini model: {str(e)}")

# System prompt for interview feedback
SYSTEM_PROMPT = """
You are an expert interview coach. Provide extremely concise feedback on interview responses in just a few sentences.

Follow these guidelines:
1. Keep feedback brief and direct - no more than 3-4 sentences total
2. Be specific and actionable
3. Mention STAR principles (Situation, Task, Action, Result) only if relevant
4. Focus on 1-2 key improvements
5. Use a supportive, encouraging tone

Your output should be a JSON object with the following structure:
{
  "message": "1-3 sentence concise feedback",
  "type": "positive | neutral | constructive",
  "details": {
    "suggestion": "One specific improvement suggestion"
  }
}
"""

def analyze_transcript(transcript, interview_type='behavioral', context=None, question_type=None):
    """
    Analyzes the interview transcript using Gemini API and provides very concise feedback.
    """
    print("\nIn analyze_transcript function")
    print(f"Transcript length: {len(transcript)} chars")
    if context:
        print(f"Context length: {len(context)} chars")
    if question_type:
        print(f"Question type: {question_type}")
    
    try:
        # Extract basic statistics
        word_count = len(transcript.split())
        
        print(f"Analyzing transcript with {word_count} words")
        
        # Prepare prompt for Gemini
        user_prompt = f"""
        Interview Type: {interview_type}
        Question Type: {question_type if question_type else "Unknown"}
        
        """
        
        if context:
            user_prompt += f"Full Conversation Context:\n{context}\n\n"
        else:
            user_prompt += f"Interviewee Response: \"{transcript}\"\n\n"
        
        user_prompt += "Provide extremely concise feedback in just a few sentences."
        
        # Create combined prompt with instructions and user prompt
        combined_prompt = f"""
        {SYSTEM_PROMPT}
        
        Now analyze this response:
        
        {user_prompt}
        """
        
        print("Attempting to call Gemini API...")
        
        # Get response from Gemini
        try:
            response = model.generate_content(
                combined_prompt,
                generation_config={
                    "temperature": 0.2,
                    "top_p": 0.95
                }
            )
            print("Successfully received response from Gemini API")
            
        except Exception as api_error:
            print(f"Error calling Gemini API: {str(api_error)}")
            raise
        
        # Extract and parse the JSON response
        try:
            # Some versions of the API return the content differently
            if hasattr(response, 'text'):
                print("Response has 'text' attribute")
                raw_text = response.text
            else:
                print("Response has 'parts' attribute")
                raw_text = response.parts[0].text
            
            print(f"Raw response text: {raw_text}")
            
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
            
            try:
                feedback_json = json.loads(cleaned_text)
                print("Successfully parsed JSON response")
                
                # Simplify to ensure it's just what we want
                simplified_feedback = {
                    'message': feedback_json.get('message', 'Good effort, but could be improved.'),
                    'type': feedback_json.get('type', 'neutral'),
                    'details': {
                        'suggestion': feedback_json.get('details', {}).get('suggestion', 'Add more specific examples.')
                    }
                }
                
                print("Feedback generated:")
                print(simplified_feedback)
                
                return simplified_feedback
            except json.JSONDecodeError as json_error:
                print(f"JSON parse error: {str(json_error)}")
                raise
            
        except json.JSONDecodeError as e:
            # If JSON parsing fails, create a fallback response
            print(f"Failed to parse Gemini response as JSON: {e}")
            print(f"Raw response: {raw_text}")
            
            fallback = {
                'message': "Good effort, but try to include a clear situation, your specific action, and the outcome.",
                'type': 'neutral',
                'details': {
                    'suggestion': "Add more context and specific examples of what you did."
                }
            }
            
            print("Using fallback response due to JSON parsing error")
            print(fallback)
            
            return fallback
                
    except Exception as e:
        print(f"Error during transcript analysis: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        
        # Fallback analysis when API fails
        fallback = fallback_analysis(transcript, interview_type, question_type)
        print("Using fallback response due to general error")
        print(fallback)
        
        return fallback

def fallback_analysis(transcript, interview_type, question_type=None):
    """
    Provides basic feedback when the Gemini API call fails.
    """
    # Simple word count analysis
    word_count = len(transcript.split())
    
    if word_count < 50:
        message = "Your response is too brief. Add more specific details about what you did and the results."
        feedback_type = "constructive"
        suggestion = "Expand your answer with a specific example."
    elif word_count > 300:
        message = "Good detail, but try to be more concise while keeping your key points."
        feedback_type = "neutral"
        suggestion = "Focus on your most impactful actions and results."
    else:
        message = "Good length. Add more specific details about your actions and the measurable results."
        feedback_type = "positive"
        suggestion = "Quantify your results to show your impact."
    
    return {
        'message': message,
        'type': feedback_type,
        'details': {
            'suggestion': suggestion
        }
    }