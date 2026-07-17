/**
 * @name nimbus-FavoriteStar
 * @author nimbus Team
 * @description Pin/unpin the selected skin as a champion's favorite from champ select
 * @link https://github.com/ddddasdfs/Nimbus
 */
(function initFavoriteStar() {
  const LOG_PREFIX = "[nimbus-FavoriteStar]";
  const STAR_ID = "nimbus-favorite-star";
  const BANNER_ID = "nimbus-favorite-banner";
  const SKIN_STATE_EVENT = "lu-skin-monitor-state"; // dispatched by nimbus-SkinMonitor
  const STAR_FILLED = "★"; // ★
  const STAR_EMPTY = "☆";  // ☆

  // Shared bridge (provided by nimbus-SkinMonitor)
  let bridge = null;
  let isInChampSelect = false;
  let favoritesMap = {}; // { "<championId>": <skinId:int> | "path:<rel>" }
  let starElement = null;
  let rollGuardChamp = null;          // champion we've already tried to auto-roll for
  let rolling = false;                // an auto-roll sequence is in progress
  let championLocked = false;         // Python's authoritative "your champion is locked" signal
  const champDataCache = new Map();   // championId -> Map(skinId -> name)

  const CSS_RULES = `
    #${STAR_ID} {
      position: absolute;
      height: 34px;
      width: 34px;
      line-height: 32px;
      text-align: center;
      font-size: 22px;
      cursor: pointer;
      pointer-events: auto;
      z-index: 10;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(1,10,19,0.78) 0%, rgba(1,10,19,0.55) 68%, rgba(1,10,19,0.05) 100%);
      border: 1px solid #785a28;
      box-shadow: 0 0 6px rgba(0,0,0,0.65);
      -webkit-user-select: none;
      user-select: none;
      transition: transform 0.1s ease, box-shadow 0.15s ease, border-color 0.15s ease;
    }
    #${STAR_ID}:hover {
      transform: scale(1.15);
      border-color: #c8aa6e;
    }
    #${STAR_ID}.pinned {
      border-color: #f0c453;
      box-shadow: 0 0 11px rgba(240,190,70,0.8), inset 0 0 7px rgba(240,190,70,0.35);
    }

    #${BANNER_ID} {
      position: fixed;
      left: 50%;
      bottom: calc(10% + 172px);
      transform: translateX(-50%);
      z-index: 50;
      display: flex;
      align-items: center;
      gap: 7px;
      padding: 5px 14px;
      background: linear-gradient(to bottom, rgba(10,20,40,0.92), rgba(1,10,19,0.92));
      border: 1px solid #785a28;
      border-radius: 2px;
      box-shadow: 0 0 10px rgba(0,0,0,0.6), inset 0 0 8px rgba(240,190,70,0.12);
      color: #f0e6d2;
      font-family: "Beaufort for LOL", serif;
      font-size: 13px;
      letter-spacing: 0.03em;
      white-space: nowrap;
      pointer-events: none;
      -webkit-user-select: none;
    }
    #${BANNER_ID} .fav-b-star {
      color: #ffd65c;
      font-size: 15px;
      text-shadow: 0 0 6px rgba(255,200,70,0.8);
    }
    #${BANNER_ID} .fav-b-name { color: #c89b3c; font-weight: 700; }
    #${BANNER_ID} .fav-b-hint { color: #8a8272; font-size: 11px; }
  `;

  function waitForBridge() {
    return new Promise((resolve, reject) => {
      const timeout = 10000;
      const interval = 50;
      let elapsed = 0;
      const check = () => {
        if (window.__nimbusBridge) return resolve(window.__nimbusBridge);
        elapsed += interval;
        if (elapsed >= timeout) return reject(new Error("Bridge not available"));
        setTimeout(check, interval);
      };
      check();
    });
  }

  function log(level, message) {
    // Mirror to the app log (via the bridge) so diagnostics are visible without devtools.
    if (bridge) {
      try {
        bridge.send({ type: "chroma-log", source: "FavoriteStar", level: level, message: message, timestamp: Date.now() });
      } catch (e) { /* ignore */ }
    }
    const consoleMethod =
      level === "error" ? console.error : level === "warn" ? console.warn : console.log;
    consoleMethod(`${LOG_PREFIX} ${message}`);
  }

  // --- Current selection context (from nimbus-SkinMonitor global) ---
  function getContext() {
    const s = window.__nimbusSkinState || {};
    const championId = Number.isFinite(s.championId) ? s.championId : null;
    const skinId = Number.isFinite(s.skinId) ? s.skinId : null;
    return { championId, skinId };
  }

  // Is the currently-centered skin the pinned favorite for the current champion?
  function isCurrentPinned() {
    const { championId, skinId } = getContext();
    if (championId === null || skinId === null) return false;
    const v = favoritesMap[String(championId)];
    if (v === undefined || v === null) return false;
    return String(v) === String(skinId);
  }

  // Does the current champion have *any* pin?
  function championHasPin() {
    const { championId } = getContext();
    if (championId === null) return false;
    const v = favoritesMap[String(championId)];
    return v !== undefined && v !== null;
  }

  // The visually-centered skin in the carousel is `.skin-carousel-offset-2`
  // (NOT `.skin-selection-item-selected`, which stays on one tile as you scroll).
  function findCentralItem() {
    if (!isInChampSelect) return null;
    const items = document.querySelectorAll(".skin-selection-item");
    for (const item of items) {
      if (item.classList.contains("skin-carousel-offset-2")) return item;
    }
    // Fallback: the persistent selected tile (better than nothing).
    return document.querySelector(".skin-selection-item.skin-selection-item-selected");
  }

  function findContainer() {
    if (!isInChampSelect) return null;
    return (
      document.querySelector(".skin-selection-carousel-container") ||
      document.querySelector(".skin-selection-carousel") ||
      (document.querySelector(".champion-select-main-container") &&
        document.querySelector(".champion-select-main-container div.visible")) ||
      null
    );
  }

  function requestFavorites() {
    if (bridge) bridge.send({ type: "get-favorites", timestamp: Date.now() });
  }

  function handleFavoritesData(payload) {
    const data = payload && payload.favorites;
    favoritesMap = data && typeof data === "object" ? data : {};
    if (starElement) renderStarState();
    updateBanner();
    scheduleAutoRoll();
  }

  function onStarClick(ev) {
    ev.stopPropagation();
    ev.preventDefault();
    const { championId, skinId } = getContext();
    if (championId === null || skinId === null) {
      log("warn", "No champion/skin selected yet - ignoring star click");
      return;
    }
    if (isCurrentPinned()) {
      if (bridge) bridge.send({ type: "unpin-favorite", championId: championId, timestamp: Date.now() });
      delete favoritesMap[String(championId)]; // optimistic
      log("info", `Unpinned favorite for champion ${championId}`);
    } else {
      if (bridge) bridge.send({ type: "pin-favorite", championId: championId, value: skinId, timestamp: Date.now() });
      favoritesMap[String(championId)] = skinId; // optimistic
      log("info", `Pinned skin ${skinId} as favorite for champion ${championId}`);
    }
    renderStarState();
    setTimeout(requestFavorites, 200); // re-sync with Python (authoritative)
  }

  function renderStarState() {
    if (!starElement) return;
    const pinnedHere = isCurrentPinned();
    starElement.textContent = pinnedHere ? STAR_FILLED : STAR_EMPTY; // textContent = no injection surface
    starElement.classList.toggle("pinned", pinnedHere);
    starElement.style.color = pinnedHere ? "#ffd65c" : "#ece3d0";
    starElement.style.textShadow = pinnedHere
      ? "0 0 8px rgba(255,200,70,0.95), 0 0 2px rgba(0,0,0,0.9)"
      : "0 0 3px rgba(0,0,0,0.95)";
    if (pinnedHere) {
      starElement.title = "Pinned favorite. Click to unpin.";
    } else if (championHasPin()) {
      starElement.title = "This champion has a different pinned favorite. Click to pin this skin instead.";
    } else {
      starElement.title = "Pin this skin as your favorite for this champion";
    }
  }

  function removeStar() {
    document.getElementById(STAR_ID)?.remove();
    starElement = null;
  }

  // Create the star once and anchor it over the centered skin (mirrors the dice button).
  function createStar() {
    if (!isInChampSelect || !championLocked) return; // only once a champion is locked
    if (starElement && document.body.contains(starElement)) return; // already present

    const central = findCentralItem();
    const container = findContainer();
    if (!central || !container) return; // carousel not ready yet; MutationObserver will retry

    const containerStyle = window.getComputedStyle(container);
    if (containerStyle.position === "static") {
      container.style.position = "relative";
    }

    const itemRect = central.getBoundingClientRect();
    const containerRect = container.getBoundingClientRect();

    const star = document.createElement("div");
    star.id = STAR_ID;
    star.setAttribute("role", "button");
    // Top-left corner of the centered skin tile (reward flag lives top-right, so no overlap).
    star.style.left = `${itemRect.left - containerRect.left - 6}px`;
    star.style.top = `${itemRect.top - containerRect.top - 6}px`;
    star.addEventListener("click", onStarClick);

    container.appendChild(star);
    starElement = star;
    renderStarState();
    updateBanner();
    log("info", "Favorite star created over centered skin");
  }

  function handlePhaseChange(data) {
    const wasInChampSelect = isInChampSelect;
    isInChampSelect = data.phase === "ChampSelect" || data.phase === "FINALIZATION";
    if (isInChampSelect && !wasInChampSelect) {
      log("debug", "Entered ChampSelect");
      requestFavorites();
    } else if (!isInChampSelect && wasInChampSelect) {
      log("debug", "Left ChampSelect - cleaning up");
      removeStar();
      removeBanner();
      rollGuardChamp = null;
      championLocked = false;
    }
  }

  // Python's authoritative signal that YOUR champion is locked (loadout screen).
  function handleChampionLocked(data) {
    const wasLocked = championLocked;
    championLocked = !!(data && data.locked === true);
    if (championLocked && !wasLocked) {
      log("debug", "Champion locked - enabling favorite star + banner");
      requestFavorites();
      setTimeout(() => { createStar(); updateBanner(); scheduleAutoRoll(); }, 300);
    } else if (!championLocked && wasLocked) {
      log("debug", "Champion unlocked - removing star + banner");
      removeStar();
      removeBanner();
      rollGuardChamp = null;
    }
  }

  // nimbus-SkinMonitor publishes the centered skin as the carousel scrolls.
  function handleSkinStateChange() {
    if (!isInChampSelect || !championLocked) return;
    if (!starElement || !document.body.contains(starElement)) {
      createStar();
    } else {
      renderStarState();
    }
    updateBanner();
    scheduleAutoRoll();
  }

  // --- Name resolution (client's local game data; same endpoint the other plugins use) ---
  function fetchChampData(championId) {
    if (champDataCache.has(championId)) return Promise.resolve(champDataCache.get(championId));
    return fetch(`/lol-game-data/assets/v1/champions/${championId}.json`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (!data || !Array.isArray(data.skins)) return null;
        const m = new Map();
        data.skins.forEach((s) => {
          m.set(Number(s.id), s.name);
          if (Array.isArray(s.chromas)) {
            s.chromas.forEach((c) => {
              const nm = c.name && c.name !== data.name ? c.name : `${s.name} (chroma)`;
              m.set(Number(c.id), nm);
            });
          }
        });
        champDataCache.set(championId, m);
        return m;
      })
      .catch(() => null);
  }

  function fetchSkinName(championId, skinId) {
    return fetchChampData(championId).then((m) => (m ? m.get(Number(skinId)) || null : null));
  }

  // --- Confirmation banner: "★ You'll get: <skin>" while a pin is active ---
  function ensureBanner() {
    let b = document.getElementById(BANNER_ID);
    if (!b) {
      b = document.createElement("div");
      b.id = BANNER_ID;
      const star = document.createElement("span");
      star.className = "fav-b-star";
      star.textContent = "★";
      const lead = document.createElement("span");
      lead.textContent = "You'll get";
      const name = document.createElement("span");
      name.className = "fav-b-name";
      const hint = document.createElement("span");
      hint.className = "fav-b-hint";
      hint.textContent = "· unless you pick another skin";
      b.append(star, lead, name, hint);
      document.body.appendChild(b);
      b._nameEl = name;
    }
    return b;
  }

  function removeBanner() {
    document.getElementById(BANNER_ID)?.remove();
  }

  function updateBanner() {
    if (!isInChampSelect || !championLocked) return removeBanner(); // only after champion lock
    const { championId } = getContext();
    if (championId === null) return removeBanner();
    const pin = favoritesMap[String(championId)];
    if (pin === undefined || pin === null) return removeBanner();

    const b = ensureBanner();
    if (typeof pin === "string") {
      b._nameEl.textContent = "your custom mod"; // path: value
      return;
    }
    fetchSkinName(championId, Number(pin)).then((nm) => {
      // Guard: banner may have been removed while the fetch was in flight.
      if (document.getElementById(BANNER_ID) === b) {
        b._nameEl.textContent = nm || "skin " + pin;
      }
    });
  }

  // --- Best-effort auto-roll: navigate the carousel to center the pinned skin ---
  // Reads each tile's skin id from its thumbnail background-image URL
  // (…/champion-tiles/<champ>/<skinId>.jpg). Works for owned skins reliably; for
  // unowned skins it previews (the client may snap the *selection* back, but the
  // banner remains the authoritative "you'll get this" indicator).
  // Read a tile's skin id from any image URL it carries (background-image, <img> src,
  // or a src-like attribute on a custom element). Skin tiles use
  // /lol-game-data/assets/v1/champion-tiles/<champ>/<skinId>.jpg.
  function getTileSkinId(item) {
    const urls = [];
    const push = (u) => { if (u && typeof u === "string") urls.push(u); };
    const els = [item].concat(Array.from(item.querySelectorAll("*")));
    for (const el of els) {
      try { push(window.getComputedStyle(el).backgroundImage); } catch (e) { /* ignore */ }
      if (el.tagName === "IMG") push(el.getAttribute("src"));
      if (el.getAttribute) {
        push(el.getAttribute("src"));
        push(el.getAttribute("image"));
        push(el.getAttribute("data-src"));
      }
    }
    for (const u of urls) {
      const m = u.match(/champion-tiles\/\d+\/(\d{4,7})|\/(\d{4,7})\.(?:jpg|jpeg|png|webp)/i);
      if (m) return Number(m[1] || m[2]);
    }
    return null;
  }

  // Best-effort: click the pinned skin's tile to center it. The reliable center id comes
  // from nimbus-SkinMonitor (__nimbusSkinState.skinId); tile ids are read from images and
  // logged so we can see whether the DOM exposes them at all. Bounded, no stepping.
  function autoRoll() {
    if (rolling || !isInChampSelect || !championLocked) return;
    const { championId, skinId } = getContext();
    if (championId === null) return;
    const pin = favoritesMap[String(championId)];
    if (pin === undefined || pin === null || typeof pin === "string") return;
    const target = Number(pin);
    if (Number(skinId) === target) { log("info", "auto-roll: pinned skin already centered"); return; }

    rolling = true;
    let attempts = 0;
    const maxAttempts = 6;

    const tryOnce = () => {
      if (!isInChampSelect || !championLocked) { rolling = false; return; }
      const cur = getContext().skinId;
      if (Number(cur) === target) { rolling = false; log("info", "auto-roll: centered on pinned skin"); return; }
      if (attempts >= maxAttempts) { rolling = false; log("warn", "auto-roll: gave up"); return; }

      const items = document.querySelectorAll(".skin-selection-item");
      const readable = [];
      let clicked = false;
      for (const it of items) {
        const sid = getTileSkinId(it);
        if (sid !== null) readable.push(sid);
        if (sid === target && !clicked) {
          try { it.click(); clicked = true; } catch (e) { /* ignore */ }
        }
      }
      log("info", `auto-roll try ${attempts}: center=${cur} target=${target} tiles=${items.length} readableIds=[${readable.join(",")}] clicked=${clicked}`);

      attempts++;
      setTimeout(tryOnce, 500);
    };
    tryOnce();
  }

  // One bounded attempt per champion, after injection has settled.
  function scheduleAutoRoll() {
    if (!isInChampSelect || !championLocked) return;
    const { championId } = getContext();
    if (championId === null || rollGuardChamp === championId) return;
    const pin = favoritesMap[String(championId)];
    if (pin === undefined || pin === null || typeof pin === "string") return;
    rollGuardChamp = championId;
    setTimeout(autoRoll, 1800);
  }

  async function init() {
    log("info", "Initializing nimbus-FavoriteStar plugin");
    bridge = await waitForBridge();

    const style = document.createElement("style");
    style.textContent = CSS_RULES;
    document.head.appendChild(style);

    bridge.subscribe("favorites-data", handleFavoritesData);
    bridge.subscribe("phase-change", handlePhaseChange);
    bridge.subscribe("champion-locked", handleChampionLocked);
    bridge.onReady(() => {
      requestFavorites();
    });

    // React to skin/champion selection changes published by nimbus-SkinMonitor.
    window.addEventListener(SKIN_STATE_EVENT, handleSkinStateChange);

    // The carousel re-renders frequently; (re)create the star if it's missing.
    const observer = new MutationObserver(() => {
      if (isInChampSelect && (!starElement || !document.body.contains(starElement))) {
        createStar();
      }
    });
    observer.observe(document.body, { childList: true, subtree: true });

    log("info", "nimbus-FavoriteStar plugin initialized");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
