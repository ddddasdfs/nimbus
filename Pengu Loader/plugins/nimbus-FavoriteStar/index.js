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

  // Is the currently-selected skin the pinned favorite for the current champion?
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

  function findSelectedItem() {
    if (!isInChampSelect) return null;
    return document.querySelector(
      ".skin-selection-item.skin-selection-item-selected"
    );
  }

  function requestFavorites() {
    if (bridge) bridge.send({ type: "get-favorites", timestamp: Date.now() });
  }

  function handleFavoritesData(payload) {
    const data = payload && payload.favorites;
    favoritesMap = data && typeof data === "object" ? data : {};
    updateStar();
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
      // Unpin this champion's favorite
      if (bridge) bridge.send({ type: "unpin-favorite", championId: championId, timestamp: Date.now() });
      delete favoritesMap[String(championId)]; // optimistic
      log("info", `Unpinned favorite for champion ${championId}`);
    } else {
      // Pin the currently-selected skin/chroma id
      if (bridge) bridge.send({ type: "pin-favorite", championId: championId, value: skinId, timestamp: Date.now() });
      favoritesMap[String(championId)] = skinId; // optimistic
      log("info", `Pinned skin ${skinId} as favorite for champion ${championId}`);
    }
    updateStar();
    // Re-sync with Python shortly after (authoritative)
    setTimeout(requestFavorites, 200);
  }

  function createStar() {
    const star = document.createElement("div");
    star.id = STAR_ID;
    star.setAttribute("role", "button");
    star.setAttribute("title", "Pin this skin as your favorite for this champion");
    Object.assign(star.style, {
      position: "absolute",
      left: "-14px",
      top: "-14px",
      height: "28px",
      width: "28px",
      lineHeight: "28px",
      textAlign: "center",
      fontSize: "22px",
      cursor: "pointer",
      pointerEvents: "auto",
      zIndex: "10",
      textShadow: "0 0 4px rgba(0,0,0,0.9)",
      WebkitUserSelect: "none",
      userSelect: "none",
    });
    star.addEventListener("click", onStarClick);
    return star;
  }

  function renderStarState(star) {
    const pinnedHere = isCurrentPinned();
    // textContent (not innerHTML) — no injection surface
    star.textContent = pinnedHere ? STAR_FILLED : STAR_EMPTY;
    star.style.color = pinnedHere ? "#f0c060" : "#c8c8c8";
    star.style.opacity = pinnedHere ? "1" : "0.75";
    if (championHasPin() && !pinnedHere) {
      // Champion has a pin, but it's a different skin than the one being viewed
      star.title = "This champion has a different pinned favorite. Click to pin this skin instead.";
    } else if (pinnedHere) {
      star.title = "Pinned favorite. Click to unpin.";
    } else {
      star.title = "Pin this skin as your favorite for this champion";
    }
  }

  function removeStar() {
    document.getElementById(STAR_ID)?.remove();
  }

  function updateStar() {
    if (!isInChampSelect) {
      removeStar();
      return;
    }
    const item = findSelectedItem();
    if (!item) {
      // Selected item not in DOM yet; the MutationObserver will re-trigger us.
      return;
    }
    // Ensure the item is a positioning context for our absolute star.
    const computed = window.getComputedStyle(item);
    if (computed.position === "static") {
      item.style.position = "relative";
    }
    let star = document.getElementById(STAR_ID);
    if (!star) {
      star = createStar();
    }
    // Move the star into the currently-selected item (selection can change).
    if (star.parentElement !== item) {
      item.appendChild(star);
    }
    renderStarState(star);
  }

  function handlePhaseChange(data) {
    const wasInChampSelect = isInChampSelect;
    isInChampSelect = data.phase === "ChampSelect" || data.phase === "FINALIZATION";
    if (isInChampSelect && !wasInChampSelect) {
      log("debug", "Entered ChampSelect - enabling favorite star");
      requestFavorites();
      setTimeout(updateStar, 200);
    } else if (!isInChampSelect && wasInChampSelect) {
      log("debug", "Left ChampSelect - removing favorite star");
      removeStar();
    }
  }

  function handleSkinStateChange() {
    // Current skin/champ changed - refresh the star's filled/empty state and anchor.
    if (isInChampSelect) updateStar();
  }

  async function init() {
    log("info", "Initializing nimbus-FavoriteStar plugin");
    bridge = await waitForBridge();

    bridge.subscribe("favorites-data", handleFavoritesData);
    bridge.subscribe("phase-change", handlePhaseChange);
    bridge.onReady(() => {
      requestFavorites();
    });

    // React to skin/champion selection changes published by nimbus-SkinMonitor.
    window.addEventListener(SKIN_STATE_EVENT, handleSkinStateChange);

    // The champ-select skin carousel re-renders frequently; re-attach the star on DOM changes.
    const observer = new MutationObserver(() => {
      if (isInChampSelect) updateStar();
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
