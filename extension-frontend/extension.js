let fullShutdown = false;
let recorder;
let data = [];
let mediaStreamFlag = true;
let recorderStateFlag = true;
let media = null;
const processingQueue = [];
let isProcessing = false;

document.addEventListener("DOMContentLoaded", function () {
  var meetingDetailsForm = document.querySelector(".meetingDetailsForm");
  var sessionIDForm = document.querySelector('.sessionIDForm');
  var emailIDForm = document.querySelector(".emailIDForm");
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
          localStorage.setItem("session_id", session_id);
          localStorage.setItem("recording_status", "false");

          sessionIDForm.classList.add("disabled");
          startRecordingButton.classList.remove("disabled");
          stopRecordingButton.classList.remove("disabled");
          userInputForm.classList.remove("disabled");

          return response.json();
      }
    })
    .then(data => {
      alert(data.message);
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

  emailIDForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    var email = document.getElementById('emailID').value;
    session_id = localStorage.getItem("session_id")

    await fetch("http://localhost:5000/submit-recipient-email", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ session_id: session_id, email: email })
    })
    .then(response => response.json())
    .then(data => {
    })
    .catch(error => console.error("Error:", error));
  });


  userInputForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    var userInput = document.getElementById('userInput').value;
    session_id = localStorage.getItem("session_id");

    await fetch("http://localhost:5000/answer-query", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ 
        userInput: userInput,
        session_id: session_id
      })
    })
    .then(response => {
      if (response.status !== 200) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      textDisplay.textContent = data.data;
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
      console.log(message.type);
      fullShutdown = true;
      stopRecording();
      break;
  }
  return true;
});


async function startRecording(streamId) {
  try {
    session_id = localStorage.getItem("session_id");
    recording_status = localStorage.getItem("recording_status");

    if (recording_status === "false") {
      recordingStatusResponse = await checkRecordingStaus(session_id);
    }

    if (recording_status === "true" || recordingStatusResponse.status === "OK") {
      if (recording_status === "false"){
        alert(recordingStatusResponse.message);
      }

      localStorage.setItem("recording_status", "true");

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

        // processRecording(blob, session_id);
        addToQueue(blob, session_id);

        URL.revokeObjectURL(recordingUrl);

        // Clear state ready for next recording
        data = [];

        // Start the next recording after a 1 millisecond delay
        setTimeout(() => startRecording(streamId), 1);
      };

      // Start the recorder
      if (recorderStateFlag) {
        recorder.start();
        stopTimer = setTimeout(async () => {
          await stopRecording();
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


async function checkRecordingStaus(session_id){
  const recordingStatusResponse = await fetch("http://localhost:5000/check-recording-status", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ session_id: session_id })
  });
  return recordingStatusResponse.json();
}


function addToQueue(blob, session_id) {
  processingQueue.push({ blob, session_id });
  processQueue();
}


// Function to process tasks from the queue
async function processQueue() {
  console.log("Processing queue", processingQueue.length);
  if (!isProcessing && processingQueue.length > 0) {
      isProcessing = true;
      const task = processingQueue.shift(); // Get the next task from the queue
      try {
          processRecording(task.blob, task.session_id)
              .then(() => {
                  isProcessing = false;
                  processQueue();
              })
              .catch((error) => {
                  console.error("Error processing task:", error);
                  isProcessing = false;
                  processQueue();
              });
      } catch (error) {
          console.error("Error processing task:", error);
          isProcessing = false;
          processQueue();
      }
  }
}


async function processRecording(blob, session_id){
  try {
    const formData = new FormData();
    formData.append("recording", blob);
    formData.append("session_id", session_id);

    const resp = await fetch("http://localhost:5000/process-recording", {
        method: "POST",
        body: formData
    })

    if (resp.status === 200) {
      console.log("Meeting recording processed successfully.");
    } else if (resp.status === 400) {
      alert("Error in recording.");
    } else {
      throw new Error("Unexpected response status: " + response.status);
    }
  } catch (error) {
    console.error("Error in recording:", error);
  }
}


async function stopRecording() {
  if (recorder && recorder.state === "recording") {
    recorder.stop();

    if (fullShutdown)
    {
      console.log("stopping")
      recorder.stream.getTracks().forEach((t) => t.stop());
      recorderStateFlag = false;
      alert("Recording stopped");
    } 
  }
}
