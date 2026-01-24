const toggleButton = document.getElementById('theme-toggle');
const currentTheme = localStorage.getItem('theme');

// Apply the saved theme (if any) on page load
if (currentTheme) {
  document.documentElement.setAttribute('data-theme', currentTheme);
}

// Toggle theme on button click
toggleButton.addEventListener('click', () => {
  const current = document.documentElement.getAttribute('data-theme');
  const newTheme = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', newTheme);

  // Save the new theme in localStorage
  localStorage.setItem('theme', newTheme);
});