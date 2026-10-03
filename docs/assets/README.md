# Article visual package

## Canonical publishing model

- **WordPress / amrelsehemy.net:** use `production-grade-tool-calling-wordpress-site-style.jpg` as the featured image.
- **LinkedIn:** use `production-grade-tool-calling-linkedin-site-style-v2.jpg` as the post/article thumbnail.
- **Technical article body:** use the two rendered PNG diagrams from `../diagrams/rendered/`.

## WordPress recommendations

- Featured image: 1200 × 675 or 1280 × 720, JPG, descriptive alt text.
- Suggested title: `From Agent Demo to Production: Making Tool Calling Trustworthy`.
- Suggested excerpt: `A practical Microsoft Foundry pattern for building a trustworthy boundary between probabilistic model behavior and deterministic application code.`
- Suggested image alt text: `Azure-inspired architecture showing a control gate between a Microsoft Foundry model and a validated tool, with Azure Monitor observability.`
- Add the canonical URL to the article’s SEO/canonical field, not only in the body.
- Link to the GitHub implementation as the inspectable proof companion.

## LinkedIn recommendations

- Use the LinkedIn thumbnail as the post image.
- Keep the first two lines of the post hook-focused before the link.
- Link to the canonical WordPress article, then add the GitHub link in the first comment if reach is the priority.
- Use the full article’s diagrams as follow-up carousel slides only if LinkedIn distribution becomes a priority; do not make the initial post visually dense.

## Azure branding boundary

The article diagrams use Microsoft Foundry terminology and Azure-aware architecture because they explain the implementation. The cover thumbnails deliberately use Amr’s own website system—paper, ink, volt lime, signal red, editorial collage, and workshop-style marks—rather than Azure blue. This keeps the personal brand consistent while still making the technology legible in the article body.

## Website consistency audit

The live homepage uses `Bricolage Grotesque` for display text and `IBM Plex Mono` for technical labels, with the following core tokens: paper `#f2efe8`, ink `#0b0b0b`, volt `#dfff39`, signal `#ff5038`, steel `#9da3a6`, and mist `#d8d4ca`. It presents an editorial/workbench identity: oversized black typography, paper texture, rules, diagrams, physical objects, and small mono metadata.

The original blue/cyan thumbnails were technically attractive but visually inconsistent with that system. The site-style pair is now the recommended set. The technical diagrams may retain restrained Azure/Foundry references because their job is explanation rather than brand identity.
