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
      if (response.status === 200 || response.status === 400) {
        return response.json().then(data => {
          alert(data.message);
        });
      } else {
        return response.json().then(data => {
          throw new Error(data.message);
        });
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
          endButton.classList.remove("disabled");

          return response.json();
      } else if (response.status === 400) {
        return response.json();
      } else {
        return response.json().then(data => {
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
      alert("Please enter the session ID.");
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
      if (response.status === 200 || response.status === 400) {
        return response.json();
      } else {
        return response.json().then(data => {
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
    recording_status = localStorage.getItem("recording_status");

    if (recording_status === "true" && fullShutdown === false) {
      alert("Stop recording before ending the session");
      return;
    } else if (recording_status === "false") { 
      return;
    } else if (recording_status === "true" && fullShutdown === true) { // only the participant recording the meeting can end the session to ensure full meeting is recorded
      alert("You will receive meeting notes shortly via email. Thank you for using MeetTrack.")
      monitorQueue();
    }
  });

});


function monitorQueue() {
  const queueMonitor = setInterval(() => {
    if (processingQueue.length === 0 && isProcessing === false) {
      // stop monitoring the queue
      clearInterval(queueMonitor);
      // call function that ends the session
      endSession();
    }
  }, 10000);
}


async function endSession() {
  session_id = localStorage.getItem("session_id");
  
  await fetch("http://localhost:5000/end-session", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ session_id: session_id })
  })
  .then(response => {
    if (response.status === 200) {
      return response.json().then(data => {
        alert(data.message);
        localStorage.clear();
      });
    } else if (response.status === 400) {
      return response.json().then(data => {
        alert(data.message);
      });
    } else {
      return response.json().then(data => {
        throw new Error(data.message);
      });
    }
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
    session_id = localStorage.getItem("session_id");
    recording_status = localStorage.getItem("recording_status");

    if (recording_status === "false") {
      recordingStatusResponse = await checkRecordingStatus(session_id);
      responseData = await recordingStatusResponse.json();
    } 

    if (recording_status === "true" || recordingStatusResponse.status === 200) {
      if (recording_status === "false"){
        alert(responseData.message);
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
        }, 15000);
      }
    } else {
      alert(responseData.message);
      throw new Error(responseData.message);
    } 
  } catch (error) {
    console.error("Error:", error);
  }
}


async function checkRecordingStatus(session_id){
  try{
    const recordingStatusResponse = await fetch("http://localhost:5000/recording-status", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ session_id: session_id })
    });
    return recordingStatusResponse;
   } catch (error) {
   console.error("Error fetching recording status:", error);
   return null;
 }
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

    const response = await fetch("http://localhost:5000/process-recording", {
        method: "POST",
        body: formData
    })

    if (response.status === 400) {
      alert(response.message);
    } else if (response.status === 500) {
      throw new Error(response.message);
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
