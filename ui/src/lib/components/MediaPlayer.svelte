<script>
    import { selectedMediaDuration } from '$lib/stores'; // Assuming selectedMediaDuration is a writable store
    export let src = '';
    export let autoplay = false;
    export let onTimeUpdate = null;
    export let controls = true;

    let videoPlayer;

    // This function is triggered when the video metadata is loaded
    function setMediaDuration() {
        if (videoPlayer && videoPlayer.duration) {
            $selectedMediaDuration = videoPlayer.duration;  // Set the media duration in the store
        }
    }

    // Function to play a specific snippet of the video
    export function playSnippet(start, end) {
        if (videoPlayer) {
            const startTime = parseFloat(start);
            const endTime = parseFloat(end);

            // Set the current time to the start of the snippet and play the video
            videoPlayer.currentTime = startTime;
            videoPlayer.play();

            // Stop playback after the end time
            const stopPlayback = () => {
                if (videoPlayer.currentTime >= endTime) {
                    videoPlayer.pause();
                    videoPlayer.removeEventListener('timeupdate', stopPlayback);
                }
            };

            videoPlayer.addEventListener('timeupdate', stopPlayback);
        }
    }

    // Optional time update event handler
    function handleTimeUpdate(event) {
        if (onTimeUpdate && typeof onTimeUpdate === 'function') {
            onTimeUpdate(event);
        }
    }
</script>

<div class="media-player-container pb-5 ">
    {#if src}
        <video 
            bind:this={videoPlayer} 
            {controls} 
            {autoplay} 
            class=" h-full w-full bg-black" 
            src={src}
            on:loadedmetadata={setMediaDuration} >
            Your browser does not support the video tag.
        </video>
    {:else}
        <video controls class=" w-full bg-black"></video>
    {/if}
</div>
