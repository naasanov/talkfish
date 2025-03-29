class FeedbackDisplay {
    constructor() {
      this.feedbackContainer = document.getElementById('feedback-container');
      if (!this.feedbackContainer) {
        this.feedbackContainer = document.createElement('div');
        this.feedbackContainer.id = 'feedback-container';
        document.body.appendChild(this.feedbackContainer);
      }
    }
  
    showFeedback(feedback) {
      // Clear previous feedback
      this.feedbackContainer.innerHTML = '';
      
      // Create main feedback container
      const feedbackCard = document.createElement('div');
      feedbackCard.className = 'feedback-card';
      
      // Add feedback type styling
      feedbackCard.classList.add(`feedback-${feedback.type || 'neutral'}`);
      
      // Create header
      const header = document.createElement('div');
      header.className = 'feedback-header';
      
      const title = document.createElement('h2');
      title.textContent = 'Interview Feedback';
      header.appendChild(title);
      
      // Create main message
      const message = document.createElement('div');
      message.className = 'feedback-message';
      message.textContent = feedback.message || 'No feedback available';
      
      // Create details section
      const detailsContainer = document.createElement('div');
      detailsContainer.className = 'feedback-details';
      
      // Add components to the main card
      feedbackCard.appendChild(header);
      feedbackCard.appendChild(message);
      
      // Only add details if they exist
      if (feedback.details) {
        // Question type
        if (feedback.details.question_type) {
          const questionType = document.createElement('div');
          questionType.className = 'feedback-section';
          
          const typeTitle = document.createElement('h3');
          typeTitle.textContent = 'Question Type';
          
          const typeValue = document.createElement('p');
          typeValue.textContent = this.capitalizeFirstLetter(feedback.details.question_type);
          
          questionType.appendChild(typeTitle);
          questionType.appendChild(typeValue);
          detailsContainer.appendChild(questionType);
        }
        
        // STAR analysis
        if (feedback.details.star_analysis) {
          const starAnalysis = document.createElement('div');
          starAnalysis.className = 'feedback-section';
          
          const starTitle = document.createElement('h3');
          starTitle.textContent = 'STAR Method Analysis';
          starAnalysis.appendChild(starTitle);
          
          // Create a table for STAR analysis
          const starTable = document.createElement('table');
          starTable.className = 'star-table';
          
          // Create table header
          const tableHeader = document.createElement('tr');
          ['Component', 'Present', 'Strength', 'Feedback'].forEach(headerText => {
            const th = document.createElement('th');
            th.textContent = headerText;
            tableHeader.appendChild(th);
          });
          starTable.appendChild(tableHeader);
          
          // Add STAR components to the table
          const starComponents = ['situation', 'task', 'action', 'result'];
          starComponents.forEach(component => {
            if (feedback.details.star_analysis[component]) {
              const row = document.createElement('tr');
              
              // Component name
              const componentCell = document.createElement('td');
              componentCell.textContent = this.capitalizeFirstLetter(component);
              row.appendChild(componentCell);
              
              // Present (Yes/No)
              const presentCell = document.createElement('td');
              const componentData = feedback.details.star_analysis[component];
              presentCell.textContent = componentData.present ? 'Yes' : 'No';
              row.appendChild(presentCell);
              
              // Strength (1-10)
              const strengthCell = document.createElement('td');
              strengthCell.className = 'strength-cell';
              
              // Create strength bar
              if (componentData.strength) {
                const strengthBar = document.createElement('div');
                strengthBar.className = 'strength-bar';
                
                const strengthValue = document.createElement('div');
                strengthValue.className = 'strength-value';
                strengthValue.style.width = `${componentData.strength * 10}%`;
                
                // Color based on strength
                if (componentData.strength >= 7) {
                  strengthValue.classList.add('strength-high');
                } else if (componentData.strength >= 4) {
                  strengthValue.classList.add('strength-medium');
                } else {
                  strengthValue.classList.add('strength-low');
                }
                
                const strengthText = document.createElement('span');
                strengthText.textContent = componentData.strength;
                
                strengthBar.appendChild(strengthValue);
                strengthCell.appendChild(strengthBar);
                strengthCell.appendChild(strengthText);
              } else {
                strengthCell.textContent = 'N/A';
              }
              row.appendChild(strengthCell);
              
              // Feedback
              const feedbackCell = document.createElement('td');
              feedbackCell.textContent = componentData.feedback || 'No specific feedback';
              row.appendChild(feedbackCell);
              
              starTable.appendChild(row);
            }
          });
          
          starAnalysis.appendChild(starTable);
          detailsContainer.appendChild(starAnalysis);
        }
        
        // Language quality
        if (feedback.details.language_quality) {
          const languageQuality = document.createElement('div');
          languageQuality.className = 'feedback-section';
          
          const languageTitle = document.createElement('h3');
          languageTitle.textContent = 'Language Quality';
          languageQuality.appendChild(languageTitle);
          
          const qualityGrid = document.createElement('div');
          qualityGrid.className = 'quality-grid';
          
          // Clarity metric
          if (feedback.details.language_quality.clarity) {
            const clarityContainer = document.createElement('div');
            clarityContainer.className = 'quality-metric';
            
            const clarityLabel = document.createElement('p');
            clarityLabel.textContent = 'Clarity: ';
            clarityLabel.className = 'metric-label';
            
            const clarityValue = document.createElement('span');
            clarityValue.textContent = `${feedback.details.language_quality.clarity}/10`;
            clarityLabel.appendChild(clarityValue);
            
            clarityContainer.appendChild(clarityLabel);
            qualityGrid.appendChild(clarityContainer);
          }
          
          // Conciseness metric
          if (feedback.details.language_quality.conciseness) {
            const concisenessContainer = document.createElement('div');
            concisenessContainer.className = 'quality-metric';
            
            const concisenessLabel = document.createElement('p');
            concisenessLabel.textContent = 'Conciseness: ';
            concisenessLabel.className = 'metric-label';
            
            const concisenessValue = document.createElement('span');
            concisenessValue.textContent = `${feedback.details.language_quality.conciseness}/10`;
            concisenessLabel.appendChild(concisenessValue);
            
            concisenessContainer.appendChild(concisenessLabel);
            qualityGrid.appendChild(concisenessContainer);
          }
          
          // Filler words
          if (feedback.details.language_quality.filler_words) {
            const fillerContainer = document.createElement('div');
            fillerContainer.className = 'quality-metric filler-words';
            
            const fillerLabel = document.createElement('p');
            fillerLabel.textContent = `Filler Words: ${feedback.details.language_quality.filler_words.frequency}`;
            fillerLabel.className = 'metric-label';
            
            fillerContainer.appendChild(fillerLabel);
            
            // Add examples if available
            if (feedback.details.language_quality.filler_words.examples && 
                feedback.details.language_quality.filler_words.examples.length > 0) {
              const examplesList = document.createElement('ul');
              feedback.details.language_quality.filler_words.examples.forEach(example => {
                const item = document.createElement('li');
                item.textContent = example;
                examplesList.appendChild(item);
              });
              fillerContainer.appendChild(examplesList);
            }
            
            qualityGrid.appendChild(fillerContainer);
          }
          
          languageQuality.appendChild(qualityGrid);
          detailsContainer.appendChild(languageQuality);
        }
        
        // Improvement suggestions
        if (feedback.details.improvement_suggestions && 
            feedback.details.improvement_suggestions.length > 0) {
          const suggestionsSection = document.createElement('div');
          suggestionsSection.className = 'feedback-section';
          
          const suggestionsTitle = document.createElement('h3');
          suggestionsTitle.textContent = 'Suggestions for Improvement';
          suggestionsSection.appendChild(suggestionsTitle);
          
          const suggestionsList = document.createElement('ul');
          suggestionsList.className = 'suggestions-list';
          
          feedback.details.improvement_suggestions.forEach(suggestion => {
            const item = document.createElement('li');
            item.textContent = suggestion;
            suggestionsList.appendChild(item);
          });
          
          suggestionsSection.appendChild(suggestionsList);
          detailsContainer.appendChild(suggestionsSection);
        }
        
        // Overall score
        if (feedback.details.overall_score) {
          const scoreSection = document.createElement('div');
          scoreSection.className = 'feedback-section overall-score';
          
          const scoreTitle = document.createElement('h3');
          scoreTitle.textContent = 'Overall Score';
          
          const scoreDisplay = document.createElement('div');
          scoreDisplay.className = 'score-display';
          
          const score = feedback.details.overall_score;
          scoreDisplay.textContent = score;
          
          // Add color class based on score
          if (score >= 8) {
            scoreDisplay.classList.add('score-high');
          } else if (score >= 5) {
            scoreDisplay.classList.add('score-medium');
          } else {
            scoreDisplay.classList.add('score-low');
          }
          
          scoreSection.appendChild(scoreTitle);
          scoreSection.appendChild(scoreDisplay);
          detailsContainer.appendChild(scoreSection);
        }
        
        // Add all details to the main card
        feedbackCard.appendChild(detailsContainer);
      }
      
      // Add feedback card to container
      this.feedbackContainer.appendChild(feedbackCard);
      
      // Make the feedback visible
      this.feedbackContainer.style.display = 'block';
    }
    
    capitalizeFirstLetter(string) {
      return string.charAt(0).toUpperCase() + string.slice(1);
    }
    
    hideFeedback() {
      if (this.feedbackContainer) {
        this.feedbackContainer.style.display = 'none';
      }
    }
  }
  
  // Export for use in other modules
  export default FeedbackDisplay;