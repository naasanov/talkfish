import FeedbackDisplay from './FeedbackDisplay.js';

// Initialize the feedback display
const feedbackDisplay = new FeedbackDisplay();

// Set up button event listeners
document.getElementById("start").addEventListener("click", () => {
  document.getElementById("start").disabled = true;
  document.getElementById("stop").disabled = false;
  
  // Hide any previous feedback when starting new interview
  feedbackDisplay.hideFeedback();
  
  // You would add your code to start recording/tracking interview here
  console.log("Mock interview started");
});

document.getElementById("stop").addEventListener("click", () => {
  document.getElementById("start").disabled = false;
  document.getElementById("stop").disabled = true;
  
  // Simulate generating feedback (you would replace this with actual feedback generation)
  const sampleFeedback = {
    type: 'positive',
    message: 'Good job on your behavioral interview question!',
    details: {
      question_type: 'behavioral',
      star_analysis: {
        situation: {
          present: true,
          strength: 8,
          feedback: 'Clear context provided'
        },
        task: {
          present: true,
          strength: 7,
          feedback: 'Role well defined'
        },
        action: {
          present: true,
          strength: 9,
          feedback: 'Detailed steps taken'
        },
        result: {
          present: true,
          strength: 6,
          feedback: 'Outcome mentioned but could include more quantifiable results'
        }
      },
      language_quality: {
        clarity: 8,
        conciseness: 7,
        filler_words: {
          frequency: 'Low',
          examples: ['um', 'like']
        }
      },
      improvement_suggestions: [
        'Quantify your results more specifically',
        'Reduce filler words like "um" and "like"',
        'Add more details about the challenges faced'
      ],
      overall_score: 7
    }
  };
  
  // Display the feedback
  feedbackDisplay.showFeedback(sampleFeedback);
  
  console.log("Mock interview stopped");
});