const state = {
  splits: {},
  selectedSplit: null,
  routine: null,
  exercises: [],
  progress: null,
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

function byId(id) {
  return document.getElementById(id);
}

function roleLabel(role) {
  return {
    strength: "스트렝스",
    hypertrophy: "근비대",
    accessory: "보조",
  }[role] ?? role;
}

async function loadInitialData() {
  const [splitsData, exercisesData, routineData, progressData, researchData] = await Promise.all([
    api("/api/splits"),
    api("/api/exercises"),
    api("/api/routines/current"),
    api("/api/progress/overview"),
    api("/api/research"),
  ]);

  state.splits = splitsData.splits;
  state.exercises = exercisesData.items;
  state.routine = routineData.data;
  state.progress = progressData;

  renderSplits();
  renderCatalog();
  renderRoutineEditor();
  renderLogForm();
  renderProgress();
  renderResearch(researchData.items);
}

function renderSplits() {
  const container = byId("splitOptions");
  const template = byId("splitCardTemplate");
  container.innerHTML = "";

  Object.entries(state.splits).forEach(([key, split]) => {
    const node = template.content.firstElementChild.cloneNode(true);
    node.querySelector(".split-label").textContent = key === "2-day" ? "Balanced" : "Focused";
    node.querySelector(".split-title").textContent = split.label;
    node.querySelector(".split-desc").textContent = split.description;
    if (state.routine?.routine?.split_type === key) {
      node.classList.add("active");
      state.selectedSplit = key;
    }
    node.addEventListener("click", async () => {
      const result = await api("/api/routines/generate", {
        method: "POST",
        body: JSON.stringify({ split_type: key }),
      });
      state.selectedSplit = key;
      state.routine = result.data;
      renderSplits();
      renderRoutineEditor();
      renderLogForm();
    });
    container.appendChild(node);
  });
}

function renderRoutineEditor() {
  const container = byId("routineEditor");
  const routine = state.routine;
  if (!routine) {
    container.className = "routine-editor empty-state";
    container.textContent = "분할을 선택하면 기본 루틴이 생성됩니다.";
    return;
  }

  container.className = "routine-editor";
  container.innerHTML = "";

  Object.entries(routine.days).forEach(([dayName, items]) => {
    const daySection = document.createElement("section");
    daySection.className = "routine-day";
    daySection.innerHTML = `<h3>${dayName}</h3><p class="muted">${items[0].focus}</p>`;

    items.forEach((item) => {
      const row = document.createElement("div");
      row.className = "routine-item";
      row.dataset.id = String(item.id);
      row.innerHTML = `
        <div>
          <strong>${item.name}</strong>
          <div class="muted">${item.muscle_group} · ${roleLabel(item.role)}</div>
        </div>
        <input value="${item.set_count}" type="number" min="1" data-field="set_count" />
        <input value="${item.rep_range}" type="text" data-field="rep_range" />
        <input value="${item.target_weight ?? ""}" type="number" min="0" step="0.5" data-field="target_weight" />
      `;
      daySection.appendChild(row);
    });

    container.appendChild(daySection);
  });
}

function collectRoutineUpdatePayload() {
  const payload = [];
  document.querySelectorAll(".routine-day").forEach((daySection, dayIndex) => {
    const dayName = daySection.querySelector("h3").textContent;
    const focus = daySection.querySelector(".muted").textContent;
    const items = state.routine.days[dayName];
    daySection.querySelectorAll(".routine-item").forEach((row, itemIndex) => {
      const original = items[itemIndex];
      payload.push({
        id: original.id,
        day_name: dayName,
        day_order: original.day_order || dayIndex + 1,
        focus,
        exercise_id: original.exercise_id,
        role: original.role,
        set_count: Number(row.querySelector('[data-field="set_count"]').value),
        rep_range: row.querySelector('[data-field="rep_range"]').value,
        notes: original.notes,
        target_weight: Number(row.querySelector('[data-field="target_weight"]').value || 0),
      });
    });
  });
  return payload;
}

async function saveRoutine() {
  if (!state.routine) return;
  const result = await api("/api/routines/current", {
    method: "PUT",
    body: JSON.stringify({
      split_type: state.routine.routine.split_type,
      days: collectRoutineUpdatePayload(),
    }),
  });
  state.routine = result.data;
  renderRoutineEditor();
  renderLogForm();
}

function renderCatalog() {
  const container = byId("exerciseCatalog");
  container.innerHTML = "";
  state.exercises.forEach((exercise) => {
    const card = document.createElement("article");
    card.className = "catalog-card";
    card.innerHTML = `
      <img src="/api/exercises/${exercise.id}/illustration.svg" alt="${exercise.name}" />
      <div>
        <strong>${exercise.name}</strong>
        <p class="exercise-meta">${exercise.muscle_group} · ${exercise.secondary_group} · ${exercise.equipment}</p>
        <div>
          <span class="badge">${exercise.movement_type}</span>
          <span class="badge">${exercise.is_unilateral ? "single-side" : "bilateral"}</span>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

function routineItemsForLog() {
  if (!state.routine) return [];
  const items = [];
  Object.values(state.routine.days).forEach((dayItems) => items.push(...dayItems));
  return items;
}

async function recommendationText(exerciseId) {
  const data = await api(`/api/recommendations/next?exercise_id=${exerciseId}`);
  return `${data.recommendation.recommended_weight}kg · ${data.recommendation.reason}`;
}

async function renderLogForm() {
  const container = byId("logForm");
  if (!state.routine) {
    container.className = "log-form empty-state";
    container.textContent = "루틴이 생성되면 자동으로 기록 폼이 준비됩니다.";
    return;
  }
  container.className = "log-form";
  const dayOptions = Object.keys(state.routine.days)
    .map((day) => `<option value="${day}">${day}</option>`)
    .join("");

  container.innerHTML = `
    <div class="log-meta">
      <input id="performedOn" class="field" type="date" value="${new Date().toISOString().slice(0, 10)}" />
      <select id="logDayName" class="field">${dayOptions}</select>
    </div>
    <div id="logRows" class="log-grid"></div>
  `;
  renderLogRows();
}

async function renderLogRows() {
  const dayName = byId("logDayName")?.value;
  const rowsContainer = byId("logRows");
  if (!dayName || !rowsContainer) return;
  rowsContainer.innerHTML = "";
  const items = state.routine.days[dayName] || [];
  for (const item of items) {
    const recommendation = await recommendationText(item.exercise_id);
    const card = document.createElement("article");
    card.className = "log-card";
    card.innerHTML = `
      <strong>${item.name}</strong>
      <p class="muted">${roleLabel(item.role)} · 추천 ${recommendation}</p>
      <div class="log-row">
        <input type="number" min="0" step="0.5" placeholder="무게(kg)" data-field="weight" value="${item.target_weight ?? ""}" />
        <input type="number" min="1" placeholder="반복 수" data-field="reps" />
        <input type="number" min="1" max="${item.set_count}" placeholder="세트 번호" data-field="set_number" />
        <input type="text" placeholder="세트 타입" data-field="set_type" value="${item.role}" />
      </div>
    `;
    card.dataset.exerciseId = item.exercise_id;
    rowsContainer.appendChild(card);
  }
}

async function submitLog() {
  if (!state.routine) return;
  const entries = [];
  document.querySelectorAll(".log-card").forEach((card) => {
    const weight = Number(card.querySelector('[data-field="weight"]').value);
    const reps = Number(card.querySelector('[data-field="reps"]').value);
    const setNumber = Number(card.querySelector('[data-field="set_number"]').value);
    const setType = card.querySelector('[data-field="set_type"]').value || "working";
    if (weight > 0 && reps > 0 && setNumber > 0) {
      entries.push({
        exercise_id: Number(card.dataset.exerciseId),
        weight,
        reps,
        set_number: setNumber,
        set_type: setType,
        notes: "",
      });
    }
  });

  if (!entries.length) {
    window.alert("최소 1개 세트 기록이 필요합니다.");
    return;
  }

  await api("/api/workouts/log", {
    method: "POST",
    body: JSON.stringify({
      performed_on: byId("performedOn").value,
      split_type: state.routine.routine.split_type,
      day_name: byId("logDayName").value,
      entries,
    }),
  });

  state.progress = await api("/api/progress/overview");
  renderProgress();
  renderLogRows();
}

function renderProgress() {
  const container = byId("progressBoard");
  if (!state.progress || (!state.progress.best_lifts.length && !state.progress.recent_sessions.length)) {
    container.className = "progress-board empty-state";
    container.textContent = "운동 기록을 쌓으면 볼륨과 추정 1RM이 표시됩니다.";
    return;
  }
  container.className = "progress-board";

  const totalVolume = state.progress.volume_history.reduce((sum, row) => sum + row.volume, 0);
  const sessions = state.progress.recent_sessions.length;
  const best = state.progress.best_lifts[0];

  container.innerHTML = `
    <div class="stats-grid">
      <div class="progress-card">
        <span class="muted">누적 표시 볼륨</span>
        <strong>${Math.round(totalVolume).toLocaleString()} kg</strong>
      </div>
      <div class="progress-card">
        <span class="muted">최근 세션 수</span>
        <strong>${sessions}</strong>
      </div>
      <div class="progress-card">
        <span class="muted">최고 추정 1RM</span>
        <strong>${best ? `${best.estimated_1rm} kg` : "-"}</strong>
      </div>
    </div>
    <div class="progress-card">
      <h3>Best Lifts</h3>
      <div class="lift-list">
        ${state.progress.best_lifts
          .map(
            (lift) => `
            <div class="session-card">
              <strong>${lift.name}</strong>
              <div class="muted">${lift.muscle_group} · max ${lift.max_weight}kg · est 1RM ${lift.estimated_1rm}kg</div>
            </div>
          `,
          )
          .join("")}
      </div>
    </div>
    <div class="progress-card">
      <h3>Recent Sessions</h3>
      <div class="session-list">
        ${state.progress.recent_sessions
          .map(
            (session) => `
            <div class="session-card">
              <strong>${session.performed_on}</strong>
              <div class="muted">${session.day_name} · ${session.sets_logged} sets</div>
            </div>
          `,
          )
          .join("")}
      </div>
    </div>
  `;
}

function renderResearch(items) {
  const container = byId("researchNotes");
  container.innerHTML = items
    .map(
      (item) => `
        <article class="research-card">
          <strong>${item.title}</strong>
          <p>${item.summary}</p>
          <a href="${item.url}" target="_blank" rel="noreferrer">원문 보기</a>
        </article>
      `,
    )
    .join("");
}

document.addEventListener("DOMContentLoaded", async () => {
  await loadInitialData();
  byId("saveRoutineButton").addEventListener("click", saveRoutine);
  byId("submitLogButton").addEventListener("click", submitLog);
  document.addEventListener("change", (event) => {
    if (event.target?.id === "logDayName") {
      renderLogRows();
    }
  });
});
