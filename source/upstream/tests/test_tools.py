"""Integration tests for the graph editing, VEX and geometry tools.

Run tests/headless_host.py in hython first (see its docstring), then:
    uv run python tests/test_tools.py [port]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import sys
import houdini_mcp_server as bridge

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 19878
CONTAINER = "/obj/MCP_TIER1_TEST"
conn = bridge.HoudiniConnection(host="127.0.0.1", port=PORT)

passed = []
def send(cmd, params=None, expect_error=False):
    resp = conn.send_command(cmd, params or {})
    status = resp.get("status")
    if expect_error:
        assert status == "error", f"{cmd}: expected error, got {resp}"
        return resp
    assert status == "success", f"{cmd} failed: {resp}"
    return resp["result"]

def ok(name):
    passed.append(name)
    print(f"  PASS  {name}")

# -- setup: isolated container ------------------------------------------------
conn.send_command("delete_node", {"path": CONTAINER})  # clean slate, either outcome ok
container = send("create_node", {"node_type": "geo", "parent_path": "/obj",
                                 "name": "MCP_TIER1_TEST"})
grid = send("create_node", {"node_type": "grid", "parent_path": CONTAINER,
                            "name": "grid1"})
ok("setup: container + grid created")

# -- set_parameters: scalar, tuple, menu token, did-you-mean -------------------
r = send("set_parameters", {"path": grid["path"], "parameters": {
    "size": [4, 6], "rows": 12, "cols": 7, "orient": "zx", "rws": 1}})
assert len(r["set"]) == 4, r
assert len(r["failed"]) == 1 and "rows" in r["failed"][0]["error"], r["failed"]
prev_rows = [e for e in r["set"] if e["name"] == "rows"][0]
assert prev_rows["value"] == 12, prev_rows
ok("set_parameters: scalar+tuple+menu-token set, did-you-mean on bad name")

# menu by LABEL should also resolve
r = send("set_parameters", {"path": grid["path"], "parameters": {"orient": "XY Plane"}})
assert not r["failed"], r
ok("set_parameters: menu label resolved")

# -- get_parameter_schema ------------------------------------------------------
r = send("get_parameter_schema", {"path": grid["path"], "pattern": "*size*"})
entry = [e for e in r["parameters"] if e["name"] == "size"][0]
assert entry["size"] == 2 and entry["value"] == [4.0, 6.0], entry
r = send("get_parameter_schema", {"path": grid["path"], "pattern": "orient"})
assert any("menu" in e for e in r["parameters"]), r
ok("get_parameter_schema: tuple size, values, menu options, pattern filter")

# -- create_wrangle (valid VEX, wired input) -----------------------------------
w = send("create_wrangle", {"parent_path": CONTAINER, "name": "color_wrangle",
                            "vex_code": "@Cd = set(1.0, 0.0, 0.0);",
                            "run_over": "points", "input_node": grid["path"]})
assert w["validation"]["cooked"] is True, w
assert w["run_over"], w
ok("create_wrangle: created, wired, VEX compiled, cooked clean")

# -- set_wrangle_code: broken VEX must surface compile errors ------------------
r = send("set_wrangle_code", {"path": w["path"], "vex_code": "@Cd = set(1, 0, 0"})
assert r["validation"]["cooked"] is False and r["validation"]["errors"], r
ok("set_wrangle_code: VEX compile error surfaced in validation")

# -- find_error_nodes must spot the broken wrangle -----------------------------
r = send("find_error_nodes", {"root_path": CONTAINER})
assert r["error_node_count"] >= 1, r
assert any(n["path"] == w["path"] for n in r["nodes"]), r
ok("find_error_nodes: broken node located with error messages")

# fix it again, sweep must come back clean
r = send("set_wrangle_code", {"path": w["path"],
                              "vex_code": "@Cd = set(0.0, 1.0, 0.0);"})
assert r["validation"]["cooked"] is True, r
r = send("find_error_nodes", {"root_path": CONTAINER})
assert r["error_node_count"] == 0, r
ok("find_error_nodes: clean after fix")

# -- connect / disconnect ------------------------------------------------------
xform = send("create_node", {"node_type": "xform", "parent_path": CONTAINER,
                             "name": "xform1"})
r = send("connect_nodes", {"from_path": w["path"], "to_path": xform["path"]})
assert r["to"] == xform["path"], r
r = send("disconnect_input", {"path": xform["path"], "input_index": 0})
assert r["was_connected_to"] == w["path"], r
send("connect_nodes", {"from_path": w["path"], "to_path": xform["path"]})
# cross-network connect must be rejected
send("connect_nodes", {"from_path": grid["path"], "to_path": CONTAINER},
     expect_error=True)
ok("connect_nodes / disconnect_input: wire, report, rewire, reject cross-network")

# -- flags, layout, cook -------------------------------------------------------
r = send("set_node_flags", {"path": xform["path"], "display": True, "render": True})
assert r["applied"].get("display") is True, r
r = send("layout_children", {"path": CONTAINER})
assert r["children_laid_out"] >= 3, r
r = send("cook_node", {"path": xform["path"]})
assert r["cooked"] is True and r["cook_time_ms"] >= 0, r
ok("set_node_flags / layout_children / cook_node")

# -- geometry introspection ----------------------------------------------------
r = send("get_geometry_info", {"path": xform["path"]})
assert r["point_count"] == 12 * 7, r["point_count"]
point_attrs = [a["name"] for a in r["attributes"]["point"]]
assert "P" in point_attrs and "Cd" in point_attrs, point_attrs
assert len(r["bounding_box"]["min"]) == 3, r
# container path must resolve to the display SOP
r2 = send("get_geometry_info", {"path": CONTAINER})
assert r2["point_count"] == r["point_count"], (r2["node"], r2["point_count"])
ok("get_geometry_info: counts, attribs, bbox, container resolution")

r = send("get_geometry_data", {"path": xform["path"], "element": "points",
                               "attributes": ["P", "Cd"], "start": 0, "limit": 10})
assert r["total"] == 84 and r["count"] == 10, r
assert r["data"][0]["Cd"] == [0.0, 1.0, 0.0], r["data"][0]
assert len(r["data"][0]["P"]) == 3, r["data"][0]
r = send("get_geometry_data", {"path": xform["path"], "element": "points",
                               "start": 80, "limit": 10})
assert r["count"] == 4, r  # pagination tail
r = send("get_geometry_data", {"path": xform["path"], "element": "primitives",
                               "limit": 5})
assert r["count"] == 5 and "type" in r["data"][0], r
send("get_geometry_data", {"path": xform["path"], "attributes": ["nope"]},
     expect_error=True)
ok("get_geometry_data: values, pagination, prims, unknown-attrib error")

# -- bridge-layer helper (_houdini_call through real MCP tool functions) --------
bridge._houdini_port = PORT
bridge._houdini_connection = None
r = bridge.set_parameters(None, grid["path"], {"rows": 5})
assert r["status"] == "success" and not r["result"]["failed"], r
r = bridge.get_geometry_info(None, CONTAINER)
assert r["status"] == "success" and r["result"]["point_count"] == 5 * 7, r
r = bridge.delete_node(None, CONTAINER + "/nonexistent")
assert r["status"] == "error" and "not found" in r["message"].lower(), r
ok("bridge layer: tool functions + _houdini_call envelope (success and error)")

# -- newest-wins: the bridge connection above must have evicted ours -------------
resp = conn.send_command("ping")
assert resp.get("status") == "error", f"expected evicted connection, got {resp}"
ok("newest-wins accept: stale connection evicted by newer client")

# -- cleanup (via the surviving bridge connection) --------------------------------
r = bridge.delete_node(None, CONTAINER)
assert r["status"] == "success" and r["result"]["deleted"] == CONTAINER, r
ok("cleanup: test container deleted")

conn.disconnect()
print(f"\nALL {len(passed)} TEST GROUPS PASSED")
