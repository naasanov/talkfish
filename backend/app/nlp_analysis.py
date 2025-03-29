import os
import google.generativeai as genai
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

# Configure the Gemini API with your API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("No Gemini API key found. Please set GEMINI_API_KEY in your environment variables.")

genai.configure(api_key=GEMINI_API_KEY)

# Initialize the model
model = genai.GenerativeModel('gemini-pro')

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
    try:
        # Extract basic statistics
        word_count = len(transcript.split())
        sentence_count = len([s for s in transcript.split('.') if s.strip()])
        
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
        
        # Get response from Gemini
        response = model.generate_content(
            [
                {"role": "system", "parts": [SYSTEM_PROMPT]},
                {"role": "user", "parts": [user_prompt]}
            ],
            generation_config={
                "temperature": 0.2,
                "top_p": 0.95,
                "response_mime_type": "application/json"
            }
        )
        
        # Extract and parse the JSON response
        try:
            # Some versions of the API return the content differently
            if hasattr(response, 'text'):
                feedback_json = json.loads(response.text)
            else:
                feedback_json = json.loads(response.parts[0].text)
            
            # Add transcript metadata
            feedback_json['details']['transcript_stats'] = {
                'word_count': word_count,
                'sentence_count': sentence_count
            }
            
            # Add question type if detected
            if question_type and 'question_type' not in feedback_json['details']:
                feedback_json['details']['question_type'] = question_type
            
            return feedback_json
            
        except json.JSONDecodeError as e:
            # If JSON parsing fails, create a fallback response
            print(f"Failed to parse Gemini response as JSON: {e}")
            print(f"Raw response: {response.text if hasattr(response, 'text') else response.parts[0].text}")
            
            return {
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
            
    except Exception as e:
        print(f"Error during Gemini API call: {str(e)}")
        
        # Fallback analysis when API fails
        return fallback_analysis(transcript, interview_type, question_type)

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