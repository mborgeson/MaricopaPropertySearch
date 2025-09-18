# SPARC Swarm Action Plan - MaricopaPropertySearch Migration & Optimization

## Executive Summary
This document outlines the comprehensive action plan for migrating, consolidating, and optimizing the MaricopaPropertySearch project using the Claude-Flow SPARC Agent Swarm system.

## Swarm Configuration
- **Swarm ID**: swarm_1758194153002_mn7w8xv5x
- **Topology**: Hierarchical
- **Max Agents**: 12
- **Strategy**: Adaptive
- **Coordination Mode**: Distributed with parallel processing

## Active Agents
1. **ProjectOrchestrator** (Coordinator) - Overall project management and delegation
2. **PathMigrationSpecialist** (Code Analyzer) - Windows to Linux path conversion
3. **ScriptConsolidationArchitect** (Architect) - Script analysis and DRY implementation
4. **GUITestingSpecialist** (Specialist) - GUI testing and optimization
5. **DocumentationExpert** (Documenter) - Documentation updates and creation
6. **DependencyAnalyzer** (Analyst) - Dependency mapping and validation
7. **PerformanceOptimizer** (Performance Analyzer) - Performance profiling and optimization

## Phase 1: Project Analysis & Path Migration (CURRENT)

### 1.1 Windows Path Conversion
**Status**: IN PROGRESS
**Agent**: PathMigrationSpecialist

#### Identified Path Issues:
- Windows-style WSL paths found in:
  - `.claude-flow/SPARC AGENT REVIEW - TASK LIST, PROCESSES, AND OTHER INFO.md`
  - `.claude-flow/SPARC AGENT REVIEW - PROJECT SUMMARY AND DESCRIPTION.md`

