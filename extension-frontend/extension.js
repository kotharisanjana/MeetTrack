let fullShutdown = false;
let recorder;
let data = [];
let mediaStreamFlag = true;
let recorderStateFlag = true;
let media = null;
const processingQueue = [];
let isProcessing = false;

document.addEventListener("DOMContentLoaded", function () {
  // get all DOM elements
  var meetingDetailsForm = document.querySelector(".meetingDetailsForm");
  var sessionIDForm = document.querySelector('.sessionIDForm');
  var emailIDForm = document.querySelector(".emailIDForm");
  var startRecordingButton = document.getElementById("startRecordingButton");
  var stopRecordingButton = document.getElementById("stopRecordingButton");
  var userInputForm = document.getElementById("userInputForm");
  var endButton = document.getElementById("endButton");

  
  meetingDetailsForm.addEventListener("submit", function (event) {
    event.preventDefault();
    var meetingName = document.getElementById('meetingName').value;
    var meetingType = document.querySelector('input[name="meetingType"]:checked').value;

    fetch("http://localhost:5000/submit-details", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ meetingName: meetingName, meetingType: meetingType})
    })
    .then(response => {
      if (response.status === 200) {
        return response.json();
      } else {
        return response.json().then(data => {
          alert(data.message);
          throw new Error(data.message);
        });
      }
    })
    .then(data => {
      alert("Session ID: " + data.session_id);
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
          endButton.classList.remove("disabled");

          return response.json();
      } else {
        return response.json().then(data => {
          alert(data.message);
          throw new Error(data.message);
        });
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

    if (session_id === null) {
      alert("Please enter the session ID first.");
      return;
    }

    await fetch("http://localhost:5000/submit-recipient-email", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ session_id: session_id, email: email })
    })
    .then(response => {
      if (response.status === 200) {
        return response.json();
      } else  {
        return response.json().then(data => {
          alert(data.message);
          throw new Error(data.message);
        });
      }
    })
    .then(data => {
      alert(data.message);
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
      if (response.status === 200) {
        return response.json();
      } else {
        return response.json().then(data => {
          textDisplay.textContent = data.message;
          throw new Error(data.message);
        });
      }
    })
    .then(data => {
      textDisplay.textContent = data.message;
    })
    .catch(error => console.error("Error:", error));
  });


  endButton.addEventListener("click", async function () {
    session_id = localStorage.getItem("session_id");
    recording_status = localStorage.getItem("recording_status");

    if (recording_status === "true" && fullShutdown === false) {
      alert("Stop recording before ending the session");
      return;
    } else if (recording_status === "false") { 
      return;
    } else if (recording_status === "true" && fullShutdown === true) { // only the participant recording the meeting can end the session to ensure full meeting is recorded
      await fetch("http://localhost:5000/end-session", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ session_id: session_id })
      })
      .then(response => {
        if (response.status === 200) {
          return response.json();
        } else {
          return response.json().then(data => {
            throw new Error(data.message);
          });
        }
      })
      .then(data => {
        alert(data.message);
        localStorage.clear();
      })
      .catch(error => console.error("Error:", error));
    }
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
    session_id = localStorage.getItem("session_id");
    recording_status = localStorage.getItem("recording_status");

    // check if recording is already enabled for the current meeting
    if (recording_status === "false") {
      recordingStatusResponse = await checkRecordingStaus(session_id);
    }

    if (recording_status === "true" || recordingStatusResponse.status === 200) {
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
        console.error("Error:", error);
      };

      // create media recorder and push data to the data array
      recorder = new MediaRecorder(media, { mimeType: "video/webm" });

      recorder.ondataavailable = (event) => {
        data.push(event.data);
      }

      // add recording to queue for processing when recording stops
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

        // Set a timer to stop the recording after 30 seconds 
        stopTimer = setTimeout(async () => {
          await stopRecording();
        }, 30000);
      }
    } else {
      alert(recordingStatusResponse.message);
      throw new Error(recordingStatusResponse.message);
    } 
  } catch (error) {
    console.error("Error:", error);
  }
}


async function checkRecordingStaus(session_id){
  const recordingStatusResponse = await fetch("http://localhost:5000/recording-status", {
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


// Function to process recordings from the queue
async function processQueue() {
  if (!isProcessing && processingQueue.length > 0) {
      isProcessing = true;

      // Get the next task from the queue
      const task = processingQueue.shift(); 
      try {
          processRecording(task.blob, task.session_id)
              .then(() => {
                  isProcessing = false;
                  processQueue();
              })
              .catch((error) => {
                  console.error("Error:", error);
                  isProcessing = false;
                  processQueue();
              });
      } catch (error) {
          console.error("Error:", error);
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

    const processRecordingResponse = await fetch("http://localhost:5000/process-recording", {
        method: "POST",
        body: formData
    })

    if (processRecordingResponse.status !== 200) {
      alert("Error in recording.");
      throw new Error(processRecordingResponse.message);
    } 
  } catch (error) {
    console.error("Error:", error);
  }
}


async function stopRecording() {
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
