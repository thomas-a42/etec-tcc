/* Galeria do detalhe do anúncio: clicar na miniatura troca a foto principal. */
(function () {
  const principal = document.getElementById('galeria-principal');
  if (!principal) return;
  document.querySelectorAll('.galeria__mini').forEach((btn) => {
    btn.addEventListener('click', () => {
      principal.src = btn.dataset.src;
      document.querySelectorAll('.galeria__mini').forEach((b) => b.classList.remove('is-ativa'));
      btn.classList.add('is-ativa');
    });
  });
})();
