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
  scrollTop: document.querySelector("#scroll-top-button"),
};

const DESCRIPTION_PREVIEW_LENGTH = 500;
const ORIGINAL_TEXT_PREVIEW_LENGTH = 360;
const trackedScrollDepths = new Set();

const CATEGORY_LABELS = {
  concert: "\u041a\u043e\u043d\u0446\u0435\u0440\u0442",
  theatre: "\u0422\u0435\u0430\u0442\u0440",
  exhibition: "\u0412\u044b\u0441\u0442\u0430\u0432\u043a\u0430",
  lecture: "\u041b\u0435\u043a\u0446\u0438\u044f",
  party: "\u0412\u0435\u0447\u0435\u0440\u0438\u043d\u043a\u0430",
  movie: "\u041a\u0438\u043d\u043e",
  workshop: "\u041c\u0430\u0441\u0442\u0435\u0440-\u043a\u043b\u0430\u0441\u0441",
  tourism: "\u0422\u0443\u0440\u0438\u0437\u043c",
  food: "\u0415\u0434\u0430",
  kids: "\u0414\u0435\u0442\u044f\u043c",
  other: "\u0414\u0440\u0443\u0433\u043e\u0435",
};

function trackEvent(name, parameters = {}) {
  window.yerevanAnalytics?.track(name, parameters);
}

function getAnalyticsSourceUrl(value) {
  try {
    return new URL(value, window.location.href).origin;
  } catch (error) {
    return "invalid_url";
  }
}

function getLoadErrorType(error) {
  const status = Number(error?.status || 0);
  const code = String(error?.code || "").toLowerCase();
  const message = String(error?.message || "").toLowerCase();

  if (status === 401 || code.includes("jwt")) return "authentication";
  if (status === 403 || code.includes("permission")) return "authorization";
  if (status === 408 || code.includes("timeout") || message.includes("timeout")) return "timeout";
  if (!status && (message.includes("fetch") || message.includes("network"))) return "network";
  if (status >= 500 || code.startsWith("pgrst")) return "database";
  return "unknown";
}

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
  const parts = new Intl.DateTimeFormat("en", {
    timeZone: "Asia/Yerevan", year: "numeric", month: "2-digit", day: "2-digit",
  }).formatToParts(new Date());
  const values = Object.fromEntries(parts.map(({ type, value }) => [type, value]));
  return `${values.year}-${values.month}-${values.day}`;
}

function isRecurringEvent(event) {
  return Boolean(event.recurring_schedule && event.display_until && !event.date_start && !event.date_end);
}

function isUpcomingOrOngoing(event) {
  const today = getTodayISO();
  if (event.display_until) return event.display_until >= today;
  const lastEventDate = event.date_end || event.date_start;

  if (!lastEventDate) return false;

  return lastEventDate >= today;
}

function hasRequiredPublicFields(event) {
  return Boolean((event.date_start || isRecurringEvent(event)) && (event.venue_name || event.address));
}

function formatDateRange(event) {
  if (isRecurringEvent(event)) return "На этой неделе";
  if (!event.date_start && !event.date_end) return "Date TBA";

  if (event.date_start && event.date_end && event.date_start !== event.date_end) {
    return `${formatDate(event.date_start)} - ${formatDate(event.date_end)}`;
  }

  return formatDate(event.date_start || event.date_end);
}

function formatTimeRange(event) {
  if (isRecurringEvent(event)) return "";
  if (event.time_start && event.time_end && event.time_start !== event.time_end) {
    return `${formatTime(event.time_start)} - ${formatTime(event.time_end)}`;
  }

  return formatTime(event.time_start);
}

