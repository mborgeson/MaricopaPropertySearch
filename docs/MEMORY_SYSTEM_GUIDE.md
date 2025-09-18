# Memory System Guide - MaricopaPropertySearch

## Overview

This document provides comprehensive guidance on the memory, session, and checkpoint systems configured for the MaricopaPropertySearch project. These systems ensure seamless work continuation across sessions and enable reliable project state management through Claude Flow, memory-keeper, and integrated checkpoint systems.

## Active Session Details

### Memory-Keeper Session
- **Session ID**: 7af01c57-6963-4a52-9aee-789502d6c316
- **Channel**: sparc-swarm-migration
- **Project Directory**: /home/mattb/MaricopaPropertySearch
- **Git Branch**: main
- **Git Commit**: 3b985a5 (Phase 1 Complete)

### SPARC Swarm Configuration
- **Swarm ID**: swarm_1758194153002_mn7w8xv5x
- **Topology**: Hierarchical
- **Active Agents**: 7 specialized agents
- **Status**: ACTIVE

### Checkpoint System
- **Latest Checkpoint**: MCA_GUI_AUDIT_CHECKPOINT_2025-09-18_0441.md
- **Checkpoint ID**: a57dfe39 (Phase1_Complete_With_Memory_System)
- **Location**: /home/mattb/MaricopaPropertySearch/checkpoints/

## Memory Commands

### 1. memory-usage
Shows current memory utilization and statistics.

**Usage:**
```bash
/memory:usage
```

**Returns:**
- Total memory entries
- Memory size in KB
- Namespace distribution
- Recent entries

### 2. memory-persist
Stores data persistently for future sessions.

**Usage:**
```bash
/memory:persist <key> <value> [namespace]
```

**Parameters:**
- `key`: Unique identifier for the memory entry
- `value`: Data to store (can be text, JSON, or structured data)
- `namespace`: Optional namespace for organizing memories (default: "default")

**Examples:**
```bash
# Store simple text
/memory:persist PROJECT_STATUS "Development phase complete"

# Store in specific namespace
/memory:persist API_CONFIG "{\"endpoint\": \"https://api.example.com\"}" api_settings

# Store debugging information
/memory:persist DEBUG_FIX_2025 "Fixed null pointer in BackgroundDataWorker"
```

### 3. memory-search
Search and retrieve stored memories.

**Usage:**
```bash
/memory:search <query> [options]
```

**Parameters:**
- `query`: Search term or pattern
- `options`:
  - `--namespace <name>`: Search within specific namespace
  - `--limit <n>`: Limit number of results
  - `--recent`: Sort by most recent first

**Examples:**
```bash
# Search all memories
/memory:search "API"

# Search in specific namespace
/memory:search "config" --namespace settings

# Get recent entries
/memory:search "*" --recent --limit 5
```

## Memory Storage Structure

### File Location
```
/memory/memory-store.json
```

### Data Format
```json
{
  "namespace": [
    {
      "key": "unique_identifier",
      "value": "stored_data",
      "namespace": "namespace_name",
      "timestamp": 1234567890
    }
  ]
}
```

## Current Project Memories

### MaricopaPropertySearch Memories

The following memories are currently stored for this project:

1. **MCA GUI TROUBLESHOOTING**
   - Tax and sales history troubleshooting complete resolution

2. **MCA_TAX_SALES_FIX**
   - Details about fixing PropertyDetailsDialog issues
   - Root cause: BackgroundDataWorker initialization problem
   - Multiple fixes applied across 4 files

3. **MCA_COMPREHENSIVE_FIXES**
   - Complete troubleshooting session documentation

4. **MCA_FILES_MODIFIED**
   - List of modified files during fixes

5. **MCA_SOLUTION_PATTERNS**
   - Reusable debugging patterns discovered

## Best Practices

### 1. Naming Conventions
- Use descriptive, uppercase keys with underscores
- Include project prefix (e.g., MCA_ for MaricopaPropertySearch)
- Add date suffixes for time-sensitive data

### 2. Namespace Organization
- `default`: General project memories
- `api_config`: API configuration and endpoints
- `fixes`: Bug fixes and solutions
- `patterns`: Reusable code patterns
- `documentation`: Important documentation notes

### 3. Data Types
- **Text**: Simple strings for status, notes
- **JSON**: Structured data like configurations
- **Markdown**: Formatted documentation
- **Lists**: Comma or newline separated values

### 4. Memory Lifecycle
- Store immediately after significant fixes
- Update existing entries rather than creating duplicates
- Clean up obsolete entries periodically
- Use timestamps for versioning

## Integration with Claude Flow

### Automatic Memory Creation
Certain operations automatically create memories:
- Critical bug fixes
- API endpoint discoveries
- Configuration changes
- Performance optimizations

### Memory-Aware Commands
Commands that utilize stored memories:
- `/analyze`: Uses past debugging patterns
- `/fix`: References previous solutions
- `/config`: Loads saved configurations
- `/test`: Recalls test scenarios

## Troubleshooting

### Common Issues

1. **Memory not persisting**
   - Check file permissions on memory directory
   - Verify JSON syntax if manually editing
   - Ensure unique keys

2. **Search not finding entries**
   - Check namespace specification
   - Use wildcards for partial matches
   - Verify case sensitivity

3. **Memory conflicts**
   - Use namespaces to separate contexts
   - Include timestamps in keys for versioning
   - Implement cleanup routines

## Advanced Usage

### Batch Operations
```bash
# Export memories
/memory:export --namespace project > memories.json

# Import memories
/memory:import memories.json --merge

# Clear namespace
/memory:clear --namespace temporary
```

### Memory Hooks
Configure automatic memory creation:
```yaml
hooks:
  on_fix_complete:
    - memory:persist FIX_{{date}} "{{description}}"
  on_api_discovery:
    - memory:persist API_{{endpoint}} "{{config}}"
```

### Cross-Session Context
Memories enable:
- Resuming interrupted work
- Sharing context between sessions
- Building knowledge base
- Pattern recognition

## Security Considerations

1. **Sensitive Data**
   - Never store passwords or API keys
   - Use environment variables for secrets
   - Sanitize user data before storing

2. **Access Control**
   - Memory files have user-only permissions
   - No network transmission of memories
   - Local storage only

3. **Data Retention**
   - Regular cleanup of old entries
   - Size limits on individual memories
   - Total storage quota management

## Maintenance

### Regular Tasks
- Weekly: Review and clean obsolete entries
- Monthly: Export backup of important memories
- Quarterly: Reorganize namespaces

### Monitoring
- Track memory growth
- Identify duplicate entries
- Optimize search patterns
- Update documentation

## Conclusion

The memory system is a powerful tool for maintaining context and building a knowledge base across Claude Flow sessions. Proper use of memory commands enhances productivity and ensures important information is never lost.