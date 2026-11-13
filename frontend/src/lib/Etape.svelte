<script>
  // Une étape ouverte : sa galerie, puis une photo en grand (flèches, touches, glissement du doigt).
  import X from '@lucide/svelte/icons/x'
  import ChevronLeft from '@lucide/svelte/icons/chevron-left'
  import ChevronRight from '@lucide/svelte/icons/chevron-right'
  import Play from '@lucide/svelte/icons/play'
  import { ageDit, periode } from '$lib/dates.js'

  let { etape, immich = '', onferme } = $props()
  let grande = $state(null) // rang de la photo ouverte en grand
  let boite
  let depart = 0

  const titre = $derived(etape.nom || periode(etape.debut, etape.fin))
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
      <h2 class="text-xl font-semibold text-balance">{titre}</h2>
      <p class="text-sm text-muted-foreground">{etape.nom ? periode(etape.debut, etape.fin) + ' · ' : ''}{ageDit(etape.age)}{etape.age != null ? ' · ' : ''}{etape.photos.length} photo{etape.photos.length > 1 ? 's' : ''}</p>
    </div>
    <button type="button" class="rond" aria-label="Fermer l'étape" onclick={() => onferme?.()}><X class="size-5" aria-hidden="true" /></button>
  </header>
  <ul class="galerie" aria-label="Photos de l'étape">
    {#each etape.photos as p, i (p.id)}
      <li>
        <button type="button" onclick={() => (grande = i)} aria-label={'Photo ' + (i + 1) + (p.video ? ' (vidéo)' : '')}>
          <img src={'/api/vignette/' + p.id} alt="" loading="lazy" />
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
      {#key p.id}<img src={'/api/vignette/' + p.id + '?grande=true'} alt="" />{/key}
      <button type="button" class="rond fermer" aria-label="Fermer la photo" onclick={() => (grande = null)}><X class="size-5" aria-hidden="true" /></button>
      {#if etape.photos.length > 1}
        <button type="button" class="rond avant" aria-label="Photo précédente" onclick={() => aller(-1)}><ChevronLeft class="size-6" aria-hidden="true" /></button>
        <button type="button" class="rond apres" aria-label="Photo suivante" onclick={() => aller(1)}><ChevronRight class="size-6" aria-hidden="true" /></button>
      {/if}
      <p class="pied">
        {grande + 1} / {etape.photos.length}{p.video ? ' · vidéo (image seule ici)' : ''}
        {#if immich}· <a href={immich + '/photos/' + p.id} target="_blank" rel="noopener">Ouvrir dans Immich</a>{/if}
      </p>
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
  .plein img { max-width: 100%; max-height: 100dvh; object-fit: contain; }
  .plein .rond { position: absolute; background: rgb(0 0 0 / 0.55); color: #fff; border-color: rgb(255 255 255 / 0.2); }
  .fermer { top: calc(0.75rem + env(safe-area-inset-top, 0px)); right: max(0.75rem, env(safe-area-inset-right, 0px)); }
  .avant { left: max(0.75rem, env(safe-area-inset-left, 0px)); top: 50%; margin-top: -1.375rem; }
  .apres { right: max(0.75rem, env(safe-area-inset-right, 0px)); top: 50%; margin-top: -1.375rem; }
  .pied { position: absolute; bottom: calc(0.75rem + env(safe-area-inset-bottom, 0px)); left: 0; right: 0; margin: 0; text-align: center; font-size: 0.85rem; color: #d8d2c8; text-shadow: 0 1px 3px #000; }
  .pied a { color: #e3b556; text-decoration: underline; }
</style>
