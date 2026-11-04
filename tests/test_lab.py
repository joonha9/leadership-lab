import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from leadershiplab import frames as fr  # noqa: E402
from leadershiplab import stats  # noqa: E402
from leadershiplab.grading import draw_metrics, idea_set  # noqa: E402


class TestFrames(unittest.TestCase):
    def test_all_frames_load(self):
        for c in fr.CONDITIONS:
            f = fr.load_frame(c)
            self.assertTrue(f["opening"] and f["closing"])

    def test_frames_pass_rules(self):
        from leadershiplab import vl
        self.assertEqual(fr.check_frames(vl.FEATURES, vl.AGGREGATORS, vl.GROUPS), [])

    def test_only_frame_differs(self):
        brief = "TASK BRIEF TEXT"
        a, b = fr.build_prompt("coercive", brief, "/p"), fr.build_prompt("coaching", brief, "/p")
        for c, p in (("coercive", a), ("coaching", b)):
            f = fr.load_frame(c)
            p = p.replace(f["opening"], "").replace(f["closing"], "")
            self.assertIn(brief, p)
        strip = lambda c, p: p.replace(fr.load_frame(c)["opening"], "").replace(fr.load_frame(c)["closing"], "")
        self.assertEqual(strip("coercive", a), strip("coaching", b))

    def test_goleman_groups(self):
        self.assertEqual(set(fr.POSITIVE), {"authoritative", "affiliative", "democratic", "coaching"})
        self.assertEqual(set(fr.NEGATIVE), {"coercive", "pacesetting"})


class TestStats(unittest.TestCase):
    def test_holm(self):
        adj = stats.holm({"a": 0.01, "b": 0.04, "c": 0.03})
        self.assertAlmostEqual(adj["a"], 0.03)
        self.assertAlmostEqual(adj["c"], 0.06)
        self.assertAlmostEqual(adj["b"], 0.06)

    def test_perm_detects_shift(self):
        self.assertLess(stats.perm_diff([1.0] * 10, [0.0] * 10, n_perm=2000)["p"], 0.01)
        self.assertGreater(stats.perm_diff([0, 1] * 5, [1, 0] * 5, n_perm=2000)["p"], 0.5)

    def test_contrast_weights_groups_equally(self):
        v = {"a": [1.0] * 2, "b": [1.0] * 20, "c": [0.0] * 5}
        self.assertAlmostEqual(stats.perm_contrast(v, ["a", "b"], ["c"], n_perm=200)["contrast"], 1.0)


class TestMetrics(unittest.TestCase):
    def test_invalid_slots_score_one(self):
        props = [{"status": "invalid"}] * 6
        m = draw_metrics(props)
        self.assertEqual(m["itt_rel_validate"], 1.0)
        self.assertEqual(m["valid_rate"], 0.0)

    def test_idea_set(self):
        spec = {"rank": {"roic": 1}, "filters": [{"same": "industry_l3"}, {"band": {"var": "log_sales", "width": 1}}],
                "fallback": [[{"same": "industry_l2"}]]}
        self.assertEqual(idea_set(spec), {"roic", "industry_l3", "log_sales", "industry_l2"})


class TestSituations(unittest.TestCase):
    def ok(self, m, a, b):
        return {"recipe": {"multiple": m, "filters": [{"same": "industry_l3"}], "rank": {a: 1, b: 1}, "k": 8,
                           "agg": "median", "min_peers": 5, "fallback": [[{"same": "industry_l2"}], []]}}

    def test_compliant_execution_reply(self):
        from leadershiplab.situations import execution_violations
        props = [self.ok("EV/EBITDA", "roic", "log_sales"), self.ok("EV/EBITDA", "roic", "net_margin"),
                 self.ok("EV/EBITDA", "roe", "log_sales"), self.ok("EV/Sales", "roic", "log_sales"),
                 self.ok("EV/Sales", "gross_margin", "log_sales"), self.ok("EV/Sales", "roic", "net_margin")]
        self.assertEqual(execution_violations(props), [[]] * 6)

    def test_each_constraint_is_caught(self):
        from leadershiplab.situations import execution_violations
        base = self.ok("EV/EBITDA", "roic", "log_sales")
        bad = {"C2": {"filters": []}, "C3": {"rank": {"roic": 2, "log_sales": 1}}, "C4": {"k": 20},
               "C5": {"agg": "mean"}, "C6": {"min_peers": 3}, "C7": {"fallback": [[]]}}
        for code, change in bad.items():
            p = {"recipe": {**base["recipe"], **change}}
            self.assertTrue(any(v.startswith(code) for v in execution_violations([p])[0]), code)
        four = [self.ok("EV/EBITDA", "roic", f) for f in ("log_sales", "roe", "net_margin", "gross_margin")]
        self.assertTrue(execution_violations(four)[3][0].startswith("C1"))
        twice = [self.ok("EV/Sales", "roic", "log_sales")] * 2
        self.assertTrue(any(v.startswith("C8") for v in execution_violations(twice)[1]))

    def test_did_and_interaction(self):
        did = stats.perm_did([0.0] * 8, [1.0] * 8, [1.0] * 8, [1.0] * 8, n_perm=500)
        self.assertAlmostEqual(did["did"], -1.0)
        self.assertLess(did["p"], 0.01)
        import numpy as np
        rng = np.random.default_rng(0)
        a = np.repeat(["s1", "s2"], 40)
        b = np.tile(np.repeat(["x", "y"], 20), 2)
        y = rng.normal(0, 0.1, 80) + ((a == "s1") & (b == "x")) * 1.0
        self.assertLess(stats.perm_interaction(y, a, b, n_perm=300)["p"], 0.01)
        y0 = rng.normal(0, 0.1, 80) + (a == "s1") * 1.0 + (b == "x") * 1.0
        self.assertGreater(stats.perm_interaction(y0, a, b, n_perm=300)["p"], 0.01)


if __name__ == "__main__":
    unittest.main()
