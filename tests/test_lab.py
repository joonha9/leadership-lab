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


if __name__ == "__main__":
    unittest.main()
