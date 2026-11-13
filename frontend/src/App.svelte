<script>
  // Sillage : rail à gauche sur PC, pilule d'icônes en bas sur iPhone (format commun des applis).
  import { onMount } from 'svelte'
  import { fly } from 'svelte/transition'
  import Waves from '@lucide/svelte/icons/waves'
  import Network from '@lucide/svelte/icons/network'
  import BedDouble from '@lucide/svelte/icons/bed-double'
  import SlidersHorizontal from '@lucide/svelte/icons/sliders-horizontal'
  import { api } from '$lib/api.js'
  import Connexion from './pages/Connexion.svelte'
  import Sillages from './pages/Sillages.svelte'
  import Chemin from './pages/Chemin.svelte'
  import Recit from './pages/Recit.svelte'
  import Invite from './pages/Invite.svelte'
  import Services from './pages/Services.svelte'
  import Chambres from './pages/Chambres.svelte'
  import Reglages from './pages/Reglages.svelte'

  const onglets = [
    { page: 'sillages', nom: 'Sillages', icone: Waves },
    { page: 'chambres', nom: 'Chambres', icone: BedDouble },
    { page: 'connexion', nom: 'Connexion', icone: Network },
    { page: 'reglages', nom: 'Réglages', icone: SlidersHorizontal },
  ]

  // 0.5 : /invite/<jeton> est la page d'un invité des chambres : ni mot de passe, ni navigation
  const jetonInvite = location.pathname.match(/^\/invite\/([A-Za-z0-9_-]+)\/?$/)?.[1] || ''
  let connecte = $state(null) // null : on ne sait pas encore
  let session = $state({ version: '' })
  let route = $state(lireRoute())

  function lireRoute() {
    const [page, id] = location.hash.replace('#/', '').split('/')
    if ((page === 'chemin' || page === 'recit') && id) return { page, id, onglet: 'sillages' }
    const p = onglets.some((o) => o.page === page) ? page : 'sillages'
    return { page: p, onglet: p }
  }

  async function verifier() {
    try {
      const s = await api.get('/api/session')
      session = s
      connecte = s.connecte
    } catch {
      connecte = false
    }
  }

  async function deconnecter() {
    try { await api.post('/api/deconnexion') } catch { /* déjà déconnecté */ }
    connecte = false
  }
  const dehors = () => (connecte = false)

  onMount(() => { if (!jetonInvite) verifier() })
</script>

<svelte:window onhashchange={() => (route = lireRoute())} />

{#if jetonInvite}
  <Invite jeton={jetonInvite} />
{:else if connecte === false}
  <Connexion onconnecte={verifier} />
{:else if connecte}
  <div class="md:pl-52">
    <nav
      aria-label="Sections"
      class="fixed bottom-[calc(0.75rem+env(safe-area-inset-bottom))] left-1/2 z-20 flex -translate-x-1/2 items-center gap-1 rounded-full border bg-card/80 p-1.5 shadow-lg backdrop-blur-md
             md:inset-y-0 md:left-0 md:w-52 md:translate-x-0 md:flex-col md:items-stretch md:gap-1 md:rounded-none md:border-0 md:border-r md:bg-transparent md:p-4 md:shadow-none md:backdrop-blur-none"
    >
      <span class="mb-4 hidden items-center gap-2 px-2 text-xl font-light tracking-tight md:flex">
        <img src="/icone.svg" alt="" class="size-7 rounded-md" />Sillage
      </span>
      {#each onglets as o}
        {@const Icone = o.icone}
        <a
          href={'#/' + o.page}
          aria-label={o.nom}
          aria-current={route.onglet === o.page ? 'page' : undefined}
          class="flex h-11 items-center gap-2 rounded-full px-4 text-sm font-medium text-muted-foreground transition-colors
                 hover:text-foreground aria-[current=page]:bg-foreground aria-[current=page]:text-background
                 md:h-10 md:rounded-lg md:px-3 md:aria-[current=page]:bg-secondary md:aria-[current=page]:text-foreground"
        >
          <Icone class="size-[1.15rem]" aria-hidden="true" />
          <span class="sr-only md:not-sr-only">{o.nom}</span>
        </a>
      {/each}
    </nav>

    <main
      class="mx-auto max-w-5xl px-[max(1rem,env(safe-area-inset-left))] pt-[calc(1.25rem+env(safe-area-inset-top))] pb-[calc(6rem+env(safe-area-inset-bottom))] md:px-8 md:pt-8 md:pb-10"
    >
      {#key route.page + (route.id || '')}
        <div in:fly={{ y: 6, duration: 180 }}>
          {#if route.page === 'chemin'}
            <Chemin id={route.id} ondeconnecte={dehors} />
          {:else if route.page === 'recit'}
            <Recit id={route.id} ondeconnecte={dehors} />
          {:else if route.page === 'chambres'}
            <Chambres ondeconnecte={dehors} />
          {:else if route.page === 'connexion'}
            <Services ondeconnecte={dehors} />
          {:else if route.page === 'reglages'}
            <Reglages {session} {deconnecter} />
          {:else}
            <Sillages ondeconnecte={dehors} />
          {/if}
        </div>
      {/key}
    </main>
  </div>
{/if}
