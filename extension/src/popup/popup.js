let isRecording = false;

function startFunc() {
  console.log("startFunc");
}

function stopFunc() {
  console.log("stopFunc");
}

document.getElementById("toggle").addEventListener("click", () => {
  isRecording = !isRecording;
  const button = document.getElementById("toggle");
  if (isRecording) {
    button.textContent = "Stop Mock Interview";
    startFunc();
  } else {
    button.textContent = "Start Mock Interview";
    stopFunc();
  }
});