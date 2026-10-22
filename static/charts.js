function initTickerCharts(ticker, labels) {
  labels = labels || {};
  const style = getComputedStyle(document.documentElement);
  const colors = {
    accent: style.getPropertyValue("--accent").trim(),
    up: style.getPropertyValue("--up").trim(),
    down: style.getPropertyValue("--down").trim(),
    muted: style.getPropertyValue("--muted").trim(),
    grid: style.getPropertyValue("--border").trim(),
  };

  const monoFont = { size: 11, family: "'Space Mono', monospace" };
  const baseScales = {
    x: { ticks: { color: colors.muted, maxTicksLimit: 8, font: monoFont }, grid: { color: colors.grid } },
    y: { ticks: { color: colors.muted, font: monoFont }, grid: { color: colors.grid } },
  };
  const baseOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    plugins: { legend: { labels: { color: colors.muted, boxWidth: 14, font: monoFont } } },
  };

  const charts = {};
  const state = { intradayTimer: null, intradayRange: "1d" };

  initChartTabs(ticker, charts, state, colors, baseOptions, baseScales, labels);
  initChartRefreshButton(ticker, charts, state, colors, baseOptions, baseScales, labels);

  loadMainCharts(ticker, charts, colors, baseOptions, baseScales, labels);
}

function loadMainCharts(ticker, charts, colors, baseOptions, baseScales, labels, onDone) {
  const errorEl = document.getElementById("charts-error");

  fetch(`/hisse/${ticker}/chart-data`)
    .then((r) => r.json())
    .then((d) => {
      if (d.error) {
        if (errorEl) errorEl.textContent = d.error;
        return;
      }
      if (errorEl) errorEl.textContent = "";

      const priceData = {
        labels: d.dates,
        datasets: [
          { label: labels.close || "Close", data: d.close, borderColor: colors.accent, backgroundColor: "transparent", pointRadius: 0, borderWidth: 2 },
          { label: "SMA20", data: d.sma_short, borderColor: colors.up, backgroundColor: "transparent", pointRadius: 0, borderWidth: 1 },
          { label: "SMA50", data: d.sma_long, borderColor: colors.down, backgroundColor: "transparent", pointRadius: 0, borderWidth: 1 },
        ],
      };
      const rsiData = {
        labels: d.dates,
        datasets: [
          { label: "RSI", data: d.rsi, borderColor: colors.accent, backgroundColor: "transparent", pointRadius: 0, borderWidth: 2 },
          { label: labels.overbought || "Overbought (70)", data: d.dates.map(() => 70), borderColor: colors.down, borderDash: [4, 4], pointRadius: 0, borderWidth: 1 },
          { label: labels.oversold || "Oversold (30)", data: d.dates.map(() => 30), borderColor: colors.up, borderDash: [4, 4], pointRadius: 0, borderWidth: 1 },
        ],
      };
      const macdData = {
        labels: d.dates,
        datasets: [
          { type: "bar", label: labels.histogram || "Histogram", data: d.macd_hist, backgroundColor: colors.muted, borderWidth: 0 },
          { type: "line", label: "MACD", data: d.macd, borderColor: colors.accent, backgroundColor: "transparent", pointRadius: 0, borderWidth: 2 },
          { type: "line", label: labels.signal || "Signal", data: d.macd_signal, borderColor: colors.down, backgroundColor: "transparent", pointRadius: 0, borderWidth: 1 },
        ],
      };

      if (charts.priceChart) {
        charts.priceChart.data = priceData;
        charts.priceChart.update();
      } else {
        charts.priceChart = new Chart(document.getElementById("priceChart"), {
          type: "line",
          data: priceData,
          options: { ...baseOptions, scales: baseScales },
        });
      }

      if (charts.rsiChart) {
        charts.rsiChart.data = rsiData;
        charts.rsiChart.update();
      } else {
        charts.rsiChart = new Chart(document.getElementById("rsiChart"), {
          type: "line",
          data: rsiData,
          options: { ...baseOptions, scales: { x: baseScales.x, y: { ...baseScales.y, min: 0, max: 100 } } },
        });
      }

      if (charts.macdChart) {
        charts.macdChart.data = macdData;
        charts.macdChart.update();
      } else {
        charts.macdChart = new Chart(document.getElementById("macdChart"), {
          type: "bar",
          data: macdData,
          options: { ...baseOptions, scales: baseScales },
        });
      }
    })
    .catch(() => {
      if (errorEl) errorEl.textContent = labels.errorData || "Failed to load chart data.";
    })
    .finally(() => {
      if (onDone) onDone();
    });
}

