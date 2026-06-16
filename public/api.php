<?php
/**
 * JSON API for the Tibetan calendar converter.
 *
 * Receives the conversion request as GET/POST parameters, shells out to the
 * stdlib-only convert.py via lib.php, and relays its JSON.
 */

require __DIR__ . '/lib.php';

header('Content-Type: application/json; charset=utf-8');

function fail(string $message): void
{
    echo json_encode(['ok' => false, 'error' => $message]);
    exit;
}

$tradition = ($_REQUEST['tradition'] ?? 'phugpa') === 'tsurphu' ? 'tsurphu' : 'phugpa';
$mode = $_REQUEST['mode'] ?? '';

$args = ['--tradition', $tradition];

if ($mode === 'g2t') {
    $year = filter_var($_REQUEST['year'] ?? null, FILTER_VALIDATE_INT);
    $month = filter_var($_REQUEST['month'] ?? null, FILTER_VALIDATE_INT);
    $day = filter_var($_REQUEST['day'] ?? null, FILTER_VALIDATE_INT);
    if ($year === false || $month === false || $day === false) {
        fail('Please enter a valid Western year, month and day.');
    }
    // convert.py validates the calendar date itself (e.g. rejects 30 February).
    $date = sprintf('%04d-%02d-%02d', $year, $month, $day);
    array_push($args, 'g2t', '--date', $date);
} elseif ($mode === 't2g') {
    $year = filter_var($_REQUEST['year'] ?? null, FILTER_VALIDATE_INT);
    $month = filter_var($_REQUEST['month'] ?? null, FILTER_VALIDATE_INT);
    $day = filter_var($_REQUEST['day'] ?? null, FILTER_VALIDATE_INT);
    if ($year === false || $month === false || $day === false) {
        fail('Please enter a valid Tibetan year, month and day.');
    }
    array_push($args, 't2g',
        '--year', (string) $year,
        '--month', (string) $month,
        '--day', (string) $day);
} else {
    fail('Unknown conversion mode.');
}

echo json_encode(run_convert($args));
