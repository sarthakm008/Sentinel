"""Group-aware dataset partitioning using connected entity components."""

import json
from typing import Dict, List, Set, Tuple
import networkx as nx
import numpy as np

from ml.data_generation.entities import Customer


class GroupAwareSplitter:
    """Partitions dataset into Train/Val/Test by connected components with zero entity leakage."""

    def __init__(
        self,
        rng: np.random.Generator,
        train_ratio: float = 0.60,
        val_ratio: float = 0.20,
        test_ratio: float = 0.20,
    ):
        self.rng = rng
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio

    def partition(
        self,
        customers: List[Customer],
        cust_bindings: Dict[str, Dict],
        abuse_rings: List[Dict],
    ) -> Dict[str, Dict[str, List[str]]]:
        # 1. Build bipartite graph of customer <-> (device, address, payment)
        g = nx.Graph()

        for c in customers:
            cid = c.customer_id
            g.add_node(cid, node_type="customer", archetype=c.archetype, ring_id=c.ring_id)
            bindings = cust_bindings[cid]

            for did in bindings["devices"]:
                g.add_node(did, node_type="device")
                g.add_edge(cid, did)

            for aid in bindings["addresses"]:
                g.add_node(aid, node_type="address")
                g.add_edge(cid, aid)

            for pid in bindings["payments"]:
                g.add_node(pid, node_type="payment")
                g.add_edge(cid, pid)

        # 2. Extract connected components
        components = list(nx.connected_components(g))
        
        # 3. Categorize components by abuse ring type vs legitimate
        type_f_components = []
        other_abuse_components = []
        legit_components = []

        for comp in components:
            comp_custs = [n for n in comp if n.startswith("CUS_")]
            comp_archetypes = {cust_bindings[cid].get("archetype", "") for cid in comp_custs}
            comp_rings = {cust_bindings[cid].get("ring_id") for cid in comp_custs if cust_bindings[cid].get("ring_id")}

            if "type_f_structural_shift" in comp_archetypes:
                type_f_components.append(comp)
            elif len(comp_rings) > 0:
                other_abuse_components.append(comp)
            else:
                legit_components.append(comp)

        # Shuffle components deterministically
        self.rng.shuffle(other_abuse_components)
        self.rng.shuffle(legit_components)

        # 4. Allocate components to splits
        train_comps, val_comps, test_comps = [], [], []

        # All Type F rings go strictly to Test
        test_comps.extend(type_f_components)

        # Split other abuse components (60 / 20 / 20)
        n_other_abuse = len(other_abuse_components)
        n_train_abuse = int(round(n_other_abuse * self.train_ratio))
        n_val_abuse = int(round(n_other_abuse * self.val_ratio))

        train_comps.extend(other_abuse_components[:n_train_abuse])
        val_comps.extend(other_abuse_components[n_train_abuse:n_train_abuse + n_val_abuse])
        test_comps.extend(other_abuse_components[n_train_abuse + n_val_abuse:])

        # Split legitimate components (60 / 20 / 20)
        n_legit = len(legit_components)
        n_train_legit = int(round(n_legit * self.train_ratio))
        n_val_legit = int(round(n_legit * self.val_ratio))

        train_comps.extend(legit_components[:n_train_legit])
        val_comps.extend(legit_components[n_train_legit:n_train_legit + n_val_legit])
        test_comps.extend(legit_components[n_train_legit + n_val_legit:])

        # 5. Extract entity sets per split
        splits = {"train": {}, "validation": {}, "test": {}}
        for split_name, comp_list in [("train", train_comps), ("validation", val_comps), ("test", test_comps)]:
            split_custs = set()
            split_devs = set()
            split_addrs = set()
            split_pms = set()

            for comp in comp_list:
                for node in comp:
                    if node.startswith("CUS_"):
                        split_custs.add(node)
                    elif node.startswith("DEV_"):
                        split_devs.add(node)
                    elif node.startswith("ADDR_"):
                        split_addrs.add(node)
                    elif node.startswith("PM_"):
                        split_pms.add(node)

            splits[split_name] = {
                "customers": sorted(list(split_custs)),
                "devices": sorted(list(split_devs)),
                "addresses": sorted(list(split_addrs)),
                "payment_tokens": sorted(list(split_pms)),
                "component_count": len(comp_list),
            }

        return splits
