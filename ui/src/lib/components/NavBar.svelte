<script lang="ts">
	import { page } from '$app/stores';
	import * as m from '$lib/i18n/messages';
	import { isAuthenticated, uiConfig, exhibitEnabled } from '$lib/stores';

	function navClass(path: string, exact = false): string {
		const active = exact
			? $page.url.pathname === path
			: $page.url.pathname === path || $page.url.pathname.startsWith(path + '/');
		return `font-medium text-white hover:text-gray-400${active ? ' underline underline-offset-4 decoration-2' : ''}`;
	}
</script>

<nav class="sticky top-0 z-50 flex w-full justify-between bg-brand-primary p-5">
	<div class="flex items-center justify-center">
		<a href="/" class="flex items-center text-2xl font-semibold text-white">
			<h1>{$uiConfig?.brand_name ?? 'Papad.alt'}</h1>
		</a>
	</div>

	<div class="flex justify-center">
		<div class="flex flex-wrap space-x-4 text-center">
			<a href="/" class={navClass('/', true)}>{m.nav_home()}</a>
			<a href="/groups" class={navClass('/groups')}>{m.nav_collections()}</a>
			{#if $exhibitEnabled}
				<a href="/exhibits" class={navClass('/exhibits')}>{m.nav_exhibits()}</a>
			{/if}
			{#if $isAuthenticated}
				<a href="/settings" class={navClass('/settings', true)}>{m.nav_settings()}</a>
				<a href="/auth/logout" class={navClass('/auth/logout', true)}>{m.nav_logout()}</a>
			{:else}
				<a href="/auth/login" class={navClass('/auth/login', true)}>{m.nav_login()}</a>
			{/if}
		</div>
	</div>
</nav>
