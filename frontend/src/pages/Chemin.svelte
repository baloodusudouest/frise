<script>
  // Le chemin d'une personne : un chapitre par décennie d'âge, les étapes posées le long du trait.
  // Sur PC les étapes alternent de part et d'autre du trait ; sur iPhone elles sont d'un seul côté.
  import { onMount } from 'svelte'
  import ArrowLeft from '@lucide/svelte/icons/arrow-left'
  import RefreshCw from '@lucide/svelte/icons/refresh-cw'
  import { api } from '$lib/api.js'
  import { Button } from '$lib/components/ui/button/index.js'
  import { ageDit, dateLongue, periode } from '$lib/dates.js'
  import Etape from '$lib/Etape.svelte'

  let { id, ondeconnecte } = $props()
  let chemin = $state(null)
  let erreur = $state('')
  let lecture = $state(false)
  let tout = $state(false)
  let ouverte = $state(null)

  const forts = $derived(chemin ? chemin.chapitres.reduce((n, c) => n + c.etapes.filter((e) => e.temps_fort).length, 0) : 0)
  // Sans aucun temps fort reconnu, on montre tout : un chemin vide ne dit rien.
  const filtre = $derived(!tout && forts > 0)
  const chapitres = $derived.by(() => {
    if (!chemin) return []
    let rang = 0
    return chemin.chapitres
      .map((c) => ({ ...c, etapes: c.etapes.filter((e) => !filtre || e.temps_fort).map((e) => ({ ...e, cote: rang++ % 2 ? 'droite' : 'gauche' })) }))
      .filter((c) => c.etapes.length)
  })

  async function lire(frais = false) {
    lecture = true
    erreur = ''
    try { chemin = await api.get(`/api/chemin/${id}${frais ? '?frais=true' : ''}`) }
    catch (err) { if (err.statut === 401) ondeconnecte?.(); else erreur = err.message }
    lecture = false
  }
  onMount(() => lire())
</script>

<a href="#/sillages" class="mb-4 inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground">
  <ArrowLeft class="size-4" aria-hidden="true" />Tous les sillages
</a>

{#if erreur}
  <p class="rounded-2xl border border-destructive/50 p-4 text-sm" role="alert">{erreur}</p>
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
      <Button variant="outline" size="icon" aria-label="Relire dans Immich" disabled={lecture} onclick={() => lire(true)}>
        <RefreshCw class={'size-4 ' + (lecture ? 'animate-spin' : '')} aria-hidden="true" />
      </Button>
    </div>
  </header>

  {#if !chemin.etapes}
    <p class="rounded-2xl border bg-card p-5 text-sm text-muted-foreground">Aucune photo datée de cette personne dans Immich pour l'instant.</p>
  {/if}

  <div class="chemin">
    {#each chapitres as c (c.cle)}
      <section aria-label={c.titre}>
        <h2 class="chapitre"><span>{c.titre}</span></h2>
        <ol>
          {#each c.etapes as e (e.cle)}
            <li class="etape {e.cote}" class:petite={e.nombre === 1 && !e.nom}>
              <span class="point" class:fort={e.temps_fort} aria-hidden="true"></span>
              <button type="button" class="carte" onclick={() => (ouverte = e)} aria-label={(e.nom || periode(e.debut, e.fin)) + ', ' + e.nombre + ' photo' + (e.nombre > 1 ? 's' : '')}>
                <img src={'/api/vignette/' + e.phare} alt="" loading="lazy" />
                <span class="dit">
                  <strong>{e.nom || periode(e.debut, e.fin)}</strong>
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

{#if ouverte}
  <Etape etape={ouverte} immich={chemin.immich} onferme={() => (ouverte = null)} />
{/if}

<style>
  .chemin { position: relative; --trait: 1.25rem; }
  .chemin::before { content: ""; position: absolute; top: 0; bottom: 0; left: var(--trait); width: 3px; margin-left: -1.5px; border-radius: 3px;
                    background: linear-gradient(var(--app), color-mix(in oklab, var(--app) 35%, transparent)); }
  ol { list-style: none; margin: 0; padding: 0; display: grid; gap: 1rem; }
  section + section { margin-top: 2rem; }
  .chapitre { position: sticky; top: env(safe-area-inset-top, 0px); z-index: 5; margin: 0 0 1rem; padding: 0.5rem 0 0.5rem calc(var(--trait) * 2 + 0.25rem); background: linear-gradient(var(--background) 70%, transparent); }
  .chapitre span { font-size: 1.9rem; font-weight: 300; letter-spacing: -0.035em; line-height: 1; color: var(--app); }
  .etape { position: relative; padding-left: calc(var(--trait) * 2 + 0.25rem); min-width: 0; }
  .point { position: absolute; left: var(--trait); top: 1.6rem; width: 0.7rem; height: 0.7rem; margin-left: -0.35rem; border-radius: 50%; background: var(--background); border: 2px solid var(--app); }
  .point.fort { background: var(--app); width: 0.95rem; height: 0.95rem; margin-left: -0.475rem; }
  .carte { display: flex; flex-direction: column; width: 100%; max-width: 26rem; overflow: hidden; text-align: left; border: 1px solid var(--border); border-radius: 1.1rem; background: var(--card); transition: border-color 0.2s, transform 0.2s; }
  .carte:hover { border-color: var(--app); transform: translateY(-2px); }
  .carte img { width: 100%; aspect-ratio: 4 / 3; object-fit: cover; background: var(--secondary); }
  .dit { display: grid; gap: 0.15rem; padding: 0.7rem 0.9rem 0.8rem; min-width: 0; }
  .dit strong { font-weight: 600; text-wrap: balance; }
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
