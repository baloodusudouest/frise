<script>
  // 0.12 : toutes les photos de l'album d'une photo, dans Sillage (propriétaire ou invité).
  // charger() → { nom, photos: [{ id, video }], total } ; image(id, grande) → adresse de la vignette.
  // video(id) → adresse de lecture (propriétaire seulement) ; sans elle, une vidéo s'affiche en image.
  let { charger, image, video = null, onferme } = $props()
  let album = $state(null)
  let erreur = $state('')
  let vue = $state(null)       // index de la photo ouverte en grand dans l'album
  let depart = 0
  $effect(() => {
    charger().then((a) => (album = a), (x) => (erreur = x.message || 'Album illisible.'))
  })
  const aller = (pas) => (vue = (vue + pas + album.photos.length) % album.photos.length)
  function touche(ev) {
    if (ev.key === 'Escape') { ev.stopPropagation(); vue !== null ? (vue = null) : onferme?.() }
    else if (vue !== null && ev.key === 'ArrowRight') aller(1)
    else if (vue !== null && ev.key === 'ArrowLeft') aller(-1)
  }
</script>

<svelte:window onkeydown={touche} />

<div class="album" role="dialog" aria-modal="true" aria-label={album?.nom ? 'Album ' + album.nom : 'Album'}>
  <header>
    <div class="titre">
      <p class="sur">Album</p>
      <h2>{album ? album.nom || 'Sans nom' : 'Lecture…'}</h2>
      {#if album}<p class="compte">{album.photos.length} photo{album.photos.length > 1 ? 's' : ''}{album.total > album.photos.length ? ` sur ${album.total}` : ''}</p>{/if}
    </div>
    <button type="button" class="rond" aria-label="Fermer l'album" onclick={() => onferme?.()}>✕</button>
  </header>
  {#if erreur}<p class="vide" role="alert">{erreur}</p>
  {:else if album && !album.photos.length}<p class="vide">Cette photo n'est dans aucun album{album.nom ? ' où l\'on vous voit' : ''}.</p>
  {:else if album}
    <ul class="grille">
      {#each album.photos as p, i (p.id)}
        <li><button type="button" onclick={() => (vue = i)} aria-label={'Photo ' + (i + 1) + (p.video ? ' (vidéo)' : '')}>
          <img src={image(p.id, false)} alt="" loading="lazy" />{#if p.video}<span class="lecture" aria-hidden="true">▶</span>{/if}
        </button></li>
      {/each}
    </ul>
  {/if}

  {#if vue !== null && album}
    {@const p = album.photos[vue]}
    <div class="grand" role="group" aria-label={'Photo ' + (vue + 1) + ' sur ' + album.photos.length}
         ontouchstart={(e) => (depart = e.touches[0].clientX)}
         ontouchend={(e) => { const d = e.changedTouches[0].clientX - depart; if (Math.abs(d) > 50) aller(d < 0 ? 1 : -1) }}>
      {#key p.id}
        {#if p.video && video}<video src={video(p.id)} poster={image(p.id, true)} controls playsinline preload="metadata"></video>
        {:else}<img src={image(p.id, true)} alt="" />{/if}
      {/key}
      <button type="button" class="rond fermer" aria-label="Revenir à l'album" onclick={() => (vue = null)}>✕</button>
      {#if album.photos.length > 1}
        <button type="button" class="rond avant" aria-label="Photo précédente" onclick={() => aller(-1)}>‹</button>
        <button type="button" class="rond apres" aria-label="Photo suivante" onclick={() => aller(1)}>›</button>
      {/if}
      <p class="pied">{vue + 1} / {album.photos.length}</p>
    </div>
  {/if}
</div>

<style>
  .album { position: fixed; inset: 0; z-index: 60; overflow-y: auto; background: color-mix(in srgb, var(--background, #151311) 97%, transparent);
    padding: calc(1rem + env(safe-area-inset-top)) max(1rem, env(safe-area-inset-right)) calc(2rem + env(safe-area-inset-bottom)) max(1rem, env(safe-area-inset-left)); }
  header { display: flex; align-items: flex-start; gap: 1rem; max-width: 72rem; margin: 0 auto 1rem; }
  .titre { flex: 1; min-width: 0; }
  .sur { margin: 0; font-size: 0.75rem; letter-spacing: 0.08em; text-transform: uppercase; opacity: 0.7; }
  h2 { margin: 0.1rem 0 0; font-size: clamp(1.4rem, 4vw, 2rem); font-weight: 300; letter-spacing: -0.01em; overflow-wrap: anywhere; }
  .compte { margin: 0.2rem 0 0; font-size: 0.85rem; opacity: 0.7; }
  .grille { list-style: none; margin: 0 auto; padding: 0; max-width: 72rem; display: grid; gap: 4px; grid-template-columns: repeat(auto-fill, minmax(min(30vw, 9rem), 1fr)); }
  .grille button { position: relative; display: block; width: 100%; aspect-ratio: 1; padding: 0; border: 0; background: rgb(255 255 255 / 0.05); cursor: pointer; overflow: hidden; border-radius: 3px; }
  .grille img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .lecture { position: absolute; right: 6px; bottom: 4px; color: #fff; text-shadow: 0 1px 3px #000; font-size: 0.85rem; }
  .vide { max-width: 72rem; margin: 2rem auto; opacity: 0.8; }
  .rond { display: grid; place-items: center; width: 2.75rem; height: 2.75rem; flex: none; border-radius: 999px; border: 1px solid rgb(255 255 255 / 0.2);
    background: rgb(0 0 0 / 0.45); color: #fff; font-size: 1.2rem; cursor: pointer; }
  .grand { position: fixed; inset: 0; z-index: 61; display: grid; place-items: center; background: #000; }
  .grand img, .grand video { max-width: 100vw; max-height: 100dvh; object-fit: contain; }
  .grand .fermer { position: absolute; top: calc(0.75rem + env(safe-area-inset-top)); right: max(0.75rem, env(safe-area-inset-right)); }
  .grand .avant, .grand .apres { position: absolute; top: 50%; transform: translateY(-50%); font-size: 1.8rem; }
  .grand .avant { left: max(0.5rem, env(safe-area-inset-left)); }
  .grand .apres { right: max(0.5rem, env(safe-area-inset-right)); }
  .pied { position: absolute; bottom: calc(0.75rem + env(safe-area-inset-bottom)); left: 0; right: 0; text-align: center; color: #fff; opacity: 0.8; font-size: 0.85rem; margin: 0; }
</style>
