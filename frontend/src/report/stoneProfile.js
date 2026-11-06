/**
 * Stone Profile Resolution (InscripLens Report Step E1)
 *
 * Resolves identity and narrative metadata for the stone under analysis.
 *
 * NOTE: Registry lookup extension point:
 * When a future stone registry is integrated (e.g. automated visual matching
 * against archaeological catalogues or curated epigraphic corpora), plug the
 * lookup query here before falling back to user-entered or unidentified profiles.
 * Do NOT synthesize or generate fictional stories or attributions.
 *
 * @param {Object} params
 * @param {Object} [params.run] - Active analysis record from Studio
 * @param {boolean} [params.isDemo] - Whether current stone is the Nagavara demo
 * @param {string} [params.userEnteredName] - User-entered stone name from preview dialog
 * @returns {{ name: string, nameSource: 'demo' | 'user' | 'unidentified', story: null, storySource: null }}
 */
export function getStoneProfile({ run, isDemo = false, userEnteredName = '' } = {}) {
  const isDemonstration = Boolean(isDemo || run?.is_demo);

  if (isDemonstration) {
    return {
      name: 'Nagavara demonstration stone',
      nameSource: 'demo',
      story: null,
      storySource: null
    };
  }

  const trimmed = typeof userEnteredName === 'string' ? userEnteredName.trim() : '';
  if (trimmed) {
    return {
      name: trimmed,
      nameSource: 'user',
      story: null,
      storySource: null
    };
  }

  // Future registry lookup plug-in point:
  // e.g.
  // const registryMatch = lookupStoneRegistry(run?.id, run?.fingerprint);
  // if (registryMatch) {
  //   return {
  //     name: registryMatch.name,
  //     nameSource: 'registry',
  //     story: registryMatch.curatedStory,
  //     storySource: registryMatch.citation
  //   };
  // }

  return {
    name: 'Stone not identified',
    nameSource: 'unidentified',
    story: null,
    storySource: null
  };
}
