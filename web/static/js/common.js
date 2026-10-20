/* Utilitários compartilhados por todas as páginas. */

const ROTULOS = {
  macho: 'Macho', femea: 'Fêmea', desconhecido: 'Não informado',
  pequeno: 'Pequeno', medio: 'Médio', grande: 'Grande',
  aberto: 'Aberto', encerrado: 'Encerrado', bloqueado: 'Bloqueado',
};

/** Escapa texto antes de inserir em innerHTML (evita XSS). */
function esc(valor) {
  return String(valor ?? '').replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}

async function getJSON(url) {
  const resp = await fetch(url, { headers: { Accept: 'application/json' } });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

async function postJSON(url, corpo) {
  const resp = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(corpo),
  });
  const dados = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(dados.erro || `HTTP ${resp.status}`);
  return dados;
}

function formatarIdade(n) {
  if (n === null || n === undefined) return 'Idade não informada';
  return `${n} ${n === 1 ? 'ano' : 'anos'}`;
}

function formatarDataHora(iso) {
  return new Date(iso).toLocaleString('pt-BR', {
    day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit',
  });
}

/** HTML do card de animal usado no feed (home e busca). */
function cardAnimal(a) {
  const foto = a.imagem
    ? `<img class="card__foto" src="${esc(a.imagem)}" alt="Foto de ${esc(a.nome_animal)}" loading="lazy">`
    : '<div class="card__sem-foto">🐾</div>';
  const detalhes = [a.especie && a.especie[0].toUpperCase() + a.especie.slice(1), a.raca, ROTULOS[a.sexo]]
    .filter(Boolean).join(' · ');
  return `
    <a class="card" href="/anuncio/${esc(a.id)}">
      ${foto}
      <div class="card__corpo">
        <h3 class="card__titulo">${esc(a.nome_animal)}</h3>
        <span class="card__meta">${esc(detalhes)}</span>
        <span class="card__meta">${esc(formatarIdade(a.idade))}${a.porte ? ' · ' + esc(ROTULOS[a.porte]) : ''}</span>
        <span class="card__meta">${esc(a.ong_nome)} — ${esc(a.cidade)}/${esc(a.estado)}</span>
      </div>
    </a>`;
}
