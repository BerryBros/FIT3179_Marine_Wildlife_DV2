const charts = [
  ["#vis01", "charts/01_occurrence_point_map.vl.json"],
  ["#vis02", "charts/02_occurrence_grid_map.vl.json"],
  ["#vis03", "charts/03_species_record_lollipop.vl.json"],
  ["#vis04", "charts/04_conservation_status.vl.json"],
  ["#vis05", "charts/05_threat_network.vl.json"],
  ["#vis06", "charts/06_bia_behaviour_map.vl.json"],
  ["#vis07", "charts/07_behaviour_heatmap.vl.json"],
  ["#vis08", "charts/08_occurrence_polar.vl.json"],
  ["#vis09", "charts/09_monthly_rank_bump.vl.json"],
  ["#vis10", "charts/10_shark_control_profile.vl.json"],
  ["#vis11", "charts/11_protection_overlap_map.vl.json"],
  ["#vis12", "charts/12_park_zone_stacked_bar.vl.json"]
];

const embedOptions = {
  actions: false,
  renderer: "svg",
  tooltip: { theme: "light" }
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
    setSignal("#vis09", "rankFocus", value),
    setSignal("#vis11", "overlaySpecies", value)
  ]);
}

embedAll().then(() => {
  const globalSpecies = document.getElementById("globalSpecies");
  if (globalSpecies) {
    globalSpecies.addEventListener("change", (event) => syncSpecies(event.target.value));
  }
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
