import importlib.util, tempfile, pathlib, unittest
spec = importlib.util.spec_from_file_location("audit", str(pathlib.Path(__file__).resolve().parents[1] / "tools" / "audit_queue.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
class Checks(unittest.TestCase):
    def q(self, **kw):
        return {"Request ID":"TEST-001", "Max USD":"0", "Permission Scope":"READ_ONLY", "Owner Approval":"TEST_ONLY", **kw}
    def test_duplicates(self):
        r=m.audit([self.q(),self.q()],[])
        self.assertTrue(any(x["kind"]=="duplicate_request_id" for x in r["findings"]))
    def test_never_infers_execution(self):
        r=m.audit([self.q()],[{"Event ID":"E1","Request ID":"TEST-001","Evidence URL":"https://example.invalid/evidence","Event Type":"COMPLETED"}])
        self.assertFalse(r["execution_verified"])
    def test_invalid_budgets(self):
        for amount in ["NaN","Infinity","-1",""]:
            self.assertTrue(any(x["kind"]=="invalid_budget" for x in m.audit([self.q(**{"Max USD":amount})],[])["findings"]))
    def test_orphan_log(self):
        self.assertTrue(any(x["kind"]=="log_request_not_in_supplied_queue" for x in m.audit([], [{"Event ID":"E1","Request ID":"unknown"}])["findings"]))
    def test_headers(self):
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/"q.csv"; p.write_text("Wrong\nvalue\n")
            with self.assertRaises(ValueError): m.read_csv(p,m.QUEUE_HEADERS)
unittest.main()
