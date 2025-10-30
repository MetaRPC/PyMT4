document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.card').forEach(el => {
    el.setAttribute('tabindex', '0');
    el.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        el.click();
      }
    });
  });

  
   const onHome = /\/(?:index\.html)?$/.test(location.pathname) || location.pathname.endsWith("/");
   const pill = document.querySelector(".top-api-pill");
   if (pill && !onHome) pill.style.display = "none";
});
