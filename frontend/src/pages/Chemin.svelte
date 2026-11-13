<script>
  // Le chemin d'une personne : un chapitre par décennie d'âge, les étapes posées le long du trait.
  // Sur PC les étapes alternent de part et d'autre du trait ; sur iPhone elles sont d'un seul côté.
  import { onMount } from 'svelte'
  import ArrowLeft from '@lucide/svelte/icons/arrow-left'
  import RefreshCw from '@lucide/svelte/icons/refresh-cw'
  import BookOpen from '@lucide/svelte/icons/book-open'
  import EyeOff from '@lucide/svelte/icons/eye-off'
  import { api } from '$lib/api.js'
  import { Button } from '$lib/components/ui/button/index.js'
  import { ageDit, dateLongue, periode } from '$lib/dates.js'
  import Etape from '$lib/Etape.svelte'

  let { id, ondeconnecte } = $props()
  let chemin = $state(null)
  let erreur = $state('')
  let lecture = $state(false)
  let tout = $state(false)
  let ouverte = $state(null)          // clé de l'étape ouverte
  let masquees = $state(false)        // montrer aussi les étapes masquées
  let deCote = $state(false)          // montrer les photos mises de côté

  const visibles = (c) => c.etapes.filter((e) => masquees || !e.masquee)
  const forts = $derived(chemin ? chemin.chapitres.reduce((n, c) => n + visibles(c).filter((e) => e.temps_fort).length, 0) : 0)
  // Sans aucun temps fort reconnu, on montre tout : un chemin vide ne dit rien.
  const filtre = $derived(!tout && forts > 0)
  const chapitres = $derived.by(() => {
    if (!chemin) return []
    let rang = 0
    return chemin.chapitres
      .map((c) => ({ ...c, etapes: visibles(c).filter((e) => !filtre || e.temps_fort).map((e) => ({ ...e, cote: rang++ % 2 ? 'droite' : 'gauche' })) }))
      .filter((c) => c.etapes.length)
  })
  const etapeOuverte = $derived(ouverte && chemin ? chemin.chapitres.flatMap((c) => c.etapes).find((e) => e.cle === ouverte) || null : null)

  // Une correction : le serveur rend le chemin recalculé. Rien n'est écrit dans Immich.
  async function corriger(corps) {
    erreur = ''
    try {
      const avant = etapeOuverte
      chemin = await api.post(`/api/chemin/${id}/marque`, corps)
      // L'étape ouverte peut avoir changé de clé (sa première photo retirée) : on la retrouve par une photo restante.
      if (avant && !chemin.chapitres.flatMap((c) => c.etapes).some((e) => e.cle === ouverte)) {
        const restantes = new Set(avant.photos.map((p) => p.id))
        ouverte = chemin.chapitres.flatMap((c) => c.etapes).find((e) => e.photos.some((p) => restantes.has(p.id)))?.cle ?? null
      }
    } catch (err) { if (err.statut === 401) ondeconnecte?.(); else erreur = err.message }
  }

  // Le trait se dessine à mesure qu'on descend ; les étapes apparaissent en entrant dans l'écran.
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

  async function lire(frais = false) {
    lecture = true
    erreur = ''
    try { chemin = await api.get(`/api/chemin/${id}${frais ? '?frais=true' : ''}`) }
    catch (err) { if (err.statut === 401) ondeconnecte?.(); else erreur = err.message }
    lecture = false
  }
  onMount(() => lire())
</script>

<svelte:window onscroll={mesurer} onresize={mesurer} />

<a href="#/sillages" class="mb-4 inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground">
  <ArrowLeft class="size-4" aria-hidden="true" />Tous les sillages
</a>

