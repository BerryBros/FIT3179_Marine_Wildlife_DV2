const charts = [
  ["#vis01", "charts/01_occurrence_point_map.vl.json"],
  ["#vis02", "charts/02_occurrence_grid_map.vl.json"],
  ["#vis03", "charts/03_species_record_lollipop.vl.json"],
  ["#vis04", "charts/04_status_pressure_slope.vl.json"],
  ["#vis05", "charts/05_threat_network.vl.json"],
  ["#vis06", "charts/06_bia_behaviour_map.vl.json"],
  ["#vis07", "charts/07_behaviour_heatmap.vl.json"],
  ["#vis08", "charts/08_occurrence_polar.vl.json"],
  ["#vis09", "charts/09_monthly_ridgeline.vl.json"],
  ["#vis10", "charts/10_protected_species_interactions.vl.json"],
  ["#vis10b", "charts/10b_interaction_outcomes.vl.json"],
  ["#vis11", "charts/11_protection_overlap_map.vl.json"],
  ["#vis12", "charts/12_bia_in_parks_waffle.vl.json"],
  ["#vis13", "charts/13_park_zone_treemap.vg.json"]
];

// Shared typography/colour defaults so every Vega / Vega-Lite chart matches the page.
const FONT = "Manrope, system-ui, -apple-system, 'Segoe UI', sans-serif";
const embedOptions = {
  actions: false,
  renderer: "svg",
  tooltip: { theme: "light" },
  config: {
    background: "transparent",
    view: { stroke: null, fill: "transparent" },
    font: FONT,
    title: {
      anchor: "start",
      font: FONT,
      color: "#173640",
      fontSize: 18,
      fontWeight: 800,
      lineHeight: 24,
      subtitleFont: FONT,
      subtitleColor: "#6C7F86",
      subtitleFontSize: 14,
      subtitleLineHeight: 20
    },
    axis: {
      labelFont: FONT,
      titleFont: FONT,
      labelColor: "#405A61",
      titleColor: "#16333A",
      titleFontWeight: 700,
      labelFontSize: 12,
      titleFontSize: 13,
      gridColor: "#CFE0E1",
      domainColor: "#A7C0C2",
      tickColor: "#A7C0C2"
    },
    legend: {
      labelFont: FONT,
      titleFont: FONT,
      labelColor: "#405A61",
      titleColor: "#16333A",
      titleFontWeight: 700,
      labelFontSize: 12,
      titleFontSize: 13
    },
    header: { labelFont: FONT, titleFont: FONT, labelColor: "#16333A", labelFontSize: 12, titleFontSize: 13 },
    text: { font: FONT, fontSize: 12, color: "#405A61" }
  }
};

const chartViews = new Map();

function showError(selector, error) {
  const el = document.querySelector(selector);
  if (!el) return;
  const isShark = selector === "#vis10";
  el.innerHTML = `
    <div class="vis-error">
      <strong>${isShark ? "This data-preparation step has not been run yet." : "This chart could not load."}</strong>
      <span>${isShark ? "Run <code>python scripts/prepare_shark_control.py</code>, then refresh the page." : "Check the data files and run <code>python scripts/check_project.py</code>."}</span>
      <details><summary>Technical detail</summary><pre>${String(error)}</pre></details>
    </div>`;
}

async function embedAll() {
  await Promise.all(
    charts.map(async ([selector, spec]) => {
      try {
        const result = await vegaEmbed(selector, spec, embedOptions);
        chartViews.set(selector, result.view);
      } catch (error) {
        showError(selector, error);
      }
    })
  );
}

async function setSignal(selector, signal, value) {
  const view = chartViews.get(selector);
  if (!view || !value) return;
  try {
    view.signal(signal, value);
    await view.runAsync();
  } catch (error) {
    // Not every chart has every signal; ignore missing-signal attempts.
  }
}

async function syncSpecies(value) {
  if (!value) return;
  await Promise.all([
    setSignal("#vis01", "speciesPick", value),
    setSignal("#vis06", "biaSpecies", value),
    setSignal("#vis08", "monthSpecies", value),
    setSignal("#vis11", "overlaySpecies", value)
  ]);
}

const protectionSelection = {
  species: "Green turtle",
  behaviour: "All behaviours"
};

let protectionOverlapRows = [];

