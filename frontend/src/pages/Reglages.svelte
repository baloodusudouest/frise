<script>
  // « Réglages » : ce qui n'est pas un service. Toujours en bas : la version et la déconnexion.
  import { onMount } from 'svelte'
  import X from '@lucide/svelte/icons/x'
  import { api } from '$lib/api.js'
  import { Button } from '$lib/components/ui/button/index.js'
  let { session, deconnecter } = $props()

  // 0.7 : les hôtes de la maison. Dans la frise de plusieurs invités, chacun garde ses photos seul ou avec eux.
  let hotes = $state([])
  let personnes = $state([])
  let choisi = $state('')
  let message = $state('')
  const libres = $derived(personnes.filter((p) => !hotes.some((h) => h.id === p.id)))

  onMount(async () => {
    try {
      hotes = (await api.get('/api/reglages')).hotes
      personnes = (await api.get('/api/personnes')).personnes
    } catch { message = 'Sillage ne répond pas pour l\'instant.' }
  })
  async function garder(ids) {
    try { hotes = (await api.put('/api/reglages', { hotes: ids })).hotes; message = 'Gardé.' }
    catch { message = 'Pas gardé : Sillage ou Immich ne répond pas.' }
  }
  const ajouter = () => { if (choisi) garder([...hotes.map((h) => h.id), choisi]); choisi = '' }
</script>

<header class="mb-5">
  <p class="etiquette">Sillage</p>
  <h1 class="titre">Réglages</h1>
</header>

<section class="rounded-2xl border bg-card p-5">
  <h2 class="text-lg font-semibold">Comment le chemin est fait</h2>
  <p class="mt-1 text-sm text-muted-foreground">Une étape réunit les photos d'une personne prises à moins de deux jours les unes des autres. Elle porte le nom de l'album de sa photo phare, sinon celui de son dossier, sinon sa date. Un temps fort est une étape dont le nom contient un des mots de la liste (mariage, baptême, anniversaire, Noël, vacances…), réglable dans la stack par SILLAGE_MOTS.</p>
</section>

<section class="mt-4 rounded-2xl border bg-card p-5" aria-labelledby="titre-hotes">
  <h2 id="titre-hotes" class="text-lg font-semibold">Hôtes de la maison</h2>
  <p class="mt-1 text-sm text-muted-foreground">Quand une chambre reçoit plusieurs invités, leur frise montre les moments où ils sont ensemble, et pour chacun ses photos seul ou avec les hôtes. Une photo où il y a quelqu'un d'autre n'y entre pas.</p>
  <ul class="mt-3 flex flex-wrap gap-2" aria-label="Hôtes choisis">
    {#each hotes as h (h.id)}
      <li class="flex items-center gap-1 rounded-full border bg-secondary py-1 pr-1 pl-3 text-sm">
        {h.nom}
        <button type="button" class="grid size-8 place-items-center rounded-full hover:bg-background" aria-label={'Retirer ' + h.nom}
                onclick={() => garder(hotes.filter((x) => x.id !== h.id).map((x) => x.id))}><X class="size-4" aria-hidden="true" /></button>
      </li>
    {:else}
      <li class="text-sm text-muted-foreground">Aucun hôte : chaque invité ne garde que ses photos seul.</li>
    {/each}
  </ul>
  <div class="mt-3 flex flex-wrap items-center gap-2">
    <label for="hote" class="sr-only">Ajouter un hôte</label>
    <select id="hote" bind:value={choisi} class="h-10 min-w-0 flex-1 rounded-lg border bg-background px-3 text-sm sm:max-w-xs">
      <option value="">Ajouter un hôte…</option>
      {#each libres as p (p.id)}<option value={p.id}>{p.nom}</option>{/each}
    </select>
    <Button variant="outline" onclick={ajouter} disabled={!choisi}>Ajouter</Button>
  </div>
  {#if message}<p class="mt-2 text-sm text-muted-foreground" role="status">{message}</p>{/if}
</section>

<p class="mt-6 flex items-center justify-between gap-3 text-sm text-muted-foreground">
  <span>Sillage {session.version}</span>
  <Button variant="outline" onclick={deconnecter}>Se déconnecter</Button>
</p>
