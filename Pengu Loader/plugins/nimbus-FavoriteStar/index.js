/**
 * @name nimbus-FavoriteStar
 * @author nimbus Team
 * @description Pin/unpin the selected skin as a champion's favorite from champ select
 * @link https://github.com/ddddasdfs/Nimbus
 */
(function initFavoriteStar() {
  const LOG_PREFIX = "[nimbus-FavoriteStar]";
  const STAR_ID = "nimbus-favorite-star";
  const SKIN_STATE_EVENT = "lu-skin-monitor-state"; // dispatched by nimbus-SkinMonitor
  const STAR_FILLED = "★"; // ★
  const STAR_EMPTY = "☆";  // ☆

  // Shared bridge (provided by nimbus-SkinMonitor)
  let bridge = null;
  let isInChampSelect = false;
  let favoritesMap = {}; // { "<championId>": <skinId:int> | "path:<rel>" }
  let starElement = null;

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
    if (!isInChampSelect) return;
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
    log("info", "Favorite star created over centered skin");
  }

  function handlePhaseChange(data) {
    const wasInChampSelect = isInChampSelect;
    isInChampSelect = data.phase === "ChampSelect" || data.phase === "FINALIZATION";
    if (isInChampSelect && !wasInChampSelect) {
      log("debug", "Entered ChampSelect - enabling favorite star");
      requestFavorites();
      setTimeout(createStar, 300);
    } else if (!isInChampSelect && wasInChampSelect) {
      log("debug", "Left ChampSelect - removing favorite star");
      removeStar();
    }
  }

  // nimbus-SkinMonitor publishes the centered skin as the carousel scrolls.
  function handleSkinStateChange() {
    if (!isInChampSelect) return;
    if (!starElement || !document.body.contains(starElement)) {
      createStar();
    } else {
      renderStarState();
    }
  }

  async function init() {
    log("info", "Initializing nimbus-FavoriteStar plugin");
    bridge = await waitForBridge();

    const style = document.createElement("style");
    style.textContent = CSS_RULES;
    document.head.appendChild(style);

    bridge.subscribe("favorites-data", handleFavoritesData);
    bridge.subscribe("phase-change", handlePhaseChange);
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