function initChartTabs(ticker, charts, state, colors, baseOptions, baseScales, labels) {
  const buttons = document.querySelectorAll(".chart-tab-btn");
  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = btn.dataset.target;

      document.querySelectorAll(".chart-tab-btn").forEach((b) => b.classList.toggle("active", b === btn));
      document.querySelectorAll(".chart-pane").forEach((pane) => {
        pane.classList.toggle("active", pane.dataset.pane === target);
      });
      document.querySelectorAll(".reading-pane").forEach((pane) => {
        pane.classList.toggle("active", pane.dataset.reading === target);
      });

      if (target === "intradayChart") {
        startIntradayLive(ticker, charts, state, colors, baseOptions, baseScales, labels);
        return;
      }

      stopIntradayLive(state);
      const chart = charts[target];
      if (chart) {
        // Pane was just unhidden — Chart.js needs an explicit resize to
        // pick up the now-visible container's dimensions.
        requestAnimationFrame(() => chart.resize());
      }
    });
  });

  const rangeButtons = document.querySelectorAll(".range-tab-btn");
  rangeButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      rangeButtons.forEach((b) => b.classList.toggle("active", b === btn));
      state.intradayRange = btn.dataset.range;
      startIntradayLive(ticker, charts, state, colors, baseOptions, baseScales, labels);
    });
  });
}

function initChartRefreshButton(ticker, charts, state, colors, baseOptions, baseScales, labels) {
  const btn = document.getElementById("chart-refresh-btn");
  if (!btn) return;

  btn.addEventListener("click", () => {
    if (btn.classList.contains("is-loading")) return;
    btn.classList.add("is-loading");
    const done = () => btn.classList.remove("is-loading");

    const activePane = document.querySelector(".chart-pane.active");
    const target = activePane ? activePane.dataset.pane : "priceChart";

    if (target === "intradayChart") {
      loadIntradayChart(ticker, charts, state, colors, baseOptions, baseScales, labels, done);
    } else {
      loadMainCharts(ticker, charts, colors, baseOptions, baseScales, labels, done);
    }
  });
}

function stopIntradayLive(state) {
  if (state.intradayTimer) {
    clearInterval(state.intradayTimer);
    state.intradayTimer = null;
  }
}

function startIntradayLive(ticker, charts, state, colors, baseOptions, baseScales, labels) {
  stopIntradayLive(state);
  loadIntradayChart(ticker, charts, state, colors, baseOptions, baseScales, labels);
  // Sadece "Günlük" görünümü gerçekten canlı — diğer periyotlar statik
  // geçmiş veri, her 60 saniyede yeniden çekmenin bir anlamı yok.
  if (state.intradayRange === "1d") {
    state.intradayTimer = setInterval(() => {
      loadIntradayChart(ticker, charts, state, colors, baseOptions, baseScales, labels);
    }, 60000);
  }
}

function intradayStatusText(range, d, labels) {
  labels = labels || {};
  const now = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  const template = labels[`intraday${range}`] || "";
  return template.replace("{date}", d.session_date).replace("{time}", now);
}

function loadIntradayChart(ticker, charts, state, colors, baseOptions, baseScales, labels, onDone) {
  labels = labels || {};
  const statusEl = document.getElementById("intraday-status");
  const range = state.intradayRange || "1d";

  fetch(`/hisse/${ticker}/intraday-data?range=${range}`)
    .then((r) => r.json())
    .then((d) => {
      if (d.error) {
        if (statusEl) statusEl.textContent = d.error;
        return;
      }

      if (statusEl) statusEl.textContent = intradayStatusText(range, d, labels);

      const chartData = {
        labels: d.timestamps,
        datasets: [
          { label: labels.price || "Price", data: d.close, borderColor: colors.accent, backgroundColor: "transparent", pointRadius: 0, borderWidth: 2, tension: 0.15 },
        ],
      };

      if (charts.intradayChart) {
        charts.intradayChart.data = chartData;
        charts.intradayChart.update();
      } else {
        charts.intradayChart = new Chart(document.getElementById("intradayChart"), {
          type: "line",
          data: chartData,
          options: { ...baseOptions, scales: baseScales },
        });
      }
      requestAnimationFrame(() => charts.intradayChart.resize());
    })
    .catch(() => {
      if (statusEl) statusEl.textContent = labels.errorGeneric || "Failed to load data.";
    })
    .finally(() => {
      if (onDone) onDone();
    });
}
