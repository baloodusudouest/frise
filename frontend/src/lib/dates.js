// Les dates telles qu'on les lit : « 15 juin 2019 », « 15 – 16 juin 2019 », « 28 juin – 3 juillet 2019 ».
const MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']
const lire = (iso) => { const [a, m, j] = iso.split('-').map(Number); return { a, m, j } }
const jour = (j) => (j === 1 ? '1er' : String(j))

export function dateLongue(iso) {
  if (!iso) return ''
  const d = lire(iso)
  return `${jour(d.j)} ${MOIS[d.m - 1]} ${d.a}`
}

export function periode(debut, fin) {
  if (!fin || debut === fin) return dateLongue(debut)
  const a = lire(debut), b = lire(fin)
  if (a.a !== b.a) return `${dateLongue(debut)} – ${dateLongue(fin)}`
  if (a.m !== b.m) return `${jour(a.j)} ${MOIS[a.m - 1]} – ${dateLongue(fin)}`
  return `${jour(a.j)} – ${dateLongue(fin)}`
}

export const ageDit = (age) => (age == null ? '' : age === 0 ? 'avant 1 an' : age === 1 ? 'à 1 an' : `à ${age} ans`)
