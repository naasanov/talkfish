from app.nlp_analysis import analyze_transcript
import json

def test_analysis():
    """Test the analysis functions directly with sample text"""
    
    print("\nTesting analysis function with sample text")
    
    # Sample transcript
    sample_transcript = """
    In my previous role, I had to deal with a difficult customer who was unhappy with our service. 
    I listened to their concerns, acknowledged their frustration, and worked with our team to find a solution.
    We ended up not only resolving their immediate issue but also implementing a new process to prevent similar problems.
    The customer became one of our strongest advocates.
    """
    
    print(f"Sample transcript length: {len(sample_transcript)} chars")
    
    # Call analyze_transcript
    print("Calling analyze_transcript...")
    feedback = analyze_transcript(sample_transcript, interview_type='behavioral', question_type='conflict')
    
    # Display results
    print("\nAnalysis results:")
    if feedback:
        print(f"Result type: {type(feedback)}")
        print(f"Message: {feedback.get('message', 'No message')}")
        print(f"Type: {feedback.get('type', 'No type')}")
        
        if 'details' in feedback:
            print("\nDetails:")
            for key, value in feedback['details'].items():
                if isinstance(value, dict):
                    print(f"  {key}: {json.dumps(value, indent=2)[:100]}...")
                else:
                    print(f"  {key}: {value}")
        
        print("\nComplete feedback:")
        print(json.dumps(feedback, indent=2))
    else:
        print("No feedback returned!")

if __name__ == "__main__":
    test_analysis() 