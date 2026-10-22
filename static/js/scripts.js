// Общие скрипты интерфейса: график, смена статуса без перезагрузки, подтверждения, форма запросов.
(function () {
  "use strict";

  // Столбчатый график новых вакансий за 7 дней
  function renderBars() {
    const box = document.getElementById("bars");
    if (!box) return;
    let days = [];
    try { days = JSON.parse(box.dataset.days || "[]"); } catch (e) { return; }
    const max = Math.max(1, ...days.map(d => d.count));
    box.innerHTML = "";
    days.forEach(d => {
      const bar = document.createElement("div");
      bar.className = "bar";
      bar.title = d.day + ": " + d.count;
      bar.innerHTML =
        '<span class="bar-value">' + d.count + "</span>" +
        '<div class="bar-fill" style="height:' + Math.round((d.count / max) * 100) + '%"></div>' +
        '<span class="bar-label">' + d.day + "</span>";
      box.appendChild(bar);
    });
  }

  // Смена статуса вакансии сразу при выборе
  function bindStatusSelects() {
    document.querySelectorAll("select[data-autosubmit]").forEach(sel => {
      sel.addEventListener("change", async () => {
        const form = sel.closest("form");
        const body = new FormData(form);
        sel.disabled = true;
        try {
          const resp = await fetch(form.action, {
            method: "POST", body, headers: { "x-requested-with": "fetch" }, credentials: "same-origin",
          });
          if (!resp.ok) throw new Error(resp.status);
          const data = await resp.json();
          sel.className = "status-select status-" + data.status;
        } catch (e) {
          alert("Не удалось сохранить статус. Обновите страницу.");
        } finally {
          sel.disabled = false;
        }
      });
    });
  }

  // Подтверждение для опасных действий
  function bindConfirms() {
    document.querySelectorAll("form[data-confirm]").forEach(form => {
      form.addEventListener("submit", e => {
        if (!confirm(form.dataset.confirm)) e.preventDefault();
      });
    });
  }

  // Заполнение формы запроса для редактирования
  function bindQueryEdit() {
    const form = document.getElementById("query-form");
    if (!form) return;
    const heading = document.getElementById("query-form-title");
    document.querySelectorAll("[data-edit-query]").forEach(btn => {
      btn.addEventListener("click", () => {
        const q = JSON.parse(btn.dataset.editQuery);
        form.elements["query_id"].value = q.id;
        form.elements["title"].value = q.title;
        form.elements["text"].value = q.text;
        form.elements["area"].value = String(q.area);
        form.elements["experience"].value = q.experience;
        form.elements["exclude_words"].value = q.exclude_words || "";
        form.elements["priority"].value = q.priority;
        form.elements["only_remote"].checked = !!q.only_remote;
        form.elements["is_active"].checked = !!q.is_active;
        heading.textContent = "Редактирование: " + q.title;
        form.scrollIntoView({ behavior: "smooth" });
      });
    });
    const reset = document.getElementById("query-form-reset");
    if (reset) reset.addEventListener("click", () => {
      form.elements["query_id"].value = "";
      heading.textContent = "Новый запрос";
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    renderBars();
    bindStatusSelects();
    bindConfirms();
    bindQueryEdit();
  });
})();
