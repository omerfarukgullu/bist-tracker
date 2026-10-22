(function () {
  var STORAGE_KEY = "theme";
  var root = document.documentElement;
  var btn = document.getElementById("theme-toggle");
  if (!btn) return;

  function systemPrefersDark() {
    if (!window.matchMedia) return true;
    return !window.matchMedia("(prefers-color-scheme: light)").matches;
  }

  function resolvedTheme() {
    var explicit = root.getAttribute("data-theme");
    if (explicit === "light" || explicit === "dark") return explicit;
    return systemPrefersDark() ? "dark" : "light";
  }

  function updateIcon() {
    var theme = resolvedTheme();
    btn.classList.toggle("is-dark", theme === "dark");
    btn.classList.toggle("is-light", theme === "light");
  }

  btn.addEventListener("click", function () {
    var next = resolvedTheme() === "dark" ? "light" : "dark";
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch (e) {}
    // Grafikler (Chart.js) sayfa yüklenirken hesaplanan renkleri kullanıyor;
    // en güvenilir yol yeni temayla sayfayı yeniden yüklemek.
    location.reload();
  });

  updateIcon();
})();
