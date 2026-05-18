const state = {
  activeMode: "text",
  activeFilter: "all",
  latestReport: null,
};

const elements = {
  profileSelect: document.querySelector("#profileSelect"),
  textForm: document.querySelector("#textForm"),
  fileForm: document.querySelector("#fileForm"),
  articleText: document.querySelector("#articleText"),
  docxFile: document.querySelector("#docxFile"),
  statusLine: document.querySelector("#statusLine"),
  reportSummary: document.querySelector("#reportSummary"),
  metrics: document.querySelector("#metrics"),
  results: document.querySelector("#results"),
  downloadReport: document.querySelector("#downloadReport"),
  sampleButton: document.querySelector("#sampleButton"),
  segments: [...document.querySelectorAll(".segment")],
  filters: [...document.querySelectorAll(".filter")],
};

const severityLabels = {
  critical: "Критично",
  warning: "Внимание",
  recommendation: "Совет",
  info: "Инфо",
};

const statusLabels = {
  passed: "Пройдено",
  failed: "Ошибка",
  skipped: "Пропущено",
};

async function loadProfiles() {
  const response = await fetch("/profiles");
  if (!response.ok) {
    throw new Error("Не удалось загрузить профили журналов.");
  }
  const profiles = await response.json();
  elements.profileSelect.replaceChildren(
    ...profiles.map((profile) => {
      const option = document.createElement("option");
      option.value = profile.id;
      option.textContent = `${profile.name} (${profile.version})`;
      return option;
    }),
  );
}

function setStatus(message, type = "neutral") {
  elements.statusLine.textContent = message;
  elements.statusLine.dataset.type = type;
}

function setMode(mode) {
  state.activeMode = mode;
  document.querySelectorAll(".input-mode").forEach((node) => {
    node.classList.toggle("active", node.id === `${mode}Form`);
  });
  elements.segments.forEach((button) => {
    const isActive = button.dataset.mode === mode;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-selected", String(isActive));
  });
}

function setFilter(filter) {
  state.activeFilter = filter;
  elements.filters.forEach((button) => button.classList.toggle("active", button.dataset.filter === filter));
  renderResults();
}

async function analyzeText(event) {
  event.preventDefault();
  const text = elements.articleText.value.trim();
  if (!text) {
    setStatus("Добавьте текст статьи для проверки.", "warning");
    return;
  }

  const formData = new FormData();
  formData.append("text", text);
  formData.append("profile_id", elements.profileSelect.value);
  await runAnalysis("/analyze-text", formData, "Проверяю текст статьи...");
}

async function analyzeDocx(event) {
  event.preventDefault();
  const file = elements.docxFile.files[0];
  if (!file) {
    setStatus("Выберите файл `.docx` для проверки.", "warning");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);
  formData.append("profile_id", elements.profileSelect.value);
  await runAnalysis("/analyze-docx", formData, "Проверяю документ...");
}

async function runAnalysis(url, formData, progressMessage) {
  setStatus(progressMessage);
  elements.downloadReport.disabled = true;

  try {
    const response = await fetch(url, {
      method: "POST",
      body: formData,
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Проверка завершилась ошибкой.");
    }
    state.latestReport = payload;
    renderReport(payload);
    setStatus("Проверка завершена.");
  } catch (error) {
    setStatus(error.message, "error");
  }
}

function renderReport(report) {
  const failed = report.results.filter((result) => result.status === "failed").length;
  const critical = report.results.filter((result) => result.status === "failed" && result.severity === "critical").length;
  elements.reportSummary.textContent = `Профиль: ${report.profile_name}. Найдено замечаний: ${failed}, критичных: ${critical}.`;
  renderMetrics(report.metrics);
  renderResults();
  elements.downloadReport.disabled = false;
}

function renderMetrics(metrics) {
  const values = [
    metrics.body_characters_with_spaces || 0,
    metrics.abstract_ru_words || 0,
    metrics.keywords_ru_count || 0,
    metrics.footnotes_count || 0,
  ];

  elements.metrics.querySelectorAll(".metric-value").forEach((node, index) => {
    node.textContent = new Intl.NumberFormat("ru-RU").format(values[index]);
  });
}

function renderResults() {
  if (!state.latestReport) {
    elements.results.className = "results empty";
    elements.results.innerHTML = "<p>Пока нет данных для отчета.</p>";
    return;
  }

  const filtered = state.latestReport.results.filter((result) => {
    return state.activeFilter === "all" || result.severity === state.activeFilter;
  });

  if (!filtered.length) {
    elements.results.className = "results empty";
    elements.results.innerHTML = "<p>Для выбранного фильтра замечаний нет.</p>";
    return;
  }

  elements.results.className = "results";
  elements.results.replaceChildren(...filtered.map(createResultRow));
}

function createResultRow(result) {
  const row = document.createElement("article");
  row.className = "result-row";
  row.dataset.severity = result.severity;
  row.dataset.status = result.status;

  const badge = document.createElement("span");
  badge.className = `badge ${result.status} ${result.severity}`;
  badge.textContent = result.status === "failed" ? severityLabels[result.severity] : statusLabels[result.status];

  const content = document.createElement("div");
  const title = document.createElement("div");
  title.className = "result-title";
  title.textContent = result.title;

  const message = document.createElement("p");
  message.className = "result-message";
  message.textContent = result.message;

  content.append(title, message);

  if (result.suggested_fix) {
    const suggestion = document.createElement("p");
    suggestion.className = "result-suggestion";
    suggestion.textContent = `Что сделать: ${result.suggested_fix}`;
    content.append(suggestion);
  }

  const meta = document.createElement("div");
  meta.className = "result-meta";
  meta.textContent = [result.location, result.rule_id].filter(Boolean).join(" · ");
  content.append(meta);

  row.append(badge, content);
  return row;
}

function fillSample() {
  const abstract = Array.from({ length: 36 }, (_, index) => `слово${index + 1}`).join(" ");
  const body = Array.from({ length: 22 }, () => "Основной текст исследования раскрывает тему и содержит примерный фрагмент рассуждения.").join(" ");
  elements.articleText.value = `УДК 2-1
Название статьи
иерей И. И. Иванов

Аннотация: ${abstract}
Ключевые слова: богословие, патристика, литургика, экзегеза, традиция

${body}

Список источников и литературы
Иванов И. И. Название книги. М.: Издательство, 2020. 200 с.

Article Title
Abstract: ${abstract}
Keywords: theology, patristics, liturgy, exegesis, tradition
References
Ivanov I. I. Book Title. Moscow, 2020.`;
  setStatus("Пример вставлен. Можно запускать проверку.");
}

function downloadLatestReport() {
  if (!state.latestReport) {
    return;
  }

  const blob = new Blob([JSON.stringify(state.latestReport, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "article-format-report.json";
  link.click();
  URL.revokeObjectURL(url);
}

elements.segments.forEach((button) => button.addEventListener("click", () => setMode(button.dataset.mode)));
elements.filters.forEach((button) => button.addEventListener("click", () => setFilter(button.dataset.filter)));
elements.textForm.addEventListener("submit", analyzeText);
elements.fileForm.addEventListener("submit", analyzeDocx);
elements.sampleButton.addEventListener("click", fillSample);
elements.downloadReport.addEventListener("click", downloadLatestReport);

loadProfiles().catch((error) => setStatus(error.message, "error"));