function eventIncludesDate(event, selectedDate) {
  if (!selectedDate) return true;
  if (isRecurringEvent(event)) return false;

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
    requestAnimationFrame(trackScrollDepth);
    return filteredEvents.length;
  }

  elements.status.textContent = "";
  elements.list.innerHTML = filteredEvents.map(renderEventCard).join("");
  requestAnimationFrame(trackScrollDepth);
  return filteredEvents.length;
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
    ? `<a class="tag source-tag" href="${escapeHtml(event.source_url)}" target="_blank" rel="noreferrer">\u2197 \u0418\u0441\u0442\u043e\u0447\u043d\u0438\u043a</a>`
    : "";

  return `
    <article class="event-card" data-event-title="${escapeHtml(event.title)}" data-category="${escapeHtml(event.category || "other")}">
      <div>
        <div class="event-date">${formatDateRange(event)}</div>
        <div class="event-time">${formatTimeRange(event)}</div>
      </div>
      <div>
        <h2 class="event-title">${escapeHtml(event.title)}</h2>
        ${isRecurringEvent(event) ? `<p class="event-description">${escapeHtml(event.recurring_schedule)}</p>` : ""}
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
          ${event.address ? `<span class="tag address-tag">Адрес: ${escapeHtml(event.address)}</span>` : ""}
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
  const today = getTodayISO();

  try {
    const { data, error } = await supabaseClient
      .from("public_events")
      .select("*")
      .or(`date_start.gte.${today},date_end.gte.${today},display_until.gte.${today}`)
      .order("date_start", { ascending: true });

    if (error) {
      elements.status.textContent = `Could not load events: ${error.message}`;
      elements.list.innerHTML = "";
      trackEvent("events_load_error", { error_type: getLoadErrorType(error) });
      return;
    }

    state.events = data || [];
    renderEvents();
    trackEvent("events_load_success", { events_count: state.events.length });
  } catch (error) {
    elements.status.textContent = "Could not load events. Please try again later.";
    elements.list.innerHTML = "";
    trackEvent("events_load_error", { error_type: getLoadErrorType(error) });
  }
}

function bindFilters() {
  elements.date.addEventListener("input", (event) => {
    state.filters.date = event.target.value;
    const resultsCount = renderEvents();
    if (state.filters.date) {
      trackEvent("filter_date", {
        selected_date: state.filters.date,
        results_count: resultsCount,
      });
    }
  });

  elements.category.addEventListener("change", (event) => {
    state.filters.category = event.target.value;
    const resultsCount = renderEvents();
    if (state.filters.category) {
      trackEvent("filter_category", {
        category: state.filters.category,
        results_count: resultsCount,
      });
    }
  });

  elements.reset.addEventListener("click", () => {
    state.filters = {
      date: "",
      category: "",
    };
    elements.date.value = "";
    elements.category.value = "";
    renderEvents();
    trackEvent("filters_reset");
  });

  elements.list.addEventListener("click", (event) => {
    const sourceLink = event.target.closest(".source-tag");
    if (sourceLink) {
      const card = sourceLink.closest(".event-card");
      trackEvent("event_source_click", {
        event_title: card.dataset.eventTitle.slice(0, 100),
        category: card.dataset.category,
        source_url: getAnalyticsSourceUrl(sourceLink.href),
      });
      return;
    }

    if (event.target.classList.contains("original-button")) {
      const button = event.target;
      const originalText = button.nextElementSibling;
      const isExpanded = button.dataset.expanded === "true";
      const card = button.closest(".event-card");

      originalText.hidden = isExpanded;
      originalText.textContent = isExpanded
        ? originalText.dataset.previewText
        : originalText.dataset.fullText;
      button.dataset.expanded = String(!isExpanded);
      button.textContent = isExpanded
        ? "\u041e\u0440\u0438\u0433\u0438\u043d\u0430\u043b\u044c\u043d\u044b\u0439 \u043f\u043e\u0441\u0442"
        : "\u0421\u043a\u0440\u044b\u0442\u044c \u043e\u0440\u0438\u0433\u0438\u043d\u0430\u043b";
      if (!isExpanded) {
        trackEvent("original_post_open", {
          event_title: card.dataset.eventTitle.slice(0, 100),
        });
      }
      return;
    }

    if (!event.target.classList.contains("details-button")) return;

    const button = event.target;
    const description = button.previousElementSibling;
    const isExpanded = button.dataset.expanded === "true";
    const card = button.closest(".event-card");

    description.textContent = isExpanded
      ? description.dataset.previewText
      : description.dataset.fullText;
    button.dataset.expanded = String(!isExpanded);
    button.textContent = isExpanded
      ? "\u041f\u043e\u0434\u0440\u043e\u0431\u043d\u0435\u0435"
      : "\u0421\u0432\u0435\u0440\u043d\u0443\u0442\u044c";
    if (!isExpanded) {
      trackEvent("event_details_open", {
        event_title: card.dataset.eventTitle.slice(0, 100),
        category: card.dataset.category,
      });
    }
  });
}

function trackScrollDepth() {
  const documentHeight = document.documentElement.scrollHeight;
  if (!documentHeight) return;

  const viewedPercent = ((window.scrollY + window.innerHeight) / documentHeight) * 100;
  [
    { depth: 50, eventName: "scroll_50" },
    { depth: 90, eventName: "scroll_90" },
  ].forEach(({ depth, eventName }) => {
    if (viewedPercent >= depth && !trackedScrollDepths.has(depth)) {
      trackedScrollDepths.add(depth);
      trackEvent(eventName, { page_path: window.location.pathname });
    }
  });
}

function bindScrollAnalytics() {
  window.addEventListener("scroll", trackScrollDepth, { passive: true });
  window.addEventListener("resize", trackScrollDepth);
}

function bindScrollTopButton() {
  const toggleScrollTopButton = () => {
    elements.scrollTop.hidden = window.scrollY < 500;
  };

  window.addEventListener("scroll", toggleScrollTopButton, { passive: true });
  elements.scrollTop.addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
  toggleScrollTopButton();
}

bindFilters();
bindScrollTopButton();
bindScrollAnalytics();
loadEvents();

// Expire offers even when the page stays open across the Sunday/Monday boundary.
let lastRenderedDay = getTodayISO();
function refreshCalendarDay() {
  const today = getTodayISO();
  if (today !== lastRenderedDay) {
    lastRenderedDay = today;
    renderEvents();
  }
}
setInterval(refreshCalendarDay, 60000);
document.addEventListener("visibilitychange", refreshCalendarDay);
