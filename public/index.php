<?php
require __DIR__ . '/lib.php';

$today = date('Y-m-d');
$gYear = (int) date('Y');
$gMonth = (int) date('n');
$gDay = (int) date('j');

// Seed the Tibetan -> Western form with *today's* Tibetan date (Phugpa, the
// default tradition) instead of an arbitrary placeholder. Falls back to a
// sensible default if the converter is unavailable.
$seed = run_convert(['--tradition', 'phugpa', 'g2t', '--date', $today]);
if (!empty($seed['ok'])) {
    $r = $seed['result'];
    $defYear = (int) $r['year'];
    $defMonth = (int) $r['month'];
    $defDay = (int) $r['day'];
} else {
    $defYear = (int) date('Y');
    $defMonth = 1;
    $defDay = 1;
}

// Labelled Tibetan-year options for the picker, e.g. "2026/27 · Fire Male Horse".
$yearRange = ['from' => 1900, 'to' => 2100];
$names = run_convert(['names', '--from', (string) $yearRange['from'],
                      '--to', (string) $yearRange['to']]);
$yearOptions = !empty($names['ok']) ? $names['years'] : [];
?>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tibetan ↔ Western Calendar Converter</title>
<meta name="description" content="Convert dates between the Tibetan lunisolar calendar (Phugpa and Tsurphu traditions) and the Western (Gregorian) calendar.">
<link rel="stylesheet" href="style.css">
</head>
<body>
<main class="wrap">
  <header class="head">
    <h1>Tibetan&nbsp;↔&nbsp;Western Calendar</h1>
    <p class="tagline">Convert dates between the Tibetan lunisolar calendar and the Western (Gregorian) calendar.</p>

    <fieldset class="tradition" aria-label="Tibetan tradition">
      <label class="seg">
        <input type="radio" name="tradition" value="phugpa" checked>
        <span>Phugpa</span>
      </label>
      <label class="seg">
        <input type="radio" name="tradition" value="tsurphu">
        <span>Tsurphu</span>
      </label>
    </fieldset>
  </header>

  <section class="cards">
    <!-- Western -> Tibetan -->
    <form class="card" id="form-g2t" autocomplete="off">
      <h2>Western&nbsp;→&nbsp;Tibetan</h2>
      <label class="field">
        <span>Year</span>
        <input type="number" name="year" value="<?= $gYear ?>" min="1" max="3000" required>
      </label>
      <div class="field-row">
        <label class="field">
          <span>Month</span>
          <select name="month">
            <?php for ($m = 1; $m <= 12; $m++): ?>
              <option value="<?= $m ?>"<?= $m === $gMonth ? ' selected' : '' ?>><?= $m ?></option>
            <?php endfor; ?>
          </select>
        </label>
        <label class="field">
          <span>Day</span>
          <select name="day">
            <?php for ($d = 1; $d <= 31; $d++): ?>
              <option value="<?= $d ?>"<?= $d === $gDay ? ' selected' : '' ?>><?= $d ?></option>
            <?php endfor; ?>
          </select>
        </label>
      </div>
      <button type="submit">Convert</button>
      <div class="result" id="result-g2t" hidden></div>
    </form>

    <!-- Tibetan -> Western -->
    <form class="card" id="form-t2g" autocomplete="off">
      <h2>Tibetan&nbsp;→&nbsp;Western</h2>
      <label class="field">
        <span>Year</span>
        <?php if ($yearOptions): ?>
          <select name="year">
            <?php foreach ($yearOptions as $y): ?>
              <option value="<?= $y['year'] ?>"<?= (int) $y['year'] === $defYear ? ' selected' : '' ?>><?= htmlspecialchars($y['label']) ?></option>
            <?php endforeach; ?>
          </select>
        <?php else: ?>
          <input type="number" name="year" value="<?= $defYear ?>" min="1" max="3000" required>
        <?php endif; ?>
      </label>
      <div class="field-row">
        <label class="field">
          <span>Tibetan month</span>
          <select name="month">
            <?php for ($m = 1; $m <= 12; $m++): ?>
              <option value="<?= $m ?>"<?= $m === $defMonth ? ' selected' : '' ?>><?= $m ?></option>
            <?php endfor; ?>
          </select>
        </label>
        <label class="field">
          <span>Tibetan day</span>
          <select name="day">
            <?php for ($d = 1; $d <= 30; $d++): ?>
              <option value="<?= $d ?>"<?= $d === $defDay ? ' selected' : '' ?>><?= $d ?></option>
            <?php endfor; ?>
          </select>
        </label>
      </div>
      <button type="submit">Convert</button>
      <div class="result" id="result-t2g" hidden></div>
    </form>
  </section>

  <footer class="foot">
    <ul>
      <li>
      Calculations follow Svante Janson,
      <a href="https://arxiv.org/abs/1401.6285" rel="noopener" target="_blank">“Tibetan Calendar Mathematics”</a>
      (arXiv:1401.6285), implementing both the Phugpa and Tsurphu traditions.
            </li>
            <li>
      This converter is new and may contain errors. If you come across a date
      that looks wrong, I'd be grateful to hear about it —
      <!-- email assembled in JS to keep it away from scrapers -->
      <a id="feedback" data-user="martin.dudek" data-domain="gmail.com" href="#">please get in touch</a>.
            </li>
      <li>
            <a class="gh-link" href="https://github.com/dorjeduck/tibcal" rel="noopener" target="_blank">
        <svg class="gh-icon" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.65 7.65 0 014 0c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path></svg>
        Source on GitHub
      </a>
            </li>
    </p>
  </footer>
</main>

<script src="app.js"></script>
</body>
</html>
