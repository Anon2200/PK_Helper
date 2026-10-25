"""Автотесты файловых инструментов. Запуск:  python -m unittest discover tests"""
import os, sys, tempfile, unittest, zipfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import tools

class FileTools(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        tools.init({"backup_dir": os.path.join(self.d, "_backup")})

    def p(self, *a):
        return os.path.join(self.d, *a)

    def test_create_folder_and_file(self):
        self.assertIn("создана", tools.create_folder(self.p("Отчёты")))
        self.assertTrue(os.path.isdir(self.p("Отчёты")))
        tools.create_file(self.p("Отчёты", "a.txt"), "привет")
        self.assertEqual(tools.read_file(self.p("Отчёты", "a.txt")), "привет")
        self.assertIn("Ошибка", tools.create_file(self.p("Отчёты", "a.txt"), "x"))

    def test_rename_by_date(self):
        for n in ("1.jpg", "2.jpg", "3.txt"):
            open(self.p(n), "w").close()
        self.assertIn("2", tools.rename_by_date(self.d, "jpg"))
        self.assertTrue(os.path.exists(self.p("3.txt")))
        self.assertFalse(os.path.exists(self.p("1.jpg")))

    def test_copy_move(self):
        tools.create_file(self.p("a.txt"), "1")
        os.mkdir(self.p("dst"))
        tools.copy_path(self.p("a.txt"), self.p("dst"))
        self.assertTrue(os.path.exists(self.p("dst", "a.txt")))
        tools.move_path(self.p("a.txt"), self.p("b.txt"))
        self.assertTrue(os.path.exists(self.p("b.txt")))
        self.assertFalse(os.path.exists(self.p("a.txt")))

    def test_search(self):
        tools.create_file(self.p("report2024.pdf"), "x")
        tools.create_file(self.p("note.txt"), "секретное слово")
        self.assertIn("report2024.pdf", tools.search_files(self.d, extension="pdf"))
        self.assertIn("note.txt", tools.search_files(self.d, content="СЕКРЕТНОЕ"))
        self.assertIn("Ничего", tools.search_files(self.d, name="нет-такого"))

    def test_zip_roundtrip(self):
        os.mkdir(self.p("Проект"))
        tools.create_file(self.p("Проект", "f.txt"), "z")
        a = self.p("p.zip")
        tools.zip_path(self.p("Проект"), a)
        self.assertTrue(zipfile.is_zipfile(a))
        tools.extract_archive(a, self.p("out"))
        self.assertTrue(os.path.exists(self.p("out", "Проект", "f.txt")))

    def test_delete_backup(self):
        try:
            import send2trash  # noqa
        except ImportError:
            self.skipTest("send2trash не установлен")
        tools.create_file(self.p("x.txt"), "1")
        self.assertIn("Удалено", tools.delete_path(self.p("x.txt")))
        self.assertFalse(os.path.exists(self.p("x.txt")))

    def test_danger_policy(self):
        self.assertIsNotNone(tools.REGISTRY["delete_path"]["danger"])
        self.assertIsNone(tools.REGISTRY["create_folder"]["danger"])

if __name__ == "__main__":
    unittest.main()
