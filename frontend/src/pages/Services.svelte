<script>
  // « Connexion » : le seul service de Sillage est Immich, et Sillage ne fait que le lire.
  import { onMount } from 'svelte'
  import Images from '@lucide/svelte/icons/images'
  import { api } from '$lib/api.js'
  import { Button } from '$lib/components/ui/button/index.js'
  import { Badge } from '$lib/components/ui/badge/index.js'

  let { ondeconnecte } = $props()
  let s = $state(null)
  let attente = $state(false)

  async function lire() {
    attente = true
    try { s = (await api.get('/api/services')).immich } catch (err) { if (err.statut === 401) ondeconnecte?.() }
    attente = false
  }
  onMount(lire)
</script>

<header class="mb-5">
  <p class="etiquette">Sillage</p>
  <h1 class="titre">Connexion</h1>
</header>

<section class="rounded-2xl border bg-card p-5" aria-label="Immich">
  <div class="flex items-start justify-between gap-3">
    <h2 class="flex items-center gap-2 text-lg font-semibold"><Images class="size-5 text-primary" aria-hidden="true" />Immich</h2>
    <span class="mt-1.5 size-2.5 rounded-full {s?.repond ? 'bg-valide' : s ? 'bg-destructive' : 'bg-muted-foreground/40'}" aria-hidden="true"></span>
  </div>
  <p class="mt-1 text-sm" role="status">
    {#if !s}Lecture…{:else if s.repond}Répond, version {s.version}. {s.personnes} personne{s.personnes > 1 ? 's nommées' : ' nommée'}.{:else}{s.erreur}{/if}
  </p>
  <p class="mt-2 text-sm text-muted-foreground">Sillage lit dans Immich les personnes, leurs photos, le nom des albums et les vignettes. Il n'y écrit rien : sa clé peut être limitée à la lecture.</p>
  <div class="mt-3 flex flex-wrap items-center gap-2">
    <Button variant="outline" onclick={lire} disabled={attente}>Vérifier</Button>
    <Badge variant="outline">lecture seule</Badge>
  </div>
</section>
