/**
 * Stone Profile Resolution (InscripLens Report Step E1)
 *
 * Resolves identity and narrative metadata for the stone under analysis.
 * Provides curated archaeological and historical brief for demonstration stones.
 *
 * @param {Object} params
 * @param {Object} [params.run] - Active analysis record from Studio
 * @param {boolean} [params.isDemo] - Whether current stone is the demonstration stone
 * @param {string} [params.userEnteredName] - User-entered stone name from preview dialog
 * @returns {Object} Stone profile with structured historical context and narrative
 */
export function getStoneProfile({ run, isDemo = false, userEnteredName = '' } = {}) {
  const isDemonstration = Boolean(
    isDemo ||
    run?.is_demo ||
    (typeof run?.display_name === 'string' && run.display_name.toLowerCase().includes('nagavara'))
  );

  const trimmed = typeof userEnteredName === 'string' ? userEnteredName.trim() : '';

  if (isDemonstration) {
    return {
      name: trimmed || 'The Halmidi Inscription',
      alternateName: 'Nagavara demonstration stone',
      nameSource: 'demo',
      overview: {
        dateOfOrigin: 'Approximately 450–500 CE',
        location: 'Halmidi village, Hassan district, Karnataka',
        discovery: 'Found in 1936 by Dr. M. H. Krishna, Director of Archaeology for the princely State of Mysore',
        medium: 'Carved stone pillar'
      },
      significance: {
        languageMilestone: 'Oldest known confirmed inscription written entirely in the Kannada language',
        scriptAndDialect: 'Kadamba script using Puruvada-hala Kannada (pre-old Kannada)',
        administrativeEvidence: 'Earliest historical proof of Kannada functioning as an official administrative language rather than solely a spoken dialect'
      },
      narrative: {
        issuingAuthority: 'The Kadamba dynasty',
        purpose: 'Official record of a royal land grant',
        story: 'The text documents the donation of the village of Palmadi (modern-day Halmidi) to a warrior named Vija Arasa. This land was awarded as a royal tribute for his battlefield heroism and decisive victory against the combined military forces of the Kekayas and the Pallavas.'
      },
      story: 'The Halmidi inscription (c. 450–500 CE), discovered in 1936 by Dr. M. H. Krishna in Halmidi village (Hassan district, Karnataka), is a carved stone pillar recognized as the oldest confirmed inscription written entirely in the Kannada language. Inscribed in the Kadamba script in Puruvada-hala Kannada (pre-old Kannada), it provides the earliest historical proof of Kannada functioning as an official administrative language. Issued by the Kadamba dynasty, the text records a royal land grant donating the village of Palmadi (modern Halmidi) to warrior Vija Arasa as tribute for his battlefield heroism and decisive victory against the combined military forces of the Kekayas and the Pallavas.',
      storySource: 'Epigraphia Carnatica & Archaeological Survey of Mysore (Dr. M. H. Krishna, 1936)'
    };
  }

  if (trimmed) {
    return {
      name: trimmed,
      nameSource: 'user',
      story: null,
      storySource: null
    };
  }

  return {
    name: 'Stone not identified',
    nameSource: 'unidentified',
    story: null,
    storySource: null
  };
}
