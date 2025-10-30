// Keep JS minimal and safe.
// 1) Add keyboard focus style similar to hover underline
document.addEventListener('DOMContentLoaded', () => {
  const items = document.querySelectorAll('.quickbar-item, .card');
  items.forEach(el => {
    el.addEventListener('focus', () => el.classList.add('is-focus'));
    el.addEventListener('blur',  () => el.classList.remove('is-focus'));
  });
});