**Pattern to Fix**: `\\wsl.localhost\Ubuntu\home\mattb\` → `/home/mattb/`

### 1.2 Script Inventory
**Status**: PENDING
**Agent**: ScriptConsolidationArchitect

#### Identified Script Categories:
1. **Main Application Launchers**
   - `/home/mattb/MaricopaPropertySearch/RUN_APPLICATION.py`
   - `/home/mattb/MaricopaPropertySearch/launch_gui_fixed.py`
   - `/home/mattb/MaricopaPropertySearch/simple_gui_test.py`
   - `/home/mattb/MaricopaPropertySearch/scripts/LAUNCH_GUI_APPLICATION.py`

2. **API Client Implementations**
   - `/home/mattb/MaricopaPropertySearch/src/api_client.py`
   - `/home/mattb/MaricopaPropertySearch/src/api_client_backup.py`
   - `/home/mattb/MaricopaPropertySearch/src/api_client_original.py`
   - `/home/mattb/MaricopaPropertySearch/src/api_client_unified.py`
   - `/home/mattb/MaricopaPropertySearch/src/batch_api_client.py`
   - `/home/mattb/MaricopaPropertySearch/src/parallel_api_client.py`

3. **Data Collectors**
   - `/home/mattb/MaricopaPropertySearch/src/background_data_collector.py`
   - `/home/mattb/MaricopaPropertySearch/src/automatic_data_collector.py`
   - `/home/mattb/MaricopaPropertySearch/src/improved_automatic_data_collector.py`
   - `/home/mattb/MaricopaPropertySearch/src/performance_optimized_data_collector.py`

4. **Database Managers**
   - `/home/mattb/MaricopaPropertySearch/src/database_manager.py`
   - `/home/mattb/MaricopaPropertySearch/src/threadsafe_database_manager.py`

5. **Web Scrapers**
   - `/home/mattb/MaricopaPropertySearch/src/web_scraper.py`
   - `/home/mattb/MaricopaPropertySearch/src/optimized_web_scraper.py`
   - `/home/mattb/MaricopaPropertySearch/src/parallel_web_scraper.py`
   - `/home/mattb/MaricopaPropertySearch/src/tax_scraper.py`
   - `/home/mattb/MaricopaPropertySearch/src/recorder_scraper.py`

6. **GUI Components**
   - `/home/mattb/MaricopaPropertySearch/src/gui/enhanced_main_window.py`
   - `/home/mattb/MaricopaPropertySearch/src/gui/enhanced_main_window_fixed.py`
   - `/home/mattb/MaricopaPropertySearch/src/gui/enhanced_main_window_backup.py`
   - `/home/mattb/MaricopaPropertySearch/src/gui/refresh_crash_fix.py`
   - `/home/mattb/MaricopaPropertySearch/src/gui/refresh_patch.py`

7. **Batch Processing**
   - `/home/mattb/MaricopaPropertySearch/src/batch_processing_manager.py`
   - `/home/mattb/MaricopaPropertySearch/src/batch_search_engine.py`
   - `/home/mattb/MaricopaPropertySearch/src/batch_search_integration.py`
   - `/home/mattb/MaricopaPropertySearch/src/enhanced_batch_search_dialog.py`

8. **Testing Scripts**
   - Multiple test files in `/tests/` directory
   - Various test scripts in root directory
   - Test scripts in `/scripts/` directory

9. **Fix/Migration Scripts**
   - Multiple fix scripts for various issues
   - Migration and cleanup scripts

10. **Configuration & Utilities**
    - `/home/mattb/MaricopaPropertySearch/src/config_manager.py`
    - `/home/mattb/MaricopaPropertySearch/src/enhanced_config_manager.py`
    - `/home/mattb/MaricopaPropertySearch/src/logging_config.py`
    - `/home/mattb/MaricopaPropertySearch/src/search_cache.py`

## Phase 2: Script Consolidation (DRY Implementation)

### Target Consolidations:
1. **API Client** → Single unified API client with all best features
2. **Data Collector** → One intelligent collector with multiple modes
3. **Web Scraper** → Unified scraper with parallel capabilities
4. **GUI Window** → Single enhanced main window implementation
5. **Database Manager** → Thread-safe unified manager
6. **Batch Processing** → Consolidated batch system
7. **Config Manager** → Single enhanced configuration system

## Phase 3: GUI Testing & Optimization

### Testing Checklist:
- [ ] Property search functionality
- [ ] Tax information retrieval
- [ ] Sales history display
- [ ] Document links
- [ ] Batch processing
- [ ] Export functionality
- [ ] API switching
- [ ] Error handling
- [ ] Performance metrics
- [ ] UI responsiveness

## Phase 4: Documentation & Cleanup

### Documentation Updates Required:
1. Update all path references
2. Create new README with current architecture
3. API documentation updates
4. Installation guide revision
5. User guide creation
6. Developer documentation
7. Changelog generation

### Cleanup Tasks:
- Remove deprecated scripts
- Delete backup files
- Clean up test files
- Archive old implementations
- Update .gitignore

## Next Immediate Actions

1. **Fix Path Issues** (PathMigrationSpecialist)
   - Convert all Windows paths in documentation
   - Update any hardcoded paths in Python scripts
   - Verify all file references work correctly

2. **Complete Script Inventory** (ScriptConsolidationArchitect)
   - Analyze each script's functionality
   - Identify best implementations
   - Create consolidation plan

3. **Test Main Application** (GUITestingSpecialist)
   - Run RUN_APPLICATION.py
   - Document any errors
   - Create fix list

## Memory & Checkpoint Integration

- Use checkpoint system for progress tracking
- Store decisions in memory system
- Create git commits at major milestones
- Generate checkpoints after each phase

## Risk Assessment

### High Priority Issues:
1. Path conversion breaking file references
2. Script consolidation losing functionality
3. GUI components not working after migration

### Mitigation Strategies:
1. Create comprehensive backups before changes
2. Test each consolidation thoroughly
3. Incremental changes with validation

## Success Criteria

- [ ] All paths converted to Linux format
- [ ] Scripts consolidated following DRY principle
- [ ] GUI fully functional with all features working
- [ ] Performance improved by at least 20%
- [ ] Documentation complete and accurate
- [ ] No duplicate or redundant files
- [ ] Clean, maintainable codebase

## Timeline Estimate

- Phase 1: 2-3 hours
- Phase 2: 3-4 hours
- Phase 3: 2-3 hours
- Phase 4: 2 hours

**Total Estimated Time**: 9-12 hours

---
*Document generated by SPARC Swarm System*
*Last Updated: 2025-09-18 04:18:00 PST*