const REVIEW_API_BASE_URL =
  window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost"
    ? "http://127.0.0.1:8000"
    : `${window.location.origin}/api`;

const state = {
  events: [],
  status: "needs_review",
  search: "",
};

const elements = {
  count: document.querySelector("#review-count"),
  countLabel: document.querySelector("#review-count-label"),
  status: document.querySelector("#review-status"),
  list: document.querySelector("#review-list"),
  reload: document.querySelector("#reload-button"),
  search: document.querySelector("#review-search-input"),
  tabs: document.querySelectorAll(".tab-button"),
};

const CATEGORIES = [
  "concert",
  "theatre",
  "exhibition",
  "party",
  "movie",
  "workshop",
  "tourism",
  "food",
  "kids",
  "other",
];

const LANGUAGES = ["hy", "ru", "en", "mixed", "unknown"];

const CATEGORY_LABELS = {
  concert: "\u041a\u043e\u043d\u0446\u0435\u0440\u0442",
  theatre: "\u0422\u0435\u0430\u0442\u0440",
  exhibition: "\u0412\u044b\u0441\u0442\u0430\u0432\u043a\u0430",
  party: "\u0412\u0435\u0447\u0435\u0440\u0438\u043d\u043a\u0430",
  movie: "\u041a\u0438\u043d\u043e",
  workshop: "\u041c\u0430\u0441\u0442\u0435\u0440-\u043a\u043b\u0430\u0441\u0441",
  tourism: "\u0422\u0443\u0440\u0438\u0437\u043c",
  food: "\u0415\u0434\u0430",
  kids: "\u0414\u0435\u0442\u044f\u043c",
  other: "\u0414\u0440\u0443\u0433\u043e\u0435",
};

const LANGUAGE_LABELS = {
  hy: "\u0410\u0440\u043c\u044f\u043d\u0441\u043a\u0438\u0439",
  ru: "\u0420\u0443\u0441\u0441\u043a\u0438\u0439",
  en: "\u0410\u043d\u0433\u043b\u0438\u0439\u0441\u043a\u0438\u0439",
  mixed: "\u0421\u043c\u0435\u0448\u0430\u043d\u043d\u044b\u0439",
  unknown: "\u041d\u0435 \u0443\u043a\u0430\u0437\u0430\u043d",
};

const TEXT = {
  untitled: "\u0411\u0435\u0437 \u043d\u0430\u0437\u0432\u0430\u043d\u0438\u044f",
  noPlace: "\u043c\u0435\u0441\u0442\u043e \u043d\u0435 \u0443\u043a\u0430\u0437\u0430\u043d\u043e",
  noDate: "\u0434\u0430\u0442\u0430 \u043d\u0435 \u0443\u043a\u0430\u0437\u0430\u043d\u0430",
  noTime: "\u0432\u0440\u0435\u043c\u044f \u043d\u0435 \u0443\u043a\u0430\u0437\u0430\u043d\u043e",
  source: "\u0418\u0441\u0442\u043e\u0447\u043d\u0438\u043a",
  save: "\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c",
  saveChanges: "\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c \u043f\u0440\u0430\u0432\u043a\u0438",
  publish: "\u041e\u043f\u0443\u0431\u043b\u0438\u043a\u043e\u0432\u0430\u0442\u044c",
  reject: "\u041e\u0442\u043a\u043b\u043e\u043d\u0438\u0442\u044c",
  saving: "\u0421\u043e\u0445\u0440\u0430\u043d\u044f\u044e...",
  saved: "\u041f\u0440\u0430\u0432\u043a\u0438 \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u044b.",
  publishing: "\u041f\u0443\u0431\u043b\u0438\u043a\u0443\u044e...",
  rejecting: "\u041e\u0442\u043a\u043b\u043e\u043d\u044f\u044e...",
  loadingReview: "\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430 \u0441\u043e\u0431\u044b\u0442\u0438\u0439 \u043d\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0435...",
  loadingPublished: "\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430 \u043e\u043f\u0443\u0431\u043b\u0438\u043a\u043e\u0432\u0430\u043d\u043d\u044b\u0445...",
  emptyReview: "\u041d\u0435\u0442 \u0441\u043e\u0431\u044b\u0442\u0438\u0439 \u043d\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0435.",
  emptyPublished: "\u041d\u0435\u0442 \u043e\u043f\u0443\u0431\u043b\u0438\u043a\u043e\u0432\u0430\u043d\u043d\u044b\u0445 \u0441\u043e\u0431\u044b\u0442\u0438\u0439.",
  originalPost: "\u041e\u0440\u0438\u0433\u0438\u043d\u0430\u043b\u044c\u043d\u044b\u0439 Telegram-\u043f\u043e\u0441\u0442",
  noOriginal: "\u041e\u0440\u0438\u0433\u0438\u043d\u0430\u043b\u044c\u043d\u044b\u0439 \u0442\u0435\u043a\u0441\u0442 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d.",
};

