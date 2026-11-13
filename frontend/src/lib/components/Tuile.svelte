<script>
  // Tuile bento : la taille dit l'importance (classes col-span / row-span posées par l'écran).
  // « accent » : fond à la couleur de l'appli, réservé à LA tuile qui demande l'attention.
  import { cn } from '$lib/utils.js'

  let { etiquette = '', accent = false, class: classe = '', children } = $props()
</script>

<section
  class={cn(
    'flex min-w-0 flex-col gap-3 rounded-2xl border p-5',
    accent ? 'border-transparent bg-primary text-primary-foreground' : 'bg-card text-card-foreground',
    classe,
  )}
>
  {#if etiquette}
    <h2 class={cn('etiquette', accent && 'text-primary-foreground/75')}>{etiquette}</h2>
  {/if}
  {@render children?.()}
</section>
