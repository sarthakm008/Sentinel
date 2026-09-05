with open('ml/tests/test_graph_features.py', 'r') as f:
    content = f.read()

# test_compute_component_event_growth_no_recent_events
old = '''def test_compute_component_event_growth_no_recent_events():
    """Zero recent events returns 0.0 growth."""
    g = MockGraph({
        "CUS_1": {"DEV_1"},
        "DEV_1": {"CUS_1"},
    })
    t_ref = datetime(2026, 6, 15, 12, 0, 0)
    
    comp_events = {
        "CUS_1": [
            (datetime(2026, 6, 10), "order"),
        ]
    }
    
    growth = compute_component_event_growth(
        g_pit=MockGraph({
            "CUS_1": {"DEV_1"},
            "DEV_1": {"CUS_1"},
        }),
        cid="CUS_1",
        t_ref=t_ref,
        cust_orders={},
        comp_events=comp_events,
    )
    assert growth == 0.0'''

new = '''def test_compute_component_event_growth_no_recent_events():
    """Zero recent events returns 0.0 growth."""
    g = nx.Graph()
    g.add_edges_from([("CUS_1", "DEV_1")])
    t_ref = datetime(2026, 6, 15, 12, 0, 0)
    
    comp_events = {
        "CUS_1": [
            (datetime(2026, 6, 10), "order"),
        ]
    }
    
    growth = compute_component_event_growth(
        g_pit=g,
        cid="CUS_1",
        t_ref=t_ref,
        cust_orders={},
        comp_events=comp_events,
    )
    assert growth == 0.0'''

content = content.replace(old, new)

# test_compute_component_event_growth_with_prior_events
old = '''def test_compute_component_event_growth_with_prior_events():
    """Growth > 0 when recent events > prior events."""
    g = MockGraph({
        "CUS_1": {"DEV_1"},
        "CUS_2": {"DEV_1"},
        "DEV_1": {"CUS_1", "CUS_2"},
    })
    t_ref = datetime(2026, 6, 15, 12, 0, 0)
    
    comp_events = {
        "CUS_1": [
            (datetime(2026, 6, 14, 10, 0, 0), "order"),
            (datetime(2026, 6, 14, 14, 0, 0), "order"),
        ],
        "CUS_2": [
            (datetime(2026, 6, 14, 12, 0, 0), "order"),
        ],
    }
    
    growth = compute_component_event_growth(
        g_pit=MockGraph({
            "CUS_1": {"DEV_1"},
            "CUS_2": {"DEV_1"},
            "DEV_1": {"CUS_1", "CUS_2"},
        }),
        cid="CUS_1",
        t_ref=t_ref,
        cust_orders={},
        comp_events=comp_events,
    )
    assert growth == 3.0'''

new = '''def test_compute_component_event_growth_with_prior_events():
    """Growth > 0 when recent events > prior events."""
    g = nx.Graph()
    g.add_edges_from([("CUS_1", "DEV_1"), ("CUS_2", "DEV_1")])
    t_ref = datetime(2026, 6, 15, 12, 0, 0)
    
    comp_events = {
        "CUS_1": [
            (datetime(2026, 6, 14, 10, 0, 0), "order"),
            (datetime(2026, 6, 14, 14, 0, 0), "order"),
        ],
        "CUS_2": [
            (datetime(2026, 6, 14, 12, 0, 0), "order"),
        ],
    }
    
    growth = compute_component_event_growth(
        g_pit=g,
        cid="CUS_1",
        t_ref=t_ref,
        cust_orders={},
        comp_events=comp_events,
    )
    assert growth == 3.0'''

content = content.replace(old, new)

