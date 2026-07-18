/**
 * @name nimbus-ChromaDice
 * @author nimbus Team
 * @description Arm a random chroma of the applied skin for this game
 * @link https://github.com/ddddasdfs/Nimbus
 */
(function initChromaDice() {
  const LOG_PREFIX = "[nimbus-ChromaDice]";
  const BTN_ID = "nimbus-chroma-dice";
  const SKIN_STATE_EVENT = "lu-skin-monitor-state"; // from nimbus-SkinMonitor

  let bridge = null;
  let isInChampSelect = false;
  let championLocked = false;
  let armed = false;
  let btn = null;

  const CSS_RULES = `
    #${BTN_ID} {
      position: absolute;
      height: 26px;
      width: 26px;
      line-height: 24px;
      text-align: center;
      font-size: 15px;
      cursor: pointer;
      pointer-events: auto;
      z-index: 10;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(1,10,19,0.8) 0%, rgba(1,10,19,0.5) 70%, rgba(1,10,19,0.05) 100%);
      border: 1px solid #785a28;
      box-shadow: 0 0 5px rgba(0,0,0,0.6);
      color: #cdbe91;
      opacity: 0.85;
      -webkit-user-select: none;
      user-select: none;
      transition: transform 0.1s ease, box-shadow 0.15s ease, border-color 0.15s ease;
    }
    #${BTN_ID}:hover { transform: scale(1.12); border-color: #c8aa6e; }
    #${BTN_ID}.armed {
      border-color: #f0c453;
      color: #ffd65c;
      opacity: 1;
      box-shadow: 0 0 10px rgba(240,190,70,0.75), inset 0 0 6px rgba(240,190,70,0.3);
    }
  `;

  function waitForBridge() {
    return new Promise((resolve, reject) => {
      const timeout = 10000, interval = 50;
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
    if (bridge) {
      try {
        bridge.send({ type: "chroma-log", source: "ChromaDice", level: level, message: message, timestamp: Date.now() });
      } catch (e) { /* ignore */ }
    }
    (level === "error" ? console.error : level === "warn" ? console.warn : console.log)(`${LOG_PREFIX} ${message}`);
  }

  function centeredSkinHasChromas() {
    const s = window.__nimbusSkinState || {};
    return s.hasChromas === true;
  }

  // Anchor next to the Random Skin dice: same carousel container, centered tile,
  // offset to the right of the dice (dice is 38px wide, centered, top+78).
  function findContainer() {
    return (
      document.querySelector(".skin-selection-carousel-container") ||
      document.querySelector(".skin-selection-carousel") ||
      null
    );
  }

  function findCentralItem() {
    const items = document.querySelectorAll(".skin-selection-item");
    for (const it of items) {
      if (it.classList.contains("skin-carousel-offset-2")) return it;
    }
    return null;
  }

  function removeButton() {
    document.getElementById(BTN_ID)?.remove();
    btn = null;
  }

  function renderState() {
    if (!btn) return;
    btn.classList.toggle("armed", armed);
    btn.title = armed
      ? "Random chroma armed for this game. Click to disarm."
      : "Roll a random chroma of your applied skin this game";
  }

  function updateButton() {
    if (!isInChampSelect || !championLocked || !centeredSkinHasChromas()) {
      removeButton();
      return;
    }
    if (btn && document.body.contains(btn)) { renderState(); return; }

    const container = findContainer();
    const central = findCentralItem();
    if (!container || !central) return; // observer will retry

    const cs = window.getComputedStyle(container);
    if (cs.position === "static") container.style.position = "relative";

    const itemRect = central.getBoundingClientRect();
    const contRect = container.getBoundingClientRect();

    const el = document.createElement("div");
    el.id = BTN_ID;
    el.setAttribute("role", "button");
    el.textContent = "⚅"; // die face-6 glyph, textContent = no injection surface
    // Right of where the RandomSkin dice sits (dice: centered, top+78, 38px wide).
    el.style.left = `${itemRect.left - contRect.left + itemRect.width / 2 + 26}px`;
    el.style.top = `${itemRect.top - contRect.top + 76}px`;
    el.addEventListener("click", (ev) => {
      ev.stopPropagation();
      ev.preventDefault();
      armed = !armed; // optimistic; broadcast is authoritative
      renderState();
      if (bridge) bridge.send({ type: "chroma-dice-click", timestamp: Date.now() });
    });

    container.appendChild(el);
    btn = el;
    renderState();
    log("info", "Chroma dice button created");
  }

  function handleChromaRandomState(payload) {
    armed = !!(payload && payload.armed === true);
    renderState();
  }

  function handlePhaseChange(data) {
    const was = isInChampSelect;
    isInChampSelect = data.phase === "ChampSelect" || data.phase === "FINALIZATION";
    if (isInChampSelect && !was) {
      armed = false; // Python resets on entry; mirror it
      if (bridge) bridge.send({ type: "get-chroma-random-state" });
    } else if (!isInChampSelect && was) {
      removeButton();
      championLocked = false;
      armed = false;
    }
  }

  function handleChampionLocked(data) {
    const was = championLocked;
    championLocked = !!(data && data.locked === true);
    if (championLocked && !was) {
      if (bridge) bridge.send({ type: "get-chroma-random-state" });
      setTimeout(updateButton, 350);
    } else if (!championLocked && was) {
      removeButton();
    }
  }

  function handleSkinStateChange() {
    // hasChromas changes as the carousel scrolls; show/hide accordingly
    if (isInChampSelect && championLocked) updateButton();
  }

  async function init() {
    log("info", "Initializing nimbus-ChromaDice plugin");
    bridge = await waitForBridge();

    const style = document.createElement("style");
    style.textContent = CSS_RULES;
    document.head.appendChild(style);

    bridge.subscribe("chroma-random-state", handleChromaRandomState);
    bridge.subscribe("phase-change", handlePhaseChange);
    bridge.subscribe("champion-locked", handleChampionLocked);

    window.addEventListener(SKIN_STATE_EVENT, handleSkinStateChange);

    const observer = new MutationObserver(() => {
      if (isInChampSelect && championLocked && (!btn || !document.body.contains(btn))) {
        updateButton();
      }
    });
    observer.observe(document.body, { childList: true, subtree: true });

    log("info", "nimbus-ChromaDice plugin initialized");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
