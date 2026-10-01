/**
 * Same-site link hover preview (mkdocs-note).
 * Loads previews.json once, shows a floating card on hover/focus.
 */
(function () {
  "use strict";

  const STATE = {
    data: null,
    loadPromise: null,
    abort: null,
    card: null,
    showTimer: null,
    hideTimer: null,
    activeAnchor: null,
    lru: new Map(),
    lruMax: 64,
    neighbors: null,
    touchArmed: null,
  };

  function options() {
    return window.preview_options || {};
  }

  function basePath() {
    const bp = options().base_path || "/";
    return bp.endsWith("/") ? bp : bp + "/";
  }

  function prefersReducedMotion() {
    return (
      window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    );
  }

  function cacheGet(key) {
    if (!STATE.lru.has(key)) return undefined;
    const val = STATE.lru.get(key);
    STATE.lru.delete(key);
    STATE.lru.set(key, val);
    return val;
  }

  function cacheSet(key, val) {
    if (STATE.lru.has(key)) STATE.lru.delete(key);
    STATE.lru.set(key, val);
    while (STATE.lru.size > STATE.lruMax) {
      const oldest = STATE.lru.keys().next().value;
      STATE.lru.delete(oldest);
    }
  }

  function ensureCard() {
    if (STATE.card) return STATE.card;
    const card = document.createElement("div");
    card.className = "mkdocs-note-preview";
    card.setAttribute("role", "tooltip");
    card.hidden = true;
    card.innerHTML =
      '<div class="mkdocs-note-preview__inner">' +
      '<div class="mkdocs-note-preview__media" hidden></div>' +
      '<div class="mkdocs-note-preview__title"></div>' +
      '<div class="mkdocs-note-preview__body"></div>' +
      "</div>";
    document.body.appendChild(card);
    card.addEventListener("mouseenter", () => clearTimeout(STATE.hideTimer));
    card.addEventListener("mouseleave", () => scheduleHide());
    STATE.card = card;
    return card;
  }

  function hideCard() {
    clearTimeout(STATE.showTimer);
    clearTimeout(STATE.hideTimer);
    if (STATE.abort) {
      try {
        STATE.abort.abort();
      } catch (_) {}
      STATE.abort = null;
    }
    const card = STATE.card;
    if (card) {
      card.hidden = true;
      card.classList.remove("mkdocs-note-preview--visible");
    }
    STATE.activeAnchor = null;
    STATE.touchArmed = null;
  }

  function scheduleHide() {
    clearTimeout(STATE.hideTimer);
    STATE.hideTimer = setTimeout(hideCard, 120);
  }

  function normalizeLookupKey(href) {
    try {
      const url = new URL(href, window.location.href);
      if (url.origin !== window.location.origin) return null;
      let path = url.pathname;
      const base = basePath();
      if (base !== "/" && path.startsWith(base)) {
        path = path.slice(base.length - 1);
      }
      // strip leading slash for JSON keys that omit it inconsistently
      let key = path.replace(/^\//, "");
      if (!key.endsWith("/") && !key.includes(".")) {
        key += "/";
      }
      // directory URLs: ensure trailing slash to match MkDocs file.url
      if (key && !key.endsWith("/") && !/\.[a-z0-9]+$/i.test(key)) {
        key += "/";
      }
      if (url.hash && url.hash.length > 1) {
        key += url.hash; // includes #
      }
      return key;
    } catch (_) {
      return null;
    }
  }

  function pageKeyWithoutFragment(key) {
    const i = key.indexOf("#");
    return i === -1 ? key : key.slice(0, i);
  }

  async function loadPreviews() {
    if (STATE.data) return STATE.data;
    if (STATE.loadPromise) return STATE.loadPromise;
    const controller = new AbortController();
    STATE.abort = controller;
    const url = basePath() + "previews/previews.json";
    STATE.loadPromise = fetch(url, { signal: controller.signal })
      .then((r) => {
        if (!r.ok) throw new Error("previews.json " + r.status);
        return r.json();
      })
      .then((data) => {
        STATE.data = data;
        return data;
      })
      .catch((err) => {
        if (err.name !== "AbortError") {
          console.warn("[mkdocs-note preview]", err);
        }
        STATE.loadPromise = null;
        return null;
      });
    return STATE.loadPromise;
  }

  function lookupEntry(data, key) {
    if (!data || !key) return null;
    const cached = cacheGet(key);
    if (cached !== undefined) return cached;

    let entry = data[key] || null;
    if (!entry && key.includes("#")) {
      entry = data[pageKeyWithoutFragment(key)] || null;
    }
    // try without trailing slash variants
    if (!entry) {
      const alt = key.endsWith("/") ? key.slice(0, -1) : key + "/";
      entry = data[alt] || null;
      if (!entry && alt.includes("#")) {
        entry = data[pageKeyWithoutFragment(alt)] || null;
      }
    }
    cacheSet(key, entry);
    return entry;
  }

  function renderCard(entry) {
    const card = ensureCard();
    const titleEl = card.querySelector(".mkdocs-note-preview__title");
    const bodyEl = card.querySelector(".mkdocs-note-preview__body");
    const mediaEl = card.querySelector(".mkdocs-note-preview__media");
    titleEl.textContent = entry.title || "";

    const mode = options().mode || "summary";
    bodyEl.className = "mkdocs-note-preview__body";
    if (mode === "excerpt" && entry.html) {
      bodyEl.classList.add("mkdocs-note-preview__body--rich");
      bodyEl.innerHTML = entry.html;
    } else if (mode === "excerpt" && entry.excerpt) {
      bodyEl.textContent = entry.excerpt;
    } else {
      bodyEl.textContent = entry.summary || "";
    }

    if (entry.image) {
      mediaEl.hidden = false;
      mediaEl.innerHTML =
        '<img class="mkdocs-note-preview__cover" alt="" src="' +
        entry.image.replace(/"/g, "&quot;") +
        '" loading="lazy"/>';
    } else {
      mediaEl.hidden = true;
      mediaEl.innerHTML = "";
    }
  }

  function positionCard(anchor) {
    const card = ensureCard();
    const rect = anchor.getBoundingClientRect();
    const margin = 8;
    card.hidden = false;
    // measure
    const cw = card.offsetWidth;
    const ch = card.offsetHeight;
    let top = rect.bottom + margin + window.scrollY;
    let left = rect.left + window.scrollX;

    if (left + cw > window.scrollX + window.innerWidth - margin) {
      left = window.scrollX + window.innerWidth - cw - margin;
    }
    if (left < window.scrollX + margin) left = window.scrollX + margin;

    if (rect.bottom + margin + ch > window.innerHeight && rect.top > ch + margin) {
      top = rect.top + window.scrollY - ch - margin;
    }

    card.style.top = top + "px";
    card.style.left = left + "px";
    if (prefersReducedMotion()) {
      card.classList.add("mkdocs-note-preview--visible");
    } else {
      requestAnimationFrame(() =>
        card.classList.add("mkdocs-note-preview--visible"),
      );
    }
  }

  async function showForAnchor(anchor) {
    const key = normalizeLookupKey(anchor.getAttribute("href") || "");
    if (!key) return;
    STATE.activeAnchor = anchor;
    const data = await loadPreviews();
    if (STATE.activeAnchor !== anchor) return;
    const entry = lookupEntry(data, key);
    if (!entry) return;
    renderCard(entry);
    positionCard(anchor);
    prefetchNeighbors(key);
  }

  function scheduleShow(anchor) {
    clearTimeout(STATE.showTimer);
    clearTimeout(STATE.hideTimer);
    const delay = prefersReducedMotion() ? 0 : Number(options().delay_ms || 300);
    STATE.showTimer = setTimeout(() => showForAnchor(anchor), delay);
  }

  function isPreviewableAnchor(a) {
    if (!a || a.tagName !== "A") return false;
    const href = a.getAttribute("href");
    if (!href || href.startsWith("#") || href.startsWith("mailto:")) return false;
    // Only inside article content
    if (!a.closest("article.md-content__inner, article.md-content, .md-content__inner")) {
      return false;
    }
    if (a.closest("nav, .md-nav, .md-footer, .md-header, .md-tabs, .toc, .md-sidebar")) {
      return false;
    }
    try {
      const url = new URL(href, window.location.href);
      if (url.origin !== window.location.origin) return false;
    } catch (_) {
      return false;
    }
    return true;
  }

  async function loadGraphNeighbors() {
    if (STATE.neighbors || !options().graph_enabled) return;
    try {
      const r = await fetch(basePath() + "graph/graph.json");
      if (!r.ok) return;
      const g = await r.json();
      const map = new Map();
      const idToUrl = new Map();
      (g.nodes || []).forEach((n) => idToUrl.set(n.id, n.url));
      (g.edges || []).forEach((e) => {
        if (!map.has(e.source)) map.set(e.source, []);
        if (!map.has(e.target)) map.set(e.target, []);
        map.get(e.source).push(e.target);
        map.get(e.target).push(e.source);
      });
      STATE.neighbors = { map, idToUrl };
    } catch (_) {
      /* soft dependency */
    }
  }

  function prefetchNeighbors(currentKey) {
    if (!STATE.data || !options().graph_enabled) return;
    loadGraphNeighbors().then(() => {
      if (!STATE.neighbors) return;
      // Warm LRU for page-level key
      const pageKey = pageKeyWithoutFragment(currentKey);
      lookupEntry(STATE.data, pageKey);
    });
  }

  function onPointerEnter(ev) {
    const a = ev.target.closest && ev.target.closest("a[href]");
    if (!isPreviewableAnchor(a)) return;
    scheduleShow(a);
  }

  function onPointerLeave(ev) {
    const a = ev.target.closest && ev.target.closest("a[href]");
    if (!a || a !== STATE.activeAnchor) {
      // leaving a tracked link
      if (a && isPreviewableAnchor(a)) scheduleHide();
      return;
    }
    scheduleHide();
  }

  function onFocusIn(ev) {
    const a = ev.target.closest && ev.target.closest("a[href]");
    if (!isPreviewableAnchor(a)) return;
    scheduleShow(a);
  }

  function onFocusOut(ev) {
    const a = ev.target.closest && ev.target.closest("a[href]");
    if (a && isPreviewableAnchor(a)) scheduleHide();
  }

  function onKeyDown(ev) {
    if (ev.key === "Escape") hideCard();
  }

  /**
   * Touch: first tap shows preview (prevent nav); second tap on same link navigates.
   */
  function onTouchEnd(ev) {
    if (!options().mobile) return;
    const a = ev.target.closest && ev.target.closest("a[href]");
    if (!isPreviewableAnchor(a)) return;
    if (STATE.touchArmed === a) {
      STATE.touchArmed = null;
      hideCard();
      return; // allow default navigation
    }
    ev.preventDefault();
    STATE.touchArmed = a;
    showForAnchor(a);
  }

  function bind() {
    const root = document.querySelector(".md-content") || document.body;
    root.addEventListener("pointerenter", onPointerEnter, true);
    root.addEventListener("pointerleave", onPointerLeave, true);
    root.addEventListener("focusin", onFocusIn, true);
    root.addEventListener("focusout", onFocusOut, true);
    document.addEventListener("keydown", onKeyDown);
    if (options().mobile) {
      root.addEventListener("touchend", onTouchEnd, { passive: false });
    }
    // Prefetch JSON idle
    if ("requestIdleCallback" in window) {
      requestIdleCallback(() => loadPreviews());
    } else {
      setTimeout(() => loadPreviews(), 800);
    }
    if (options().graph_enabled) {
      loadGraphNeighbors();
    }
  }

  function boot() {
    hideCard();
    bind();
  }

  if (window.document$) {
    document$.subscribe(boot);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