# test_compute_component_event_growth_pit_cutoff
old = '''def test_compute_component_event_growth_pit_cutoff():
    """Events at or after t_ref must be excluded."""
    g = MockGraph({
        "CUS_1": {"DEV_1"},
        "CUS_2": {"DEV_1"},
        "DEV_1": {"CUS_1", "CUS_2"},
    })
    t_ref = datetime(2026, 6, 15, 12, 0, 0)
    
    comp_events = {
        "CUS_1": [
            (datetime(2026, 6, 14, 10, 0, 0), "order"),
            (datetime(2026, 6, 15, 14, 0, 0), "order"),
        ],
        "CUS_2": [
            (datetime(2026, 6, 14, 12, 0, 0), "order"),
        ],
    }
    
    growth = compute_component_event_growth(
        g_pit=MockGraph({
            "CUS_1": {"DEV_1"},
            "CUS_2": {"DEV_1"},
            "DEV_1": {"CUS_1", "CUS_2"},
        }),
        cid="CUS_1",
        t_ref=t_ref,
        cust_orders={},
        comp_events=comp_events,
    )
    assert growth == 2.0'''

new = '''def test_compute_component_event_growth_pit_cutoff():
    """Events at or after t_ref must be excluded."""
    g = nx.Graph()
    g.add_edges_from([("CUS_1", "DEV_1"), ("CUS_2", "DEV_1")])
    t_ref = datetime(2026, 6, 15, 12, 0, 0)
    
    comp_events = {
        "CUS_1": [
            (datetime(2026, 6, 14, 10, 0, 0), "order"),
            (datetime(2026, 6, 15, 14, 0, 0), "order"),
        ],
        "CUS_2": [
            (datetime(2026, 6, 14, 12, 0, 0), "order"),
        ],
    }
    
    growth = compute_component_event_growth(
        g_pit=g,
        cid="CUS_1",
        t_ref=t_ref,
        cust_orders={},
        comp_events=comp_events,
    )
    assert growth == 2.0'''

content = content.replace(old, new)

# test_compute_component_new_neighbors_no_new
old = '''def test_compute_component_new_neighbors_no_new():
    """No new neighbors when same neighbors in both windows."""
    g = MockGraph({
        "CUS_1": {"DEV_1"},
        "CUS_2": {"DEV_1"},
        "DEV_1": {"CUS_1", "CUS_2"},
    })
    t_ref = datetime(2026, 6, 15, 12, 0, 0)
    
    comp_events = {
        "CUS_1": [
            (datetime(2026, 6, 14, 10, 0, 0), "order"),
        ],
        "CUS_2": [
            (datetime(2026, 6, 13, 10, 0, 0), "order"),
            (datetime(2026, 6, 14, 12, 0, 0), "order"),
        ],
    }
    
    new = compute_component_new_neighbors(
        g_pit=MockGraph({
            "CUS_1": {"DEV_1"},
            "CUS_2": {"DEV_1"},
            "DEV_1": {"CUS_1", "CUS_2"},
        }),
        cid="CUS_1",
        t_ref=t_ref,
        comp_events=comp_events,
    )
    assert new == 0.0'''

new = '''def test_compute_component_new_neighbors_no_new():
    """No new neighbors when same neighbors in both windows."""
    g = nx.Graph()
    g.add_edges_from([("CUS_1", "DEV_1"), ("CUS_2", "DEV_1")])
    t_ref = datetime(2026, 6, 15, 12, 0, 0)
    
    comp_events = {
        "CUS_1": [
            (datetime(2026, 6, 14, 10, 0, 0), "order"),
        ],
        "CUS_2": [
            (datetime(2026, 6, 13, 10, 0, 0), "order"),
            (datetime(2026, 6, 14, 12, 0, 0), "order"),
        ],
    }
    
    new = compute_component_new_neighbors(
        g_pit=g,
        cid="CUS_1",
        t_ref=t_ref,
        comp_events=comp_events,
    )
    assert new == 0.0'''

content = content.replace(old, new)

