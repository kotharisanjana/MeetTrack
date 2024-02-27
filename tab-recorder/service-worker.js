let recording = false;

chrome.action.onClicked.addListener(async (tab) => {

  const existingContexts = await chrome.runtime.getContexts({});

  const offscreenDocument = existingContexts.find(
    (c) => c.contextType === 'OFFSCREEN_DOCUMENT'
  );

  // If an offscreen document is not already open, create one.
  if (!offscreenDocument) {
    console.log('Creating offscreen document');
    // Create an offscreen document.
    await chrome.offscreen.createDocument({
      url: 'offscreen.html',
      reasons: ['USER_MEDIA'],
      justification: 'Recording from chrome.tabCapture API'
    });
  }

  if (recording) {
    chrome.runtime.sendMessage({
      type: 'stop-recording',
    });
    console.log('Recording stopped message in service-worker.js');
    recording = false;
    return;
  }

  // Get a MediaStream for the active tab.
  const streamId = await chrome.tabCapture.getMediaStreamId({
    targetTabId: tab.id
  });

  // Send the stream ID to the offscreen document to start recording.
  chrome.runtime.sendMessage({
    type: 'start-recording',
    data: streamId
  });
  console.log('Recording started message in service-worker.js');
  recording = true;

});


// chrome.runtime.onMessage.addListener((message) => {
//   if (message.type === 'saveRecording') {
//     const { blobUrl, filename } = message;
//     console.log('Received blobUrl:', blobUrl);

//     // Download the recording using chrome.downloads.download
//     chrome.downloads.download({
//       url: blobUrl,
//       filename: filename,
//       saveAs: false // Set to true if you want to prompt user for download location
//     }, downloadId => {
//       if (downloadId === undefined) {
//         console.error('Failed to start download');
//       } else {
//         console.log('Download started successfully');
//       }
//     });
//   }
// });

