async function getMixedOutput() {
  try {
    const micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const tabStream = await navigator.mediaDevices.getDisplayMedia({ audio: true, video: false });

    const audioContext = new (window.AudioContext || window.webkitAudioContext)();

    // Create audio nodes for each stream
    const micSource = audioContext.createMediaStreamSource(micStream);
    const tabSource = audioContext.createMediaStreamSource(tabStream);

    // Create a merger to combine both audio streams
    const merger = audioContext.createChannelMerger(2);

    // Connect the audio sources to the merger
    micSource.connect(merger, 0, 0); // Mic -> first channel
    tabSource.connect(merger, 0, 1); // Tab -> second channel

    // Create a MediaStreamDestination to capture the merged output
    const mixedOutput = audioContext.createMediaStreamDestination();
    merger.connect(mixedOutput); // Connect merged audio to destination

    return mixedOutput;
  } catch (err) {
    console.error('Error:', err);
    return null;
  }
}

export default getMixedOutput
