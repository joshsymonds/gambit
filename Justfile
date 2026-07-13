# Gambit release automation
# Usage: just release 1.6.0

generate:
    python3 tools/render_skills.py

check:
    python3 tools/render_skills.py --check
    python3 -m unittest discover -s tests -v

release version:
    @echo "Releasing v{{version}}..."
    @just generate
    @# Update plugin.json
    @jq --arg v "{{version}}" '.version = $v' .claude-plugin/plugin.json > .claude-plugin/plugin.json.tmp \
        && mv .claude-plugin/plugin.json.tmp .claude-plugin/plugin.json
    @# Update marketplace.json
    @jq --arg v "{{version}}" '.plugins[0].version = $v' .claude-plugin/marketplace.json > .claude-plugin/marketplace.json.tmp \
        && mv .claude-plugin/marketplace.json.tmp .claude-plugin/marketplace.json
    @jq --arg v "{{version}}" '.version = $v' src/backends/codex/plugin.json > src/backends/codex/plugin.json.tmp \
        && mv src/backends/codex/plugin.json.tmp src/backends/codex/plugin.json
    @just generate
    @echo "Updated Claude and Codex manifests to v{{version}}"
    @just check
    @git add .claude-plugin/plugin.json .claude-plugin/marketplace.json src/backends/codex/plugin.json skills contracts plugins/gambit
    @git commit -m "Bump version to {{version}}"
    @echo "Committed. Push when ready: git push"
