<script lang="ts">
	import { page } from '$app/stores';
</script>

<div class="flex min-h-[60vh] flex-col items-center justify-center px-4 text-center">
	<h1 class="text-6xl font-bold text-gray-800">{$page.status}</h1>
	<p class="mt-4 text-lg text-gray-600">{$page.error?.message ?? 'Something went wrong'}</p>
	<a href="/" class="mt-8 rounded bg-brand-primary px-6 py-2 text-white hover:opacity-90">
		Back to home
	</a>
</div>
