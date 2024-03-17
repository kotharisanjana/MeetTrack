let fullShutdown = false;
let recorder;
let data = [];
let mediaStreamFlag = true;
let recorderStateFlag = true;
let media = null;

document.addEventListener("DOMContentLoaded", function () {
  var meetingDetailsForm = document.getElementById("meetingDetailsForm");
  var toggleButton = document.getElementById("toggleButton");
  var userInputForm = document.getElementById("userInputForm");
  
  toggleButton.addEventListener("click", function () {
    chrome.runtime.sendMessage({
      type: "toggle-recording",
    });
  });

  meetingDetailsForm.addEventListener("submit", function (event) {
    event.preventDefault();
    var name = document.getElementById('meetingName').value;
    var meetingType = document.querySelector('input[name="meetingType"]:checked').value;

    fetch("http://localhost:5000/meeting_details", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ name: name, meetingType: meetingType})
    })
    .catch(error => console.error("Error:", error));

    meetingDetailsForm.classList.add("disabled");
    toggleButton.classList.remove("disabled");
    userInputForm.classList.remove("disabled");
  });

  userInputForm.addEventListener("submit", function (event) {
    event.preventDefault();
    var userInput = document.getElementById('userInput').value;

    fetch("http://localhost:5000/user_query", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ userInput: userInput })
    })
    .then(response => response.json())
    .then(data => {
      textDisplay.textContent = data.response;
  })
    .catch(error => console.error("Error:", error));
  });
});

chrome.runtime.onMessage.addListener(async (message) => {
  switch (message.type) {
    case "start-recording":
      startRecording(message.data);
      break;
    case "stop-recording":
      fullShutdown = true;
      stopRecording();
      break;
  }
  return true;
});

async function startRecording(streamId) {
  try {
    // Check if a recording is already in progress
    if (recorder && recorder.state === "recording") {
      return;
    }

    // Create media stream for the first time
    try{
      if (mediaStreamFlag) {
        media = await navigator.mediaDevices.getUserMedia({
          audio: {
            mandatory: {
              chromeMediaSource: "tab",
              chromeMediaSourceId: streamId
            }
          },
          video: {
            mandatory: {
              chromeMediaSource: "tab",
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
    console.error("Error starting tab capture:", error);
  };

    recorder = new MediaRecorder(media, { mimeType: "video/webm" });

    recorder.ondataavailable = (event) => {
      data.push(event.data);
    }

    recorder.onstop = () => {
      const blob = new Blob(data, { type: "video/webm" });
      const recordingUrl = URL.createObjectURL(blob);

      // CHANGE TO UPLOAD TO S3 BUCKET AND MAINTAIN SEQUENTIAL ORDERING OF FILE NAMES
      const a = document.createElement("a");
      a.style.display = "none";
      document.body.appendChild(a);
      a.href = recordingUrl;
      a.download = "recording.webm";
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
    console.error("Error starting tab capture:", error);
  }
}

function stopRecording() {
  if (recorder && recorder.state === "recording") {
    recorder.stop();

    if (fullShutdown)
    {
      recorder.stream.getTracks().forEach((t) => t.stop());
      recorderStateFlag = false;
    } 
  }
}
