const profilesRoot = document.querySelector("#profile-list");
const knowledgeContent = document.querySelector("#knowledge-content");
let profileGroups = null;
let renderingGroups = false;
const hasDeepLink = new URLSearchParams(location.search).has("make") || new URLSearchParams(location.search).has("model");
let modelChosen = hasDeepLink;

const escapeGroupHtml = (value) => {
  const element = document.createElement("span");
  element.textContent = value || "";
  return element.innerHTML;
};

function renderGroups() {
  if (!profileGroups || renderingGroups) return;
  renderingGroups = true;
  const grouped = new Map();
  for (const profile of profileGroups) {
    const group = grouped.get(profile.make) || [];
    group.push(profile);
    grouped.set(profile.make, group);
  }
  profilesRoot.innerHTML = [...grouped.entries()].sort(([a], [b]) => a.localeCompare(b, "pl")).map(([make, profiles]) => `
    <details class="knowledge-make-group">
      <summary>${escapeGroupHtml(make)}<span>${profiles.length}</span></summary>
      <div>${profiles.map((profile) => `<button data-profile="${escapeGroupHtml(profile.slug)}"><strong>${escapeGroupHtml(profile.model)}</strong><small>${escapeGroupHtml(profile.generation)} · ${escapeGroupHtml(profile.production_years)}</small></button>`).join("")}</div>
    </details>`).join("");
  renderingGroups = false;
}

function showWelcome() {
  if (modelChosen || hasDeepLink) return;
  document.querySelector("#profile-select").value = "";
  knowledgeContent.innerHTML = `<section class="knowledge-welcome"><p class="eyebrow">Vehicle Knowledge Base</p><h2>Выберите марку и модель<br>слева</h2><p>Здесь появятся заводские конфигурации, заметки по двигателям и коробкам, известные риски и рыночные сигналы для выбранной модели.</p><ul><li>Сначала раскройте нужную марку.</li><li>Затем выберите модель из каталога фокуса.</li><li>Проверенные данные всегда отделены от заготовок.</li></ul></section>`;
}

async function prepareKnowledgeGroups() {
  const response = await fetch("/api/v1/knowledge/profiles", {cache: "no-store"});
  if (!response.ok) return;
  profileGroups = await response.json();
  renderGroups();
  if (!hasDeepLink) {
    setTimeout(showWelcome, 0);
    setTimeout(showWelcome, 250);
  }
  new MutationObserver(() => {
    if (!renderingGroups && !profilesRoot.querySelector(".knowledge-make-group")) renderGroups();
  }).observe(profilesRoot, {childList: true});
}

profilesRoot.addEventListener("click", () => { modelChosen = true; }, true);
prepareKnowledgeGroups().catch(() => {});
