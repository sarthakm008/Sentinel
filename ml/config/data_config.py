"""Simulation and Data Generation Configuration for Sentinel."""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class DataConfig:
    seed: int = 42
    simulation_days: int = 180
    
    # Scale targets
    n_merchants: int = 12
    n_customers_target: int = 50000
    n_orders_target_min: int = 120000
    n_orders_target_max: int = 180000
    n_refunds_target_min: int = 15000
    n_refunds_target_max: int = 25000
    n_abuse_rings: int = 200
    
    # Split proportions
    train_ratio: float = 0.60
    val_ratio: float = 0.20
    test_ratio: float = 0.20
    
    # Legitimate Archetype Shares (sum to 1.0)
    legit_proportions: Dict[str, float] = field(default_factory=lambda: {
        "independent": 0.64,
        "family": 0.12,
        "hostel": 0.08,
        "office": 0.08,
        "heavy_returner": 0.03,
        "gift_buyer": 0.03,
        "sale_buyer": 0.02,
    })
    
    # Abuse Ring Type Allocations (sum to 1.0)
    abuse_type_proportions: Dict[str, float] = field(default_factory=lambda: {
        "type_a_dense": 0.20,
        "type_b_partial": 0.20,
        "type_c_sparse": 0.20,
        "type_d_temporal": 0.15,
        "type_e_mixed": 0.10,
        "type_f_structural_shift": 0.15,
    })
    
    # Product categories and merchant baseline refund rates
    categories: List[str] = field(default_factory=lambda: [
        "electronics", "apparel", "footwear", "home_kitchen", "beauty", "books"
    ])
    
    # Typical refund rates by category
    category_refund_rates: Dict[str, float] = field(default_factory=lambda: {
        "electronics": 0.08,
        "apparel": 0.22,
        "footwear": 0.18,
        "home_kitchen": 0.10,
        "beauty": 0.05,
        "books": 0.03,
    })
    
    # Refund reasons
    refund_reasons: List[str] = field(default_factory=lambda: [
        "wrong_size", "defective_item", "not_as_described", 
        "arrived_late", "damaged_in_transit", "changed_mind"
    ])

    # Shared refund delay distribution (lognormal mixture, identical for legitimate and abuse)
    # Component format: (weight, lognormal_mean, lognormal_sigma, min_days, max_days)
    refund_delay_mixture: List[tuple] = field(default_factory=lambda: [
        (0.50, 1.1, 0.45, 1.0, 10.0),    # standard logistics: median ~3.5d
        (0.35, 1.8, 0.50, 3.0, 21.0),    # extended processing: median ~6.5d
        (0.15, 2.5, 0.60, 7.0, 45.0),    # dispute/resolution: median ~12d
    ])

    # Shared account creation time distribution (uniform, identical for legitimate and abuse)
    # Days relative to simulation start (negative = before start)
    account_age_min_days_before_start: int = -365
    account_age_max_days_after_start: int = 144  # 0.8 * simulation_days