# test_compute_component_new_neighbors_with_new
old = '''def test_compute_component_new_neighbors_with_new():
    """Counts neighbors appearing only in recent window."""
    g = MockGraph({
        "CUS_1": {"DEV_1"},
        "CUS_2": {"DEV_1"},
        "CUS_3": {"DEV_1"},
        "DEV_1": {"CUS_1", "CUS_2", "CUS_3"},
    })
    t_ref = datetime(2026, 6, 15, 12, 0, 0)
    
    comp_events = {
        "CUS_1": [
            (datetime(2026, 6, 14, 10, 0, 0), "order"),
        ],
        "CUS_2": [
            (datetime(2026, 6, 13, 10, 0, 0), "order"),
        ],
        "CUS_3": [
            (datetime(2026, 6, 14, 12, 0, 0), "order"),
        ],
    }
    
    new = compute_component_new_neighbors(
        g_pit=MockGraph({
            "CUS_1": {"DEV_1"},
            "CUS_2": {"DEV_1"},
            "CUS_3": {"DEV_1"},
            "DEV_1": {"CUS_1", "CUS_2", "CUS_3"},
        }),
        cid="CUS_1",
        t_ref=t_ref,
        comp_events=comp_events,
    )
    assert new == 1.0'''

new = '''def test_compute_component_new_neighbors_with_new():
    """Counts neighbors appearing only in recent window."""
    g = nx.Graph()
    g.add_edges_from([("CUS_1", "DEV_1"), ("CUS_2", "DEV_1"), ("CUS_3", "DEV_1")])
    t_ref = datetime(2026, 6, 15, 12, 0, 0)
    
    comp_events = {
        "CUS_1": [
            (datetime(2026, 6, 14, 10, 0, 0), "order"),
        ],
        "CUS_2": [
            (datetime(2026, 6, 13, 10, 0, 0), "order"),
        ],
        "CUS_3": [
            (datetime(2026, 6, 14, 12, 0, 0), "order"),
        ],
    }
    
    new = compute_component_new_neighbors(
        g_pit=g,
        cid="CUS_1",
        t_ref=t_ref,
        comp_events=comp_events,
    )
    assert new == 1.0'''

content = content.replace(old, new)

# test_compute_component_new_neighbors_pit_cutoff
old = '''def test_compute_component_new_neighbors_pit_cutoff():
    """Events at or after t_ref excluded."""
    g = MockGraph({
        "CUS_1": {"DEV_1"},
        "CUS_2": {"DEV_1"},
        "DEV_1": {"CUS_1", "CUS_2"},
    })
    t_ref = datetime(2026, 6, 15, 12, 0, 0)
    
    comp_events = {
        "CUS_1": [],
        "CUS_2": [
            (datetime(2026, 6, 14, 10, 0, 0), "order"),
            (datetime(2026, 6, 15, 14, 0, 0), "order"),
        ],
    }
    
    new = compute_component_new_neighbors(
        g_pit=MockGraph({
            "CUS_1": {"DEV_1"},
            "CUS_2": {"DEV_1"},
            "DEV_1": {"CUS_1", "CUS_2"},
        }),
        cid="CUS_1",
        t_ref=t_ref,
        comp_events=comp_events,
    )
    assert new == 0.0'''

new = '''def test_compute_component_new_neighbors_pit_cutoff():
    """Events at or after t_ref excluded."""
    g = nx.Graph()
    g.add_edges_from([("CUS_1", "DEV_1"), ("CUS_2", "DEV_1")])
    t_ref = datetime(2026, 6, 15, 12, 0, 0)
    
    comp_events = {
        "CUS_1": [],
        "CUS_2": [
            (datetime(2026, 6, 14, 10, 0, 0), "order"),
            (datetime(2026, 6, 15, 14, 0, 0), "order"),
        ],
    }
    
    new = compute_component_new_neighbors(
        g_pit=g,
        cid="CUS_1",
        t_ref=t_ref,
        comp_events=comp_events,
    )
    assert new == 0.0'''

content = content.replace(old, new)

with open('ml/tests/test_graph_features.py', 'w') as f:
    f.write(content)

print('Done')