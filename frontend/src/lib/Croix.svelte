<script>
  // 0.12.2 : la croix de fermeture commune (même place, même dessin partout) ; voir .croix dans app.css
  let { label, onclick } = $props()
</script>

<button type="button" class="croix" aria-label={label} {onclick}>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 6 6 18M6 6l12 12" /></svg>
</button>
