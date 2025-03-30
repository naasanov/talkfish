let isRecording = false

// Global function to show the modal
window.showModal = async function () {
  const modal = document.createElement('div');

  let html = null
  try {
    const response = await fetch(chrome.runtime.getURL('src/resources/overlay.html'));
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    html = await response.text();
  } catch (error) {
    console.error('Failed to load overlay:', error);
    modal.textContent = 'Failed to load overlay.';
    document.body.appendChild(modal);
    modal.style.display = 'block';
  }

  if (!html) {
    throw new Error("Modal html retrieval failed")
  }

  // Modal content
  modal.innerHTML = html

  const logoImg = modal.querySelector('.logo');
  if (logoImg) {
    logoImg.src = chrome.runtime.getURL('assets/logo.png');
  }

  // Append modal to the body
  document.body.appendChild(modal);

  // Show the modal
  modal.style.display = 'block';


  // function stopStreamOnServer() {
  //   fetch('http://localhost:5000/stop-stream', {
  //     method: 'POST',
  //   })
  //     .then(response => response.text())
  //     .then(data => {
  //       console.log(data);  // "Stream will stop"
  //     })
  //     .catch(error => {
  //       console.error("Error stopping the stream:", error);
  //     });
  // }

  let eventSource = null

  // Example of running a script from the modal
  document.getElementById('toggle').addEventListener('click', function () {
    console.log('toggle clicked')
    isRecording = !isRecording;
    const button = document.getElementById('toggle');
    if (isRecording) {
      // const eventSource = new EventSource('http://localhost:5000/start-stream');
      // eventSource.onmessage = (event) => {
        // const data = JSON.parse(event.data); //In JSON, right?
        // const cardType = data.type; //question, answer, tip
        // const cardContent = data.content; // card content

        function createCard(type, content) {
          console.log('createCard called')
          const cardContainer = document.querySelector('.card-container');
          if (!cardContainer) {
            console.error('Card container not found');
            return;
          }

          const card = document.createElement('div');
          card.className = 'card ${type}';

          const title = document.createElement('h3');
          title.textContent = type.charAt(0).toUpperCase() + type.slice(1); // Capitalize type
          card.appendChild(title);

          const paragraph = document.createElement('p');
          paragraph.textContent = content;
          card.appendChild(paragraph);

          cardContainer.appendChild(card);
        }

        // Call the function to create the card
        createCard('question', 'how many fingers do I have?');
        createCard('answer', '10');
        createCard('tip', 'Im storking it.');
        console.log('cards created')
      //}
      button.classList.add('recording');
      button.textContent = '⏸';
    } else {
      // if (eventSource) {
      //   eventSource.close()
      // }
      // stopStreamOnServer()
      button.classList.remove('recording');
      button.textContent = '▶';
    }
  });
};
