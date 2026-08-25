import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "decompile_terranigma.py"
spec = importlib.util.spec_from_file_location("decompile_terranigma", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class RomInputTests(unittest.TestCase):
    def test_rejects_wrong_rom(self):
        with self.assertRaises(ValueError):
            mod._verify_rom(b"not terranigma")

    def test_zip_requires_one_rom(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "bad.zip"
            with zipfile.ZipFile(p, "w") as zf:
                zf.writestr("a.sfc", b"a")
                zf.writestr("b.smc", b"b")
            with self.assertRaises(ValueError):
                mod._open_rom(p)

    def test_zip_reads_single_rom_member(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "one.zip"
            with zipfile.ZipFile(p, "w") as zf:
                zf.writestr("notes.txt", "ignored")
                zf.writestr("Terranigma.sfc", b"rom bytes")
            raw, name = mod._open_rom(p)
            self.assertEqual(raw, b"rom bytes")
            self.assertEqual(name, "Terranigma.sfc")


if __name__ == "__main__":
    unittest.main()
