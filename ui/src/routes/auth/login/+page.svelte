<script lang="ts">
	import { goto } from '$app/navigation';
	import { auth } from '$lib/api';
	import { currentUser } from '$lib/stores';

	let username = $state('');
	let password = $state('');
	let error = $state('');
	let loading = $state(false);

	async function handleLogin() {
		if (!username || !password) {
			error = 'Username and password are required.';
			return;
		}
		loading = true;
		error = '';
		try {
			const { data: tokens } = await auth.login(username, password);
			localStorage.setItem('access_token', tokens.access);
			localStorage.setItem('refresh_token', tokens.refresh);
			const { data: user } = await auth.me();
			currentUser.set(user);
			await goto('/groups');
		} catch {
			error = 'Invalid username or password.';
		} finally {
			loading = false;
		}
	}
</script>

<div class="flex min-h-[70vh] items-center justify-center">
	<div class="w-full max-w-sm rounded-lg bg-white p-8 shadow-md">
		<h1 class="mb-6 text-center text-2xl font-bold text-gray-700">Sign In</h1>

		{#if error}
			<p class="mb-4 rounded bg-red-100 px-3 py-2 text-sm text-red-700">{error}</p>
		{/if}

		<label class="mb-1 block text-sm font-medium text-gray-600" for="username">Username</label>
		<input
			id="username"
			type="text"
			bind:value={username}
			placeholder="your username"
			class="mb-4 w-full rounded border border-gray-300 px-4 py-2 text-sm focus:outline-none focus:ring focus:ring-blue-200"
		/>

		<label class="mb-1 block text-sm font-medium text-gray-600" for="password">Password</label>
		<input
			id="password"
			type="password"
			bind:value={password}
			placeholder="••••••••"
			class="mb-6 w-full rounded border border-gray-300 px-4 py-2 text-sm focus:outline-none focus:ring focus:ring-blue-200"
		/>

		<button
			onclick={() => void handleLogin()}
			disabled={loading}
			class="w-full rounded bg-blue-950 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
		>
			{loading ? 'Signing in…' : 'Sign In'}
		</button>

		<p class="mt-4 text-center text-sm text-gray-500">
			No account? <a href="/auth/register" class="text-blue-600 hover:underline">Register</a>
		</p>
	</div>
</div>
