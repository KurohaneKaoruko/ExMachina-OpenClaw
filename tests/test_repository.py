import unittest

from exmachina.repository import parse_repository_reference


class RepositoryParserTests(unittest.TestCase):
    def test_parse_https_url(self) -> None:
        repo = parse_repository_reference("https://code.example.com/example/exmachina")
        self.assertEqual(repo.owner, "example")
        self.assertEqual(repo.name, "exmachina")
        self.assertEqual(repo.url, "https://code.example.com/example/exmachina")

    def test_parse_tree_url(self) -> None:
        repo = parse_repository_reference("https://code.example.com/example/exmachina/tree/main/templates")
        self.assertEqual(repo.branch, "main")
        self.assertEqual(repo.subpath, "templates")


if __name__ == "__main__":
    unittest.main()
