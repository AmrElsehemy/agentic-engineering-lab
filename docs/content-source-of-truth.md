# Content Source of Truth Policy

## The rule

Do not maintain multiple competing full copies of an article.

Use each system for one job:

| Layer | System | Source of truth for | What belongs there |
|---|---|---|---|
| Technical master | GitHub | Technical claims, code references, evaluation results, diagrams, evidence, revision history | Full Markdown article, editable diagrams, sanitized traces, implementation links |
| Operating system | Notion | Editorial workflow and accountability | Brief, audience, status, review checklist, publishing date, repurposing plan, KPI, evidence links |
| Public canonical | WordPress on amrelsehemy.net | The public reading URL and SEO canonical page | Published article, metadata, featured image, internal links, comments and public presentation |
| Distribution | LinkedIn | Reach and conversation | Short adaptation, selected visual, link to the WordPress canonical URL |

## Which one should be trusted?

For a technical article, **GitHub is the master source**. It is version-controlled, reviewable, connected to the implementation, and able to preserve the exact evidence behind a claim.

Notion should not become a second manuscript. It should contain the article brief, editorial decisions, review status, publishing record, and links to the GitHub master and WordPress URL.

WordPress is the **public canonical destination**, not the drafting master. Once the article is published, its canonical URL should be used in social posts and search metadata. If a correction changes the technical substance, update GitHub first, then update WordPress from the revised master.

## Article workflow

1. Create the article master in `docs/articles/` in GitHub.
2. Link the implementation, diagrams, evaluation rubric, and sanitized evidence from the article.
3. Run the repository checks and review the technical claims.
4. Record the article brief and review status in Notion.
5. Publish the approved article to WordPress.
6. Set the WordPress page as the canonical URL.
7. Publish the LinkedIn adaptation pointing to WordPress.
8. Record the live URL, publication date, and performance metrics in Notion.
9. When the implementation changes, update GitHub first and mark WordPress as needing a content refresh.

## Naming and linking convention

Each article should have:

- One GitHub master: `docs/articles/<slug>.md`
- One WordPress canonical URL: `https://amrelsehemy.net/<published-route>`
- One Notion editorial record containing both links
- One or more channel adaptations that link back to WordPress

The GitHub article may include a `Canonical article` line pointing to WordPress. The WordPress article should include a link to the GitHub implementation as its technical proof companion.

## Correction policy

If the error is technical, correct GitHub first, rerun the relevant checks, then update WordPress.

If the error is editorial only—headline, paragraph order, image crop, or CTA—WordPress may be updated directly, but the change should still be recorded in Notion. If the editorial change changes a technical claim, it must also be reflected in GitHub.

## Current article

- GitHub master: `docs/articles/production-grade-tool-calling.md`
- WordPress destination: `https://amrelsehemy.net/` until the final article route is confirmed
- LinkedIn adaptation: `docs/articles/production-grade-tool-calling-linkedin.md`
- Operating record: Mission Control in Notion
