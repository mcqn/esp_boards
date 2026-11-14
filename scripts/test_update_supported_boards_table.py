import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("update_supported_boards_table.py")
SPEC = importlib.util.spec_from_file_location("update_supported_boards_table", SCRIPT_PATH)
tables = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(tables)


class UpdateSupportedBoardsTableTest(unittest.TestCase):
    HEADER = "| Photo | Board | Chip | Device capabilities |\n| --- | --- | --- | --- |\n"

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        self.readme = self.repo_root / "README.md"

    def tearDown(self):
        self.temp_dir.cleanup()

    def _add_board(self, relative_dir, chip="esp32s3"):
        board_dir = self.repo_root / relative_dir
        board_dir.mkdir(parents=True)
        (board_dir / "board_info.yaml").write_text(
            f"board: {board_dir.name}\nchip: {chip}\n", encoding="utf-8"
        )
        return board_dir

    def _readme(self, table):
        content = "# Vendor\n\n" + tables.BEGIN_MARKER + "\n" + table + tables.END_MARKER + "\n\nKeep this footer.\n"
        self.readme.write_text(content, encoding="utf-8")
        return content

    def test_preserves_manual_header_photos_capabilities_and_removed_board_rows(self):
        self._add_board("existing_board")
        self._add_board("new_board")
        existing = '| <img src="my-photo.png" width="111"> | <a href="product">Product</a><br><code>existing_board</code> | ESP32 | Audio: ES8311<br>Handwritten text |\n'
        removed = '| custom photo | `removed_board` | ESP32-H2 | Manual capabilities |\n'
        before = self._readme(self.HEADER + existing + removed)

        tables.update_readme(self.readme, self.repo_root, "en")

        after = self.readme.read_text(encoding="utf-8")
        inserted = '| <img src="docs/images/example_board.svg" alt="Board photo" width="120"> | `new_board` | ESP32-S3 | |\n'
        self.assertEqual(after, before.replace(tables.END_MARKER, inserted + tables.END_MARKER))
        self.assertEqual(after.count("existing_board"), 1)

    def test_new_row_has_four_columns_placeholder_and_empty_capability(self):
        self._add_board("display/round/new_board", chip="esp32p4")
        self._readme(self.HEADER)
        tables.update_readme(self.readme, self.repo_root, "en")
        row = next(line for line in self.readme.read_text(encoding="utf-8").splitlines() if "`new_board`" in line)
        self.assertEqual(tables._table_cells(row), [
            '<img src="docs/images/example_board.svg" alt="Board photo" width="120">',
            '`new_board`', 'ESP32-P4', '',
        ])

    def test_same_chip_appends_to_existing_group_and_new_chip_gets_separate_group(self):
        self._add_board("existing_board")
        self._add_board("new_s3_board")
        self._add_board("new_p4_board", chip="esp32p4")
        existing = '| photo | `existing_board` | ESP32-S3 | Manual text |\n'
        self._readme("### ESP32-S3\n\n" + self.HEADER + existing + "\n")

        tables.update_readme(self.readme, self.repo_root, "en")

        after = self.readme.read_text(encoding="utf-8")
        s3, p4 = after.split("### ESP32-P4")
        self.assertIn("`new_s3_board`", s3)
        self.assertNotIn("`new_p4_board`", s3)
        self.assertIn("`new_p4_board`", p4)
        self.assertIn(self.HEADER, p4)
        self.assertIn(existing, s3)
        self.assertEqual(after.count("### ESP32-S3"), 1)

    def test_existing_chip_group_in_middle_keeps_following_group_unchanged(self):
        self._add_board("new_s3_board")
        p4_section = "### ESP32-P4\n\n" + self.HEADER + '| photo | `manual_p4` | ESP32-P4 | Manual |\n\n'
        self._readme("### ESP32-S3\n\n" + self.HEADER + '| photo | `manual_s3` | ESP32-S3 | Manual |\n\n' + p4_section)
        tables.update_readme(self.readme, self.repo_root, "en")
        after = self.readme.read_text(encoding="utf-8")
        self.assertIn(p4_section, after)
        self.assertLess(after.index("`new_s3_board`"), after.index("### ESP32-P4"))

    def test_repeated_run_does_not_append_html_or_backtick_board_ids_again(self):
        self._add_board("html_board")
        self._add_board("backtick_board")
        self._add_board("new_board")
        self._readme(self.HEADER + '| photo | <code>html_board</code> | ESP32-S3 | Manual |\n' + '| photo | `backtick_board` | ESP32-S3 | Manual |\n')
        tables.update_readme(self.readme, self.repo_root, "en")
        once = self.readme.read_bytes()
        tables.update_readme(self.readme, self.repo_root, "en")
        self.assertEqual(once, self.readme.read_bytes())
        self.assertEqual(once.count(b"html_board"), 1)
        self.assertEqual(once.count(b"backtick_board"), 1)
        self.assertEqual(once.count(b"new_board"), 1)

    def test_manual_cells_with_escaped_pipes_do_not_duplicate_existing_boards(self):
        self._add_board("existing_board")
        for board_cell in ["<code>existing_board</code>", "`existing_board`", "existing_board"]:
            with self.subTest(board_cell=board_cell):
                before = self._readme(
                    self.HEADER
                    + f'| photo | {board_cell} | ESP32-S3 | I2S \\| I2C |\n'
                )
                tables.update_readme(self.readme, self.repo_root, "en")
                self.assertEqual(self.readme.read_text(encoding="utf-8"), before)

    def test_discovers_three_levels_and_ignores_hidden_or_deeper_directories(self):
        self._add_board("display/round/screen_board")
        self._add_board("a/b/c/too_deep_board")
        self._add_board(".hidden/hidden_board")
        self._readme(self.HEADER)
        tables.update_readme(self.readme, self.repo_root, "en")
        after = self.readme.read_text(encoding="utf-8")
        self.assertIn("`screen_board`", after)
        self.assertNotIn("too_deep_board", after)
        self.assertNotIn("hidden_board", after)

    def test_chinese_new_group_uses_localized_four_column_header(self):
        self._add_board("new_board", chip="esp32c6")
        self._readme("### ESP32-S3\n\n| 板卡图片 | 开发板 | 芯片 | 设备能力 |\n| --- | --- | --- | --- |\n")
        tables.update_readme(self.readme, self.repo_root, "cn")
        after = self.readme.read_text(encoding="utf-8")
        self.assertIn("### ESP32-C6\n\n| 板卡图片 | 开发板 | 芯片 | 设备能力 |", after)
        self.assertIn('alt="板卡图片"', after)
        self.assertIn('| `new_board` | ESP32-C6 | |', after)


if __name__ == "__main__":
    unittest.main()