const FIELD_LABELS = {
  title: "\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435",
  date_start: "\u0414\u0430\u0442\u0430 \u043d\u0430\u0447\u0430\u043b\u0430",
  time_start: "\u0412\u0440\u0435\u043c\u044f \u043d\u0430\u0447\u0430\u043b\u0430",
  date_end: "\u0414\u0430\u0442\u0430 \u043e\u043a\u043e\u043d\u0447\u0430\u043d\u0438\u044f",
  time_end: "\u0412\u0440\u0435\u043c\u044f \u043e\u043a\u043e\u043d\u0447\u0430\u043d\u0438\u044f",
  venue_name: "\u041c\u0435\u0441\u0442\u043e",
  address: "\u0410\u0434\u0440\u0435\u0441",
  price_text: "\u0426\u0435\u043d\u0430",
  category: "\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f",
  language: "\u042f\u0437\u044b\u043a",
  description: "\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435",
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatDateTime(event) {
  const date = event.date_start || TEXT.noDate;
  const time = event.time_start || TEXT.noTime;
  return `${date} ${time}`;
}

function getCountLabel(count) {
  const lastTwo = count % 100;
  const lastOne = count % 10;

  if (lastTwo >= 11 && lastTwo <= 14) return "\u0441\u043e\u0431\u044b\u0442\u0438\u0439";
  if (lastOne === 1) return "\u0441\u043e\u0431\u044b\u0442\u0438\u0435";
  if (lastOne >= 2 && lastOne <= 4) return "\u0441\u043e\u0431\u044b\u0442\u0438\u044f";
  return "\u0441\u043e\u0431\u044b\u0442\u0438\u0439";
}

function renderOptions(options, selectedValue) {
  return options
    .map((option) => {
      const selected = option === selectedValue ? "selected" : "";
      const label = CATEGORY_LABELS[option] || LANGUAGE_LABELS[option] || option;
      return `<option value="${escapeHtml(option)}" ${selected}>${escapeHtml(label)}</option>`;
    })
    .join("");
}

function renderField(name, value, type = "text") {
  return `
    <label>
      <span>${FIELD_LABELS[name]}</span>
      <input name="${name}" type="${type}" value="${escapeHtml(value)}" />
    </label>
  `;
}

function renderActions() {
  if (state.status === "published") {
    return `<button type="button" data-action="save">${TEXT.save}</button>`;
  }

  return `
    <button type="button" data-action="save">${TEXT.saveChanges}</button>
    <button type="button" data-action="publish">${TEXT.publish}</button>
    <button class="danger-button" type="button" data-action="reject">${TEXT.reject}</button>
  `;
}

function renderReviewEvent(event) {
  return `
    <article class="review-card" data-event-id="${escapeHtml(event.id)}">
      <div class="review-card-header">
        <div>
          <p class="review-id">${escapeHtml(event.id)}</p>
          <h2 class="event-title">${escapeHtml(event.title || TEXT.untitled)}</h2>
          <p class="review-summary">
            ${escapeHtml(formatDateTime(event))} ·
            ${escapeHtml(event.venue_name || event.address || TEXT.noPlace)} ·
            status ${escapeHtml(event.status)} ·
            confidence ${escapeHtml(event.confidence_score ?? "unknown")}
          </p>
        </div>
        <a class="tag source-tag" href="${escapeHtml(event.source_url || "#")}" target="_blank" rel="noreferrer">${TEXT.source}</a>
      </div>

      <div class="review-grid">
        ${renderField("title", event.title)}
        ${renderField("date_start", event.date_start, "date")}
        ${renderField("time_start", event.time_start ? event.time_start.slice(0, 5) : "", "time")}
        ${renderField("date_end", event.date_end, "date")}
        ${renderField("time_end", event.time_end ? event.time_end.slice(0, 5) : "", "time")}
        ${renderField("venue_name", event.venue_name)}
        ${renderField("address", event.address)}
        ${renderField("price_text", event.price_text)}

        <label>
          <span>${FIELD_LABELS.category}</span>
          <select name="category">${renderOptions(CATEGORIES, event.category || "other")}</select>
        </label>

        <label>
          <span>${FIELD_LABELS.language}</span>
          <select name="language">${renderOptions(LANGUAGES, event.language || "unknown")}</select>
        </label>

        <label class="full-width">
          <span>${FIELD_LABELS.description}</span>
          <textarea name="description" rows="4">${escapeHtml(event.description)}</textarea>
        </label>
      </div>

      <details class="original-details">
        <summary>${TEXT.originalPost}</summary>
        <pre>${escapeHtml(event.original_text || TEXT.noOriginal)}</pre>
      </details>

      <div class="review-actions">
        ${renderActions()}
      </div>
      <p class="review-card-status" aria-live="polite"></p>
    </article>
  `;
}

function renderReviewEvents() {
  elements.count.textContent = String(state.events.length);
  elements.countLabel.textContent = getCountLabel(state.events.length);

  if (!state.events.length) {
    elements.status.textContent = "";
    elements.list.innerHTML = `<div class="empty">${state.status === "published" ? TEXT.emptyPublished : TEXT.emptyReview}</div>`;
    return;
  }

  elements.status.textContent = "";
  elements.list.innerHTML = state.events.map(renderReviewEvent).join("");
}

async function loadReviewEvents() {
  elements.status.textContent = state.status === "published" ? TEXT.loadingPublished : TEXT.loadingReview;
  elements.list.innerHTML = "";

  const params = new URLSearchParams({ status: state.status });
  if (state.search.trim()) {
    params.set("search", state.search.trim());
  }

  try {
    const response = await fetch(`${REVIEW_API_BASE_URL}/review/events?${params.toString()}`);
    const payload = await response.json();

    if (!response.ok) {
      throw new Error(payload.error || "Could not load events.");
    }

    state.events = payload.events || [];
    renderReviewEvents();
  } catch (error) {
    elements.status.textContent = `Ошибка: ${error.message}`;
    elements.list.innerHTML = "";
  }
}

function collectFormData(card) {
  const fields = [
    "title",
    "date_start",
    "time_start",
    "date_end",
    "time_end",
    "venue_name",
    "address",
    "price_text",
    "category",
    "language",
    "description",
  ];
  const payload = {};

  for (const field of fields) {
    const input = card.querySelector(`[name="${field}"]`);
    payload[field] = input ? input.value.trim() : "";
  }

  return payload;
}

function setCardStatus(card, message, type = "info") {
  const status = card.querySelector(".review-card-status");
  status.textContent = message;
  status.dataset.type = type;
}

function setCardBusy(card, isBusy) {
  card.querySelectorAll("button[data-action]").forEach((button) => {
    button.disabled = isBusy;
  });
}

async function requestJson(path, options = {}) {
  const response = await fetch(`${REVIEW_API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  const payload = await response.json();

  if (!response.ok) {
    throw new Error(payload.error || "API request failed.");
  }

  return payload;
}

function removeEventFromState(eventId) {
  state.events = state.events.filter((event) => event.id !== eventId);
  elements.count.textContent = String(state.events.length);
  elements.countLabel.textContent = getCountLabel(state.events.length);
}

async function saveEvent(card, eventId) {
  const payload = collectFormData(card);
  setCardStatus(card, TEXT.saving);
  setCardBusy(card, true);

  await requestJson(`/review/events/${eventId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });

  setCardStatus(card, TEXT.saved, "success");
  setCardBusy(card, false);
}

async function publishEvent(card, eventId) {
  setCardStatus(card, TEXT.publishing);
  setCardBusy(card, true);

  await saveEvent(card, eventId);
  await requestJson(`/review/events/${eventId}/publish`, {
    method: "POST",
    body: JSON.stringify({}),
  });

  removeEventFromState(eventId);
  card.remove();
  renderEmptyStateIfNeeded();
}

async function rejectEvent(card, eventId) {
  const reason = window.prompt("Причина отклонения", "Rejected during manual review.");
  if (reason === null) return;

  setCardStatus(card, TEXT.rejecting);
  setCardBusy(card, true);

  await requestJson(`/review/events/${eventId}/reject`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });

  removeEventFromState(eventId);
  card.remove();
  renderEmptyStateIfNeeded();
}

