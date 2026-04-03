const FTE_URL = "https://projects.fivethirtyeight.com/nba-model/nba_elo.csv";
const KAGGLE_FALLBACK_URL = "data/kaggle_nba_datasets_fallback.csv";

const FTE_FALLBACK = [
  { date: "2024-10-22", team1: "BOS", team2: "NYK", score1: 132, score2: 109, elo1_pre: 1672, elo2_pre: 1501 },
  { date: "2024-10-22", team1: "LAL", team2: "MIN", score1: 110, score2: 103, elo1_pre: 1598, elo2_pre: 1562 },
  { date: "2024-10-23", team1: "DEN", team2: "PHX", score1: 118, score2: 114, elo1_pre: 1640, elo2_pre: 1621 }
];

const parseCsv = async (url) => {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Failed to fetch ${url}`);
  const text = await response.text();
  return Papa.parse(text, { header: true, dynamicTyping: true, skipEmptyLines: true }).data;
};

const latestTeamElos = (rows) => {
  const latest = new Map();
  const sorted = [...rows].sort((a, b) => new Date(a.date) - new Date(b.date));

  for (const row of sorted) {
    if (row.team1 && Number.isFinite(row.elo1_pre)) latest.set(row.team1, Number(row.elo1_pre));
    if (row.team2 && Number.isFinite(row.elo2_pre)) latest.set(row.team2, Number(row.elo2_pre));
  }

  return [...latest.entries()]
    .map(([team, elo]) => ({ team, elo }))
    .sort((a, b) => b.elo - a.elo);
};

const renderTable = (tbodyEl, rows, rowMapper) => {
  tbodyEl.innerHTML = "";
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = rowMapper(row);
    tbodyEl.appendChild(tr);
  });
};

const renderEloChart = (rows) => {
  const ctx = document.getElementById("elo-chart");
  const top = rows.slice(0, 12);
  new Chart(ctx, {
    type: "bar",
    data: {
      labels: top.map((r) => r.team),
      datasets: [{
        label: "ELO",
        data: top.map((r) => r.elo),
        backgroundColor: "rgba(34, 211, 238, 0.7)"
      }]
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        y: { ticks: { color: "#e5e7eb" }, grid: { color: "#1f2937" } },
        x: { ticks: { color: "#e5e7eb" }, grid: { color: "#1f2937" } }
      }
    }
  });
};

const init = async () => {
  let fteRows = FTE_FALLBACK;
  let eloSource = "Embedded fallback sample";

  try {
    const liveRows = await parseCsv(FTE_URL);
    if (liveRows.length > 0) {
      fteRows = liveRows;
      eloSource = FTE_URL;
    }
  } catch (_) {
    // Keep fallback if live data fetch fails.
  }

  document.getElementById("elo-source").textContent = `Loaded from: ${eloSource}`;

  const elos = latestTeamElos(fteRows);
  renderTable(
    document.querySelector("#elo-table tbody"),
    elos.slice(0, 20),
    (r) => `<td>${r.team}</td><td>${r.elo.toFixed(0)}</td>`
  );
  renderEloChart(elos);

  const games = [...fteRows]
    .filter((r) => r.date && r.team1 && r.team2 && Number.isFinite(r.score1) && Number.isFinite(r.score2))
    .sort((a, b) => new Date(b.date) - new Date(a.date))
    .slice(0, 25);

  renderTable(
    document.querySelector("#games-table tbody"),
    games,
    (r) => `<td>${r.date}</td><td>${r.team1} vs ${r.team2}</td><td>${r.score1}-${r.score2}</td>`
  );

  const kaggleRows = await parseCsv(KAGGLE_FALLBACK_URL);
  const datasetBody = document.querySelector("#dataset-table tbody");
  const renderDatasetRows = (query = "") => {
    const q = query.trim().toLowerCase();
    const view = q
      ? kaggleRows.filter((r) => Object.values(r).some((v) => String(v).toLowerCase().includes(q)))
      : kaggleRows;

    renderTable(
      datasetBody,
      view,
      (r) => `<td>${r.dataset_name ?? ""}</td><td>${r.owner ?? ""}</td><td><a href="${r.dataset_url}" target="_blank" rel="noreferrer">Open</a></td>`
    );
  };

  renderDatasetRows();
  document.getElementById("dataset-filter").addEventListener("input", (e) => {
    renderDatasetRows(e.target.value);
  });
};

init();
