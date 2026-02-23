<script>
    import { handleDelete } from '$lib/services/api.js';
    // Props to be passed in
    export let annotations = [];
    export let onPlaySnippet = () => {};

    // Utility function to format time
    function formatTime(seconds) {
        if (isNaN(seconds)) return "00:00";
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    }

    // Utility function to extract and validate time parts
    function getTimeParts(mediaTarget) {
        try {
            // Clean up the string (remove any spaces if present)
            const cleanTarget = mediaTarget.replace(/\s+/g, '');

            // If the string starts with "t=", remove it
            if (cleanTarget.startsWith("t=")) {
                const target = cleanTarget.slice(2); // Remove "t=" prefix
                return parseTimeRange(target);
            }

            // If no "t=" prefix, handle the raw string
            return parseTimeRange(cleanTarget);
        } catch (error) {
            console.error("Error parsing media target:", error);
        }
        return null; // Return null if parsing fails
    }

    // Function to parse time range like "00:40,00:50" or "180.772502,234.070646"
    function parseTimeRange(target) {
        // Regular expression to match valid time range in the format HH:MM,HH:MM
        const timePattern = /^(\d{2}):(\d{2}),(\d{2}):(\d{2})$/;
        
        // Check if the target matches the time pattern
        const match = target.match(timePattern);
        
        if (match) {
            // If matched, convert to seconds
            const start = convertTimeToSeconds(match[1], match[2]);
            const end = convertTimeToSeconds(match[3], match[4]);
            return [start, end]; // Return as start and end times in seconds
        }

        // If the format doesn't match, check if it's a numeric range like "180.772502,234.070646"
        const parts = target.split(',').map(Number); 
        if (parts.length === 2 && !isNaN(parts[0]) && !isNaN(parts[1])) {
            return parts; // Return as start and end times in seconds
        }

        // If the format is invalid, log the issue and return null
        console.error("Invalid timestamp format:", target);
        return null;
    }

    // Helper function to convert HH:MM to seconds
    function convertTimeToSeconds(hours, minutes) {
        return parseInt(hours) * 60 + parseInt(minutes);
    }

    // Pre-calculate timeParts for each annotation
    $: annotations = annotations.map(annotation => {
        const timeParts = getTimeParts(annotation.media_target);
        return { ...annotation, timeParts }; // Add timeParts to annotation
    });

    const editAnno = (annotation) => {
    if (annotation) {
        annoDescription = annotation.annotation_text; // Set current description
    }
    };
    const deleteAnno = async (annotation) => {
        if (annotation) {
            try {
                // Call deleteRecording from api.js to delete the media
                await handleDelete(annotation.uuid);      
                window.history.back();            
            } catch (err) {
                console.error("Error deleting media:", err);
                let error = err.response?.data?.detail || "An error occurred during deletion.";
            } finally {
            }
        }
    };

</script>

<div class="annotation-viewer">
    {#if annotations && annotations.length > 0}
        <ul>
            {#each annotations as annotation}
                <li class="bg-white p-4 my-2 mb-5 rounded shadow-sm">
                    {#if annotation.media_target && annotation.timeParts}
                        <p>
                            <strong>Timestamp:</strong>
                            <span 
                                class="cursor-pointer text-blue-500 underline" 
                                on:click={() => onPlaySnippet(annotation.timeParts[0], annotation.timeParts[1])}
                            >
                                {formatTime(annotation.timeParts[0])} - {formatTime(annotation.timeParts[1])}
                            </span>
                        </p>
                    {:else}
                        <p><strong>Timestamp:</strong> Invalid timestamp</p>
                    {/if}
                    <div class="text-gray-600 mt-4">
                        {@html annotation.annotation_text || "No note available"}
                    </div>
                    <button 
                        class="bg-yellow-500 text-white px-4 py-2 rounded hover:bg-yellow-600" 
                        on:click={() => editAnno(annotation)}>
                        Edit
                    </button>
                    <button 
                    class="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600" on:click={()=>deleteAnno(annotation)}>
                    Delete
                </button>
                </li>
            {/each}
        </ul>
    {:else}
        <p class="text-gray-500">No annotations available.</p>
    {/if}
</div>
