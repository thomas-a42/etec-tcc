/* Feed com rolagem infinita (home e busca).
   - Busca os cards em /api/anuncios (endpoint em data-endpoint de #feed)
   - Se existir um <form id="filtros">, seus campos viram parâmetros da API
   - Carrega a próxima página quando #feed-sentinel se aproxima da tela */
(function () {
  const feed = document.getElementById('feed');
  if (!feed) return;

  const form = document.getElementById('filtros');
  const statusEl = document.getElementById('feed-status');
  const sentinel = document.getElementById('feed-sentinel');
  const endpoint = feed.dataset.endpoint;

  let offset = 0;
  let carregando = false;
  let temMais = true;
  let geracao = 0; // invalida requisições antigas quando os filtros mudam

  function parametros() {
    const p = new URLSearchParams();
    if (form) {
      new FormData(form).forEach((valor, chave) => {
        if (String(valor).trim() !== '') p.append(chave, valor);
      });
    }
    return p;
  }

  async function carregarMais() {
    if (carregando || !temMais) return;
    carregando = true;
    const minha = geracao;
    statusEl.textContent = 'Carregando…';

    try {
      const p = parametros();
      p.set('offset', offset);
      const dados = await getJSON(`${endpoint}?${p}`);
      if (minha !== geracao) return;

      feed.insertAdjacentHTML('beforeend', dados.items.map(cardAnimal).join(''));
      offset += dados.items.length;
      temMais = dados.has_more;

      if (!feed.children.length) statusEl.textContent = 'Nenhum animal encontrado.';
      else statusEl.textContent = temMais ? '' : 'Isso é tudo por enquanto 🐾';
    } catch (erro) {
      if (minha === geracao) statusEl.textContent = 'Não foi possível carregar os animais.';
    } finally {
      if (minha === geracao) {
        carregando = false;
        // se a tela ainda não está cheia, o observer não dispara de novo: confere na mão
        if (temMais) requestAnimationFrame(verificarSentinela);
      }
    }
  }

  function verificarSentinela() {
    if (sentinel.getBoundingClientRect().top < window.innerHeight + 300) carregarMais();
  }

  function recomecar() {
    geracao += 1;
    offset = 0;
    temMais = true;
    carregando = false;
    feed.innerHTML = '';
    carregarMais();
  }

  new IntersectionObserver((entradas) => {
    if (entradas.some((e) => e.isIntersecting)) carregarMais();
  }, { rootMargin: '300px' }).observe(sentinel);

  if (form) {
    form.addEventListener('submit', (ev) => {
      ev.preventDefault();
      history.replaceState(null, '', `?${parametros()}`); // URL compartilhável
      recomecar();
    });
  }

  carregarMais();
})();
