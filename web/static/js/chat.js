/* Chat (usuário e ONG). Usa polling simples a cada 4 s.
   API: GET /api/chats  |  GET/POST /api/chats/<id>/mensagens */
(function () {
  const app = document.getElementById('chat-app');
  if (!app) return;

  const lista = document.getElementById('chat-list');
  const cabecalho = document.getElementById('chat-header');
  const mensagensEl = document.getElementById('chat-messages');
  const aviso = document.getElementById('chat-aviso');
  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-input');

  let atual = app.dataset.selected || null;
  let assinatura = ''; // evita redesenhar quando nada mudou

  // ---------- lista de conversas ----------
  async function carregarLista() {
    try {
      const { chats } = await getJSON('/api/chats');
      if (!chats.length) {
        lista.innerHTML = '<p class="muted chat-list__vazio">Nenhuma conversa ainda.</p>';
        return;
      }
      lista.innerHTML = chats.map((c) => `
        <button type="button" class="chat-item ${c.id === atual ? 'is-ativa' : ''}" data-id="${esc(c.id)}">
          <div class="chat-item__topo">
            <span>${esc(c.nome_animal)}</span>
            ${c.nao_lidas > 0 ? `<span class="contador">${c.nao_lidas}</span>` : ''}
          </div>
          <div class="chat-item__sub">${esc(c.contraparte)}${c.status !== 'aberto' ? ' · ' + esc(ROTULOS[c.status]) : ''}</div>
          <div class="chat-item__previa">${esc(c.ultima || 'Sem mensagens ainda')}</div>
        </button>`).join('');
    } catch (e) { /* tenta de novo no próximo ciclo */ }
  }

  lista.addEventListener('click', (ev) => {
    const item = ev.target.closest('.chat-item');
    if (item) abrir(item.dataset.id);
  });

  // ---------- conversa aberta ----------
  function abrir(id) {
    atual = id;
    assinatura = '';
    const url = new URL(window.location);
    url.searchParams.set('c', id);
    history.replaceState(null, '', url);
    carregarMensagens(true);
    carregarLista();
  }

  async function carregarMensagens(forcarScroll) {
    if (!atual) return;
    try {
      const dados = await getJSON(`/api/chats/${encodeURIComponent(atual)}/mensagens`);
      const nova = `${dados.chat.status}|${dados.mensagens.length}|${dados.mensagens.at(-1)?.id || ''}`;
      if (nova === assinatura) return;
      assinatura = nova;

      cabecalho.innerHTML = `<a href="/anuncio/${esc(dados.chat.anuncio_id)}">${esc(dados.chat.nome_animal)}</a>
        <span class="muted"> — ${esc(dados.chat.contraparte)}</span>`;

      const noFim = mensagensEl.scrollHeight - mensagensEl.scrollTop - mensagensEl.clientHeight < 80;
      mensagensEl.innerHTML = dados.mensagens.length
        ? dados.mensagens.map((m) => `
          <div class="msg ${m.minha ? 'msg--minha' : 'msg--outro'}">
            <span class="msg__autor">${esc(m.autor)}</span>
            <div class="msg__texto">${esc(m.conteudo)}</div>
            <span class="msg__hora">${esc(formatarDataHora(m.data_envio))}</span>
          </div>`).join('')
        : '<p class="muted">Nenhuma mensagem ainda. Diga olá! 👋</p>';
      if (forcarScroll || noFim) mensagensEl.scrollTop = mensagensEl.scrollHeight;

      const aberto = dados.chat.status === 'aberto';
      form.hidden = !aberto;
      aviso.hidden = aberto;
      if (!aberto) aviso.textContent = `Esta conversa está ${ROTULOS[dados.chat.status].toLowerCase()} e não aceita novas mensagens.`;
    } catch (e) {
      cabecalho.textContent = 'Conversa não encontrada';
      mensagensEl.innerHTML = '';
      form.hidden = true;
    }
  }

  // ---------- envio ----------
  form.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    const texto = input.value.trim();
    if (!texto || !atual) return;
    input.disabled = true;
    try {
      await postJSON(`/api/chats/${encodeURIComponent(atual)}/mensagens`, { conteudo: texto });
      input.value = '';
      await carregarMensagens(true);
      carregarLista();
    } catch (e) {
      alert(e.message);
    } finally {
      input.disabled = false;
      input.focus();
    }
  });

  // Enter envia, Shift+Enter quebra linha
  input.addEventListener('keydown', (ev) => {
    if (ev.key === 'Enter' && !ev.shiftKey) {
      ev.preventDefault();
      form.requestSubmit();
    }
  });

  // ---------- início + polling ----------
  carregarLista();
  if (atual) carregarMensagens(true);
  setInterval(() => {
    if (document.hidden) return;
    carregarLista();
    carregarMensagens(false);
  }, 4000);
})();
