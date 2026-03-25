function setActiveNav(page) {
  document.querySelectorAll("[data-page-target]").forEach((node) => {
    node.classList.toggle("active", node.dataset.pageTarget === page);
  });
}

function updateExerciseSummary(select) {
  const row = select.closest(".routine-item");
  const option = select.selectedOptions[0];
  if (!row || !option) return;
  const role = row.dataset.role;
  const roleLabel =
    {
      strength: "스트렝스",
      hypertrophy: "근비대",
      accessory: "보조",
    }[role] ?? role;

  row.querySelector(".exercise-name").textContent = option.dataset.name || option.textContent;
  row.querySelector(".exercise-meta-line").textContent = `${option.dataset.group} · ${roleLabel} · ${option.dataset.equipment}`;
  row.querySelector(".exercise-description").textContent = option.dataset.description || "";
}

document.addEventListener("DOMContentLoaded", () => {
  document.body.addEventListener("change", (event) => {
    if (event.target.matches(".exercise-select")) {
      updateExerciseSummary(event.target);
    }
  });

  document.body.addEventListener("htmx:afterSwap", (event) => {
    if (event.detail.target.id !== "page-shell") return;
    const page = event.detail.target.querySelector(".page-fragment")?.dataset.page;
    if (page) {
      setActiveNav(page);
    }
  });
});
