let fullShutdown = false;
let recorder;
let data = [];
let mediaStreamFlag = true;
let recorderStateFlag = true;
let media = null;

document.addEventListener('DOMContentLoaded', function () {
  var toggleButton = document.getElementById('toggleButton');
  var userInputForm = document.getElementById('userInputForm');

  toggleButton.addEventListener('click', function () {
    chrome.runtime.sendMessage({
      type: 'toggle-recording',
    });
  });

  userInputForm.addEventListener('submit', function (event) {
    event.preventDefault();
    var userInput = document.getElementById('userInput').value;
    textDisplay.textContent = userInput;
  });
});

chrome.runtime.onMessage.addListener(async (message) => {
  switch (message.type) {
    case 'start-recording':
      startRecording(message.data);
      break;
    case 'stop-recording':
      fullShutdown = true;
      stopRecording();
      break;
  }
  return true;
});

async function startRecording(streamId) {
  try {
    // Check if a recording is already in progress
    if (recorder && recorder.state === 'recording') {
      return;
    }

    // Create media stream for the first time
    try{
      if (mediaStreamFlag) {
        media = await navigator.mediaDevices.getUserMedia({
          audio: {
            mandatory: {
              chromeMediaSource: 'tab',
              chromeMediaSourceId: streamId
            }
          },
          video: {
            mandatory: {
              chromeMediaSource: 'tab',
              chromeMediaSourceId: streamId
            }
          }
        });

        const output = new AudioContext();
        const source = output.createMediaStreamSource(media);
        source.connect(output.destination);

        mediaStreamFlag = false;
    }
  } catch (error) {
    console.error('Error starting tab capture:', error);
  };

    recorder = new MediaRecorder(media, { mimeType: 'video/webm' });

    recorder.ondataavailable = (event) => {
      data.push(event.data);
    }

    recorder.onstop = () => {
      const blob = new Blob(data, { type: 'video/webm' });
      const recordingUrl = URL.createObjectURL(blob);

      const a = document.createElement('a');
      a.style.display = 'none';
      document.body.appendChild(a);
      a.href = recordingUrl;
      a.download = 'recording.webm';
      a.click();

      URL.revokeObjectURL(recordingUrl);

      // Clear state ready for next recording
      data = [];

      // Start the next recording after a 1 millisecond delay
      setTimeout(() => startRecording(streamId), 1);
    };

    // Start the recorder
    if (recorderStateFlag) {
      recorder.start();
      // Stop the recorder after 30 seconds
      stopTimer = setTimeout(() => {
        stopRecording();
      }, 30000);
    }
  } catch (error) {
    console.error('Error starting tab capture:', error);
    // Retry after a delay if the error is related to tab capture
    // if (error.name === 'AbortError') {
    //   setTimeout(() => startRecording(streamId), 1000);
    // }
  }
}

function stopRecording() {
  if (recorder && recorder.state === 'recording') {
    recorder.stop();

    if (fullShutdown)
    {
      recorder.stream.getTracks().forEach((t) => t.stop());
      recorderStateFlag = false;
    } 
  }
}
