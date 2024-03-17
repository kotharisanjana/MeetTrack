let recording = false;

chrome.runtime.onMessage.addListener(async (message) => {
  if (message.type === "start-recording") {
    createOffScreenDocument();
    sendStartMessage();
  }
  else if (message.type === "stop-recording") {
    sendStopMessage();
  }
});

async function createOffScreenDocument() {
  const existingContexts = await chrome.runtime.getContexts({});
  const offscreenDocument = existingContexts.find(
    (c) => c.contextType === "OFFSCREEN_DOCUMENT"
  );

  // If an offscreen document is not already open, create one.
  if (!offscreenDocument) {
    // Create an offscreen document.
    await chrome.offscreen.createDocument({
      url: "extension.html",
      reasons: ["USER_MEDIA"],
      justification: "Recording from chrome.tabCapture API"
    });
  }
}


async function getMediaStream() {
  // Get a MediaStream for the active tab.
  const tab = await chrome.tabs.query({ active: true, currentWindow: true });
  return await chrome.tabCapture.getMediaStreamId({
    targetTabId: tab[0].id
  });
}


async function sendStartMessage() {
  try {
    const streamId = await getMediaStream();

    chrome.runtime.sendMessage({
      type: "start-recording",
      data: streamId
    });
    recording = true;
  } catch (error) {
    console.error("Error getting media stream:", error);
  }
}


function sendStopMessage() {
  if (recording) {
    chrome.runtime.sendMessage({
      type: "stop-recording",
    });
    recording = false;
  } 
}



