/* Pequenos comportamentos de formulários (painel admin, dashboard da ONG, edição de anúncio). */

// <select data-autosubmit> envia o formulário assim que o valor muda
document.querySelectorAll('select[data-autosubmit]').forEach((sel) => {
  sel.addEventListener('change', () => sel.form.submit());
});

// <button data-confirmar="texto"> pede confirmação antes de enviar
document.querySelectorAll('[data-confirmar]').forEach((el) => {
  el.addEventListener('click', (ev) => {
    if (!confirm(el.dataset.confirmar)) ev.preventDefault();
  });
});
