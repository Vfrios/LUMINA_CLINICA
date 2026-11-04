// Carrega o <model-viewer> (≥ 3.x): primeiro cópia local (vendor/, se gerada com --vendor), depois CDNs com versão FIXA.
export const MV_VERSAO = '3.5.0';
export async function carregarModelViewer() {
  if (customElements.get('model-viewer')) return 'já carregado';
  const fontes = [
    new URL('../vendor/model-viewer.min.js', import.meta.url).href,
    `https://ajax.googleapis.com/ajax/libs/model-viewer/${MV_VERSAO}/model-viewer.min.js`,
    `https://cdn.jsdelivr.net/npm/@google/model-viewer@${MV_VERSAO}/dist/model-viewer.min.js`,
  ];
  for (const u of fontes) {
    try { await import(u); await customElements.whenDefined('model-viewer'); return u; } catch (e) { /* tenta a próxima */ }
  }
  throw new Error('Não foi possível carregar o <model-viewer> (sem rede e sem vendor/).');
}
