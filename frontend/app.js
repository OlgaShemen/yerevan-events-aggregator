const { createClient } = window.supabase;

const supabaseClient = createClient(
  window.YEREVAN_EVENTS_CONFIG.supabaseUrl,
  window.YEREVAN_EVENTS_CONFIG.supabaseAnonKey
);

const state = {
  events: [],
  filters: {
    date: "",
    category: "",
  },
};

const elements = {
  count: document.querySelector("#event-count"),
  countLabel: document.querySelector("#event-count-label"),
  status: document.querySelector("#status-message"),
  list: document.querySelector("#events-list"),
  date: document.querySelector("#date-input"),
  category: document.querySelector("#category-input"),
  reset: document.querySelector("#reset-button"),
};

const DESCRIPTION_PREVIEW_LENGTH = 500;
const ORIGINAL_TEXT_PREVIEW_LENGTH = 360;

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

function formatDate(value) {
  if (!value) return "Date TBA";

  return new Intl.DateTimeFormat("ru", {
    day: "numeric",
    month: "short",
  })
    .format(new Date(`${value}T00:00:00`))
    .replace(".", "");
}

function formatTime(value) {
  return value ? value.slice(0, 5) : "Time TBA";
}

function getTodayISO() {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, "0");
  const day = String(today.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function isUpcomingOrOngoing(event) {
  const today = getTodayISO();
  const lastEventDate = event.date_end || event.date_start;

  if (!lastEventDate) return false;

  return lastEventDate >= today;
}

function hasRequiredPublicFields(event) {
  return Boolean(event.date_start && (event.venue_name || event.address));
}

function formatDateRange(event) {
  if (!event.date_start && !event.date_end) return "Date TBA";

  if (event.date_start && event.date_end && event.date_start !== event.date_end) {
    return `${formatDate(event.date_start)} - ${formatDate(event.date_end)}`;
  }

  return formatDate(event.date_start || event.date_end);
}

function formatTimeRange(event) {
  if (event.time_start && event.time_end && event.time_start !== event.time_end) {
    return `${formatTime(event.time_start)} - ${formatTime(event.time_end)}`;
  }

  return formatTime(event.time_start);
}

function eventIncludesDate(event, selectedDate) {
  if (!selectedDate) return true;

  const startDate = event.date_start || event.date_end;
  const endDate = event.date_end || event.date_start;

  if (!startDate && !endDate) return false;

  return selectedDate >= startDate && selectedDate <= endDate;
}

function matchesFilters(event) {
  if (!eventIncludesDate(event, state.filters.date)) return false;
  if (state.filters.category && event.category !== state.filters.category) return false;

  return true;
}

function compareEventsByDateTime(firstEvent, secondEvent) {
  const firstDate = firstEvent.date_start || firstEvent.date_end || "9999-12-31";
  const secondDate = secondEvent.date_start || secondEvent.date_end || "9999-12-31";

  if (firstDate !== secondDate) {
    return firstDate.localeCompare(secondDate);
  }

  const firstTime = firstEvent.time_start || "23:59";
  const secondTime = secondEvent.time_start || "23:59";

  if (firstTime !== secondTime) {
    return firstTime.localeCompare(secondTime);
  }

  return String(firstEvent.title || "").localeCompare(String(secondEvent.title || ""), "ru");
}

function getEventCountLabel(count) {
  const lastTwo = count % 100;
  const lastOne = count % 10;

  if (lastTwo >= 11 && lastTwo <= 14) return "\u0441\u043e\u0431\u044b\u0442\u0438\u0439";
  if (lastOne === 1) return "\u0441\u043e\u0431\u044b\u0442\u0438\u0435";
  if (lastOne >= 2 && lastOne <= 4) return "\u0441\u043e\u0431\u044b\u0442\u0438\u044f";
  return "\u0441\u043e\u0431\u044b\u0442\u0438\u0439";
}

function renderEvents() {
  const filteredEvents = state.events
    .filter(hasRequiredPublicFields)
    .filter(isUpcomingOrOngoing)
    .filter(matchesFilters)
    .sort(compareEventsByDateTime);

  elements.count.textContent = String(filteredEvents.length);
  elements.countLabel.textContent = getEventCountLabel(filteredEvents.length);

  if (!filteredEvents.length) {
    elements.status.textContent = "";
    elements.list.innerHTML = `<div class="empty">\u0421\u043e\u0431\u044b\u0442\u0438\u044f \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u044b.</div>`;
    return;
  }

  elements.status.textContent = "";
  elements.list.innerHTML = filteredEvents.map(renderEventCard).join("");
}

function renderEventCard(event) {
  const descriptionText = event.description || "";
  const hasDescription = Boolean(descriptionText);
  const hasLongDescription = descriptionText.length > DESCRIPTION_PREVIEW_LENGTH;
  const previewText = hasLongDescription
    ? `${descriptionText.slice(0, DESCRIPTION_PREVIEW_LENGTH).trim()}...`
    : descriptionText;
  const originalText = event.original_text || "";
  const hasOriginalText = Boolean(originalText && originalText !== descriptionText);
  const originalPreviewText =
    hasOriginalText && originalText.length > ORIGINAL_TEXT_PREVIEW_LENGTH
      ? `${originalText.slice(0, ORIGINAL_TEXT_PREVIEW_LENGTH).trim()}...`
      : originalText;
  const sourceLink = event.source_url
    ? `<a class="tag source-tag" href="${escapeHtml(event.source_url)}" target="_blank" rel="noreferrer">\u0421\u0441\u044b\u043b\u043a\u0430 \u043d\u0430 \u0438\u0441\u0442\u043e\u0447\u043d\u0438\u043a</a>`
    : "";

  return `
    <article class="event-card">
      <div>
        <div class="event-date">${formatDateRange(event)}</div>
        <div class="event-time">${formatTimeRange(event)}</div>
      </div>
      <div>
        <h2 class="event-title">${escapeHtml(event.title)}</h2>
        ${
          hasDescription
            ? `
              <p class="event-description" data-full-text="${escapeHtml(descriptionText)}" data-preview-text="${escapeHtml(previewText)}">
                ${escapeHtml(previewText)}
              </p>
            `
            : ""
        }
        ${
          hasLongDescription
            ? `<button class="details-button" type="button" data-expanded="false">\u041f\u043e\u0434\u0440\u043e\u0431\u043d\u0435\u0435</button>`
            : ""
        }
        ${
          hasOriginalText
            ? `
              <button class="original-button" type="button" data-expanded="false">\u041e\u0440\u0438\u0433\u0438\u043d\u0430\u043b\u044c\u043d\u044b\u0439 \u043f\u043e\u0441\u0442</button>
              <p class="original-text" hidden data-full-text="${escapeHtml(originalText)}" data-preview-text="${escapeHtml(originalPreviewText)}">
                ${escapeHtml(originalPreviewText)}
              </p>
            `
            : ""
        }
        <div class="event-meta">
          <span class="tag">${escapeHtml(getCategoryLabel(event.category))}</span>
          ${event.venue_name ? `<span class="tag">${escapeHtml(event.venue_name)}</span>` : ""}
          ${event.price_text ? `<span class="tag">${escapeHtml(event.price_text)}</span>` : ""}
          ${sourceLink}
        </div>
      </div>
    </article>
  `;
}

function getCategoryLabel(category) {
  return CATEGORY_LABELS[category] || CATEGORY_LABELS.other;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function loadEvents() {
  elements.status.textContent = "Loading events...";

  const { data, error } = await supabaseClient
    .from("public_events")
    .select("*")
    .order("date_start", { ascending: true });

  if (error) {
    elements.status.textContent = `Could not load events: ${error.message}`;
    elements.list.innerHTML = "";
    return;
  }

  state.events = data || [];
  renderEvents();
}

function bindFilters() {
  elements.date.addEventListener("input", (event) => {
    state.filters.date = event.target.value;
    renderEvents();
  });

  elements.category.addEventListener("change", (event) => {
    state.filters.category = event.target.value;
    renderEvents();
  });

  elements.reset.addEventListener("click", () => {
    state.filters = {
      date: "",
      category: "",
    };
    elements.date.value = "";
    elements.category.value = "";
    renderEvents();
  });

  elements.list.addEventListener("click", (event) => {
    if (event.target.classList.contains("original-button")) {
      const button = event.target;
      const originalText = button.nextElementSibling;
      const isExpanded = button.dataset.expanded === "true";

      originalText.hidden = isExpanded;
      originalText.textContent = isExpanded
        ? originalText.dataset.previewText
        : originalText.dataset.fullText;
      button.dataset.expanded = String(!isExpanded);
      button.textContent = isExpanded
        ? "\u041e\u0440\u0438\u0433\u0438\u043d\u0430\u043b\u044c\u043d\u044b\u0439 \u043f\u043e\u0441\u0442"
        : "\u0421\u043a\u0440\u044b\u0442\u044c \u043e\u0440\u0438\u0433\u0438\u043d\u0430\u043b";
      return;
    }

    if (!event.target.classList.contains("details-button")) return;

    const button = event.target;
    const description = button.previousElementSibling;
    const isExpanded = button.dataset.expanded === "true";

    description.textContent = isExpanded
      ? description.dataset.previewText
      : description.dataset.fullText;
    button.dataset.expanded = String(!isExpanded);
    button.textContent = isExpanded
      ? "\u041f\u043e\u0434\u0440\u043e\u0431\u043d\u0435\u0435"
      : "\u0421\u0432\u0435\u0440\u043d\u0443\u0442\u044c";
  });
}

bindFilters();
loadEvents();
