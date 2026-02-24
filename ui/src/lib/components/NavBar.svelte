<script lang="ts">
	import * as m from '$lib/i18n/messages';
	import { isAuthenticated, uiConfig, exhibitEnabled } from '$lib/stores';
</script>

<nav class="sticky top-0 z-50 flex w-full justify-between bg-brand-primary p-5">
	<div class="flex items-center justify-center">
		<a href="/" class="flex items-center text-2xl font-semibold text-white">
			<h1>{$uiConfig?.brand_name ?? 'Papad.alt'}</h1>
		</a>
	</div>

	<div class="flex justify-center">
		<div class="flex flex-wrap space-x-4 text-center">
			<a href="/" class="font-medium text-white hover:text-gray-400">{m.nav_home()}</a>
			<a href="/groups" class="font-medium text-white hover:text-gray-400"
				>{m.nav_collections()}</a
			>
			{#if $exhibitEnabled}
				<a href="/exhibits" class="font-medium text-white hover:text-gray-400"
					>{m.nav_exhibits()}</a
				>
			{/if}
			{#if $isAuthenticated}
				<a href="/settings" class="font-medium text-white hover:text-gray-400"
					>{m.nav_settings()}</a
				>
				<a href="/auth/logout" class="font-medium text-white hover:text-gray-400"
					>{m.nav_logout()}</a
				>
			{:else}
				<a href="/auth/login" class="font-medium text-white hover:text-gray-400"
					>{m.nav_login()}</a
				>
			{/if}
		</div>
	</div>
</nav>
