<script lang="ts">
	import { uiConfig } from '$lib/stores';
</script>

<section
	id="cover"
	class="flex h-[90vh] w-screen bg-[var(--scheme-bg,#f3f4f6)] p-4 pb-72 pt-10 md:items-center md:justify-center md:p-1"
>
	<div
		class="flex flex-col items-center justify-center gap-x-10 rounded-lg p-10 pt-40 md:flex-row md:p-32"
	>
		<!-- Image Section -->
		<div class="flex-shrink-0">
			<img class="h-40 md:h-52" src={$uiConfig?.brand_logo_url || '/img/Frame 4.png'} alt={$uiConfig?.brand_name ?? 'Logo'} />
		</div>
		<!-- Text Section -->
		<div class="text-center md:text-left">
			<h1 class="my-5 text-4xl font-black text-white md:text-7xl">
				{$uiConfig?.brand_name ?? 'Papad.alt'}
			</h1>
			<p class="mt-1 max-w-md text-sm text-gray-100 md:text-lg">
				Papad.alt is a front end written for the PAPAD API, developed by Janastu. Sankalana is a
				hypermedia media fragment annotator.
			</p>
			<a
				href="/groups"
				class="mt-5 block w-full rounded bg-white px-4 py-2 text-center text-brand-primary hover:bg-brand-primary hover:text-white"
			>
				View Collections
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
