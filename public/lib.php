<?php
/**
 * Shared server-side helpers for the Tibetan calendar converter.
 *
 * Both api.php (live conversions) and index.php (seeding form defaults) run the
 * stdlib-only convert.py through these functions. Stand-alone: the only server
 * requirement is a Python 3 interpreter (no extensions, no pip packages).
 */

// Optional override: create config.php defining PYTHON_BIN with a full path.
$config = __DIR__ . '/config.php';
if (is_file($config)) {
    require $config;
}

/**
 * Locate a usable `python3` interpreter, or null if none is found. Override by
 * creating a `config.php` next to this file that defines PYTHON_BIN, e.g.:
 *   <?php define('PYTHON_BIN', '/usr/bin/python3');
 */
function python_bin(): ?string
{
    if (defined('PYTHON_BIN')) {
        return PYTHON_BIN;
    }
    $candidates = ['python3', '/usr/bin/python3', '/usr/local/bin/python3',
                   '/opt/homebrew/bin/python3'];
    foreach ($candidates as $cand) {
        // `command -v` resolves names on PATH and absolute paths alike.
        $resolved = trim((string) @shell_exec('command -v ' . escapeshellarg($cand) . ' 2>/dev/null'));
        if ($resolved !== '') {
            return $resolved;
        }
    }
    return null;
}

/**
 * Run convert.py with the given trailing argument list (everything after the
 * script path). Returns the decoded JSON object, or an
 * ['ok' => false, 'error' => ...] array on any failure.
 *
 * @param string[] $convertArgs
 * @return array<string, mixed>
 */
function run_convert(array $convertArgs): array
{
    $python = python_bin();
    if ($python === null) {
        return ['ok' => false, 'error' => 'No Python 3 interpreter found on the '
            . 'server. Create config.php defining PYTHON_BIN with the full path.'];
    }

    $args = array_merge([$python, __DIR__ . '/convert.py'], $convertArgs);
    $cmd = implode(' ', array_map('escapeshellarg', $args)) . ' 2>&1';
    $output = shell_exec($cmd);

    if ($output === null || trim($output) === '') {
        return ['ok' => false, 'error' => 'The converter produced no output. '
            . 'Check the server Python setup.'];
    }

    $decoded = json_decode($output, true);
    if ($decoded === null) {
        return ['ok' => false, 'error' => 'Converter error: ' . trim($output)];
    }
    return $decoded;
}
