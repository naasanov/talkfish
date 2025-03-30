console.log("hello world")

let isRecording = false;
let mediaRecorder = null;
console.log("running overlay")
function startFunc() {
  console.log("startFunc");
}

function stopFunc() {
  console.log("stopFunc");
}

document.getElementById("toggle").addEventListener("click", () => {
  console.log("click")
  isRecording = !isRecording;
  const button = document.getElementById("toggle");
  if (isRecording) {
    button.classList.add("recording");
    button.textContent = "⏸";
    startFunc();
  } else {
    button.classList.remove("recording");
    button.textContent = "▶";
    stopFunc();
  }
});