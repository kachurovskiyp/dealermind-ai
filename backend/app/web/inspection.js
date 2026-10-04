const $ = (selector) => document.querySelector(selector);
const esc = (value) => { const element = document.createElement("div"); element.textContent = value ?? "—"; return element.innerHTML; };
const price = (value) => value == null ? "Нет данных" : `${Number(value).toLocaleString("pl-PL")} PLN`;
let catalog = [];

function options(select, items, placeholder) {
  select.innerHTML = `<option value="">${placeholder}</option>` + items.map((item) => `<option value="${esc(item)}">${esc(item)}</option>`).join("");
}

async function loadConfigurations() {
  const make = $("#make").value, model = $("#model").value, select = $("#configuration");
  select.disabled = true;
  options(select, [], "Загружаем конфигурации…");
  try {
    const response = await fetch(`/api/v1/market-intelligence/poland/configurations?make=${encodeURIComponent(make)}&model=${encodeURIComponent(model)}`);
    const configurations = await response.json();
    if (!response.ok) throw new Error();
    options(select, configurations.map((item) => item.configuration), configurations.length ? "Выберите конфигурацию" : "Нет собранных конфигураций");
    select.disabled = !configurations.length;
  } catch (_) {
    options(select, [], "Не удалось загрузить конфигурации");
  }
}

function render(result) {
  const valuation = result.market_valuation;
  const liquidity = result.liquidity || [];
  const notes = result.knowledge_notes || [];
  $("#inspection-result").innerHTML = `<article class="inspect-card"><p class="eyebrow">${esc(result.catalog_label || "Вне текущего фокуса")}</p><h2>${esc(result.make)} ${esc(result.model)}</h2><p>${esc(result.configuration)}</p><div class="inspect-facts"><div><span>Регистрации</span><strong>${result.registrations_30_days ?? "Нет снимка"}</strong></div><div><span>Период</span><strong>${esc(result.registrations_period || "—")}</strong></div><div><span>Выборка рынка</span><strong>${valuation?.sample_size ?? "Нет данных"}</strong></div></div><section><strong>Рыночный ориентир</strong><p>${valuation ? `${price(valuation.median_price)} · уверенность ${esc(valuation.confidence)}` : "Для этой конфигурации пока недостаточно сравнений."}</p>${valuation ? `<small>${esc(valuation.basis)}</small>` : ""}</section><section><strong>Ликвидность конфигураций</strong><ul>${liquidity.length ? liquidity.map((item) => `<li>${esc(item.configuration)}: медиана ${price(item.median_price)}, объявлений ${item.sample_size}, ${esc(item.confidence)}</li>`).join("") : "<li>Наблюдений пока нет.</li>"}</ul></section><section><strong>База знаний</strong><ul>${notes.length ? notes.map((item) => `<li>${esc(item)}</li>`).join("") : "<li>Профиль модели пока не создан.</li>"}</ul></section></article>`;
}

$("#make").onchange = () => {
  const group = catalog.find((item) => item.make === $("#make").value);
  const model = $("#model");
  options(model, group?.models || [], "Выберите модель");
  model.disabled = !group;
  $("#configuration").disabled = true;
  options($("#configuration"), [], "Сначала выберите модель");
};
$("#model").onchange = loadConfigurations;
$("#inspection-form").onsubmit = async (event) => {
  event.preventDefault();
  const button = event.currentTarget.querySelector("button"), root = $("#inspection-result");
  button.disabled = true; button.textContent = "Проверяем…"; root.textContent = "";
  try {
    const params = new URLSearchParams({make: $("#make").value, model: $("#model").value, configuration: $("#configuration").value});
    const response = await fetch(`/api/v1/inspection/review?${params}`), result = await response.json();
    if (!response.ok) throw new Error(result.detail || `Ошибка ${response.status}`);
    render(result);
  } catch (error) { root.innerHTML = `<p class="error">${esc(error.message)}</p>`; }
  finally { button.disabled = false; button.textContent = "Проверить"; }
};

fetch("/api/v1/vehicle-catalog/poland-budget").then((response) => response.json()).then((data) => { catalog = data.groups || []; options($("#make"), catalog.map((item) => item.make), "Выберите марку"); }).catch(() => { $("#inspection-result").innerHTML = '<p class="error">Не удалось загрузить каталог.</p>'; });
