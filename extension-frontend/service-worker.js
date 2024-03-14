let recording = false;

chrome.runtime.onMessage.addListener(async (message) => {
  if (message.type === "toggle-recording") {
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
    toggleRecording();
  }
});

async function toggleRecording() {
  if (recording) {
    chrome.runtime.sendMessage({
      type: "stop-recording",
    });
    recording = false;
  } 
  else {
    // Get a MediaStream for the active tab.
    const tab = await chrome.tabs.query({ active: true, currentWindow: true });
    const streamId = await chrome.tabCapture.getMediaStreamId({
      targetTabId: tab[0].id
    });

    chrome.runtime.sendMessage({
      type: "start-recording",
      data: streamId
    });
    recording = true;
  }
}



