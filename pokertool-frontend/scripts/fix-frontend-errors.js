#!/usr/bin/env node
/**
 * Automated Frontend Error Fixer
 * Scans TypeScript/ESLint errors and applies automated fixes
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// ANSI colors for output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  cyan: '\x1b[36m',
  blue: '\x1b[34m',
};

const log = {
  info: (msg) => console.log(`${colors.cyan}ℹ${colors.reset} ${msg}`),
  success: (msg) => console.log(`${colors.green}✓${colors.reset} ${msg}`),
  warning: (msg) => console.log(`${colors.yellow}⚠${colors.reset} ${msg}`),
  error: (msg) => console.log(`${colors.red}✗${colors.reset} ${msg}`),
  header: (msg) => console.log(`\n${colors.bright}${colors.blue}${msg}${colors.reset}\n`),
};

// Statistics
const stats = {
  filesScanned: 0,
  errorsFound: 0,
  errorsFixed: 0,
  warningsFixed: 0,
  filesFailed: [],
};

// Error patterns to fix
const fixPatterns = {
  // Unused imports/variables
  unusedImport: {
    pattern: /^(\s*)import\s+\{([^}]+)\}\s+from\s+['"]([^'"]+)['"];?$/gm,
    description: 'Remove unused imports',
  },

  // Unused variables
  unusedVar: {
    lines: [
      /Line \d+:\d+:\s+'([^']+)' is (defined|assigned a value) but never used/,
      /@typescript-eslint\/no-unused-vars/,
    ],
    description: 'Remove unused variables',
  },
};

// Get TypeScript errors
function getTypeScriptErrors() {
  log.header('Step 1: Collecting TypeScript Errors');

  try {
    execSync('npx tsc --noEmit', { encoding: 'utf-8', stdio: 'pipe' });
    log.success('No TypeScript errors found!');
    return { stdout: '', errors: [] };
  } catch (error) {
    const output = error.stdout || error.stderr || '';
    log.info(`Found ${output.split('error TS').length - 1} TypeScript errors`);
    return { stdout: output, errors: parseTypeScriptErrors(output) };
  }
}

// Parse TypeScript error output
function parseTypeScriptErrors(output) {
  const errors = [];
  const lines = output.split('\n');

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Match error format: src/path/file.tsx:line:col
    const match = line.match(/^(.+\.tsx?)\((\d+),(\d+)\):\s*error\s+(TS\d+):\s*(.+)$/);
    if (match) {
      errors.push({
        file: match[1],
        line: parseInt(match[2]),
        col: parseInt(match[3]),
        code: match[4],
        message: match[5],
      });
    }

    // Alternative format: ERROR in src/path/file.tsx:line:col
    const altMatch = line.match(/^ERROR in (.+\.tsx?):(\d+):(\d+)$/);
    if (altMatch && i + 1 < lines.length) {
      const nextLine = lines[i + 1];
      const codeMatch = nextLine.match(/^(TS\d+):\s*(.+)$/);
      if (codeMatch) {
        errors.push({
          file: altMatch[1],
          line: parseInt(altMatch[2]),
          col: parseInt(altMatch[3]),
          code: codeMatch[1],
          message: codeMatch[2],
        });
      }
    }
  }

  return errors;
}

// Get ESLint warnings
function getESLintWarnings() {
  log.header('Step 2: Collecting ESLint Warnings');

  try {
    const output = execSync('npm run build 2>&1', {
      encoding: 'utf-8',
      stdio: 'pipe',
      maxBuffer: 10 * 1024 * 1024
    });

    return parseESLintWarnings(output);
  } catch (error) {
    const output = error.stdout || error.stderr || '';
    return parseESLintWarnings(output);
  }
}

// Parse ESLint warning output
function parseESLintWarnings(output) {
  const warnings = [];
  const lines = output.split('\n');

  for (const line of lines) {
    // Match: src/components/File.tsx
    //   Line X:Y:  'varName' is defined but never used  @typescript-eslint/no-unused-vars
    const match = line.match(/Line (\d+):(\d+):\s+'([^']+)' is (defined|assigned a value) but never used/);
    if (match) {
      // Find the file from previous lines
      let file = '';
      const lineIdx = lines.indexOf(line);
      for (let i = lineIdx - 1; i >= Math.max(0, lineIdx - 10); i--) {
        const fileMatch = lines[i].match(/^(src\/.+\.tsx?)$/);
        if (fileMatch) {
          file = fileMatch[1];
          break;
        }
      }

      if (file) {
        warnings.push({
          file,
          line: parseInt(match[1]),
          col: parseInt(match[2]),
          varName: match[3],
          type: 'unused-var',
        });
      }
    }
  }

  log.info(`Found ${warnings.length} ESLint warnings`);
  return warnings;
}

// Fix unused imports
function fixUnusedImports(filePath, unusedVars) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.split('\n');
  let modified = false;

  const unusedNames = new Set(unusedVars.map(v => v.varName));

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const importMatch = line.match(/^(\s*)import\s+\{([^}]+)\}\s+from\s+(['"][^'"]+['"];?)$/);

    if (importMatch) {
      const indent = importMatch[1];
      const imports = importMatch[2].split(',').map(s => s.trim());
      const fromClause = importMatch[3];

      const usedImports = imports.filter(imp => {
        const name = imp.split(' as ')[0].trim();
        return !unusedNames.has(name);
      });

      if (usedImports.length !== imports.length) {
        if (usedImports.length === 0) {
          // Remove entire import line
          lines[i] = '';
          modified = true;
          stats.warningsFixed++;
        } else {
          // Keep only used imports
          lines[i] = `${indent}import { ${usedImports.join(', ')} } from ${fromClause}`;
          modified = true;
          stats.warningsFixed++;
        }
      }
    }
  }

  if (modified) {
    fs.writeFileSync(filePath, lines.join('\n'), 'utf-8');
    return true;
  }

  return false;
}

// Fix unused variables
function fixUnusedVariables(filePath, unusedVars) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.split('\n');
  let modified = false;

  for (const warning of unusedVars) {
    if (warning.line > 0 && warning.line <= lines.length) {
      const line = lines[warning.line - 1];

      // Check if it's a destructured assignment
      const destructureMatch = line.match(/const\s+\[([^\]]+)\]\s*=\s*useState/);
      if (destructureMatch) {
        const vars = destructureMatch[1].split(',').map(s => s.trim());
        if (vars.includes(warning.varName)) {
          // Replace unused with underscore
          const newVars = vars.map(v => v === warning.varName ? '_' : v);
          lines[warning.line - 1] = line.replace(destructureMatch[1], newVars.join(', '));
          modified = true;
          stats.warningsFixed++;
        }
      }

      // Check if it's a simple const declaration that's unused
      const constMatch = line.match(/^\s*const\s+(\w+)\s*=/);
      if (constMatch && constMatch[1] === warning.varName) {
        // Comment out the line
        lines[warning.line - 1] = `  // ${line.trim()} // Unused - commented out by auto-fixer`;
        modified = true;
        stats.warningsFixed++;
      }
    }
  }

  if (modified) {
    fs.writeFileSync(filePath, lines.join('\n'), 'utf-8');
    return true;
  }

  return false;
}

// Process files
function processFiles(warnings) {
  log.header('Step 3: Applying Fixes');

  // Group warnings by file
  const fileWarnings = {};
  for (const warning of warnings) {
    if (!fileWarnings[warning.file]) {
      fileWarnings[warning.file] = [];
    }
    fileWarnings[warning.file].push(warning);
  }

  // Process each file
  for (const [file, warns] of Object.entries(fileWarnings)) {
    const fullPath = path.join(process.cwd(), file);

    if (!fs.existsSync(fullPath)) {
      log.warning(`File not found: ${file}`);
      continue;
    }

    stats.filesScanned++;
    log.info(`Processing: ${file}`);

    const unusedVars = warns.filter(w => w.type === 'unused-var');

    try {
      let fixed = false;

      // Fix unused imports
      if (fixUnusedImports(fullPath, unusedVars)) {
        fixed = true;
      }

      // Fix unused variables
      if (fixUnusedVariables(fullPath, unusedVars)) {
        fixed = true;
      }

      if (fixed) {
        log.success(`  Fixed ${warns.length} issues in ${file}`);
      }
    } catch (error) {
      log.error(`  Failed to fix ${file}: ${error.message}`);
      stats.filesFailed.push(file);
    }
  }
}

// Generate report
function generateReport() {
  log.header('Fix Summary');

  console.log(`${colors.bright}Files Scanned:${colors.reset} ${stats.filesScanned}`);
  console.log(`${colors.green}Warnings Fixed:${colors.reset} ${stats.warningsFixed}`);

  if (stats.filesFailed.length > 0) {
    console.log(`${colors.red}Files Failed:${colors.reset} ${stats.filesFailed.length}`);
    stats.filesFailed.forEach(f => console.log(`  - ${f}`));
  }

  console.log('');
}

// Main execution
async function main() {
  console.log(`
${colors.bright}${colors.blue}╔═══════════════════════════════════════════════════════════╗
║         Automated Frontend Error Fixer v1.0.0            ║
║              PokerTool Frontend Maintenance               ║
╚═══════════════════════════════════════════════════════════╝${colors.reset}
  `);

  // Get errors
  const tsErrors = getTypeScriptErrors();
  const eslintWarnings = getESLintWarnings();

  stats.errorsFound = tsErrors.errors.length;

  // Process fixes
  if (eslintWarnings.length > 0) {
    processFiles(eslintWarnings);
  } else {
    log.success('No fixable warnings found!');
  }

  // Generate report
  generateReport();

  // Final verification
  log.header('Step 4: Final Verification');
  log.info('Running TypeScript compiler to verify fixes...');

  try {
    execSync('npx tsc --noEmit', { encoding: 'utf-8', stdio: 'inherit' });
    log.success('All TypeScript errors resolved!');
  } catch (error) {
    log.warning('Some TypeScript errors remain. Review manually.');
  }

  console.log(`\n${colors.bright}${colors.green}✓ Fix process complete!${colors.reset}\n`);
}

// Run
main().catch(error => {
  log.error(`Fatal error: ${error.message}`);
  process.exit(1);
});
