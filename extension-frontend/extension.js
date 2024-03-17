let fullShutdown = false;
let recorder;
let data = [];
let mediaStreamFlag = true;
let recorderStateFlag = true;
let media = null;

document.addEventListener("DOMContentLoaded", function () {
  var meetingDetailsForm = document.getElementById("meetingDetailsForm");
  var meetingIDForm = document.querySelector('.meetingIDForm');
  var startRecordingButton = document.getElementById("startRecordingButton");
  var stopRecordingButton = document.getElementById("stopRecordingButton");
  var userInputForm = document.getElementById("userInputForm");
   
  startRecordingButton.addEventListener("click", function () {
    chrome.runtime.sendMessage({
      type: "start-recording",
    });
  });

  stopRecordingButton.addEventListener("click", function () {
    chrome.runtime.sendMessage({
      type: "stop-recording",
    });
  });

  meetingDetailsForm.addEventListener("submit", function (event) {
    event.preventDefault();
    var name = document.getElementById('meetingName').value;
    var meetingType = document.querySelector('input[name="meetingType"]:checked').value;

    fetch("http://localhost:5000/submit-meeting-details", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ name: name, meetingType: meetingType})
    })
    .then(response => response.json())
    .then(data => {
      if (data.meeting_id) {
        var confirmation = confirm("Meeting ID: " + data.meeting_id + "\nClick OK to start the meeting session.");
      } else {
        var confirmation = confirm(data.error);
      } 

      if (confirmation) {
        startMeetingSession()
      }
    })
    .catch(error => console.error("Error:", error));

    meetingDetailsForm.classList.add("disabled");
    startRecordingButton.classList.remove("disabled");
    stopRecordingButton.classList.remove("disabled");
    userInputForm.classList.remove("disabled");
  });

  meetingIDForm.addEventListener("submit", function (event) {
    event.preventDefault();
    var meeting_id = document.getElementById('meetingID').value;

    fetch("http://localhost:5000/join-meeting-session", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ meeting_id: meeting_id})
    })
    .then(response => response.json())
    .then(data => {
    })
    .catch(error => console.error("Error:", error));

    meetingDetailsForm.classList.add("disabled");
    startRecordingButton.classList.remove("disabled");
    stopRecordingButton.classList.remove("disabled");
    userInputForm.classList.remove("disabled");
    meetingIDForm.classList.add("disabled");
  });


  userInputForm.addEventListener("submit", function (event) {
    event.preventDefault();
    var userInput = document.getElementById('userInput').value;

    fetch("http://localhost:5000/answer-user-query", {
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

function startMeetingSession() {
  // Make a request to the Flask server to start the meeting session
  fetch("http://localhost:5000/start-meeting-session", {
      method: "POST",
      headers: {
          "Content-Type": "application/json"
      },
      body: JSON.stringify({ /* Include any necessary data */ })
  })
  .then(response => {
  })
  .catch(error => console.error("Error:", error));
}


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
    // Check if a recording is already in progress - for the user who starts the recording but we are disbaling the button so may be redundant
    if (recorder && recorder.state === "recording") {
      alert("Recording is already in progress.");
      return;
    }

    // Check if the meeting is already being recorded and prevent uother users from satrting a new recording
    const recordingStatusResponse = await fetch("http://localhost:5000/meeting-recording-status", {
      method: "POST"
    });

    if (recordingStatusResponse.status === 200) {
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

      recorder.onstop = async () => {
        const blob = new Blob(data, { type: "video/webm" });
        const recordingUrl = URL.createObjectURL(blob);

        try {
          const formData = new FormData();
          formData.append("recording", blob);

          await fetch("http://localhost:5000/process-meeting-recording", {
              method: "POST",
              body: formData
          })
          .then(response => {
            if (response.status === 200) {
                console.log("Meeting recording processed successfully.");
            } else
            if (response.status === 400) {
                alert("Error in processing meeting recording.");
            } else {
                throw new Error("Unexpected response status: " + response.status);
            }
          });
        } catch (error) {
            console.error("Error in recording:", error);
        }

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
    } else if (recordingStatusResponse.status === 400) {
      alert("Recording is already in progress.");
    } else {
      throw new Error("Unexpected response status: " + recordingStatusResponse.status);
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
      alert("Recording stopped");
    } 
  }
}
