<script>
  // 0.5 : le chemin montré à un invité des chambres, ouvert par l'adresse à jeton que Home Assistant a demandée.
  // Ni mot de passe, ni corrections, ni lien vers Immich : la photo phare de chaque étape, et rien d'autre.
  // Deux invités : leur chemin commun (par décennie) ; sans photo ensemble, le chemin de chacun.
  import { onMount } from 'svelte'
  import { periode } from '$lib/dates.js'

  // apercu (0.6) : la même page, montrée au propriétaire dans l'onglet « Chambres »
  let { jeton, apercu = false } = $props()
  let d = $state(null)
  let erreur = $state('')
  let tout = $state(false)
  let rang = $state(0)

  const chemins = $derived(d ? (d.commun ? [d.commun] : d.chacun) : [])
  const vu = $derived(chemins[Math.min(rang, chemins.length - 1)] || null)
  const forts = $derived(vu ? vu.chapitres.reduce((n, c) => n + c.etapes.filter((e) => e.temps_fort).length, 0) : 0)
  const chapitres = $derived.by(() => {
    if (!vu) return []
    let i = 0
    return vu.chapitres
      .map((c) => ({ ...c, etapes: c.etapes.filter((e) => tout || !forts || e.temps_fort).map((e) => ({ ...e, cote: i++ % 2 ? 'droite' : 'gauche' })) }))
      .filter((c) => c.etapes.length)
  })
  const ageDit = (a) => (a == null ? '' : a === 0 ? 'avant 1 an' : a === 1 ? 'à 1 an' : `à ${a} ans`)
  const prenoms = (noms) => noms.length < 2 ? noms.join('') : noms.slice(0, -1).join(', ') + ' et ' + noms.at(-1)

  // Le trait se remplit à mesure qu'on descend, les étapes apparaissent en entrant dans l'écran.
  let boite = $state(null)
  let avancee = $state(0)
  function mesurer() {
    if (!boite) return
    const r = boite.getBoundingClientRect()
    avancee = Math.max(0, Math.min(1, (innerHeight * 0.72 - r.top) / Math.max(r.height, 1)))
  }
  function apparait(noeud) {
    if (!('IntersectionObserver' in window) || matchMedia('(prefers-reduced-motion: reduce)').matches) { noeud.classList.add('vue'); return }
    const o = new IntersectionObserver((vus) => vus.forEach((v) => { if (v.isIntersecting) { v.target.classList.add('vue'); o.unobserve(v.target) } }), { rootMargin: '0px 0px -8% 0px' })
    o.observe(noeud)
    return { destroy: () => o.disconnect() }
  }
  $effect(() => { chapitres; requestAnimationFrame(mesurer) })

  onMount(async () => {
    try {
      const r = await fetch(`/api/invite/${encodeURIComponent(jeton)}`)
      if (!r.ok) throw new Error(r.status === 404 ? 'Cette page n\'est plus valable : le séjour est terminé, ou le lien a changé.' : 'Sillage ne répond pas pour l\'instant.')
      d = await r.json()
    } catch (e) { erreur = e.message }
  })
</script>

<svelte:window onscroll={mesurer} onresize={mesurer} />

