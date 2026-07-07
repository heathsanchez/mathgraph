## Tool Type
Custom CLI tool (Node/Deno)

## Purpose
Give agents structured access to Kaggle — the data science competition platform and community. Kaggle provides active competitions (what problems the ML community is working on right now), trending notebooks (how people are solving them), and datasets.

## API
- **Kaggle API**: https://www.kaggle.com/docs/api — REST-based
- **Authentication**: API token required (free, from kaggle.com/settings)
- **Existing CLI**: \`kaggle\` Python CLI exists but is Python-only and focused on download/submission
- **Public data**: Competition listings, public notebooks, public datasets

## CLI Interface (proposed)

\`\`\`bash
# Competitions
kaggle competitions                  # Active competitions
kaggle competition <slug>            # Competition details + description
kaggle leaderboard <slug>            # Competition leaderboard
kaggle leaderboard <slug> --limit 20 # Top N entries

# Notebooks
kaggle notebooks --sort trending     # Trending notebooks
kaggle notebooks --competition <slug>  # Notebooks for a competition
kaggle notebook <slug>               # Notebook details + metadata

# Datasets
kaggle datasets --sort trending      # Trending datasets
kaggle datasets --search "query"     # Search datasets
kaggle dataset <slug>                # Dataset details + columns + preview

# Search
kaggle search "query"                # Search across competitions, notebooks, datasets
kaggle search "query" --type notebook

# Discovery
kaggle topics                        # Discussion topics/forums
kaggle discussion <id>               # Read discussion thread
kaggle user <username>               # User profile + tier + medals
\`\`\`

## Output Format
- **YAML** for all structured output
- Competition metadata: title, description, deadline, reward, team count, evaluation metric, tags
- Notebook metadata: title, author, votes, language (Python/R), competition link, last run date
- Dataset metadata: title, creator, size, download count, columns, usability score
- User metadata: username, tier (Grandmaster/Master/etc.), medals, competition ranking

## Key Design Decisions
1. **Competition-centric**: Competitions are Kaggle's unique signal — what ML problems have prizes and deadlines right now.
2. **Tier/medal system as signal**: Kaggle's ranking system (Grandmaster → Novice) indicates expertise. Surface it.
3. **No data download**: Discovery tool, not a data pipeline. Show metadata, schemas, and previews — not full datasets.
4. **API token required**: Setup instructions in CLAUDE.md.

## CLAUDE.md Content
- Kaggle as the ML competition platform — what problems are being solved and how
- Competition lifecycle: launch → join → submit → leaderboard → end
- Tier system and what each tier means for expertise signal
- Notebooks as shared solutions — the Kaggle community's knowledge base
- Datasets as structured data discovery
- Using Kaggle for "how do people solve X?" research

## Acceptance Criteria
- [ ] CLI is implemented in Node or Deno
- [ ] All output is YAML
- [ ] Competition listing and details work
- [ ] Notebook browsing works
- [ ] Dataset metadata and preview work
- [ ] \`tools/kaggle/CLAUDE.md\` covers discovery patterns
- [ ] Tests cover all subcommands