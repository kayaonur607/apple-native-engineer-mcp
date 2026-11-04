#!/usr/bin/env node
/**
 * Apple Native Engineer — Model Context Protocol (MCP) Server
 * Exposes executable Apple development, audit, and App Store Connect tools
 * over the standard stdio JSON-RPC 2.0 protocol.
 */

import { execFile } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import readline from 'node:readline';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, '../../..');

const TOOLS = [
  {
    name: 'inspect_apple_project',
    description: 'Inspects an Xcode project or Swift Package to analyze structure, frameworks, and architecture.',
    inputSchema: {
      type: 'object',
      properties: {
        path: { type: 'string', description: 'Path to project directory (default: current directory)' }
      }
    }
  },
  {
    name: 'validate_app_icon',
    description: 'Validates an App Store icon asset for exact 1024x1024 dimensions, PNG signature, and zero alpha transparency.',
    inputSchema: {
      type: 'object',
      properties: {
        icon_path: { type: 'string', description: 'Path to app icon PNG file' }
      },
      required: ['icon_path']
    }
  },
  {
    name: 'validate_app_metadata',
    description: 'Validates App Store metadata JSON for character limits, mandatory URLs, and keyword optimization.',
    inputSchema: {
      type: 'object',
      properties: {
        metadata_path: { type: 'string', description: 'Path to metadata JSON file' }
      },
      required: ['metadata_path']
    }
  },
  {
    name: 'audit_privacy_manifest',
    description: 'Scans source code for Apple Required-Reason APIs and verifies PrivacyInfo.xcprivacy declarations.',
    inputSchema: {
      type: 'object',
      properties: {
        path: { type: 'string', description: 'Path to project directory' }
      }
    }
  },
  {
    name: 'generate_release_readiness_report',
    description: 'Evaluates project, metadata, assets, and privacy compliance to produce a complete App Store release report.',
    inputSchema: {
      type: 'object',
      properties: {
        path: { type: 'string', description: 'Path to project directory' },
        metadata_path: { type: 'string', description: 'Optional path to metadata JSON' },
        icon_path: { type: 'string', description: 'Optional path to 1024x1024 icon' }
      }
    }
  },
  {
    name: 'connect_app_store_connect',
    description: 'Verifies connection to the official Apple App Store Connect REST API.',
    inputSchema: {
      type: 'object',
      properties: {
        mock_mode: { type: 'boolean', description: 'Run in mock diagnostic mode (default: false)' }
      }
    }
  },
  {
    name: 'list_applications',
    description: 'Lists registered applications in the connected App Store Connect account.',
    inputSchema: {
      type: 'object',
      properties: {
        mock_mode: { type: 'boolean', description: 'Run in mock diagnostic mode' }
      }
    }
  },
  {
    name: 'inspect_app_version',
    description: 'Inspects current versions, localizations, and submission states for an application.',
    inputSchema: {
      type: 'object',
      properties: {
        app_id: { type: 'string', description: 'Application ID or Bundle Identifier' },
        mock_mode: { type: 'boolean', description: 'Run in mock mode' }
      },
      required: ['app_id']
    }
  },
  {
    name: 'check_project_localization',
    description: 'Audits Swift files for hardcoded strings, non-RTL padding (.left/.right), and String Catalog completeness.',
    inputSchema: {
      type: 'object',
      properties: {
        path: { type: 'string', description: 'Path to project directory (default: current directory)' }
      }
    }
  },
  {
    name: 'validate_project_widgets',
    description: 'Validates WidgetKit and ActivityKit Live Activities for Dynamic Island completeness and Info.plist flags.',
    inputSchema: {
      type: 'object',
      properties: {
        path: { type: 'string', description: 'Path to project directory (default: current directory)' }
      }
    }
  }
];

