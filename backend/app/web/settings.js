const form = document.querySelector("#logistics-form");
const message = document.querySelector("#logistics-message");

async function request(path, options = {}) {
  const response = await fetch(`/api/v1${path}`, {
    headers: {"Content-Type": "application/json"},
    ...options,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Ошибка ${response.status}`);
  }
  return response.json();
}

function fill(values) {
  for (const [key, value] of Object.entries(values)) {
    if (form.elements[key] && value != null) form.elements[key].value = value;
  }
}

request("/logistics/profile").then(fill).catch(() => {});
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = form.querySelector("button");
  const values = Object.fromEntries(new FormData(form));
  for (const key of ["fixed_cost", "cost_per_km", "trip_multiplier", "cross_border_surcharge"]) values[key] = Number(values[key]);
  values.origin_country_code = values.origin_country_code.toUpperCase();
  message.textContent = "";
  button.disabled = true;
  button.textContent = "Сохраняем…";
  try {
    fill(await request("/logistics/profile", {method: "PUT", body: JSON.stringify(values)}));
    message.className = "settings-success";
    message.textContent = "Профиль логистики сохранён.";
  } catch (error) {
    message.className = "error";
    message.textContent = error.message;
  } finally {
    button.disabled = false;
    button.textContent = "Сохранить профиль";
  }
});
