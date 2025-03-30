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

def analyze_transcript(transcript, interview_type='behavioral', context=None, question_type=None):
    """
    Analyzes the interview transcript using Gemini API and provides detailed feedback.
    
    Parameters:
    - transcript: The interviewee's response text
    - interview_type: The type of interview (behavioral, technical, etc.)
    - context: Optional full conversation context including interviewer's question
    - question_type: Optional detected question category
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
        sentence_count = len([s for s in transcript.split('.') if s.strip()])
        
        print(f"Analyzing transcript with {word_count} words, {sentence_count} sentences")
        
        # Prepare prompt for Gemini
        user_prompt = f"""
        Interview Type: {interview_type}
        Question Type: {question_type if question_type else "Unknown"}
        
        """
        
        if context:
            user_prompt += f"Full Conversation Context:\n{context}\n\n"
        else:
            user_prompt += f"Interviewee Response: \"{transcript}\"\n\n"
        
        user_prompt += "Please analyze this interview response and provide detailed feedback following the guidelines."
        
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
                
                # Add transcript metadata
                feedback_json['details']['transcript_stats'] = {
                    'word_count': word_count,
                    'sentence_count': sentence_count
                }
                
                # Add question type if detected
                if question_type and 'question_type' not in feedback_json['details']:
                    feedback_json['details']['question_type'] = question_type
                
                print("Feedback generated:")
                print(feedback_json)
                
                return feedback_json
            except json.JSONDecodeError as json_error:
                print(f"JSON parse error: {str(json_error)}")
                raise
            
        except json.JSONDecodeError as e:
            # If JSON parsing fails, create a fallback response
            print(f"Failed to parse Gemini response as JSON: {e}")
            print(f"Raw response: {raw_text}")
            
            fallback = {
                'message': "I analyzed your response but encountered an error formatting the detailed feedback.",
                'type': 'neutral',
                'details': {
                    'transcript_stats': {
                        'word_count': word_count,
                        'sentence_count': sentence_count
                    },
                    'question_type': question_type if question_type else "Unknown",
                    'error': 'Failed to parse AI response'
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
        message = "Your response was quite brief. Consider providing more details using the STAR method."
        feedback_type = "constructive"
    elif word_count > 300:
        message = "Your response was comprehensive but could be more concise while maintaining the STAR structure."
        feedback_type = "neutral"
    else:
        message = "Your response had a good length. Check that you covered all elements of the STAR method."
        feedback_type = "positive"
    
    return {
        'message': message,
        'type': feedback_type,
        'details': {
            'transcript_stats': {
                'word_count': word_count
            },
            'question_type': question_type if question_type else "Unknown",
            'note': 'Limited analysis provided due to API connection issue.'
        }
    }