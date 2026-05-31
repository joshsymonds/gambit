# Defense-in-Depth Validation

## Overview

When you fix a bug caused by invalid data, adding validation at one place feels sufficient. But that single check can be bypassed by a different code path, by refactoring, or by mocks.

**Core principle:** Validate at EVERY layer the data passes through. Make the bug structurally impossible, not merely patched.

Single validation says "we fixed the bug." Multiple layers say "we made the bug impossible." Different layers catch different cases: entry validation catches most bugs, business logic catches edge cases, environment guards prevent context-specific dangers, and debug logging helps when the others fail.

## The Four Layers

### Layer 1: Entry-point validation
Reject obviously invalid input at the API boundary.

```typescript
function createProject(name: string, workingDirectory: string) {
  if (!workingDirectory || workingDirectory.trim() === '') {
    throw new Error('workingDirectory cannot be empty');
  }
  if (!existsSync(workingDirectory)) {
    throw new Error(`workingDirectory does not exist: ${workingDirectory}`);
  }
  if (!statSync(workingDirectory).isDirectory()) {
    throw new Error(`workingDirectory is not a directory: ${workingDirectory}`);
  }
  // ... proceed
}
```

### Layer 2: Business-logic validation
Ensure the data makes sense for this specific operation.

```typescript
function initializeWorkspace(projectDir: string, sessionId: string) {
  if (!projectDir) {
    throw new Error('projectDir required for workspace initialization');
  }
  // ... proceed
}
```

### Layer 3: Environment guards
Prevent dangerous operations in specific contexts.

```typescript
async function gitInit(directory: string) {
  // In tests, refuse git init outside temp directories
  if (process.env.NODE_ENV === 'test') {
    const normalized = normalize(resolve(directory));
    const tmpDir = normalize(resolve(tmpdir()));
    if (!normalized.startsWith(tmpDir)) {
      throw new Error(`Refusing git init outside temp dir during tests: ${directory}`);
    }
  }
  // ... proceed
}
```

### Layer 4: Debug instrumentation
Capture context for forensics when the other layers are bypassed.

```typescript
async function gitInit(directory: string) {
  const stack = new Error().stack;
  logger.debug('About to git init', { directory, cwd: process.cwd(), stack });
  // ... proceed
}
```

## Applying the Pattern

When you find a bug:

1. **Trace the data flow** — where does the bad value originate, and where is it used? (See [root-cause-tracing.md](root-cause-tracing.md).)
2. **Map all checkpoints** — list every point the data passes through.
3. **Add validation at each layer** — entry, business, environment, debug.
4. **Test each layer** — try to bypass layer 1, verify layer 2 catches it.

All four layers earn their place: different code paths bypass entry validation, mocks bypass business-logic checks, platform edge cases need environment guards, and debug logging identifies structural misuse. Don't stop at one validation point.
