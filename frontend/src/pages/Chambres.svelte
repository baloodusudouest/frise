<script>
  // 0.6 : les pages que Home Assistant a préparées pour les chambres (séjour programmé ou en cours).
  // Lecture seule : c'est HA qui les crée et les retire. L'aperçu est la page même que verront les invités.
  import { onMount } from 'svelte'
  import BedDouble from '@lucide/svelte/icons/bed-double'
  import { api } from '$lib/api.js'
  import { periode } from '$lib/dates.js'
  import Invite from './Invite.svelte'

  let { ondeconnecte } = $props()
  let liste = $state(null)
  let erreur = $state('')
  let rang = $state(0)
  const vue = $derived(liste?.[Math.min(rang, liste.length - 1)] || null)
  const nomChambre = (c) => 'Chambre ' + c.charAt(0).toUpperCase() + c.slice(1)
  const et = (noms) => (noms.length < 2 ? noms.join('') : noms.slice(0, -1).join(', ') + ' et ' + noms.at(-1))
  const quand = (c) => (c.du ? periode(c.du, c.au) : `jusqu'au ${periode(c.au)}`)

  onMount(async () => {
    try { liste = (await api.get('/api/chambres')).chambres }
    catch (err) { if (err.statut === 401) ondeconnecte?.(); else erreur = 'Sillage ne répond pas pour l\'instant.' }
  })
</script>

<header class="mb-5">
  <p class="etiquette">Sillage</p>
  <h1 class="titre">Chambres</h1>
</header>

{#if erreur}
  <p class="text-sm text-destructive" role="alert">{erreur}</p>
{:else if !liste}
  <p class="text-sm text-muted-foreground" role="status">Lecture…</p>
{:else if !liste.length}
  <div class="vide">
    <BedDouble class="size-8 text-muted-foreground" aria-hidden="true" />
    <p>Aucun invité programmé dans les chambres.</p>
    <p class="text-sm text-muted-foreground">Home Assistant prépare la page d'une chambre dès qu'un séjour y est programmé ; elle apparaîtra ici.</p>
  </div>
{:else}
  {#if liste.length > 1}
    <div class="choix" role="group" aria-label="Chambre">
      {#each liste as c, i}
        <button type="button" aria-pressed={i === rang} onclick={() => (rang = i)}>{nomChambre(c.chambre)}</button>
      {/each}
    </div>
  {/if}
  <section class="fiche" aria-label={nomChambre(vue.chambre)}>
    <h2 class="flex items-center gap-2 text-lg font-semibold"><BedDouble class="size-5 text-primary" aria-hidden="true" />{nomChambre(vue.chambre)}</h2>
    <p class="mt-1 text-sm">{et(vue.noms)} · {quand(vue)}</p>
    {#if vue.introuvables.length}
      <p class="mt-1 text-sm text-destructive">{et(vue.introuvables)} : pas de personne de ce nom dans Immich. Le nom doit s'écrire comme dans Immich, ou la personne a un homonyme.</p>
    {/if}
    <p class="mt-2 text-xs text-muted-foreground">Ce qu'affichera le tableau de bord de la chambre. Lecture seule : Home Assistant crée et retire cette page.</p>
  </section>
  {#key vue.jeton}
    <div class="apercu"><Invite jeton={vue.jeton} apercu /></div>
  {/key}
{/if}

<style>
  .vide { display: grid; justify-items: center; gap: 0.5rem; padding: 3rem 1rem; text-align: center; border: 1px dashed var(--border); border-radius: 1.1rem; }
  .vide p { margin: 0; max-width: 40ch; }
  .choix { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 1rem; }
  .choix button { min-height: 2.75rem; padding: 0 1rem; border-radius: 999px; border: 1px solid var(--border); background: var(--card); font-size: 0.95rem; }
  .choix button[aria-pressed='true'] { background: var(--foreground); color: var(--background); font-weight: 600; }
  .fiche { padding: 1rem 1.25rem; border: 1px solid var(--border); border-radius: 1.1rem; background: var(--card); margin-bottom: 1.25rem; }
  .apercu { padding-top: 0.5rem; }
</style>
