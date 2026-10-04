const navigationItems = [
  ["/", "Возможности"],
  ["/inspect", "Проверка авто"],
  ["/market", "Аналитика рынка"],
  ["/knowledge", "База знаний"],
  ["/settings", "Настройки"],
];

document.querySelectorAll(".topbar nav").forEach((nav) => {
  nav.innerHTML = navigationItems.map(([href, label]) => {
    const active = location.pathname === href;
    return `<a href="${href}"${active ? ' aria-current="page"' : ""}>${label}</a>`;
  }).join("");
});
