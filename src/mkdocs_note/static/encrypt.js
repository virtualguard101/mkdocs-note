/**
 * Encrypted note unlock (mkdocs-note).
 *
 * Each encrypted page ships a locked stub plus an AES-GCM payload. This script
 * derives the key with PBKDF2 (WebCrypto), decrypts the payload and replaces
 * the stub with the real Material content. A derived key can be remembered in
 * sessionStorage or localStorage; the password itself is never stored.
 */
(function () {
  "use strict";

  const STUB_SELECTOR = "[data-mkdocs-note-encrypted]";
  const PAYLOAD_SELECTOR = ".mkdocs-note-encrypted__payload";
  const ERROR_SELECTOR = ".mkdocs-note-encrypted__error";
  const STORAGE_PREFIX = "mkdocs-note:encrypt:";

  function options() {
    return window.mkdocs_note_encrypt_options || {};
  }

  function labels() {
    return options().labels || {};
  }

  function label(key, fallback) {
    const value = labels()[key];
    return typeof value === "string" && value ? value : fallback;
  }

  function hasWebCrypto() {
    return Boolean(
      window.isSecureContext &&
        window.crypto &&
        window.crypto.subtle &&
        typeof window.crypto.subtle.decrypt === "function"
    );
  }

  function b64ToBytes(value) {
    const binary = atob(value);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes;
  }

  function bytesToB64(bytes) {
    let binary = "";
    for (let i = 0; i < bytes.length; i += 1) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }

  function storage() {
    const mode = options().remember || "session";
    if (mode === "none") return null;
    try {
      return mode === "local" ? window.localStorage : window.sessionStorage;
    } catch (_) {
      return null;
    }
  }

  function storageKey(salt) {
    return STORAGE_PREFIX + salt;
  }

  function rememberKey(salt, key) {
    const store = storage();
    if (!store) return;
    try {
      window.crypto.subtle
        .exportKey("raw", key)
        .then(function (raw) {
          try {
            store.setItem(storageKey(salt), bytesToB64(new Uint8Array(raw)));
          } catch (_) {
            /* storage may be full or blocked */
          }
        })
        .catch(function () {
          /* non-extractable key: skip remembering */
        });
    } catch (_) {
      /* ignore */
    }
  }

  function restoreKey(salt) {
    const store = storage();
    if (!store) return Promise.resolve(null);
    let raw = null;
    try {
      raw = store.getItem(storageKey(salt));
    } catch (_) {
      return Promise.resolve(null);
    }
    if (!raw) return Promise.resolve(null);
    try {
      return window.crypto.subtle.importKey(
        "raw",
        b64ToBytes(raw),
        "AES-GCM",
        true,
        ["decrypt"]
      );
    } catch (_) {
      return Promise.resolve(null);
    }
  }

  function normalizePassword(value) {
    let text = String(value);
    if (typeof text.normalize === "function") {
      text = text.normalize("NFC");
    }
    return text.trim();
  }

  async function deriveKey(password, payload) {
    const baseKey = await window.crypto.subtle.importKey(
      "raw",
      new TextEncoder().encode(normalizePassword(password)),
      "PBKDF2",
      false,
      ["deriveKey"]
    );
    return window.crypto.subtle.deriveKey(
      {
        name: "PBKDF2",
        salt: b64ToBytes(payload.salt),
        iterations: payload.iter,
        hash: "SHA-256",
      },
      baseKey,
      { name: "AES-GCM", length: 256 },
      true,
      ["decrypt"]
    );
  }

  async function decryptPayload(payload, key) {
    const plaintext = await window.crypto.subtle.decrypt(
      {
        name: "AES-GCM",
        iv: b64ToBytes(payload.iv),
        additionalData: b64ToBytes(payload.aad),
        tagLength: 128,
      },
      key,
      b64ToBytes(payload.ct)
    );
    return JSON.parse(new TextDecoder().decode(plaintext));
  }

  function injectToc(tocHtml) {
    if (!tocHtml) return;
    let nav = document.querySelector(
      ".md-sidebar--secondary .md-nav--secondary"
    );
    if (!nav) {
      const inner = document.querySelector(
        ".md-sidebar--secondary .md-sidebar__inner"
      );
      if (!inner) return;
      nav = document.createElement("nav");
      nav.className = "md-nav md-nav--secondary";
      inner.appendChild(nav);
    }
    nav.innerHTML = tocHtml;
  }

  function scrollToHash() {
    const hash = window.location.hash;
    if (!hash || hash.length < 2) return;
    let id = hash.slice(1);
    try {
      id = decodeURIComponent(id);
    } catch (_) {
      /* keep the raw fragment */
    }
    const target =
      document.getElementById(id) || document.getElementsByName(id)[0];
    if (target && typeof target.scrollIntoView === "function") {
      target.scrollIntoView();
    }
  }

  function reveal(stub, data) {
    const holder = document.createElement("div");
    holder.className = "mkdocs-note-encrypted__content";
    holder.innerHTML = data.content || "";
    stub.replaceWith(holder);
    injectToc(data.toc || "");
    scrollToHash();
    try {
      document.dispatchEvent(
        new CustomEvent("mkdocs-note:decrypted", {
          detail: { element: holder },
        })
      );
    } catch (_) {
      /* CustomEvent is unavailable in very old browsers */
    }
    if (options().rerender !== false && window.document$) {
      window.document$.next(document);
    }
  }

  function showError(node, message) {
    if (node) node.textContent = message;
  }

  function clearError(node) {
    if (node) node.textContent = "";
  }

  function setBusy(button, busy) {
    if (!button) return;
    button.disabled = busy;
    button.setAttribute("aria-busy", busy ? "true" : "false");
  }

  async function unlockWithKey(stub, payload, key) {
    const data = await decryptPayload(payload, key);
    reveal(stub, data);
  }

  function bindStub(stub) {
    if (stub.dataset.mkdocsNoteBound === "1") return;
    stub.dataset.mkdocsNoteBound = "1";

    const payloadNode = stub.querySelector(PAYLOAD_SELECTOR);
    if (!payloadNode) return; // e.g. an unavailable stub

    let payload;
    try {
      payload = JSON.parse(payloadNode.textContent);
    } catch (_) {
      return;
    }

    const form = stub.querySelector("form");
    const input = stub.querySelector("input[type=password]");
    const errorNode = stub.querySelector(ERROR_SELECTOR);
    const submit = stub.querySelector("button[type=submit]");

    if (!hasWebCrypto()) {
      showError(
        errorNode,
        label("unsupported", "Decryption needs a modern browser over HTTPS.")
      );
      if (form) form.hidden = true;
      return;
    }

    if (form && input) {
      form.addEventListener("submit", async function (event) {
        event.preventDefault();
        clearError(errorNode);
        setBusy(submit, true);
        try {
          const key = await deriveKey(input.value, payload);
          await unlockWithKey(stub, payload, key);
          rememberKey(payload.salt, key);
        } catch (_) {
          showError(errorNode, label("error", "Incorrect password."));
          setBusy(submit, false);
        }
      });
    }

    restoreKey(payload.salt).then(function (key) {
      if (!key) return;
      unlockWithKey(stub, payload, key).catch(function () {
        showError(errorNode, label("error", "Incorrect password."));
      });
    });
  }

  function boot() {
    const stubs = document.querySelectorAll(STUB_SELECTOR);
    for (let i = 0; i < stubs.length; i += 1) {
      bindStub(stubs[i]);
    }
  }

  // Node-based interop tests load this file with `require` and call the same
  // routines the browser uses. Browsers have no `module`, so nothing changes
  // there.
  if (typeof module === "object" && module.exports) {
    module.exports = {
      normalizePassword: normalizePassword,
      deriveKey: deriveKey,
      decryptPayload: decryptPayload,
    };
  }

  if (typeof document === "undefined") {
    return;
  }

  if (window.document$) {
    window.document$.subscribe(boot);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
