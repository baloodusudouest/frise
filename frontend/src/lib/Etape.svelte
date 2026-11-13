<script>
  // Une étape ouverte : sa galerie, puis une photo en grand (flèches, touches, glissement du doigt).
  import X from '@lucide/svelte/icons/x'
  import ChevronLeft from '@lucide/svelte/icons/chevron-left'
  import ChevronRight from '@lucide/svelte/icons/chevron-right'
  import Play from '@lucide/svelte/icons/play'
  import Pencil from '@lucide/svelte/icons/pencil'
  import Star from '@lucide/svelte/icons/star'
  import { ageDit, periode, quandDit, foisDit } from '$lib/dates.js'

  let { etape, immich = '', portImmich = 0, onferme, oncorrige } = $props()
  // Immich dans le navigateur : l'adresse réglée, sinon le même hôte que Sillage sur le port d'Immich (en http).
  // Ce lien fait partie des gestes de correction : il est pour le propriétaire, pas pour une future vue d'invité.
  const adresseImmich = $derived(immich || (portImmich && location.protocol === 'http:' ? `http://${location.hostname}:${portImmich}` : ''))
  let corrige = $state(false)   // les gestes de correction sont rangés : on les sort par le crayon
  let nom = $state('')
  const ids = $derived(etape.photos.map((p) => p.id))

  function ouvrirCorrection() { corrige = !corrige; nom = etape.nom }
  // Une photo retirée fait reculer le curseur s'il était sur la dernière
  async function retirer(sorte) {
    const p = etape.photos[grande]
    if (etape.photos.length === 1) { grande = null; await oncorrige?.({ sorte, poser: p.id }); onferme?.(); return }
    await oncorrige?.({ sorte, poser: p.id })
    grande = Math.min(grande, etape.photos.length - 1)
  }
  let grande = $state(null) // rang de la photo ouverte en grand
  let boite
  let depart = 0

  const titre = $derived(etape.nom || quandDit(etape))
  const aller = (pas) => { grande = (grande + pas + etape.photos.length) % etape.photos.length }

  function touche(e) {
    if (e.key === 'Escape') { e.preventDefault(); grande === null ? onferme?.() : (grande = null) }
    else if (grande !== null && e.key === 'ArrowRight') aller(1)
    else if (grande !== null && e.key === 'ArrowLeft') aller(-1)
  }
  $effect(() => { boite?.showModal(); document.documentElement.style.overflow = 'hidden'; return () => (document.documentElement.style.overflow = '') })
</script>

<svelte:window onkeydown={touche} />

