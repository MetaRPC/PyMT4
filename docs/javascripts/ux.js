// === Progress auto-fill from data-progress attribute ===
document.addEventListener('DOMContentLoaded', () => {
  const items = document.querySelectorAll('.progress-wrap');
  items.forEach(el => {
    const val = Math.max(0, Math.min(100, Number(el.dataset.progress) || 0));
    const bar = el.querySelector('.progress-bar > span');
    if (bar) bar.style.width = `${val}%`;
  });
});
