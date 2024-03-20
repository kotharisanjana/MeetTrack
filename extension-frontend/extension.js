let fullShutdown = false;
let recorder;
let data = [];
let mediaStreamFlag = true;
let recorderStateFlag = true;
let media = null;

document.addEventListener("DOMContentLoaded", function () {
  var meetingDetailsForm = document.getElementById("meetingDetailsForm");
  var sessionIDForm = document.querySelector('.sessionIDForm');
  var startRecordingButton = document.getElementById("startRecordingButton");
  var stopRecordingButton = document.getElementById("stopRecordingButton");
  var userInputForm = document.getElementById("userInputForm");


  meetingDetailsForm.addEventListener("submit", function (event) {
    event.preventDefault();
    var name = document.getElementById('meetingName').value;
    var meetingType = document.querySelector('input[name="meetingType"]:checked').value;

    fetch("http://localhost:5000/submit-details", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ name: name, meetingType: meetingType})
    })
    .then(response => response.json())
    .then(data => {
      if (data.status === "OK") {
        alert("Session ID: " + data.session_id);
      } 
    })
    .catch(error => console.error("Error:", error));

    meetingDetailsForm.classList.add("disabled");
  });


  sessionIDForm.addEventListener("submit", function (event) {
    event.preventDefault();
    var session_id = document.getElementById('sessionID').value;

    fetch("http://localhost:5000/access-session", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ session_id: session_id})
    })
    .then(response => {
      if (response.status === 200) {
          alert(response.message);
          localStorage.setItem("session_id", session_id);

          sessionIDForm.classList.add("disabled");
          startRecordingButton.classList.remove("disabled");
          stopRecordingButton.classList.remove("disabled");
          userInputForm.classList.remove("disabled");
      }
      else if (response.status === 400) {
          alert(response.message);
      }
    })
    .then(data => {
    })
    .catch(error => console.error("Error:", error));
  });


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


  userInputForm.addEventListener("submit", function (event) {
    event.preventDefault();
    var userInput = document.getElementById('userInput').value;
    session_id = localStorage.getItem("session_id");

    fetch("http://localhost:5000/answer-query", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ 
        userInput: userInput,
        session_id: session_id
      })
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
    if (recorder && recorder.state === "recording") {
      alert("Recording already in progress.");
      return;
    }

    session_id = localStorage.getItem("session_id");

    // Check if the meeting is already being recorded and prevent other users from starting a new recording
    const recordingStatusResponse = await fetch("http://localhost:5000/recording-status", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ session_id: session_id })
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
          formData.append("session_id", session_id);

          await fetch("http://localhost:5000/process-recording", {
              method: "POST",
              body: formData
          })
          .then(response => {
            if (response.status === 200) {
                console.log("Meeting recording processed successfully.");
            } else
            if (response.status === 400) {
                alert("Error in recording.");
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
