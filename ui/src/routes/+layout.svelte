<script>
	import '../app.css'; // Ensure the CSS file is imported
</script>

<!-- Navigation Bar -->
<nav class="sticky top-0 z-50 w-full bg-blue-950 flex justify-between p-5">
	<!-- First Line: Logo Section -->
	<div class="flex items-center justify-center">
		<a href="/" class="text-white flex items-center text-2xl font-semibold">
			<h1>Papad.alt</h1>
			<!-- <img src="" alt="Sankalana" class="" /> -->
		</a>
	</div>

	<!-- Second Line: Navigation Links -->
	<div class="flex justify-center">
		<div class="flex flex-wrap space-x-4 text-center">
			<a href="/" class="text-white font-medium hover:text-gray-400">Home</a>
			<a href="/groups" class="text-white font-medium hover:text-gray-400">Collections</a>
		</div>
	</div>
</nav>

<!-- Main Content -->
<main class=" bg-gray-100">
	<slot />
</main>

<footer class="w-screen bg-gray-900 p-10 text-gray-400">
	<div class="text-sm max-w-6xl mx-auto flex flex-col lg:flex-row justify-between items-center lg:items-start gap-6">
	  <!-- Column 1: Organization Info -->
	  <div class="text-sm text-center lg:text-left">
		<p class="mb-1 max-w-md">
		  Developed at <strong>Aruvu Collaboratory LLP</strong>, leveraging the <strong>PAPAD API</strong>, by <strong>Janastu Serveleots</strong>.
		</p>
		<p class="mb-1">
		  Reach out to us:
		</p>
		<ul class="list-none">
		  <li>Email: <a href="mailto:wellbeing@aruvu.org" class="text-gray-300 hover:underline">wellbeing@aruvu.org</a></li>
		  <li>Website: <a href="https://aruvu.org" class="text-gray-300 hover:underline">aruvu.org</a></li>
		</ul>
	  </div>
  
	  <!-- Column 2: Social Media Links -->
	  <div class="text-sm text-center lg:text-right">
		<p class="mb-4">Links:</p>
		<ul class="list-none flex gap-x-3 md:flex-col justify-center lg:justify-end">
		  <li>
			<a href="https://github.com/Aruvu-collab" target="_blank" class="text-gray-300 hover:underline">GitHub</a>
		  </li>
		  <li>
			<a href="https://instagram.com/aruvu" target="_blank" class="text-gray-300 hover:underline">Instagram</a>
		  </li>
		  <li>
			<a href="https://aruvu.org" target="_blank" class="text-gray-300 hover:underline">Website</a>
		  </li>
		</ul>
	  </div>
	</div>
  
	<!-- Copyright -->
	<div class="mt-6 text-center text-sm text-gray-400">
	  &copy; <span id="year"></span> Aruvu Collaboratory LLP
	</div>
  </footer>

<style>
	@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
</style>
