<script>
  // L'écran d'ouverture : les personnes nommées d'Immich. Toucher une personne ouvre son chemin.
  import { onMount } from 'svelte'
  import Search from '@lucide/svelte/icons/search'
  import { api } from '$lib/api.js'

  let { ondeconnecte } = $props()
  let personnes = $state(null)
  let erreur = $state('')
  let cherche = $state('')

  const plat = (t) => t.toLowerCase().normalize('NFD').replace(/\p{Mn}/gu, '')
  const montrees = $derived((personnes || []).filter((p) => plat(p.nom).includes(plat(cherche.trim()))))

  onMount(async () => {
    try { personnes = (await api.get('/api/personnes')).personnes }
    catch (err) { if (err.statut === 401) ondeconnecte?.(); else erreur = err.message }
  })
</script>

<header class="mb-5 flex flex-wrap items-end justify-between gap-3">
  <div>
    <p class="etiquette">Sillage</p>
    <h1 class="titre">Sillages</h1>
  </div>
  <label class="relative w-full sm:w-64">
    <span class="sr-only">Chercher une personne</span>
    <Search class="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
    <input type="search" bind:value={cherche} placeholder="Chercher une personne"
           class="h-10 w-full rounded-lg border border-input bg-transparent pr-3 pl-9 text-base outline-none focus:border-ring" />
  </label>
</header>

{#if erreur}
  <p class="rounded-2xl border border-destructive/50 p-4 text-sm" role="alert">{erreur}</p>
{:else if personnes === null}
  <p class="text-sm text-muted-foreground" role="status">Lecture des personnes dans Immich…</p>
{:else if !personnes.length}
  <p class="rounded-2xl border bg-card p-5 text-sm text-muted-foreground">Immich ne connaît encore aucune personne nommée. Donne un nom à un visage dans Immich : il apparaîtra ici.</p>
{:else}
  <ul class="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4" aria-label="Personnes">
    {#each montrees as p (p.id)}
      <li>
        <a href={'#/chemin/' + p.id} class="flex h-full flex-col items-center gap-2 rounded-2xl border bg-card p-4 text-center transition-colors hover:border-primary">
          <img src={'/api/portrait/' + p.id} alt="" loading="lazy" class="size-20 rounded-full bg-secondary object-cover" />
          <span class="font-medium text-balance">{p.nom}</span>
          <span class="text-sm text-muted-foreground">{p.age != null ? p.age + ' ans' : 'date de naissance inconnue'}</span>
        </a>
      </li>
    {/each}
  </ul>
  {#if !montrees.length}<p class="text-sm text-muted-foreground">Personne ne porte ce nom.</p>{/if}
{/if}