function renderEmptyStateIfNeeded() {
  if (state.events.length) return;

  elements.status.textContent = "";
  elements.list.innerHTML = `<div class="empty">${state.status === "published" ? TEXT.emptyPublished : TEXT.emptyReview}</div>`;
}

function setActiveTab(status) {
  state.status = status;
  elements.tabs.forEach((tab) => {
    tab.classList.toggle("is-active", tab.dataset.status === status);
  });
}

function bindReviewPage() {
  elements.reload.addEventListener("click", loadReviewEvents);

  elements.search.addEventListener("input", (event) => {
    state.search = event.target.value;
    window.clearTimeout(elements.search._timer);
    elements.search._timer = window.setTimeout(loadReviewEvents, 250);
  });

  elements.tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      setActiveTab(tab.dataset.status);
      loadReviewEvents();
    });
  });

  elements.list.addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-action]");
    if (!button) return;

    const card = button.closest(".review-card");
    const action = button.dataset.action;
    const eventId = card.dataset.eventId;

    try {
      if (action === "save") {
        await saveEvent(card, eventId);
      } else if (action === "publish") {
        await publishEvent(card, eventId);
      } else if (action === "reject") {
        await rejectEvent(card, eventId);
      }
    } catch (error) {
      setCardStatus(card, `Ошибка: ${error.message}`, "error");
      setCardBusy(card, false);
    }
  });
}

bindReviewPage();
loadReviewEvents();