function parseSimpleCsv(text) {
  const lines = text.trim().split(/\r?\n/);
  if (lines.length < 2) return [];

  const headers = lines[0].split(",");
  return lines.slice(1).map((line) => {
    const values = line.split(",");
    return Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""]));
  });
}

function formatBehaviour(behaviour) {
  return behaviour === "All behaviours" ? "All mapped behaviours" : behaviour;
}

function updateProtectionSummary() {
  const box = document.getElementById("protectionSelectionSummary");
  const title = document.getElementById("protectionSelectionTitle");
  const fact = document.getElementById("protectionSelectionFact");
  if (!box || !title || !fact) return;

  title.textContent = `${protectionSelection.species} · ${formatBehaviour(protectionSelection.behaviour)}`;

  const row = protectionOverlapRows.find(
    (item) =>
      item.species === protectionSelection.species &&
      item.behaviour === protectionSelection.behaviour
  );

  if (!row) {
    box.classList.add("is-empty");
    fact.textContent = "No mapped BIA is available for this selection. Try another behaviour.";
    return;
  }

  box.classList.remove("is-empty");

  const featureCount = Number(row.feature_count);
  const biaArea = Number(row.bia_area_km2);
  const insideArea = Number(row.inside_parks_km2);
  const exactPercent = biaArea > 0 ? (insideArea / biaArea) * 100 : 0;

  const featureText = `${featureCount.toLocaleString("en-AU")} mapped BIA ${featureCount === 1 ? "feature" : "features"}`;
  const areaText = `${biaArea.toLocaleString("en-AU", { maximumFractionDigits: 0 })} km²`;

  let overlapText;
  if (insideArea <= 0) {
    overlapText = "No overlap with Commonwealth marine parks is mapped.";
  } else if (exactPercent < 0.1) {
    overlapText = "Less than 0.1% lies inside Commonwealth marine parks.";
  } else {
    overlapText = `${exactPercent.toFixed(1)}% lies inside Commonwealth marine parks.`;
  }

  fact.textContent = `${featureText} cover about ${areaText}. ${overlapText}`;
}

async function setupProtectionSummary() {
  const view = chartViews.get("#vis11");
  if (!view) return;

  try {
    const response = await fetch("data/bia_park_overlap.csv");
    if (response.ok) {
      protectionOverlapRows = parseSimpleCsv(await response.text());
    }
  } catch (error) {
    protectionOverlapRows = [];
  }

  try {
    protectionSelection.species = view.signal("overlaySpecies");
    protectionSelection.behaviour = view.signal("overlayBehaviour");

    view.addSignalListener("overlaySpecies", (_name, value) => {
      protectionSelection.species = value;
      updateProtectionSummary();
    });

    view.addSignalListener("overlayBehaviour", (_name, value) => {
      protectionSelection.behaviour = value;
      updateProtectionSummary();
    });
  } catch (error) {
    // The map still works if the summary listener is unavailable.
  }

  updateProtectionSummary();
}

embedAll().then(async () => {
  const globalSpecies = document.getElementById("globalSpecies");
  if (globalSpecies) {
    globalSpecies.addEventListener("change", (event) => syncSpecies(event.target.value));
  }

  await setupProtectionSummary();
});

// Scroll progress.
const progress = document.getElementById("scrollProgress");
const backToTop = document.getElementById("backToTop");

function updateScrollUI() {
  const max = document.documentElement.scrollHeight - window.innerHeight;
  const pct = max > 0 ? (window.scrollY / max) * 100 : 0;
  progress.style.width = `${Math.min(100, Math.max(0, pct))}%`;
  backToTop.classList.toggle("is-visible", window.scrollY > 700);
}

window.addEventListener("scroll", updateScrollUI, { passive: true });
updateScrollUI();
backToTop.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));

// Highlight the current story section in the sticky navigation.
const navLinks = [...document.querySelectorAll(".story-nav__links a")];
const sections = navLinks
  .map(a => document.querySelector(a.getAttribute("href")))
  .filter(Boolean);

const observer = new IntersectionObserver((entries) => {
  const visible = entries
    .filter(e => e.isIntersecting)
    .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];

  if (!visible) return;

  navLinks.forEach(a =>
    a.classList.toggle(
      "is-active",
      a.getAttribute("href") === `#${visible.target.id}`
    )
  );
}, {
  rootMargin: "-25% 0px -60% 0px",
  threshold: [0.05, 0.2, 0.5]
});

sections.forEach(section => observer.observe(section));
