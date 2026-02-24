<script lang="ts">
</script>

<section
	id="cover"
	class="flex h-[90vh] w-screen bg-gray-100 p-4 pb-72 pt-10 md:items-center md:justify-center md:p-1"
>
	<div
		class="flex flex-col items-center justify-center gap-x-10 rounded-lg p-10 pt-40 md:flex-row md:p-32"
	>
		<!-- Image Section -->
		<div class="flex-shrink-0">
			<img class="h-40 md:h-52" src="/img/Frame 4.png" alt="Sankalana Logo" />
		</div>
		<!-- Text Section -->
		<div class="text-center md:text-left">
			<h1 class="my-5 text-4xl font-black text-blue-100 md:text-7xl">Papad.alt</h1>
			<p class="mt-1 max-w-md text-sm text-gray-100 md:text-lg">
				Papad.alt is a front end written for the PAPAD API, developed by Janastu. Sankalana is a
				hypermedia media fragment annotator.
			</p>
			<a href="/groups">
				<button
					class="mt-5 w-full rounded bg-blue-100 px-4 py-2 text-black hover:bg-blue-800 hover:text-white"
				>
					View Collections
				</button>
			</a>
		</div>
	</div>
</section>

<style>
	#cover {
		background-image: url('/img/cover.jpg');
		background-size: cover;
		background-repeat: no-repeat;
		background-color: rgba(0, 0, 0, 0.7); /* 70% black overlay */
		background-blend-mode: darken; /* Blend the color with the image */
	}
</style>
