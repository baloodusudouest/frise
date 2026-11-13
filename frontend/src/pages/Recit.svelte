<script>
  // « Raconter » : le récit du chemin, proposé par Sillage à partir des étapes visibles, relu et corrigé ici.
  import { onMount } from 'svelte'
  import ArrowLeft from '@lucide/svelte/icons/arrow-left'
  import { api } from '$lib/api.js'
  import { Button } from '$lib/components/ui/button/index.js'

  let { id, ondeconnecte } = $props()
  let recit = $state(null)
  let texte = $state('')
  let erreur = $state('')
  let dit = $state('')
  let zone

  const change = $derived(recit !== null && texte !== recit.texte)
  const prendre = (r) => { recit = r; texte = r.texte }
  const quand = (iso) => new Date(iso).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })

  async function appel(faire, apres = '') {
    erreur = ''
    try { prendre(await faire()); dit = apres } catch (err) { if (err.statut === 401) ondeconnecte?.(); else erreur = err.message }
  }
  const garder = () => appel(() => api.put('/api/recit/' + id, { texte }), 'Récit gardé.')
  const repartir = () => appel(() => api.put('/api/recit/' + id, { texte: null }), 'Récit refait depuis le chemin.')
  async function copier() {
    try { await navigator.clipboard.writeText(texte); dit = 'Copié.' }
    catch { zone?.select(); dit = 'Texte sélectionné : copie-le avec le menu.' }
  }
  onMount(() => appel(() => api.get('/api/recit/' + id)))
</script>

<a href={'#/chemin/' + id} class="mb-4 inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground">
  <ArrowLeft class="size-4" aria-hidden="true" />Retour au chemin
</a>

<header class="mb-5">
  <p class="etiquette">Sillage</p>
  <h1 class="titre">Raconter</h1>
</header>

{#if erreur}<p class="mb-4 rounded-2xl border border-destructive/50 p-4 text-sm" role="alert">{erreur}</p>{/if}

{#if recit === null && !erreur}
  <p class="text-sm text-muted-foreground" role="status">Lecture du chemin…</p>
{:else if recit}
  <p class="mb-3 max-w-[65ch] text-sm text-muted-foreground">
    {recit.garde_le ? `Ton texte, gardé le ${quand(recit.garde_le)}.` : 'Proposé par Sillage à partir des étapes visibles du chemin : une phrase par étape nommée, rien d\'inventé.'}
    Corrige-le ici. Pour qu'une étape n'y soit pas, masque-la dans le chemin ; pour qu'elle ait sa phrase, donne-lui un nom.
  </p>
  <label class="sr-only" for="recit">Le récit</label>
  <textarea id="recit" bind:this={zone} bind:value={texte} rows="18" spellcheck="true"
            class="w-full max-w-[75ch] rounded-2xl border border-input bg-card p-4 text-base leading-relaxed outline-none focus:border-ring"></textarea>
  <div class="mt-3 flex flex-wrap items-center gap-2">
    <Button onclick={garder} disabled={!change}>Garder ce texte</Button>
    <Button variant="outline" onclick={copier}>Copier</Button>
    {#if recit.garde_le || change}<Button variant="outline" onclick={repartir}>Repartir du chemin</Button>{/if}
    <span class="text-sm text-muted-foreground" role="status">{dit}</span>
  </div>
{/if}
