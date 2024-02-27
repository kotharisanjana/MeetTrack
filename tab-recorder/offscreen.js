let fullShutdown = false;
let recorder;
let data = [];
let mediaStreamFlag = true;
let recorderStateFlag = true;
let media = null;

chrome.runtime.onMessage.addListener(async (message) => {
  switch (message.type) {
    case 'start-recording':
      console.log('Received start-recording message');
      startRecording(message.data);
      break;
    case 'stop-recording':
      console.log('Received stop-recording message');
      fullShutdown = true;
      stopRecording();
      break;
    default:
      throw new Error('Unrecognized message:', message.type);
  }
});

async function startRecording(streamId) {
  // Check if a recording is already in progress
  if (recorder && recorder.state === 'recording') {
    return;
  }

  // Create media stream for the first time
  if (mediaStreamFlag){
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
  if (recorderStateFlag){
    recorder.start();
    // Stop the recorder after 30 seconds
    stopTimer = setTimeout(() => {
      stopRecording();
    }, 30000);
  } 
}

function stopRecording() {
  if (recorder && recorder.state === 'recording') {
    console.log(recorder.state);
    console.log('Stopping the recorder');
    recorder.stop();

    console.log('fullShutDown = ', fullShutdown);

    if (fullShutdown)
    {
      recorder.stream.getTracks().forEach((t) => t.stop());
      recorderStateFlag = false;
    } 
  }
}