{#if erreur}
  <p class="mb-4 rounded-2xl border border-destructive/50 p-4 text-sm" role="alert">{erreur}</p>
{/if}
{#if erreur && !chemin}
  <span></span>
{:else if !chemin}
  <p class="text-sm text-muted-foreground" role="status">Lecture des photos dans Immich… Pour une personne très photographiée, cela prend quelques secondes.</p>
{:else}
  <header class="mb-6 flex flex-wrap items-center gap-4">
    <img src={'/api/portrait/' + id} alt="" class="size-20 rounded-full bg-secondary object-cover" />
    <div class="min-w-0 flex-1">
      <p class="etiquette">Sillage</p>
      <h1 class="titre text-balance">{chemin.personne.nom}</h1>
      <p class="mt-1 text-sm text-muted-foreground">
        {chemin.personne.naissance ? 'Naissance le ' + dateLongue(chemin.personne.naissance) + ' · ' : ''}{chemin.etapes} étape{chemin.etapes > 1 ? 's' : ''}, {chemin.photos} photo{chemin.photos > 1 ? 's' : ''}
      </p>
    </div>
    <div class="flex w-full items-center gap-2 sm:w-auto">
      {#if forts > 0}
        <div class="flex rounded-full border p-1" role="group" aria-label="Ce que le chemin montre">
          <button type="button" aria-pressed={!tout} onclick={() => (tout = false)} class="h-8 rounded-full px-3 text-sm aria-pressed:bg-primary aria-pressed:text-primary-foreground">Temps forts</button>
          <button type="button" aria-pressed={tout} onclick={() => (tout = true)} class="h-8 rounded-full px-3 text-sm aria-pressed:bg-primary aria-pressed:text-primary-foreground">Tout</button>
        </div>
      {/if}
      <Button variant="outline" href={'#/recit/' + id}><BookOpen class="size-4" aria-hidden="true" />Raconter</Button>
      <Button variant="outline" size="icon" aria-label="Relire dans Immich" disabled={lecture} onclick={() => lire(true)}>
        <RefreshCw class={'size-4 ' + (lecture ? 'animate-spin' : '')} aria-hidden="true" />
      </Button>
    </div>
  </header>

  {#if !chemin.etapes}
    <p class="rounded-2xl border bg-card p-5 text-sm text-muted-foreground">Aucune photo datée de cette personne dans Immich pour l'instant.</p>
  {/if}

  <div class="chemin" bind:this={boite} style:--avancee={avancee}>
    {#each chapitres as c (c.cle)}
      <section aria-label={c.titre}>
        <h2 class="chapitre"><span>{c.titre}</span></h2>
        <ol>
          {#each c.etapes as e (e.cle)}
            <li class="etape {e.cote}" class:petite={e.nombre === 1 && !e.nom} class:masquee={e.masquee} use:apparait>
              <span class="point" class:fort={e.temps_fort} aria-hidden="true"></span>
              <button type="button" class="carte" onclick={() => (ouverte = e.cle)} aria-label={(e.nom || periode(e.debut, e.fin)) + ', ' + e.nombre + ' photo' + (e.nombre > 1 ? 's' : '')}>
                <img src={'/api/vignette/' + e.phare} alt="" loading="lazy" />
                <span class="dit">
                  <strong class:plume={!!e.nom}>{#if e.masquee}<EyeOff class="mr-1 inline size-4 align-[-2px]" aria-label="Masquée" />{/if}{e.nom || periode(e.debut, e.fin)}</strong>
                  <small>{e.nom ? periode(e.debut, e.fin) + ' · ' : ''}{ageDit(e.age)}{e.age != null && e.nombre > 1 ? ' · ' : ''}{e.nombre > 1 ? e.nombre + ' photos' : ''}</small>
                </span>
              </button>
            </li>
          {/each}
        </ol>
      </section>
    {/each}
  </div>

  {#if chemin.ecartees.avant_naissance || chemin.ecartees.sans_date}
    <p class="mt-8 rounded-2xl border bg-card p-4 text-sm text-muted-foreground" role="note">
      Laissées hors du chemin :
      {#if chemin.ecartees.avant_naissance}{chemin.ecartees.avant_naissance} photo{chemin.ecartees.avant_naissance > 1 ? 's datées' : ' datée'} d'avant sa naissance{chemin.ecartees.sans_date ? ', ' : '.'}{/if}
      {#if chemin.ecartees.sans_date}{chemin.ecartees.sans_date} sans date lisible.{/if}
      Leur date est sans doute à corriger dans Immich ou dans Millésime.
    </p>
  {/if}
{/if}

{#if chemin && (chemin.masquees || chemin.de_cote.length)}
  <section class="mt-8 rounded-2xl border bg-card p-4 text-sm" aria-label="Corrections">
    <h2 class="etiquette mb-2">Tes corrections</h2>
    <div class="flex flex-wrap gap-2">
      {#if chemin.masquees}
        <Button variant="outline" aria-pressed={masquees} onclick={() => (masquees = !masquees)}>{masquees ? 'Cacher' : 'Afficher'} {chemin.masquees} étape{chemin.masquees > 1 ? 's masquées' : ' masquée'}</Button>
      {/if}
      {#if chemin.de_cote.length}
        <Button variant="outline" aria-pressed={deCote} onclick={() => (deCote = !deCote)}>{deCote ? 'Cacher' : 'Afficher'} {chemin.de_cote.length} photo{chemin.de_cote.length > 1 ? 's mises' : ' mise'} de côté</Button>
      {/if}
    </div>
    {#if deCote && chemin.de_cote.length}
      <ul class="cote" aria-label="Photos mises de côté">
        {#each chemin.de_cote as p (p.id)}
          <li>
            <img src={'/api/vignette/' + p.id} alt="" loading="lazy" />
            <span>{p.sorte === 'pas_elle' ? 'Pas cette personne' : 'Retirée du chemin'}</span>
            <Button variant="outline" size="sm" onclick={() => corriger({ sorte: p.sorte, effacer: [p.id] })}>Remettre</Button>
          </li>
        {/each}
      </ul>
    {/if}
    <p class="mt-3 text-muted-foreground">Ces corrections sont gardées dans Sillage. Rien n'est changé dans Immich.</p>
  </section>
{/if}

{#if etapeOuverte}
  <Etape etape={etapeOuverte} immich={chemin.immich} portImmich={chemin.immich_port} oncorrige={corriger} onferme={() => (ouverte = null)} />
{/if}

<style>
  .chemin { position: relative; --trait: 1.25rem; }
  .chemin::before { content: ""; position: absolute; top: 0; bottom: 0; left: var(--trait); width: 3px; margin-left: -1.5px; border-radius: 3px;
                    background: color-mix(in oklab, var(--app) 22%, transparent); }
  /* Le trait plein : il descend avec la lecture */
  .chemin::after { content: ""; position: absolute; top: 0; bottom: 0; left: var(--trait); width: 3px; margin-left: -1.5px; border-radius: 3px;
                   background: var(--app); transform-origin: top; transform: scaleY(var(--avancee, 1)); transition: transform 0.25s ease-out; }
  .etape { opacity: 0; translate: 0 14px; transition: opacity 0.45s ease, translate 0.45s cubic-bezier(0.2, 0.8, 0.2, 1); }
  .etape:global(.vue) { opacity: 1; translate: 0 0; }
  .etape.masquee .carte { opacity: 0.55; border-style: dashed; }
  .cote { list-style: none; margin: 0.9rem 0 0; padding: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(8.5rem, 1fr)); gap: 0.6rem; }
  .cote li { display: grid; gap: 0.35rem; justify-items: start; min-width: 0; }
  .cote img { width: 100%; aspect-ratio: 1; object-fit: cover; border-radius: 0.6rem; background: var(--secondary); }
  .cote span { font-size: 0.8rem; color: var(--muted-foreground); }
  @media (prefers-reduced-motion: reduce) { .chemin::after { transition: none; transform: none; } .etape { opacity: 1; translate: 0 0; transition: none; } }
  ol { list-style: none; margin: 0; padding: 0; display: grid; gap: 1rem; }
  section + section { margin-top: 2rem; }
  .chapitre { position: sticky; top: env(safe-area-inset-top, 0px); z-index: 5; margin: 0 0 1rem; padding: 0.5rem 0 0.5rem calc(var(--trait) * 2 + 0.25rem); background: linear-gradient(var(--background) 70%, transparent); }
  .chapitre span { font-size: 1.9rem; font-weight: 300; letter-spacing: -0.035em; line-height: 1; color: var(--app); }
  .etape { position: relative; padding-left: calc(var(--trait) * 2 + 0.25rem); min-width: 0; }
  .point { z-index: 1; position: absolute; left: var(--trait); top: 1.6rem; width: 0.7rem; height: 0.7rem; margin-left: -0.35rem; border-radius: 50%; background: var(--background); border: 2px solid var(--app); }
  .point.fort { background: var(--app); width: 0.95rem; height: 0.95rem; margin-left: -0.475rem; }
  .carte { display: flex; flex-direction: column; width: 100%; max-width: 26rem; overflow: hidden; text-align: left; border: 1px solid var(--border); border-radius: 1.1rem; background: var(--card); transition: border-color 0.2s, transform 0.2s; }
  .carte:hover { border-color: var(--app); transform: translateY(-2px); }
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
</style>
