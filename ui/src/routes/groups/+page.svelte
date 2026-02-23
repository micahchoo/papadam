<script>
    import { goto } from '$app/navigation';

    const colors = ['bg-red-500', 'bg-blue-500', 'bg-green-500', 'bg-yellow-500', 'bg-purple-500', 'bg-pink-500', 'bg-cyan-500'];
    let collections = [];
    let error = '';
    let loading = false; // Loading state
    export let data;
    $: collections = data.collections;

    function handleClick(url) {
        loading = true; // Set loading state
        goto(url).then(() => {
            loading = false; // Reset loading state after navigation
        }).catch(err => {
            console.error(err);
            error = 'Failed to navigate.';
            loading = false; // Reset loading state in case of error
        });
    }
</script>

<div class="container mx-auto p-6 relative">
    <h1 class="text-2xl font-bold mb-6 mx-auto max-w-5xl">My Collections</h1>
    {#if error}
        <p class="text-red-500">{error}</p>
    {:else if collections.length === 0}
        <p class="text-gray-500">No collections found.</p>
    {:else}
    <div class="grid max-w-5xl mx-auto grid-cols-1 md:grid-cols-2 gap-4">
        {#each collections as collection, index}
        <div 
        class="bg-white shadow-md cursor-pointer hover:shadow-lg transition-shadow flex flex-col"
        on:click={() => handleClick(`/groups/${collection.id}`)}
    >
        <!-- Colored box above the heading -->
        <div class={`h-60 w-full ${colors[index % colors.length]}`}></div>
        <div class="flex flex-col justify-center items-center text-center p-5">
            <h2 class="text-xl font-semibold">{collection.name}</h2>
            <p class="text-gray-600 mt-2">{@html collection.description}</p>
        </div>
    </div>    
        {/each}
    </div>    
    {/if}

    <!-- Loading overlay -->
    {#if loading}
    <div class="fixed inset-0 flex items-center justify-center bg-gray-500 bg-opacity-50 z-50">
        <div class="loader ease-linear rounded-full border-4 border-t-4 border-gray-200 h-12 w-12"></div>
    </div>
    {/if}
</div>

<style>
    /* Basic spinner styles */
    .loader {
        border-top-color: #3498db;
        animation: spinner 0.6s linear infinite;
    }
    @keyframes spinner {
        0% {
            transform: rotate(0deg);
        }
        100% {
            transform: rotate(360deg);
        }
    }
</style>