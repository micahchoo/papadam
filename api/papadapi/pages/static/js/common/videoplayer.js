function videoPlayerPlay(playerObj) {
    playerObj.play()
}

function videoPlayerStop(playerObj) {
    playerObj.stop()
}
function videoPlayerPause(playerObj) {
    playerObj.pause()
}

function videoPlayerReset(playerObj) {
    playerObj.reset()
}

function getCurrentTime(playerObj) {
    return playerObj.currentTime()
}
  
function updateVideoSource(url, extension) {
  // const player = videojs(document.getElementById('my-video'))
  // player.dispose()
  const player = videojs(document.getElementById('my-video'),{
    playbackRates: [0.5, 1, 1.5, 2],
    height: 220,
    width: 240,
  });
  
  // Update the source
  // player.src({
  //   src: url,
  //   type: extension,//'application/x-mpegURL' // or the appropriate type for your video
  // });

  // Load the new source 
  player.load();
  //     // Event handlers for play and pause
  //     var startTime = playerObj.on('play', getCurrentTime(playerObj));
  //     var endTime = playerObj.on('pause', getCurrentTime(playerObj));
}