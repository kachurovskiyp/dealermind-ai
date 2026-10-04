from pathlib import Path
import yaml

CATALOG_PATH = Path(__file__).parents[1] / "catalog" / "poland_budget_v1.yaml"

def poland_budget_catalog() -> dict[str, object]:
    with CATALOG_PATH.open(encoding="utf-8") as source:
        return yaml.safe_load(source)

def catalog_entry(make: str, model: str) -> dict[str, object] | None:
    for group in poland_budget_catalog()["groups"]:
        if group["make"].casefold() == make.casefold() and any(item.casefold() == model.casefold() for item in group["models"]):
            return {"make": group["make"], "model": model, "tier": group["tier"]}
    return None
