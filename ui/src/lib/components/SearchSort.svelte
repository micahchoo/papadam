<script>
    import { selectedGroupMedia, selectedGroupDetails } from '$lib/stores';
    
    let sortOrder = 'newest'; // Default sorting option
	let searchQuery = ''; // Search input
	let searchBy = 'name'; // Default search by name

    export let sortedRecordings, filteredRecordings;
    // Function to sort the recordings based on the selected sort order
	$: sortedRecordings = $selectedGroupMedia
		? [...$selectedGroupMedia].sort((a, b) => {
			if (sortOrder === "newest") {
				return new Date(b.created_at) - new Date(a.created_at);
			} else if (sortOrder === "oldest") {
				return new Date(a.created_at) - new Date(b.created_at);
			} else if (sortOrder === "ascending") {
				return a.name.localeCompare(b.name);
			} else if (sortOrder === "descending") {
				return b.name.localeCompare(a.name);
			}
		})
		: [];

	// Function to filter recordings based on the search query and search criteria
	$: filteredRecordings = sortedRecordings.filter((recording) => {
		if (searchBy === "name") {
			return recording.name.toLowerCase().includes(searchQuery.toLowerCase());
		} else if (searchBy === "tags") {
			const searchTags = searchQuery
				.split(",")
				.map(tag => tag.trim().toLowerCase())
				.filter(tag => tag); // Remove empty strings
			// Ensure all tags in the search query exist in the recording's tags
			return searchTags.every(searchTag =>
				recording.tags.some(tag =>
					tag.name.toLowerCase().includes(searchTag)
				)
			);
		}
	});
</script>

	<!-- Right Section: Search, Sort, and Media Cards -->
	<div class="mb-6 sticky w-full flex-1 overflow-y-auto px-3 md:my-6 md:w-3/4">
		<div class="my-4 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
			<!-- Search Bar -->
			<div class="flex w-full items-center gap-2">
				<select
					bind:value={searchBy}
					class="w-1/5 rounded border border-gray-300 px-2 py-1 text-sm focus:outline-none focus:ring focus:ring-blue-200"
				>
					<option value="name">Name</option>
					<option value="tags">Tags</option>
				</select>
				<input
					type="text"
					placeholder="Search..."
					bind:value={searchQuery}
					class="w-4/5 rounded border border-gray-300 px-4 py-2 text-sm focus:outline-none focus:ring focus:ring-blue-200"
				/>
			</div>
		
			<!-- Sort Dropdown -->
			<div class="flex items-center">
				<label for="sortOrder" class="mr-2 text-xs font-medium text-gray-600">Sort:</label>
				<select
					id="sortOrder"
					bind:value={sortOrder}
					class="rounded border border-gray-300 px-2 py-1 text-sm focus:outline-none focus:ring focus:ring-blue-200"
				>
					<option value="newest">Newest to Oldest</option>
					<option value="oldest">Oldest to Newest</option>
					<option value="ascending">Name Ascending</option>
					<option value="descending">Name Descending</option>
				</select>
			</div>
		</div>		
        </div>