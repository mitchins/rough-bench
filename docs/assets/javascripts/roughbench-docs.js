(async function () {
  const scriptUrl = new URL(document.currentScript.src);
  const dataUrl = new URL("../data/docs_data.json", scriptUrl);
  const response = await fetch(dataUrl);
  const data = await response.json();

  const taskMap = new Map((data.tasks || []).map((task) => [task.id, task]));
  const runMap = new Map((data.runs || []).map((run) => [run.run_id, run]));

  function number(value) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) {
      return "—";
    }
    return Number(value).toLocaleString();
  }

  function pct(value) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) {
      return "—";
    }
    return `${Number(value).toFixed(1)}%`;
  }

  function badge(run) {
    if (run.status !== "complete") {
      return `<span class="rb-badge rb-badge-partial">${run.status}</span>`;
    }
    if (run.tainted) {
      return `<span class="rb-badge rb-badge-tainted">tainted</span>`;
    }
    return `<span class="rb-badge rb-badge-clean">clean</span>`;
  }

  function awardPills(run) {
    const awards = run?.awards || [];
    if (!awards.length) {
      return "";
    }
    return `
      <div class="rb-award-pill-row">
        ${awards.map((award) => `<span class="rb-award-pill">${award.label}</span>`).join("")}
      </div>
    `;
  }

  function runLabel(run) {
    return `${run.title} (${run.run_id})`;
  }

  function bar(value) {
    const width = Math.max(0, Math.min(100, Number(value) || 0));
    return `
      <div class="rb-bar-track">
        <div class="rb-bar-fill" style="width:${width}%"></div>
      </div>
    `;
  }

  function renderTable(table, columns, rows) {
    const thead = `<thead><tr>${columns.map((column) => `<th>${column.label}</th>`).join("")}</tr></thead>`;
    const tbody = `<tbody>${rows
      .map(
        (row) =>
          `<tr>${columns
            .map((column) => `<td>${column.render ? column.render(row) : row[column.key] ?? ""}</td>`)
            .join("")}</tr>`,
      )
      .join("")}</tbody>`;
    table.innerHTML = thead + tbody;
  }

  function renderSummaryCards() {
    const root = document.getElementById("rb-summary-cards");
    if (!root) {
      return;
    }
    const runs = data.runs || [];
    const cleanRuns = runs.filter((run) => run.status === "complete" && !run.tainted && !run.failed_task_count);
    const cards = [
      ["Runs", number(runs.length), "Saved compare runs discovered under runs/"],
      ["Clean Runs", number(cleanRuns.length), "Complete, untainted, no task failures"],
      ["Tasks", number((data.tasks || []).length), "Benchmark leaves included in the export"],
      ["Categories", number((data.categories || []).length), "Top-level meta categories in the UI"],
    ];
    root.innerHTML = cards
      .map(
        ([title, value, note]) => `
          <section class="rb-card">
            <h3>${title}</h3>
            <div class="rb-card-value">${value}</div>
            <div class="rb-card-note">${note}</div>
          </section>
        `,
      )
      .join("");
  }

  function renderAwards() {
    const root = document.getElementById("rb-awards-grid");
    if (!root) {
      return;
    }
    const awards = data.awards || [];
    root.innerHTML = awards
      .map(
        (award) => `
          <section class="rb-card">
            <h3>${award.label}</h3>
            <div class="rb-card-value">${award.metric_display}</div>
            <div class="rb-card-note"><strong>${award.winner_title}</strong><br>${award.winner_model}</div>
            <div class="rb-card-note">${award.description}</div>
          </section>
        `,
      )
      .join("");
  }

  function renderOverviewTables() {
    const overall = document.getElementById("rb-overall-table");
    const efficiency = document.getElementById("rb-efficiency-table");
    if (overall) {
      renderTable(
        overall,
        [
          { label: "Rank", render: (_, index) => String(index + 1) },
          { label: "Run", render: (row) => `${runLabel(row)}<br><span class="rb-muted">${row.model}</span>${awardPills(row)}` },
          { label: "Status", render: (row) => badge(row) },
          { label: "Demerits", render: (row) => `${number(row.roughbench_demerits)} / ${number(row.suite_max_demerits)}` },
          { label: "Quality", render: (row) => pct(row.overall_quality) },
          { label: "Tokens", render: (row) => number(row.usage_total_tokens) },
          {
            label: "Efficiency",
            render: (row) =>
              row.demerits_per_1k_total_tokens !== null && row.demerits_per_1k_total_tokens !== undefined
                ? `${Number(row.demerits_per_1k_total_tokens).toFixed(2)} / 1k`
                : "—",
          },
        ],
        (data.leaderboards?.overall || []).map((row, index) => ({ ...row, __index: index })),
      );
      // patch rank column with index
      [...overall.querySelectorAll("tbody tr")].forEach((tr, index) => {
        tr.children[0].textContent = String(index + 1);
      });
    }
    if (efficiency) {
      renderTable(
        efficiency,
        [
          { label: "Rank", render: (_, index) => String(index + 1) },
          { label: "Run", render: (row) => `${runLabel(row)}<br><span class="rb-muted">${row.model}</span>${awardPills(row)}` },
          { label: "Demerits / 1k", render: (row) => Number(row.demerits_per_1k_total_tokens).toFixed(2) },
          { label: "Quality", render: (row) => pct(row.overall_quality) },
          { label: "Tokens", render: (row) => number(row.usage_total_tokens) },
          { label: "Status", render: (row) => badge(row) },
        ],
        (data.leaderboards?.efficiency || []).map((row, index) => ({ ...row, __index: index })),
      );
      [...efficiency.querySelectorAll("tbody tr")].forEach((tr, index) => {
        tr.children[0].textContent = String(index + 1);
      });
    }
  }

  function radarValue(run, categoryId, mode) {
    if (mode === "relative") {
      return Number(run.categories?.[categoryId]?.relative_quality || 0);
    }
    return Number(run.categories?.[categoryId]?.quality || 0);
  }

  function renderRadar(run, mode) {
    const root = document.getElementById("rb-radar");
    const note = document.getElementById("rb-radar-note");
    if (!root || !run) {
      return;
    }
    const categories = data.category_order || [];
    const labels = categories.map((id) => {
      const category = (data.categories || []).find((item) => item.id === id);
      return category ? category.label : id;
    });
    const values = categories.map((id) => radarValue(run, id, mode));
    const size = 420;
    const center = size / 2;
    const radius = 150;
    const levels = 5;
    const angleStep = (Math.PI * 2) / categories.length;

    function pointFor(index, valueRatio, offset = 0) {
      const angle = -Math.PI / 2 + index * angleStep + offset;
      const r = radius * valueRatio;
      return [center + Math.cos(angle) * r, center + Math.sin(angle) * r];
    }

    const gridPolys = [];
    for (let level = 1; level <= levels; level += 1) {
      const ratio = level / levels;
      const points = categories.map((_, index) => pointFor(index, ratio).join(",")).join(" ");
      gridPolys.push(`<polygon points="${points}" fill="none" stroke="#d5ddd9" stroke-width="1" />`);
    }

    const axes = categories
      .map((_, index) => {
        const [x, y] = pointFor(index, 1);
        const [lx, ly] = pointFor(index, 1.13);
        return `
          <line x1="${center}" y1="${center}" x2="${x}" y2="${y}" stroke="#c7d2cd" stroke-width="1" />
          <text x="${lx}" y="${ly}" text-anchor="middle" dominant-baseline="middle" font-size="12" fill="#5e6f69">${labels[index]}</text>
        `;
      })
      .join("");

    const dataPoints = values
      .map((value, index) => pointFor(index, Math.max(0, Math.min(100, value)) / 100).join(","))
      .join(" ");

    root.innerHTML = `
      <svg viewBox="0 0 ${size} ${size}" role="img" aria-label="Category radar for ${run.title}">
        ${gridPolys.join("")}
        ${axes}
        <polygon points="${dataPoints}" fill="rgba(11,107,87,0.18)" stroke="#0b6b57" stroke-width="3" />
      </svg>
    `;

    if (note) {
      if (mode === "relative") {
        note.textContent = "Relative radar: each category is scaled against the best clean run currently recorded in that category.";
      } else {
        note.textContent = "Absolute radar: category quality is shown directly as normalized benchmark quality.";
      }
    }
  }

  function renderCategoryTable(run) {
    const table = document.getElementById("rb-category-table");
    if (!table || !run) {
      return;
    }
    const rows = (data.category_order || []).map((categoryId) => {
      const row = run.categories?.[categoryId] || {};
      const category = (data.categories || []).find((item) => item.id === categoryId);
      return {
        label: category ? category.label : categoryId,
        quality: row.quality,
        demerits: row.demerits,
        max_demerits: row.max_demerits,
        task_count: row.task_count,
      };
    });
    renderTable(
      table,
      [
        { label: "Category", key: "label" },
        { label: "Quality", render: (row) => `${pct(row.quality)} ${bar(row.quality)}` },
        { label: "Demerits", render: (row) => `${number(row.demerits)} / ${number(row.max_demerits)}` },
        { label: "Tasks", render: (row) => number(row.task_count) },
      ],
      rows,
    );
  }

  function renderModelExplorer() {
    const select = document.getElementById("rb-model-select");
    const modeSelect = document.getElementById("rb-radar-mode");
    if (!select) {
      return;
    }
    const runs = data.leaderboards?.overall || [];
    select.innerHTML = runs.map((run) => `<option value="${run.run_id}">${runLabel(run)}</option>`).join("");
    const update = () => {
      const run = runMap.get(select.value);
      const mode = modeSelect?.value || "absolute";
      renderRadar(run, mode);
      renderCategoryTable(run);
    };
    select.addEventListener("change", update);
    modeSelect?.addEventListener("change", update);
    if (runs.length) {
      select.value = runs[0].run_id;
      update();
    }
  }

  function renderComparePage() {
    const selectA = document.getElementById("rb-compare-a");
    const selectB = document.getElementById("rb-compare-b");
    if (!selectA || !selectB) {
      return;
    }
    const runs = data.leaderboards?.overall || [];
    const options = runs.map((run) => `<option value="${run.run_id}">${runLabel(run)}</option>`).join("");
    selectA.innerHTML = options;
    selectB.innerHTML = options;
    if (runs.length > 1) {
      selectA.value = runs[0].run_id;
      selectB.value = runs[1].run_id;
    } else if (runs.length === 1) {
      selectA.value = runs[0].run_id;
      selectB.value = runs[0].run_id;
    }

    const compareCards = document.getElementById("rb-compare-cards");
    const categoryTable = document.getElementById("rb-compare-category-table");
    const betterA = document.getElementById("rb-compare-better-a");
    const betterB = document.getElementById("rb-compare-better-b");

    function render() {
      const runA = runMap.get(selectA.value);
      const runB = runMap.get(selectB.value);
      if (!runA || !runB) {
        return;
      }

      if (compareCards) {
        const cards = [runA, runB].map(
          (run) => `
            <section class="rb-card">
              <h3>${run.title}</h3>
              <div class="rb-card-value">${number(run.roughbench_demerits)} / ${number(run.suite_max_demerits)}</div>
              <div class="rb-card-note">${pct(run.overall_quality)} quality · ${number(run.usage_total_tokens)} tokens · ${badge(run)}</div>
            </section>
          `,
        );
        compareCards.innerHTML = cards.join("");
      }

      if (categoryTable) {
        const rows = (data.category_order || []).map((categoryId) => {
          const category = (data.categories || []).find((item) => item.id === categoryId);
          const a = runA.categories?.[categoryId] || {};
          const b = runB.categories?.[categoryId] || {};
          const delta = (Number(a.quality) || 0) - (Number(b.quality) || 0);
          return {
            category: category ? category.label : categoryId,
            aQuality: a.quality,
            bQuality: b.quality,
            delta,
          };
        });
        renderTable(
          categoryTable,
          [
            { label: "Category", key: "category" },
            { label: "Model A", render: (row) => pct(row.aQuality) },
            { label: "Model B", render: (row) => pct(row.bQuality) },
            {
              label: "Delta",
              render: (row) =>
                `<span class="${row.delta >= 0 ? "rb-delta-positive" : "rb-delta-negative"}">${row.delta >= 0 ? "+" : ""}${row.delta.toFixed(1)}</span>`,
            },
          ],
          rows,
        );
      }

      const deltas = [];
      const allTaskIds = new Set([...Object.keys(runA.task_penalties || {}), ...Object.keys(runB.task_penalties || {})]);
      for (const taskId of allTaskIds) {
        const a = Number(runA.task_penalties?.[taskId]?.total_penalty || 0);
        const b = Number(runB.task_penalties?.[taskId]?.total_penalty || 0);
        deltas.push({
          taskId,
          title: taskMap.get(taskId)?.title || taskId,
          delta: b - a,
          a,
          b,
        });
      }
      const aBetter = deltas.filter((row) => row.delta > 0).sort((left, right) => right.delta - left.delta).slice(0, 10);
      const bBetter = deltas.filter((row) => row.delta < 0).sort((left, right) => left.delta - right.delta).slice(0, 10);

      const columns = [
        { label: "Task", render: (row) => `${row.taskId}<br><span class="rb-muted">${row.title}</span>` },
        { label: "A", render: (row) => number(row.a) },
        { label: "B", render: (row) => number(row.b) },
        { label: "Delta", render: (row) => number(Math.abs(row.delta)) },
      ];
      if (betterA) {
        renderTable(betterA, columns, aBetter);
      }
      if (betterB) {
        renderTable(betterB, columns, bBetter);
      }
    }

    selectA.addEventListener("change", render);
    selectB.addEventListener("change", render);
    render();
  }

  function renderCategoryPage() {
    const pageRoot = document.getElementById("rb-category-page");
    const table = document.getElementById("rb-category-leaderboard");
    if (!pageRoot || !table) {
      return;
    }

    const categoryId = pageRoot.dataset.categoryId;
    if (!categoryId) {
      return;
    }

    const categoryMeta = (data.categories || []).find((item) => item.id === categoryId);
    const reference = data.category_reference_scores?.[categoryId];
    const rows = data.leaderboards?.categories?.[categoryId] || [];

    const note = document.getElementById("rb-category-note");
    if (note) {
      const basis = reference?.basis === "clean" ? "best clean run" : "best headline-eligible run";
      if (reference?.quality !== null && reference?.quality !== undefined) {
        note.textContent = `${categoryMeta?.label || categoryId} is ranked by absolute category quality. Current reference ceiling: ${Number(reference.quality).toFixed(1)}% (${basis}).`;
      } else {
        note.textContent = `${categoryMeta?.label || categoryId} is ranked by absolute category quality.`;
      }
    }

    const cards = document.getElementById("rb-category-cards");
    if (cards) {
      const top = rows[0];
      const cardRows = [
        ["Headline Runs", number(rows.length), "Complete runs with zero failed tasks in this category leaderboard"],
        ["Best Quality", reference?.quality !== null && reference?.quality !== undefined ? pct(reference.quality) : "—", "Highest absolute category quality currently recorded"],
        ["Best Model", top ? top.title : "—", top ? top.model : "No eligible run recorded"],
      ];
      cards.innerHTML = cardRows
        .map(
          ([title, value, noteText]) => `
            <section class="rb-card">
              <h3>${title}</h3>
              <div class="rb-card-value">${value}</div>
              <div class="rb-card-note">${noteText}</div>
            </section>
          `,
        )
        .join("");
    }

    renderTable(
      table,
      [
        { label: "Rank", render: (_, index) => String(index + 1) },
        { label: "Run", render: (row) => `${row.title}<br><span class="rb-muted">${row.model}</span>` },
        { label: "Quality", render: (row) => `${pct(row.quality)} ${bar(row.quality)}` },
        { label: "Demerits", render: (row) => `${number(row.demerits)} / ${number(row.max_demerits)}` },
        { label: "Tasks", render: (row) => number(row.task_count) },
        {
          label: "Status",
          render: (row) => {
            const run = (data.runs || []).find((candidate) => candidate.run_id === row.run_id);
            return run ? badge(run) : "—";
          },
        },
      ],
      rows.map((row, index) => ({ ...row, __index: index })),
    );
    [...table.querySelectorAll("tbody tr")].forEach((tr, index) => {
      tr.children[0].textContent = String(index + 1);
    });
  }

  renderSummaryCards();
  renderAwards();
  renderOverviewTables();
  renderModelExplorer();
  renderComparePage();
  renderCategoryPage();
})();
