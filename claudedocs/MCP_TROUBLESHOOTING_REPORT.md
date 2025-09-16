# MCP Server Troubleshooting Report
Date: 2025-09-13

## Issues Resolved

### 1. VSCode Settings Conflict ✅
**Problem**: 
- `terminal.integrated: false` disabled the integrated terminal
- `terminal.integrated.automationProfile.windows` was being ignored due to the disabled terminal

**Solution**:
- Changed `terminal.integrated: false` to `terminal.integrated.enabled: true`
- Updated WSL path from `/home/mattb` to `wsl.exe` with proper arguments
- Settings now properly configure WSL integration

### 2. Crashpad Error ✅
**Problem**:
- `CreateFile: The system cannot find the file specified` error
- Related to MCP server initialization failure

**Root Cause**:
- The `fetch` MCP server package (`@modelcontextprotocol/server-fetch`) doesn't exist in npm registry
- This was causing initialization failures that triggered crashpad errors

**Solution**:
- Removed the non-existent `fetch` MCP server from configuration
- Crashpad errors should no longer occur with valid MCP servers

### 3. MCP Server Configuration ✅
**Current Status**:
- `memory` server: ✓ Connected and working
- `claude-mem` server: ✓ Connected and working
- `fetch` server: Removed (package doesn't exist)

## Verification Commands

```bash
# Check MCP server status
claude mcp list

# Restart Claude CLI to apply changes
claude restart

# Verify Node.js environment
node --version  # v24.4.1
npm --version   # 11.4.1
```

## Additional Notes

1. The `@modelcontextprotocol/server-fetch` package doesn't exist in the npm registry
2. Available MCP packages include:
   - `@modelcontextprotocol/sdk` (core SDK)
   - `figma-mcp` (Figma integration)
   - `ref-tools-mcp` (Reference tools)
   - `puppeteer-mcp-server` (Browser automation)

3. If you need fetch/HTTP capabilities, consider:
   - Using a different MCP server that provides HTTP functionality
   - Installing a properly named and available MCP server package

## Prevention Tips

1. Always verify package existence before adding MCP servers:
   ```bash
   npm search "@modelcontextprotocol"
   ```

2. Keep VSCode settings consistent - avoid conflicting terminal configurations

3. When adding new MCP servers, test them directly first:
   ```bash
   npx -y [package-name] --version
   ```

## Resolution Status
All identified issues have been successfully resolved. The Claude CLI should now function without errors.