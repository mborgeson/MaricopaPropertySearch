# Hive-Mind Swarm Guide for Issue Resolution

## Current Situation
- **Active Swarm**: swarm-1758004865030-qt92inpji
- **Issues Found**: 2 critical, 2 minor (see GUI_LAUNCHER_TEST_REPORT.md)
- **Fix Script Created**: scripts/fix_gui_issues.py

## Three Methods to Use Swarm for Fixes

### Method 1: Direct Claude Code with Swarm Context
```bash
# Spawn a new focused swarm for fixing issues
npx claude-flow hive-mind spawn "Review GUI_LAUNCHER_TEST_REPORT.md and apply fixes for ConfigManager methods and search button issues" --claude --queen-type tactical

# The swarm will generate a Claude Code command with full context
# Execute it to have Claude fix the issues with swarm coordination
```

### Method 2: Use Existing Fix Script with Swarm Verification
```bash
# Run the fix script
python scripts/fix_gui_issues.py

# Then spawn swarm to verify
npx claude-flow hive-mind spawn "Verify that GUI launcher issues from GUI_LAUNCHER_TEST_REPORT.md have been resolved" --claude
```

### Method 3: Interactive Wizard Approach
```bash
# Use the wizard for step-by-step guidance
npx claude-flow hive-mind wizard

# Select:
# 1. "Fix and verify code issues"
# 2. Point to: docs/GUI_LAUNCHER_TEST_REPORT.md
# 3. Choose workers: analyst, coder, tester
# 4. Execute with Claude Code integration
```

## Understanding Swarm Workflow

### 1. Issue Analysis Phase
The swarm will:
- **Researcher Worker**: Read and analyze GUI_LAUNCHER_TEST_REPORT.md
- **Analyst Worker**: Identify root causes and dependencies
- **Queen**: Build consensus on fix approach

### 2. Implementation Phase
The swarm will:
- **Coder Worker**: Implement fixes for ConfigManager and search button
- **Queen**: Coordinate changes across multiple files
- **Collective Memory**: Track all modifications

### 3. Verification Phase
The swarm will:
- **Tester Worker**: Run gui_launcher_test.py
- **Analyst Worker**: Compare results with previous report
- **Queen**: Determine if issues are resolved

## Manual Swarm Commands

### Check Swarm Status
```bash
npx claude-flow hive-mind status
```

### View Collective Memory
```bash
npx claude-flow hive-mind memory --swarm-id swarm-1758004865030-qt92inpji
```

### View Consensus Decisions
```bash
npx claude-flow hive-mind consensus --swarm-id swarm-1758004865030-qt92inpji
```

### Stop Current Swarm
```bash
npx claude-flow hive-mind stop swarm-1758004865030-qt92inpji
```

## Using MCP Tools for Coordination

When Claude Code is spawned with hive-mind, you can use these MCP tools:

```javascript
// Check swarm status
mcp__claude-flow__swarm_status({ verbose: true })

// View agent metrics
mcp__claude-flow__agent_metrics({ metric: "all" })

// Orchestrate task
mcp__claude-flow__task_orchestrate({
  task: "Fix ConfigManager missing methods",
  strategy: "sequential",
  priority: "high"
})
```

## Quick Fix Process

### Option A: Automated Fix (Recommended)
```bash
# 1. Run the fix script
python scripts/fix_gui_issues.py

# 2. If successful, you'll see:
# ✓ ALL ISSUES RESOLVED - GUI LAUNCHER READY!
```

### Option B: Manual Fix with Swarm Guidance
```bash
# 1. Spawn tactical swarm for fixes
npx claude-flow hive-mind spawn "Fix critical issues in ConfigManager and search button" --claude --queen-type tactical

# 2. The swarm will:
#    - Add methods to src/config_manager.py
#    - Fix search_button in src/gui/enhanced_main_window.py
#    - Run tests to verify

# 3. Check results
python tests/gui_launcher_test.py
```

## Expected Outcomes

After successful fixes, the test should show:
```
======================================================================
 TEST SUMMARY
======================================================================
[OK] DEPENDENCIES: PASSED
[OK] CONFIGURATION: PASSED  ← Was FAILED
[OK] DATABASE: PASSED
[OK] GUI: PASSED            ← Was FAILED
[OK] BATCH_SEARCH: PASSED

======================================================================
 [OK] ALL TESTS PASSED - GUI LAUNCHER IS FUNCTIONAL
======================================================================
```

## Troubleshooting

### If Swarm Gets Stuck
```bash
# Stop and restart
npx claude-flow hive-mind stop swarm-1758004865030-qt92inpji
npx claude-flow hive-mind spawn "Fix GUI issues" --claude --queen-type adaptive
```

### If Fixes Don't Apply
```bash
# Use verbose mode to see what's happening
npx claude-flow hive-mind spawn "Debug and fix GUI launcher issues" --verbose --claude
```

### To Resume Work Later
```bash
# List sessions
npx claude-flow hive-mind sessions

# Resume specific session
npx claude-flow hive-mind resume session-1758004865032-mmjhot08s
```

## Best Practices

1. **Use Tactical Queen** for focused fixes
2. **Use Strategic Queen** for broad analysis
3. **Use Adaptive Queen** when approach is unclear
4. **Always verify** fixes with the test script
5. **Check collective memory** for decisions made
6. **Use --verbose** flag for detailed logging

## Next Steps After Fixes

1. Run full application: `python RUN_APPLICATION.py`
2. Test batch search with sample CSV
3. Verify background data collection
4. Monitor performance metrics
5. Document any new issues found