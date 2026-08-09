// Keep unversioned and previously shared links on the newest published bundle.
(function () {
  var root = document.documentElement;
  root.style.visibility = "hidden";

  var configUrl = new URL("./assets/config.json", window.location.href);
  configUrl.searchParams.set("_fresh", Date.now().toString());

  fetch(configUrl.toString(), { cache: "no-store" })
    .then(function (response) {
      if (!response.ok) throw new Error("Unable to read bundle version");
      return response.json();
    })
    .then(function (config) {
      var current = String(config.bundleVersion || "").trim();
      if (!current) return;

      var pageUrl = new URL(window.location.href);
      if (pageUrl.searchParams.get("v") !== current) {
        pageUrl.searchParams.set("v", current);
        window.location.replace(pageUrl.toString());
        return;
      }
      root.style.visibility = "";
    })
    .catch(function () {
      // Do not make an offline copy unusable when the network is unavailable.
      root.style.visibility = "";
    });
})();
