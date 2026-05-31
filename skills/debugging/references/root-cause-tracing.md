# Root Cause Tracing

## Overview

Bugs often manifest deep in the call stack — a file created in the wrong location, a database opened with the wrong path, a `git init` in the wrong directory. Your instinct is to fix where the error appears, but that's treating a symptom.

**Core principle:** Trace backward through the call chain until you find the original trigger, then fix at the source.

**Use when:** the error happens deep in execution (not at the entry point), the stack trace shows a long call chain, it's unclear where the invalid data originated, or you need to find which test/code triggers the problem. If you genuinely can't trace backward (a dead end), fix at the symptom point — but that's the exception, not the default.

## The Tracing Process

### 1. Observe the symptom
```
Error: git init failed in /Users/me/project/packages/core
```

### 2. Find the immediate cause — what code directly causes this?
```typescript
await execFileAsync('git', ['init'], { cwd: projectDir });
```

### 3. Ask: what called this? Keep climbing.
```
WorktreeManager.createSessionWorktree(projectDir, sessionId)
  ← Session.initializeWorkspace()
  ← Session.create()
  ← test at Project.create()
```

### 4. Trace the value, not just the calls — what was passed?
- `projectDir = ''` (empty string!)
- Empty string as `cwd` resolves to `process.cwd()`
- That's the source-code directory — the bug.

### 5. Find the original trigger — where did the empty string come from?
```typescript
const context = setupCoreTest();        // Returns { tempDir: '' }
Project.create('name', context.tempDir); // Accessed before beforeEach ran!
```

**Root cause:** a top-level variable read the value before `beforeEach` populated it. Fix at the source (e.g., make `tempDir` a getter that throws if accessed too early), not at the `git init` call.

## Adding Stack Traces

When you can't trace manually, instrument the dangerous operation to capture its caller:

```typescript
async function gitInit(directory: string) {
  const stack = new Error().stack;
  console.error('DEBUG git init:', {
    directory,
    cwd: process.cwd(),
    nodeEnv: process.env.NODE_ENV,
    stack,
  });
  await execFileAsync('git', ['init'], { cwd: directory });
}
```

**In tests, use `console.error()`** — a logger may be suppressed. Log **before** the operation (not after it fails), include context (directory, cwd, env vars), and capture the chain with `new Error().stack`. Then run and filter:

```bash
npm test 2>&1 | grep 'DEBUG git init'
```

Look for the test file name and line number in the stack, and the pattern (same test? same parameter?).

## Instrumenting Boundaries in Multi-Component Systems

When the failing path crosses 3+ components, you can't reason out *which* one is broken from the error alone — the error surfaces at the last layer but the bug usually lives earlier. Log what **enters** and **exits** each boundary, plus the config/env state each layer reads, then run once and read top-to-bottom. The first layer where reality diverges from expectation is where the bug lives.

Template (a macOS code-signing pipeline — adapt the commands to your stack):

```bash
# Layer 1 — CI workflow: which secrets did the runner actually inject?
echo "=== Workflow env ==="
echo "IDENTITY: ${IDENTITY:+SET}${IDENTITY:-UNSET}"
echo "KEYCHAIN_PASSWORD: ${KEYCHAIN_PASSWORD:+SET}${KEYCHAIN_PASSWORD:-UNSET}"

# Layer 2 — Build script: did env vars propagate from the workflow?
echo "=== Build script env ==="
env | grep -E '^(IDENTITY|KEYCHAIN)' || echo "signing env vars not present"

# Layer 3 — Signing step: is the keychain in the expected state?
echo "=== Keychain state ==="
security list-keychains -d user
security find-identity -v -p codesigning

# Layer 4 — Actual sign: the failing command, with maximum verbosity
codesign --sign "$IDENTITY" --verbose=4 "$APP_PATH"
```

Code-signing errors surface at Layer 4, but 90% of the time the real bug is Layer 1 (secret not set) or Layer 2 (env var not propagated). **Remove the instrumentation once the root cause is identified** — don't commit scaffolding.

## Finding Which Test Causes Pollution

If unwanted state (a stray `.git`, a leftover file) appears during a test run but you don't know which test created it, bisect with [find-polluter.sh](find-polluter.sh):

```bash
./find-polluter.sh '.git' 'src/**/*.test.ts'
```

It runs tests one by one and stops at the first one that produces the pollution.

## Key Principle

Found the immediate cause? Ask whether you can trace one level up. If yes, keep tracing until you reach the source, then fix there. **Never fix just where the error appears.** After fixing at the source, consider adding [defense-in-depth.md](defense-in-depth.md) validation at each layer so the bug becomes impossible to reintroduce.