<dialog bind:this={boite} class="etape-ouverte" aria-label={titre} oncancel={(e) => e.preventDefault()}>
  <header>
    <div class="min-w-0">
      <h2 class={etape.nom ? 'plume text-[2.4rem] text-balance' : 'text-xl font-semibold text-balance'}>{titre}</h2>
      <p class="text-sm text-muted-foreground">{etape.nom ? quandDit(etape) + foisDit(etape) + ' · ' : ''}{ageDit(etape.age)}{etape.age != null ? ' · ' : ''}{etape.photos.length} photo{etape.photos.length > 1 ? 's' : ''}</p>
    </div>
    <div class="flex flex-none gap-2">
      <button type="button" class="rond" aria-label="Corriger l'étape" aria-pressed={corrige} onclick={ouvrirCorrection}><Pencil class="size-5" aria-hidden="true" /></button>
      <button type="button" class="rond" aria-label="Fermer l'étape" onclick={() => onferme?.()}><X class="size-5" aria-hidden="true" /></button>
    </div>
  </header>
  {#if corrige}
    <form class="correction" aria-label="Corriger l'étape" onsubmit={(e) => { e.preventDefault(); if (nom.trim()) oncorrige?.({ sorte: 'titre', effacer: ids, poser: etape.phare, valeur: nom.trim() }) }}>
      <label for="nom-etape">Nom de l'étape</label>
      <div class="ligne">
        <input id="nom-etape" bind:value={nom} placeholder="Par exemple : Mariage de…" maxlength="200" />
        <button type="submit" class="geste" disabled={!nom.trim() || nom.trim() === etape.nom}>Nommer</button>
        {#if etape.nom_choisi}<button type="button" class="geste" onclick={async () => { await oncorrige?.({ sorte: 'titre', effacer: ids }); nom = etape.nom }}>Rendre le nom d'origine</button>{/if}
      </div>
      <div class="ligne">
        {#if etape.masquee}
          <button type="button" class="geste" onclick={() => oncorrige?.({ sorte: 'masquee', effacer: ids })}>Remettre l'étape dans le chemin</button>
        {:else}
          <button type="button" class="geste" onclick={() => oncorrige?.({ sorte: 'masquee', effacer: ids, poser: etape.phare })}>Masquer cette étape</button>
        {/if}
        <span class="aide">Pour une photo : ouvre-la, les gestes sont en bas.</span>
      </div>
    </form>
  {/if}
  <ul class="galerie" aria-label="Photos de l'étape">
    {#each etape.photos as p, i (p.id)}
      <li>
        <button type="button" onclick={() => (grande = i)} aria-label={'Photo ' + (i + 1) + (p.video ? ' (vidéo)' : '')}>
          <img src={'/api/vignette/' + p.id} alt="" loading="lazy" />
          {#if p.id === etape.phare}<span class="phare" title="Photo phare"><Star class="size-3.5" aria-label="Photo phare" /></span>{/if}
          {#if p.video}<span class="video"><Play class="size-4" aria-hidden="true" /></span>{/if}
        </button>
      </li>
    {/each}
  </ul>

  {#if grande !== null}
    {@const p = etape.photos[grande]}
    <div class="plein" role="group" aria-label={'Photo ' + (grande + 1) + ' sur ' + etape.photos.length}
         ontouchstart={(e) => (depart = e.touches[0].clientX)}
         ontouchend={(e) => { const d = e.changedTouches[0].clientX - depart; if (Math.abs(d) > 50) aller(d < 0 ? 1 : -1) }}>
      {#key p.id}
        {#if p.video}
          <!-- 0.10 : la vidéo se lit ici (lue par morceaux dans Immich) -->
          <video src={'/api/video/' + p.id} poster={'/api/vignette/' + p.id + '?grande=true'} controls playsinline preload="metadata"></video>
        {:else}
          <img src={'/api/vignette/' + p.id + '?grande=true'} alt="" />
        {/if}
      {/key}
      <button type="button" class="rond fermer" aria-label="Fermer la photo" onclick={() => (grande = null)}><X class="size-5" aria-hidden="true" /></button>
      {#if etape.photos.length > 1}
        <button type="button" class="rond avant" aria-label="Photo précédente" onclick={() => aller(-1)}><ChevronLeft class="size-6" aria-hidden="true" /></button>
        <button type="button" class="rond apres" aria-label="Photo suivante" onclick={() => aller(1)}><ChevronRight class="size-6" aria-hidden="true" /></button>
      {/if}
      {#if oncorrige}
        <div class="gestes" role="group" aria-label="Corriger cette photo">
          <button type="button" disabled={p.id === etape.phare} onclick={() => oncorrige({ sorte: 'phare', effacer: ids, poser: p.id })}>{p.id === etape.phare ? 'Photo phare' : 'En faire la photo phare'}</button>
          <button type="button" onclick={() => retirer('retiree')}>Retirer du chemin</button>
          <button type="button" onclick={() => retirer('pas_elle')}>Ce n'est pas cette personne</button>
          {#if adresseImmich}<a href={adresseImmich + '/photos/' + p.id} target="_blank" rel="noopener">Ouvrir dans Immich</a>{/if}
        </div>
      {/if}
      <p class="pied">{grande + 1} / {etape.photos.length}{p.video ? ' · vidéo' : ''}</p>
    </div>
  {/if}
</dialog>

<style>
  .etape-ouverte { width: min(64rem, 100%); max-width: 100%; height: 100dvh; max-height: 100dvh; margin: 0 auto; padding: 0; border: 0; background: var(--background); color: var(--foreground); overflow-y: auto; }
  .etape-ouverte::backdrop { background: rgb(0 0 0 / 0.7); }
  header { position: sticky; top: 0; z-index: 2; display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem;
           padding: calc(1rem + env(safe-area-inset-top, 0px)) max(1rem, env(safe-area-inset-right, 0px)) 0.9rem max(1rem, env(safe-area-inset-left, 0px)); background: var(--background); border-bottom: 1px solid var(--border); }
  .rond { display: grid; place-items: center; flex: none; width: 2.75rem; height: 2.75rem; border-radius: 50%; border: 1px solid var(--border); background: var(--card); color: var(--foreground); }
  .rond:hover { border-color: var(--app); }
  .galerie { list-style: none; margin: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(7.5rem, 1fr)); gap: 0.4rem;
             padding: 1rem max(1rem, env(safe-area-inset-right, 0px)) calc(1.5rem + env(safe-area-inset-bottom, 0px)) max(1rem, env(safe-area-inset-left, 0px)); }
  .galerie button { position: relative; display: block; width: 100%; overflow: hidden; border-radius: 0.6rem; }
  .galerie img { width: 100%; aspect-ratio: 1; object-fit: cover; background: var(--secondary); transition: transform 0.2s; }
  .galerie button:hover img { transform: scale(1.04); }
  .video { position: absolute; right: 0.35rem; bottom: 0.35rem; display: grid; place-items: center; width: 1.6rem; height: 1.6rem; border-radius: 50%; background: rgb(0 0 0 / 0.6); color: #fff; }
  .plein { position: fixed; inset: 0; z-index: 10; display: grid; place-items: center; background: #0b0a09; }
  .plein img, .plein video { max-width: 100%; max-height: 100dvh; object-fit: contain; }
  .plein video { z-index: 1; max-height: calc(100dvh - 9rem); }
  .plein .rond { z-index: 2; position: absolute; background: rgb(0 0 0 / 0.55); color: #fff; border-color: rgb(255 255 255 / 0.2); }
  .fermer { top: calc(0.75rem + env(safe-area-inset-top, 0px)); right: max(0.75rem, env(safe-area-inset-right, 0px)); }
  .avant { left: max(0.75rem, env(safe-area-inset-left, 0px)); top: 50%; margin-top: -1.375rem; }
  .apres { right: max(0.75rem, env(safe-area-inset-right, 0px)); top: 50%; margin-top: -1.375rem; }
  /* Le compteur passe sous les boutons et ne prend pas les clics : il recouvrait la croix. */
  .pied { pointer-events: none; z-index: 0; position: absolute; top: calc(1.4rem + env(safe-area-inset-top, 0px)); left: 0; right: 0; margin: 0; text-align: center; font-size: 0.85rem; color: #d8d2c8; text-shadow: 0 1px 3px #000; }
  .rond[aria-pressed='true'] { border-color: var(--app); color: var(--app); }
  .correction { display: grid; gap: 0.6rem; padding: 0.9rem max(1rem, env(safe-area-inset-right, 0px)) 1rem max(1rem, env(safe-area-inset-left, 0px)); border-bottom: 1px solid var(--border); background: var(--card); }
  .correction label { font-size: 0.8rem; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted-foreground); }
  .ligne { display: flex; flex-wrap: wrap; align-items: center; gap: 0.5rem; }
  .ligne input { flex: 1 1 14rem; min-width: 0; height: 2.75rem; padding: 0 0.8rem; font-size: 1rem; border: 1px solid var(--input); border-radius: 0.6rem; background: transparent; color: inherit; }
  .geste { height: 2.75rem; padding: 0 0.9rem; border: 1px solid var(--border); border-radius: 0.6rem; background: var(--background); font-size: 0.9rem; }
  .geste:hover:not(:disabled) { border-color: var(--app); } .geste:disabled { opacity: 0.45; }
  .aide { font-size: 0.82rem; color: var(--muted-foreground); }
  .phare { position: absolute; left: 0.35rem; top: 0.35rem; display: grid; place-items: center; width: 1.5rem; height: 1.5rem; border-radius: 50%; background: var(--app); color: var(--app-contraste); }
  .gestes { position: absolute; left: 0; right: 0; bottom: calc(0.75rem + env(safe-area-inset-bottom, 0px)); display: flex; flex-wrap: wrap; justify-content: center; gap: 0.4rem; padding: 0 0.75rem; }
  .gestes { z-index: 2; }
  .gestes a { display: inline-flex; align-items: center; min-height: 2.75rem; padding: 0 0.85rem; border-radius: 999px; border: 1px solid #a98fd8; background: rgb(0 0 0 / 0.6); color: #a98fd8; font-size: 0.88rem; }
  .gestes button { min-height: 2.75rem; padding: 0 0.85rem; border-radius: 999px; border: 1px solid rgb(255 255 255 / 0.22); background: rgb(0 0 0 / 0.6); color: #fff; font-size: 0.88rem; }
  .gestes button:hover:not(:disabled) { border-color: #a98fd8; } .gestes button:disabled { color: #a98fd8; border-color: #a98fd8; }
</style>
