# RoughBench Overview

This is the static benchmark explorer POC. It reads generated JSON from
`docs/assets/data/docs_data.json`.

<div class="rb-grid rb-top-cards" id="rb-summary-cards"></div>

## Awards

<p class="rb-muted">
Fun auto-calculated badges from the current clean run set. These update whenever the docs data is rebuilt.
</p>

<div class="rb-grid rb-top-cards" id="rb-awards-grid"></div>

## Overall Leaderboard

<p class="rb-muted" id="rb-overall-note"></p>

<div class="rb-table-wrap">
  <table class="rb-table" id="rb-overall-table"></table>
</div>

## Efficiency Leaderboard

<p class="rb-muted">
Efficiency only includes complete, untainted current full-suite runs above the pass mark, and ranks them by utility per 1k tokens, where utility = suite max demerits minus observed demerits.
</p>

<div class="rb-table-wrap">
  <table class="rb-table" id="rb-efficiency-table"></table>
</div>

## Token Composition

<p class="rb-muted">
Grey is prompt, purple is reasoning, green is final answer. When a provider does not expose reasoning telemetry, completion is shown as an unsplit segment instead of a fake think split.
</p>

<div class="rb-panel">
  <div id="rb-token-mix-list"></div>
</div>

## Model Shape

<p class="rb-muted">
Higher is better. Category scores are normalized as quality percentages within each meta-category.
</p>

<div class="rb-controls">
  <label for="rb-model-select">Model run</label>
  <select id="rb-model-select"></select>
</div>

<div class="rb-controls rb-inline-controls">
  <div>
    <label for="rb-radar-mode">Radar mode</label>
    <select id="rb-radar-mode">
      <option value="absolute">Absolute quality</option>
      <option value="relative">Relative to best clean</option>
    </select>
  </div>
</div>

<div class="rb-two-col">
  <div class="rb-panel">
    <h3>Category Radar</h3>
    <p class="rb-muted" id="rb-radar-note"></p>
    <div id="rb-radar"></div>
  </div>
  <div class="rb-panel">
    <h3>Category Breakdown</h3>
    <div class="rb-table-wrap">
      <table class="rb-table" id="rb-category-table"></table>
    </div>
  </div>
</div>
