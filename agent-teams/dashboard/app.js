const fallbackData = {
  session: {
    id: "2026-02-08_1805",
    started_at: "2026-02-08 18:05",
    phases_complete: 8,
    phases_total: 12,
    alerts: "2 Warnings",
    progress_pct: 66,
  },
  teams: [
    {
      id: "S1",
      name: "Structure Team",
      focus: "Finance codes, schools, departments",
      status: "Needs review",
      badge: "warn",
    },
    {
      id: "S2",
      name: "Staff Team",
      focus: "Contracts, allowances, pensions",
      status: "Running",
      badge: "run",
    },
    {
      id: "S3",
      name: "Financial Team",
      focus: "Budgets, funding, pupil numbers",
      status: "Approved",
      badge: "ok",
    },
  ],
  timeline: [
    { team: "S1", phase: "Analyze", status: "Complete", time: "10:12" },
    { team: "S1", phase: "Clean", status: "Complete", time: "10:45" },
    { team: "S1", phase: "Transform", status: "Needs review", time: "11:05" },
    { team: "S2", phase: "Analyze", status: "Complete", time: "11:30" },
    { team: "S2", phase: "Clean", status: "Running", time: "12:10" },
    { team: "S3", phase: "Analyze", status: "Complete", time: "13:40" },
  ],
  quality: [
    { label: "Data Quality Score", value: "82%", note: "+4% vs last run" },
    { label: "Assumptions", value: "12", note: "3 low confidence" },
    { label: "Validation Errors", value: "4", note: "2 critical" },
    { label: "Next Check-in", value: "Transform", note: "S2 in progress" },
  ],
  reports: [
    {
      title: "S1 Analysis",
      summary: "3 warnings, 1 critical. Finance code formatting needs review.",
      status: "Needs Review",
      pill: "warn",
    },
    {
      title: "S2 Cleanup",
      summary: "Whitespace normalized, 2 missing columns created.",
      status: "Approved",
      pill: "ok",
    },
    {
      title: "S3 Transform",
      summary: "Budget sign conventions normalized for 3 accounts.",
      status: "In Progress",
      pill: "info",
    },
  ],
};

const sessionId = document.querySelector(".metric__value");
const phasesComplete = document.querySelectorAll(".metric__value")[1];
const alerts = document.querySelectorAll(".metric__value")[2];
const progress = document.querySelector(".progress__bar");
const qualityGrid = document.querySelector(".quality");
const teamList = document.getElementById("team-list");
const timelineList = document.getElementById("timeline");
const reportsList = document.querySelector(".reports");

function renderDashboard(data) {
  if (data.session) {
    sessionId.textContent = data.session.started_at || data.session.id;
    phasesComplete.textContent = `${data.session.phases_complete} / ${data.session.phases_total}`;
    alerts.textContent = data.session.alerts;
    progress.style.width = `${data.session.progress_pct}%`;
  }

  teamList.innerHTML = "";
  data.teams.forEach((team) => {
    const card = document.createElement("div");
    card.className = "team";
    card.innerHTML = `
      <div>
        <h3>${team.id} - ${team.name}</h3>
        <p>${team.focus}</p>
      </div>
      <span class="badge badge--${team.badge}">${team.status}</span>
    `;
    teamList.appendChild(card);
  });

  timelineList.innerHTML = "";
  data.timeline.forEach((item) => {
    const row = document.createElement("li");
    row.innerHTML = `
      <span class="dot"></span>
      <div>
        <strong>${item.team} ${item.phase}</strong>
        <div class="muted">${item.status}</div>
      </div>
      <span>${item.time}</span>
    `;
    timelineList.appendChild(row);
  });

  qualityGrid.innerHTML = "";
  data.quality.forEach((item) => {
    const block = document.createElement("div");
    block.className = "quality__item";
    block.innerHTML = `
      <p>${item.label}</p>
      <strong>${item.value}</strong>
      <span>${item.note}</span>
    `;
    qualityGrid.appendChild(block);
  });

  reportsList.innerHTML = "";
  data.reports.forEach((report) => {
    const card = document.createElement("article");
    card.className = "report";
    card.innerHTML = `
      <div>
        <h3>${report.title}</h3>
        <p>${report.summary}</p>
      </div>
      <span class="status status--${report.pill}">${report.status}</span>
    `;
    reportsList.appendChild(card);
  });
}

fetch("data.json")
  .then((res) => (res.ok ? res.json() : Promise.reject(new Error("Failed to load data.json"))))
  .then((data) => renderDashboard(data))
  .catch(() => renderDashboard(fallbackData));
