# Complete Checkpoint & Memory System Guide

**Created:** January 17, 2025 @ 15:00 PST
**Purpose:** Comprehensive documentation of ALL memory persistence and checkpoint systems

## Table of Contents

1. [Overview of All Systems](#overview)
2. [Knowledge Graph System](#knowledge-graph)
3. [Automated Checkpoint Generation](#automated-checkpoints)
4. [Manual Checkpoint Commands](#manual-commands)
5. [Git Hook Integration](#git-hooks)
6. [SPARC Agent Swarm](#sparc-swarm)
7. [Session Management](#session-management)
8. [Complete Command Reference](#command-reference)

---

## Overview of All Systems

### Active Memory & Persistence Systems

1. **MCP Knowledge Graph** - Structured entity storage with relationships
2. **Filesystem Checkpoints** - Timestamped markdown documents in `/checkpoints/`
3. **Git Hooks** - Automatic checkpoint on significant commits
4. **Python Generator** - Automated checkpoint creation with analysis
5. **SPARC Templates** - Embedded agent orchestration configurations
6. **Session Memory** - Claude's context window persistence

### Data Flow Architecture

```
User Action → Multiple Storage Systems → Persistent Record
    ↓
Git Commit → Post-Commit Hook → generate_checkpoint.py → .md file
    ↓
Claude Session → Knowledge Graph → Entities & Relations
    ↓
Manual Save → checkpoint_commands.sh → Timestamped Checkpoint
```

---

## Knowledge Graph System

### Storage Operations

```python
# STORE: Create entities with observations
mcp__knowledge-graph__create_entities([{
    "name": "Maricopa Property Search GUI Audit Sept 2025",
    "entityType": "ProjectCheckpoint",
    "observations": ["Latest status", "Next steps", "Achievements"]
}])

# LINK: Create relationships between entities
mcp__knowledge-graph__create_relations([{
    "from": "Maricopa Property Search GUI Audit Sept 2025",
    "to": "Search GUI Next Steps",
    "relationType": "defines"
}])
```

### Retrieval Operations

```python
# SEARCH: Find entities by name or content
mcp__knowledge-graph__search_nodes("search gui audit")

# RETRIEVE: Get specific entities
mcp__knowledge-graph__open_nodes(["Maricopa Property Search GUI Audit Sept 2025"])

# VIEW ALL: Read entire graph
mcp__knowledge-graph__read_graph()
```

### Monitoring & Management

```bash
# Check what's stored in knowledge graph (from Claude)
"Search knowledge graph for 'Maricopa Property Search GUI'"

# Delete outdated entities
mcp__knowledge-graph__delete_entities(["old-checkpoint-name"])

# Update observations
mcp__knowledge-graph__add_observations([{
    "entityName": "Maricopa Property Search GUI Audit Sept 2025",
    "contents": ["New achievement", "Updated status"]
}])
```

---

## Automated Checkpoint Generation

### Automatic Triggers

1. **Git Post-Commit Hook** (`.git/hooks/post-commit`)

   - Triggers when: >10 files changed OR keywords detected
   - Keywords: "refactor", "milestone", "checkpoint", "major"
   - Location: `.git/hooks/post-commit`
2. **Daily Cron Job** (optional)

   ```bash
   # Setup daily checkpoint at 5 PM
   ./scripts/checkpoint_commands.sh setup-daily

   # Verify cron job
   crontab -l | grep checkpoint
   ```
3. **Manual Trigger from Claude**

   ```bash
   # Generate checkpoint now
   python3 scripts/generate_checkpoint.py manual
   ```

### What Gets Captured

Each checkpoint automatically includes:

- Current git commit hash and status
- Recent commit history (last 5)
- Changed files count
- Large files needing refactoring (>500 lines)
- TODO items from previous checkpoint
- SPARC agent swarm template
- Timestamp and trigger type

---

## Manual Checkpoint Commands

### Primary Commands

```bash
  # Generate new checkpoint immediately
  ./scripts/checkpoint_commands.sh generate

  # View latest checkpoint
  ./scripts/checkpoint_commands.sh view

  # List all checkpoints (newest first)
  ./scripts/checkpoint_commands.sh list

  # Test checkpoint generation
  ./scripts/checkpoint_commands.sh test

  # Setup daily automatic generation
  ./scripts/checkpoint_commands.sh setup-daily
```

### Direct Python Usage

```bash
# Generate with specific trigger type
python3 scripts/generate_checkpoint.py manual
python3 scripts/generate_checkpoint.py git-commit
python3 scripts/generate_checkpoint.py daily
python3 scripts/generate_checkpoint.py test
```

### Quick Access Shortcuts

```bash
# Alias for quick checkpoint (add to ~/.bashrc)
alias checkpoint='cd /home/mattb/MaricopaPropertySearch && ./scripts/checkpoint_commands.sh generate'

# View latest checkpoint quickly
alias checkpoint-view='cat $(ls -t /home/mattb/MaricopaPropertySearch/checkpoints/*.md | grep -v README | head -1)'
```

---

## Git Hook Integration

### Post-Commit Hook Details

**Location:** `.git/hooks/post-commit`

**Activation Criteria:**

```bash
if [[ $CHANGED_FILES -gt 10 ]] ||           # More than 10 files changed
   [[ "$COMMIT_MSG" == *"refactor"* ]] ||   # Refactoring work
   [[ "$COMMIT_MSG" == *"milestone"* ]] ||  # Milestone reached
   [[ "$COMMIT_MSG" == *"checkpoint"* ]] || # Explicit checkpoint request
   [[ "$COMMIT_MSG" == *"major"* ]]         # Major changes
```

### Managing Git Hooks

```bash
# Disable automatic checkpoint generation
mv .git/hooks/post-commit .git/hooks/post-commit.disabled

# Re-enable automatic generation
mv .git/hooks/post-commit.disabled .git/hooks/post-commit

# Test hook without committing
bash .git/hooks/post-commit

# View hook status
ls -la .git/hooks/post-commit
```

---

## SPARC Agent Swarm

### Embedded Template Location

Every checkpoint includes the SPARC template at the bottom with:

- Task overview and objectives
- Context from previous achievements
- Detailed steps for each TODO item
- Input materials and expected outputs
- Success criteria and guidelines
- Agent orchestration commands

### Executing SPARC Commands

```bash
# Full swarm orchestration
npx claude-flow sparc-mode \
  --task "Dashboard Security and Refactoring Sprint" \
  --agents "security-manager,code-analyzer,refactorer,tester,architect,documentation-specialist" \
  --phases "security,analysis,extraction,integration,documentation" \
  --checkpoint-interval "phase-complete"

# Individual task execution
npx claude-flow task-orchestrate \
  --task "Change admin password and verify authentication" \
  --priority "critical" \
  --agent "security-manager" \
  --validation "test_system.py"

# Parallel execution
npx claude-flow parallel-execute \
  --tasks "analyze-market_analysis.py,document-postgresql-setup" \
  --agents "code-analyzer,documentation-specialist"
```

### Monitoring SPARC Execution

```bash
# Check swarm status
npx claude-flow swarm-status

# View agent metrics
npx claude-flow agent-metrics

# Monitor task progress
npx claude-flow task-status

# Get performance report
npx claude-flow performance-report
```

### Stopping SPARC Agents

```bash
# Graceful shutdown
npx claude-flow swarm-destroy --swarmId [ID]

# Force stop all agents
pkill -f "claude-flow"

# Clean up resources
npx claude-flow cleanup
```

---

## Session Management

### Starting a New Session

```python
# 1. Load latest checkpoint
"Please load checkpoints/[latest-checkpoint].md and continue"

# 2. Retrieve knowledge graph context
"Search knowledge graph for 'Maricopa Property Search GUI Audit Sept 2025'"

# 3. Check current git status
"Run git status and show recent commits"
```

### During a Session

```python
# Periodic checkpoint saves (every major milestone)
"Generate a checkpoint to save current progress"

# Update knowledge graph with achievements
"Store in knowledge graph: [achievement description]"

# Track progress with TodoWrite
"Update todo list with completed items"
```

### Ending a Session

```python
# 1. Generate final checkpoint
"Create checkpoint with current status and next steps"

# 2. Update knowledge graph
"Update knowledge graph entities with session achievements"

# 3. Commit any changes
"Commit current changes with descriptive message"
```

### Session Recovery

```python
# If session crashes or disconnects
"Load latest checkpoint from /checkpoints/ folder"
"Show knowledge graph entities for Maricopa Property Search GUI"
"Display current TODO status from checkpoint"
```

---

## Complete Command Reference

### Checkpoint Generation

| Command                                           | Purpose           | When to Use         |
| ------------------------------------------------- | ----------------- | ------------------- |
| `./scripts/checkpoint_commands.sh generate`     | Manual checkpoint | After major work    |
| `python3 scripts/generate_checkpoint.py manual` | Direct generation | From scripts        |
| `git commit -m "refactor: ..."`                 | Auto-checkpoint   | Significant commits |
| `crontab -e` → add checkpoint line             | Daily automation  | Scheduled saves     |

### Checkpoint Retrieval

| Command                                   | Purpose          | Output             |
| ----------------------------------------- | ---------------- | ------------------ |
| `./scripts/checkpoint_commands.sh view` | View latest      | Full checkpoint    |
| `./scripts/checkpoint_commands.sh list` | List all         | Chronological list |
| `ls -t checkpoints/*.md \| head -1`      | Find latest file | Filename           |
| `grep -l "topic" checkpoints/*.md`      | Search content   | Matching files     |

### Knowledge Graph Operations

| Operation | MCP Command                                | Purpose          |
| --------- | ------------------------------------------ | ---------------- |
| Store     | `mcp__knowledge-graph__create_entities`  | Save new data    |
| Link      | `mcp__knowledge-graph__create_relations` | Connect entities |
| Search    | `mcp__knowledge-graph__search_nodes`     | Find by content  |
| Retrieve  | `mcp__knowledge-graph__open_nodes`       | Get specific     |
| Delete    | `mcp__knowledge-graph__delete_entities`  | Remove old       |
| Update    | `mcp__knowledge-graph__add_observations` | Add new info     |

### SPARC Agent Commands

| Command              | Purpose            | Example         |
| -------------------- | ------------------ | --------------- |
| `sparc-mode`       | Full orchestration | Complex tasks   |
| `task-orchestrate` | Single task        | Specific work   |
| `parallel-execute` | Multiple tasks     | Concurrent work |
| `swarm-status`     | Check progress     | Monitoring      |
| `swarm-destroy`    | Stop agents        | Cleanup         |

### Git Integration

| Action                | Command                           | Triggers Checkpoint? |
| --------------------- | --------------------------------- | -------------------- |
| Commit with >10 files | `git commit`                    | Yes                  |
| Commit with keyword   | `git commit -m "refactor: ..."` | Yes                  |
| Normal commit         | `git commit -m "fix: typo"`     | No                   |
| Check hook            | `bash .git/hooks/post-commit`   | Test only            |

---

## Best Practices

### When to Generate Checkpoints

1. **Automatically happens when:**

   - Major git commits (>10 files or keywords)
   - Daily at 5 PM (if configured)
   - SPARC phase completion (if configured)
2. **Manually generate when:**

   - Completing major milestone
   - Before starting complex work
   - End of work session
   - After significant debugging

### What to Include in Checkpoints

- ✅ Current TODO status with checkmarks
- ✅ Specific commit hashes for reference
- ✅ Metrics and performance data
- ✅ Next concrete steps with priorities
- ✅ Risk assessments and blockers
- ✅ SPARC configuration for automation

### Checkpoint Maintenance

```bash
# Clean old checkpoints (keep last 10)
ls -t checkpoints/*.md | tail -n +11 | xargs rm -f

# Archive old checkpoints
mkdir -p checkpoints/archive
mv checkpoints/*2024*.md checkpoints/archive/

# Backup all checkpoints
tar -czf checkpoints_backup_$(date +%Y%m%d).tar.gz checkpoints/
```

---

## Troubleshooting

### Common Issues and Solutions

**Checkpoint not generating automatically:**

```bash
# Check hook is executable
ls -la .git/hooks/post-commit
chmod +x .git/hooks/post-commit

# Test hook manually
bash .git/hooks/post-commit

# Check Python script
python3 scripts/generate_checkpoint.py test
```

**Knowledge graph not finding entities:**

```python
# Check exact entity name
mcp__knowledge-graph__read_graph()

# Try broader search
mcp__knowledge-graph__search_nodes("dashboard")
```

**SPARC agents not starting:**

```bash
# Check claude-flow installation
npm list -g | grep claude-flow

# Reinstall if needed
npm install -g @anthropic/claude-flow

# Check for running processes
ps aux | grep claude-flow
```

---

## Complete System Health Check

Run this sequence to verify all systems:

```bash
# 1. Test checkpoint generation
./scripts/checkpoint_commands.sh test

# 2. Verify git hook
bash .git/hooks/post-commit

# 3. Check knowledge graph (from Claude)
"Show all knowledge graph entities"

# 4. List existing checkpoints
ls -la checkpoints/*.md

# 5. Test SPARC (if installed)
npx claude-flow --version

# 6. Verify cron job (if configured)
crontab -l | grep checkpoint
```

---

## Summary

This checkpoint system provides:

1. **Multiple Persistence Layers** - Knowledge graph + filesystem + git
2. **Automatic Triggers** - Git hooks + cron + SPARC phases
3. **Manual Controls** - Scripts for on-demand generation
4. **Session Continuity** - Context preserved across conversations
5. **SPARC Integration** - Agent orchestration embedded
6. **Easy Recovery** - Multiple retrieval methods

**Remember:** The system captures progress automatically, but manual checkpoints after major achievements ensure nothing is lost.
**Remember:** ALWAYS USE THE SPARC AGENT SWARM THAT IS REFERENCED, DEFINED, AND DESCRIBED AT THE FOLLOWING PATH: \ws
  l.localhost\Ubuntu\home\mattb\MaricopaPropertySearch\checkpoints\CHECKPOINT_SYSTEM_COMPLETE_GUIDE.md
------------------------------------------------------------------------------------------------------

**Guide Version:** 1.0
**Last Updated:** January 17, 2025 @ 15:00 PST
**Location:** /checkpoints/CHECKPOINT_SYSTEM_COMPLETE_GUIDE.md
