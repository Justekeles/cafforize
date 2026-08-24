(() => {
  const defaults = window.CAFFORIZE_DEFAULTS || { water: 1.5, spoons: 2 };

  const waterSlider = document.getElementById("water-slider");
  const waterInput = document.getElementById("water");
  const actualSpoons = document.getElementById("actual-spoons");
  const spoonsValue = document.getElementById("spoons-value");
  const cupLiquid = document.getElementById("cup-liquid");
  const ratioText = document.getElementById("ratio-text");
  const logBtn = document.getElementById("log-btn");
  const feedback = document.getElementById("feedback");
  const historyList = document.getElementById("history-list");

  let currentSuggestion = defaults.spoons;
  let userEditedActual = false;
  let debounceHandle = null;

  function fmt(n) {
    const rounded = Math.round(n * 100) / 100;
    return Number.isInteger(rounded) ? String(rounded) : rounded.toFixed(2).replace(/0+$/, "").replace(/\.$/, "");
  }

  function setCupLevel(water) {
    const pct = Math.max(10, Math.min(100, (water / 4) * 100));
    cupLiquid.style.height = pct + "%";
  }

  async function refreshSuggestion() {
    const water = parseFloat(waterInput.value);
    if (!water || water <= 0) return;
    setCupLevel(water);

    try {
      const res = await fetch(`/api/suggestion?water=${encodeURIComponent(water)}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to get suggestion");

      currentSuggestion = data.spoons;
      spoonsValue.textContent = fmt(data.spoons);
      if (!userEditedActual) {
        actualSpoons.value = fmt(data.spoons);
      }

      if (data.source === "learned") {
        ratioText.textContent = `learned: your best-graded ratio (avg ${data.avg_grade}★, ${data.sample_size} brews)`;
      } else {
        ratioText.textContent = `default ratio: ${defaults.spoons} spoons per ${defaults.water} units`;
      }
    } catch (err) {
      ratioText.textContent = "couldn't reach the server";
    }
  }

  function scheduleRefresh() {
    clearTimeout(debounceHandle);
    debounceHandle = setTimeout(refreshSuggestion, 150);
  }

  waterSlider.addEventListener("input", () => {
    waterInput.value = waterSlider.value;
    scheduleRefresh();
  });

  waterInput.addEventListener("input", () => {
    const v = parseFloat(waterInput.value);
    if (!isNaN(v)) {
      waterSlider.value = Math.min(Math.max(v, waterSlider.min), waterSlider.max);
    }
    scheduleRefresh();
  });

  actualSpoons.addEventListener("input", () => {
    userEditedActual = true;
  });

  function timeAgo(iso) {
    const then = new Date(iso).getTime();
    const diffMin = Math.round((Date.now() - then) / 60000);
    if (diffMin < 1) return "just now";
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffH = Math.round(diffMin / 60);
    if (diffH < 24) return `${diffH}h ago`;
    return `${Math.round(diffH / 24)}d ago`;
  }

  function renderStars(brew) {
    const wrap = document.createElement("div");
    wrap.className = "stars" + (brew.grade ? " locked" : "");
    for (let i = 1; i <= 5; i++) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "★";
      if (brew.grade && i <= brew.grade) btn.classList.add("filled");
      btn.addEventListener("click", () => gradeBrew(brew.id, i));
      wrap.appendChild(btn);
    }
    return wrap;
  }

  async function gradeBrew(id, grade) {
    try {
      const res = await fetch(`/api/brews/${id}/grade`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ grade }),
      });
      if (!res.ok) throw new Error();
      loadHistory();
      refreshSuggestion();
    } catch {
      feedback.textContent = "Couldn't save that grade.";
      feedback.classList.add("error");
    }
  }

  async function loadHistory() {
    try {
      const res = await fetch("/api/brews");
      const data = await res.json();
      historyList.innerHTML = "";

      if (!data.history || data.history.length === 0) {
        const p = document.createElement("p");
        p.className = "empty";
        p.textContent = "No brews logged yet. Make one!";
        historyList.appendChild(p);
        return;
      }

      for (const brew of data.history) {
        const item = document.createElement("div");
        item.className = "brew-item";

        const meta = document.createElement("div");
        meta.className = "meta";
        const amounts = document.createElement("div");
        amounts.className = "amounts";
        amounts.textContent = `${fmt(brew.spoons_used)} spoons / ${fmt(brew.water_amount)} water`;
        const when = document.createElement("div");
        when.className = "when";
        when.textContent = timeAgo(brew.created_at);
        meta.appendChild(amounts);
        meta.appendChild(when);

        item.appendChild(meta);
        item.appendChild(renderStars(brew));
        historyList.appendChild(item);
      }
    } catch {
      // leave whatever was already rendered
    }
  }

  logBtn.addEventListener("click", async () => {
    const water = parseFloat(waterInput.value);
    const spoons = parseFloat(actualSpoons.value);
    feedback.classList.remove("error");

    if (!water || water <= 0 || !spoons || spoons <= 0) {
      feedback.textContent = "Enter valid water and spoon amounts.";
      feedback.classList.add("error");
      return;
    }

    try {
      const res = await fetch("/api/brews", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ water, spoons }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to log brew");

      feedback.textContent = "Brew logged! Grade it once you've tasted it.";
      userEditedActual = false;
      loadHistory();
    } catch (err) {
      feedback.textContent = err.message;
      feedback.classList.add("error");
    }
  });

  setCupLevel(defaults.water);
  refreshSuggestion();
  loadHistory();
})();