function runPythonScript(scriptRelPath, args = []) {
  return new Promise((resolve) => {
    const fullScriptPath = path.join(REPO_ROOT, scriptRelPath);
    execFile('python3', [fullScriptPath, ...args, '--json'], { maxBuffer: 10 * 1024 * 1024 }, (err, stdout, stderr) => {
      if (err && !stdout) {
        resolve({ error: err.message, stderr });
      } else {
        try {
          const parsed = JSON.parse(stdout);
          resolve(parsed);
        } catch {
          resolve({ output: stdout || stderr });
        }
      }
    });
  });
}

async function handleToolCall(name, args) {
  switch (name) {
    case 'inspect_apple_project':
      return await runPythonScript('tools/project-inspector/inspect_project.py', [args?.path || '.']);
    case 'validate_app_icon':
      return await runPythonScript('tools/asset-validator/validate_assets.py', ['--icon', args.icon_path]);
    case 'validate_app_metadata':
      return await runPythonScript('tools/metadata-validator/validate_metadata.py', [args.metadata_path]);
    case 'audit_privacy_manifest':
      return await runPythonScript('tools/privacy-auditor/audit_privacy.py', [args?.path || '.']);
    case 'generate_release_readiness_report': {
      const cliArgs = [args?.path || '.'];
      if (args?.metadata_path) cliArgs.push('--metadata', args.metadata_path);
      if (args?.icon_path) cliArgs.push('--icon', args.icon_path);
      return await runPythonScript('tools/release-readiness/generate_report.py', cliArgs);
    }
    case 'connect_app_store_connect': {
      const cliArgs = ['verify'];
      if (args?.mock_mode) cliArgs.unshift('--mock');
      return await runPythonScript('tools/app-store-connect/cli.py', cliArgs);
    }
    case 'list_applications': {
      const cliArgs = ['list-apps'];
      if (args?.mock_mode) cliArgs.unshift('--mock');
      return await runPythonScript('tools/app-store-connect/cli.py', cliArgs);
    }
    case 'inspect_app_version': {
      const cliArgs = ['inspect-version', '--app', args.app_id];
      if (args?.mock_mode) cliArgs.unshift('--mock');
      return await runPythonScript('tools/app-store-connect/cli.py', cliArgs);
    }
    case 'check_project_localization':
      return await runPythonScript('tools/localization-checker/check_localization.py', ['--project-dir', args?.path || '.']);
    case 'validate_project_widgets':
      return await runPythonScript('tools/widget-validator/validate_widget.py', ['--project-dir', args?.path || '.']);
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

rl.on('line', async (line) => {
  if (!line.trim()) return;
  try {
    const msg = JSON.parse(line);
    const { id, method, params } = msg;

    if (method === 'initialize') {
      const response = {
        jsonrpc: '2.0',
        id,
        result: {
          protocolVersion: '2024-11-05',
          capabilities: { tools: {} },
          serverInfo: {
            name: 'apple-native-engineer-mcp',
            version: '1.0.0'
          }
        }
      };
      process.stdout.write(JSON.stringify(response) + '\n');
    } else if (method === 'tools/list') {
      const response = {
        jsonrpc: '2.0',
        id,
        result: { tools: TOOLS }
      };
      process.stdout.write(JSON.stringify(response) + '\n');
    } else if (method === 'tools/call') {
      const { name, arguments: toolArgs } = params;
      try {
        const result = await handleToolCall(name, toolArgs);
        const response = {
          jsonrpc: '2.0',
          id,
          result: {
            content: [{ type: 'text', text: JSON.stringify(result, null, 2) }]
          }
        };
        process.stdout.write(JSON.stringify(response) + '\n');
      } catch (err) {
        const response = {
          jsonrpc: '2.0',
          id,
          error: { code: -32603, message: err.message }
        };
        process.stdout.write(JSON.stringify(response) + '\n');
      }
    } else {
      // Respond to notifications or unhandled methods
      if (id !== undefined) {
        const response = {
          jsonrpc: '2.0',
          id,
          error: { code: -32601, message: `Method not found: ${method}` }
        };
        process.stdout.write(JSON.stringify(response) + '\n');
      }
    }
  } catch (err) {
    // Malformed JSON
  }
});