<svelte:element this={apercu ? 'div' : 'main'} class={apercu ? '' : 'mx-auto max-w-5xl px-[max(1rem,env(safe-area-inset-left))] pt-[calc(1.25rem+env(safe-area-inset-top))] pb-[calc(2rem+env(safe-area-inset-bottom))]'}>
  {#if erreur}
    <div class="accueil" role="alert"><h1 class="plume">Sillage</h1><p>{erreur}</p></div>
  {:else if !d}
    <p class="text-sm text-muted-foreground" role="status">Un instant…</p>
  {:else if d.accueil}
    <div class="accueil">
      <h1 class="plume">Bienvenue{d.invites.length ? ' ' + prenoms(d.invites) : ''}</h1>
      <p>Pas encore de souvenirs ici : les photos du séjour viendront.</p>
    </div>
  {:else}
    <header class="mb-5">
      <p class="etiquette">{d.commun ? 'Votre chemin ensemble' : chemins.length > 1 ? 'Vos chemins' : 'Votre chemin'}</p>
      <h1 class="plume text-[2.8rem] leading-none text-balance">{vu.nom}</h1>
    </header>

    {#if chemins.length > 1}
      <div class="onglets" role="group" aria-label="Chemin de">
        {#each chemins as c, i}<button type="button" aria-pressed={i === rang} onclick={() => (rang = i)}>{c.nom}</button>{/each}
      </div>
    {/if}
    {#if forts > 0 && forts < vu.etapes}
      <div class="onglets" role="group" aria-label="Ce que le chemin montre">
        <button type="button" aria-pressed={!tout} onclick={() => (tout = false)}>Temps forts</button>
        <button type="button" aria-pressed={tout} onclick={() => (tout = true)}>Tout</button>
      </div>
    {/if}

    {#key vu.nom}
      <div class="chemin" bind:this={boite} style:--avancee={avancee}>
        {#each chapitres as c (c.cle)}
          <section aria-label={c.titre}>
            <h2 class="chapitre"><span>{c.titre}</span></h2>
            <ol>
              {#each c.etapes as e (e.cle)}
                <li class="etape {e.cote}" class:petite={e.nombre === 1 && !e.nom} use:apparait>
                  <span class="point" class:fort={e.temps_fort} aria-hidden="true"></span>
                  <div class="carte">
                    <img src={`/api/invite/${encodeURIComponent(jeton)}/vignette/${e.phare}`} alt="" loading="lazy" />
                    <span class="dit">
                      <strong class:plume={!!e.nom}>{e.nom || periode(e.debut, e.fin)}</strong>
                      <small>{e.nom ? periode(e.debut, e.fin) : ''}{e.nom && e.age != null ? ' · ' : ''}{ageDit(e.age)}{e.nombre > 1 ? (e.nom || e.age != null ? ' · ' : '') + e.nombre + ' photos' : ''}</small>
                    </span>
                  </div>
                </li>
              {/each}
            </ol>
          </section>
        {/each}
      </div>
    {/key}
  {/if}
</svelte:element>

<style>
  .chemin { position: relative; --trait: 1.25rem; }
  .chemin::before { content: ""; position: absolute; top: 0; bottom: 0; left: var(--trait); width: 3px; margin-left: -1.5px; border-radius: 3px;
                    background: color-mix(in oklab, var(--app) 22%, transparent); }
  /* Le trait plein : il descend avec la lecture */
  .chemin::after { content: ""; position: absolute; top: 0; bottom: 0; left: var(--trait); width: 3px; margin-left: -1.5px; border-radius: 3px;
                   background: var(--app); transform-origin: top; transform: scaleY(var(--avancee, 1)); transition: transform 0.25s ease-out; }
  .etape { opacity: 0; translate: 0 14px; transition: opacity 0.45s ease, translate 0.45s cubic-bezier(0.2, 0.8, 0.2, 1); }
  .etape:global(.vue) { opacity: 1; translate: 0 0; }
  @media (prefers-reduced-motion: reduce) { .chemin::after { transition: none; transform: none; } .etape { opacity: 1; translate: 0 0; transition: none; } }
  ol { list-style: none; margin: 0; padding: 0; display: grid; gap: 1rem; }
  section + section { margin-top: 2rem; }
  .chapitre { position: sticky; top: env(safe-area-inset-top, 0px); z-index: 5; margin: 0 0 1rem; padding: 0.5rem 0 0.5rem calc(var(--trait) * 2 + 0.25rem); background: linear-gradient(var(--background) 70%, transparent); }
  .chapitre span { font-size: 1.9rem; font-weight: 300; letter-spacing: -0.035em; line-height: 1; color: var(--app); }
  .etape { position: relative; padding-left: calc(var(--trait) * 2 + 0.25rem); min-width: 0; }
  .point { z-index: 1; position: absolute; left: var(--trait); top: 1.6rem; width: 0.7rem; height: 0.7rem; margin-left: -0.35rem; border-radius: 50%; background: var(--background); border: 2px solid var(--app); }
  .point.fort { background: var(--app); width: 0.95rem; height: 0.95rem; margin-left: -0.475rem; }
  .carte { display: flex; flex-direction: column; width: 100%; max-width: 26rem; overflow: hidden; text-align: left; border: 1px solid var(--border); border-radius: 1.1rem; background: var(--card); transition: border-color 0.2s, transform 0.2s; }
  .carte img { width: 100%; aspect-ratio: 4 / 3; object-fit: cover; background: var(--secondary); }
  .dit { display: grid; gap: 0.15rem; padding: 0.7rem 0.9rem 0.8rem; min-width: 0; }
  .dit strong { font-weight: 600; text-wrap: balance; }
  .dit strong:global(.plume) { font-size: 2.3rem; padding-top: 0.1rem; }
  .petite .dit strong:global(.plume) { font-size: 1.9rem; }
  .dit small { font-size: 0.82rem; color: var(--muted-foreground); }
  /* Une photo isolée, sans nom : une simple ligne sur le trait */
  .petite .carte { flex-direction: row; align-items: center; max-width: 22rem; border-radius: 0.9rem; }
  .petite .carte img { width: 4rem; flex: none; aspect-ratio: 1; }
  .petite .point { top: 1.65rem; }
  .petite .dit strong { font-weight: 500; }

  @media (min-width: 768px) {
    .chemin { --trait: 50%; }
    .chapitre { padding-left: 0; text-align: center; }
    .chapitre span { background: var(--background); padding: 0 0.75rem; }
    .etape { padding-left: 0; width: calc(50% - 2rem); }
    .etape.droite { margin-left: calc(50% + 2rem); }
    .etape.gauche .carte { margin-left: auto; }
    .etape.gauche .point { left: calc(100% + 2rem); }
    .etape.droite .point { left: -2rem; }
    ol { gap: 0; }
    .etape + .etape { margin-top: -2.5rem; }
    .etape.petite + .etape, .etape + .etape.petite { margin-top: 0.75rem; }
  }
  .onglets { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 1.25rem; }
  .onglets button { min-height: 2.75rem; padding: 0 1rem; border-radius: 999px; border: 1px solid var(--border); background: var(--card); font-size: 0.95rem; }
  .onglets button[aria-pressed='true'] { background: var(--app); border-color: var(--app); color: var(--app-contraste); font-weight: 600; }
  .accueil { min-height: 40dvh; display: grid; place-content: center; gap: 0.75rem; text-align: center; padding: 2rem 1rem; }
  .accueil h1 { font-size: 3.4rem; margin: 0; }
  .accueil p { margin: 0; max-width: 34ch; color: var(--muted-foreground); }
</style>
