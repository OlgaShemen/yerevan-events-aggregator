(function initializeAnalytics() {
  const config = window.YEREVAN_EVENTS_ANALYTICS;
  const pendingEvents = [];
  const debugMode = new URLSearchParams(window.location.search).get("ga_debug") === "1";
  let consent = config?.consent || null;

  const elements = {
    banner: document.querySelector("#cookie-banner"),
    allow: document.querySelector("#analytics-allow-button"),
    deny: document.querySelector("#analytics-deny-button"),
    close: document.querySelector("#analytics-close-button"),
    settings: document.querySelector("#analytics-settings-button"),
    feedback: document.querySelector("#feedback-link"),
  };

  function safeStorageSet(value) {
    try {
      localStorage.setItem(config.storageKey, value);
    } catch (error) {
      // Consent still applies for this page when browser storage is unavailable.
    }
  }

  function deleteAnalyticsCookies() {
    const cookieNames = document.cookie
      .split(";")
      .map((cookie) => cookie.split("=")[0].trim())
      .filter((name) => name === "_ga" || name.startsWith("_ga_"));
    const hostnameParts = window.location.hostname.split(".");
    const domains = new Set([window.location.hostname, `.${window.location.hostname}`]);

    for (let index = 1; index < hostnameParts.length - 1; index += 1) {
      const parentDomain = hostnameParts.slice(index).join(".");
      domains.add(parentDomain);
      domains.add(`.${parentDomain}`);
    }

    cookieNames.forEach((name) => {
      document.cookie = `${name}=; Max-Age=0; Path=/; SameSite=Lax`;
      domains.forEach((domain) => {
        document.cookie = `${name}=; Max-Age=0; Path=/; Domain=${domain}; SameSite=Lax`;
      });
    });
  }

  function hideBanner() {
    elements.banner.hidden = true;
  }

  function showBanner() {
    elements.close.hidden = consent === null;
    elements.banner.hidden = false;
  }

  function sendEvent(name, parameters = {}) {
    const eventParameters = debugMode
      ? { ...parameters, debug_mode: true }
      : parameters;
    window.gtag("event", name, eventParameters);
  }

  function flushPendingEvents() {
    pendingEvents.splice(0).forEach(({ name, parameters }) => {
      sendEvent(name, parameters);
    });
  }

  function track(name, parameters = {}) {
    if (consent === "granted") {
      sendEvent(name, parameters);
      return;
    }

    if (consent === null && pendingEvents.length < 50) {
      pendingEvents.push({ name, parameters });
    }
  }

  function updateConsent(value) {
    const wasGranted = consent === "granted";
    consent = value;
    config.consent = value;
    safeStorageSet(value);

    window.gtag("consent", "update", {
      analytics_storage: value,
      ad_storage: "denied",
      ad_user_data: "denied",
      ad_personalization: "denied",
    });

    if (value === "granted") {
      if (!wasGranted) {
        sendEvent("page_view", {
          page_path: `${window.location.pathname}${window.location.search}`,
        });
      }
      flushPendingEvents();
    } else {
      pendingEvents.length = 0;
      deleteAnalyticsCookies();
    }

    hideBanner();
  }

  window.yerevanAnalytics = { track };

  elements.allow.addEventListener("click", () => updateConsent("granted"));
  elements.deny.addEventListener("click", () => updateConsent("denied"));
  elements.close.addEventListener("click", hideBanner);
  elements.settings.addEventListener("click", showBanner);
  elements.feedback.addEventListener("click", () => {
    track("feedback_click", { location: "test_notice" });
  });

  if (consent === null) {
    showBanner();
  }
})();
