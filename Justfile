# Gambit release automation
# Usage: just release 1.6.0

release version:
    @echo "Releasing v{{version}}..."
    @# Update plugin.json
    @jq --arg v "{{version}}" '.version = $v' .claude-plugin/plugin.json > .claude-plugin/plugin.json.tmp \
        && mv .claude-plugin/plugin.json.tmp .claude-plugin/plugin.json
    @# Update marketplace.json
    @jq --arg v "{{version}}" '.plugins[0].version = $v' .claude-plugin/marketplace.json > .claude-plugin/marketplace.json.tmp \
        && mv .claude-plugin/marketplace.json.tmp .claude-plugin/marketplace.json
    @echo "Updated .claude-plugin/plugin.json and .claude-plugin/marketplace.json to v{{version}}"
    @git add .claude-plugin/plugin.json .claude-plugin/marketplace.json
    @git commit -m "Bump version to {{version}}"
    @echo "Committed. Push when ready: git push"
