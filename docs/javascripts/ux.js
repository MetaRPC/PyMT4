// Minimal accessibility polish for keyboard navigation
document.addEventListener('DOMContentLoaded', () => {
  const focusables = document.querySelectorAll('.card');
  focusables.forEach(el => {
    el.setAttribute('tabindex', '0');
    el.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        el.click();
      }
    });
  });
});
