from pydantic import BaseModel, Field


class PowertrainDeepDiveRead(BaseModel):
    outputs_hp: list[int] = Field(default_factory=list)
    market_role: str
    suitable_for: str
    inspection_checks: list[str] = Field(default_factory=list)
    risk_signals: list[str] = Field(default_factory=list)
    evidence_status: str
    decision_rule: str
    reliability_score: int | None = None
    repair_exposure_score: int | None = None
    evidence_confidence: str = "low"


class KnownIssueRead(BaseModel):
    component: str
    applicability: str
    classification: str
    severity: str
    symptoms: list[str] = Field(default_factory=list)
    inspection: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    note: str


class GearboxKnowledgeRead(BaseModel):
    name: str
    variants: list[str] = Field(default_factory=list)
    identification_rule: str
    suitable_for: str
    inspection_checks: list[str] = Field(default_factory=list)
    risk_signals: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    evidence_status: str = "partial"


class DealerConfigurationRead(BaseModel):
    id: str
    label: str
    engine_patterns: list[str] = Field(default_factory=list)
    gearbox_patterns: list[str] = Field(default_factory=list)
    power_hp: list[int] = Field(default_factory=list)
    verdict: str
    confidence: str
    dealer_rationale: list[str] = Field(default_factory=list)
    required_checks: list[str] = Field(default_factory=list)
    reject_if: list[str] = Field(default_factory=list)


class DealerMarketSignalRead(BaseModel):
    sample_size: int
    active_listings: int
    median_days_observed: int | None
    price_reduction_rate: float
    disappearance_signal_rate: float
    confidence: str


class DealerAssessmentRead(BaseModel):
    profile_slug: str | None = None
    configuration_id: str | None = None
    configuration_label: str | None = None
    verdict: str
    verdict_label: str
    confidence: str
    reasons: list[str] = Field(default_factory=list)
    required_checks: list[str] = Field(default_factory=list)
    reject_if: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    market_signal: DealerMarketSignalRead | None = None


class PowertrainKnowledgeRead(BaseModel):
    name: str
    fuel: str
    transmissions: list[str] = Field(default_factory=list)
    drivetrains: list[str] = Field(default_factory=list)
    verdict: str = "unreviewed"
    performance: bool = False
    evidence_refs: list[str] = Field(default_factory=list)
    review_note: str | None = None
    deep_dive: PowertrainDeepDiveRead | None = None


class FactoryLineRead(BaseModel):
    name: str
    positioning: str
    equipment_notes: list[str] = Field(default_factory=list)


class EquipmentGroupRead(BaseModel):
    name: str
    values: list[str]
    note: str | None = None


class KnowledgeSourceRead(BaseModel):
    id: str
    title: str
    url: str
    source_type: str
    trust_level: str
    checked_at: str | None = None
    scope: str
    limitation: str


class KnowledgeImageRead(BaseModel):
    url: str
    alt: str
    caption: str
    author: str
    source_url: str
    license: str
    license_url: str


class KnowledgeProfileRead(BaseModel):
    slug: str
    make: str
    model: str
    generation: str
    market_code: str
    production_years: str
    version: str
    verification_status: str
    profile_origin: str = "reviewed_profile"
    catalog_tier: str | None = None
    summary: str
    image: KnowledgeImageRead | None = None
    body_types: list[str]
    powertrains: list[PowertrainKnowledgeRead]
    gearbox_profiles: list[GearboxKnowledgeRead] = Field(default_factory=list)
    known_issues: list[KnownIssueRead] = Field(default_factory=list)
    dealer_configurations: list[DealerConfigurationRead] = Field(default_factory=list)
    factory_lines: list[FactoryLineRead]
    equipment_groups: list[EquipmentGroupRead]
    decision_notes: list[str]
    sources: list[KnowledgeSourceRead]


class KnowledgeProfileSummaryRead(BaseModel):
    slug: str
    make: str
    model: str
    generation: str
    production_years: str
    verification_status: str
    version: str
    profile_origin: str = "reviewed_profile"
    catalog_tier: str | None = None
