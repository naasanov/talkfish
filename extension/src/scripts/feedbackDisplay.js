function displayFeedback(feedbackData) {
    // Create or get the feedback container
    let feedbackElement = document.getElementById("interview-feedback-container");
    if (!feedbackElement) {
      feedbackElement = document.createElement("div");
      feedbackElement.id = "interview-feedback-container";
      feedbackElement.style.position = "fixed";
      feedbackElement.style.top = "20px";
      feedbackElement.style.right = "20px";
      feedbackElement.style.width = "350px";
      feedbackElement.style.maxHeight = "80vh";
      feedbackElement.style.overflowY = "auto";
      feedbackElement.style.backgroundColor = "#fff";
      feedbackElement.style.boxShadow = "0 0 10px rgba(0,0,0,0.2)";
      feedbackElement.style.borderRadius = "8px";
      feedbackElement.style.padding = "15px";
      feedbackElement.style.zIndex = "10000";
      feedbackElement.style.fontFamily = "Arial, sans-serif";
      document.body.appendChild(feedbackElement);
    }
  
    // Determine the feedback header color based on type
    let headerColor = "#4287f5"; // Default blue
    if (feedbackData.type === "positive") {
      headerColor = "#42b883"; // Green
    } else if (feedbackData.type === "constructive") {
      headerColor = "#f59042"; // Orange
    } else if (feedbackData.type === "warning" || feedbackData.type === "error") {
      headerColor = "#f54242"; // Red
    }
  
    // Build the feedback HTML
    let feedbackHtml = `
      <div style="border-bottom: 2px solid ${headerColor}; margin-bottom: 10px;">
        <h3 style="color: ${headerColor}; margin: 0 0 10px 0;">Interview Feedback</h3>
      </div>
      <p style="font-weight: bold;">${feedbackData.message}</p>
    `;
  
    // Add detailed feedback if available
    if (feedbackData.details) {
      const details = feedbackData.details;
      
      // Add overall score if available
      if (details.overall_score) {
        feedbackHtml += `
          <div style="margin: 10px 0; text-align: center;">
            <span style="font-size: 24px; font-weight: bold; color: ${headerColor};">
              ${details.overall_score}/10
            </span>
            <div style="background: #eee; height: 10px; border-radius: 5px; margin-top: 5px;">
              <div style="background: ${headerColor}; width: ${details.overall_score * 10}%; height: 10px; border-radius: 5px;"></div>
            </div>
          </div>
        `;
      }
  
      // Add STAR method analysis if available
      if (details.star_analysis) {
        feedbackHtml += `<div style="margin-top: 15px;"><h4 style="margin: 5px 0;">STAR Method Analysis</h4>`;
        
        const star = details.star_analysis;
        const components = ["situation", "task", "action", "result"];
        
        components.forEach(component => {
          if (star[component]) {
            const present = star[component].present;
            const strength = star[component].strength || 0;
            
            feedbackHtml += `
              <div style="margin: 8px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <span style="text-transform: capitalize; font-weight: bold;">${component}:</span>
                  <span>${present ? "✓" : "✗"}</span>
                </div>
                ${strength > 0 ? `
                  <div style="background: #eee; height: 6px; border-radius: 3px; margin-top: 5px;">
                    <div style="background: ${headerColor}; width: ${strength * 10}%; height: 6px; border-radius: 3px;"></div>
                  </div>
                ` : ""}
                ${star[component].feedback ? `<p style="margin: 5px 0; font-size: 12px;">${star[component].feedback}</p>` : ""}
              </div>
            `;
          }
        });
        
        feedbackHtml += `</div>`;
      }
  
      // Add language quality feedback if available
      if (details.language_quality) {
        const language = details.language_quality;
        
        feedbackHtml += `<div style="margin-top: 15px;"><h4 style="margin: 5px 0;">Language Quality</h4>`;
        
        if (language.clarity) {
          feedbackHtml += `
            <div style="margin: 5px 0;">
              <div style="display: flex; justify-content: space-between;">
                <span>Clarity:</span>
                <span>${language.clarity}/10</span>
              </div>
              <div style="background: #eee; height: 6px; border-radius: 3px; margin-top: 5px;">
                <div style="background: ${headerColor}; width: ${language.clarity * 10}%; height: 6px; border-radius: 3px;"></div>
              </div>
            </div>
          `;
        }
  
        if (language.conciseness) {
          feedbackHtml += `
            <div style="margin: 5px 0;">
              <div style="display: flex; justify-content: space-between;">
                <span>Conciseness:</span>
                <span>${language.conciseness}/10</span>
              </div>
              <div style="background: #eee; height: 6px; border-radius: 3px; margin-top: 5px;">
                <div style="background: ${headerColor}; width: ${language.conciseness * 10}%; height: 6px; border-radius: 3px;"></div>
              </div>
            </div>
          `;
        }
  
        if (language.filler_words && language.filler_words.frequency) {
          feedbackHtml += `
            <div style="margin: 5px 0;">
              <div><span>Filler Words: </span><span>${language.filler_words.frequency}</span></div>
              ${language.filler_words.examples && language.filler_words.examples.length > 0 ? 
                `<div style="font-size: 12px; color: #666; margin-top: 3px;">Examples: ${language.filler_words.examples.join(", ")}</div>` : ""}
            </div>
          `;
        }
  
        feedbackHtml += `</div>`;
      }
  
      // Add improvement suggestions if available
      if (details.improvement_suggestions && details.improvement_suggestions.length > 0) {
        feedbackHtml += `
          <div style="margin-top: 15px;">
            <h4 style="margin: 5px 0;">Suggestions for Improvement</h4>
            <ul style="margin: 5px 0; padding-left: 20px;">
              ${details.improvement_suggestions.map(suggestion => `<li>${suggestion}</li>`).join("")}
            </ul>
          </div>
        `;
      }
  
      // Add transcript stats if available
      if (details.transcript_stats) {
        feedbackHtml += `
          <div style="margin-top: 15px; font-size: 12px; color: #666;">
            <div>Word count: ${details.transcript_stats.word_count || "N/A"}</div>
            ${details.transcript_stats.sentence_count ? `<div>Sentence count: ${details.transcript_stats.sentence_count}</div>` : ""}
          </div>
        `;
      }
    }
  
    // Add close button
    feedbackHtml += `
      <div style="margin-top: 15px; text-align: right;">
        <button id="close-feedback" style="padding: 5px 10px; background: #eee; border: none; border-radius: 5px; cursor: pointer;">Close</button>
      </div>
    `;
  
    // Set the HTML content
    feedbackElement.innerHTML = feedbackHtml;
  
    // Add event listener to close button
    document.getElementById("close-feedback").addEventListener("click", () => {
      feedbackElement.remove();
    });
  }