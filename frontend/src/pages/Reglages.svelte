<script>
  // « Réglages » : ce qui n'est pas un service. Toujours en bas : la version et la déconnexion.
  import { Button } from '$lib/components/ui/button/index.js'
  let { session, deconnecter } = $props()
</script>

<header class="mb-5">
  <p class="etiquette">Sillage</p>
  <h1 class="titre">Réglages</h1>
</header>

<section class="rounded-2xl border bg-card p-5">
  <h2 class="text-lg font-semibold">Comment le chemin est fait</h2>
  <p class="mt-1 text-sm text-muted-foreground">Une étape réunit les photos d'une personne prises à moins de deux jours les unes des autres. Elle porte le nom de l'album de sa photo phare, sinon celui de son dossier, sinon sa date. Un temps fort est une étape dont le nom contient un des mots de la liste (mariage, baptême, anniversaire, Noël, vacances…), réglable dans la stack par SILLAGE_MOTS.</p>
</section>

<p class="mt-6 flex items-center justify-between gap-3 text-sm text-muted-foreground">
  <span>Sillage {session.version}</span>
  <Button variant="outline" onclick={deconnecter}>Se déconnecter</Button>
</p>
