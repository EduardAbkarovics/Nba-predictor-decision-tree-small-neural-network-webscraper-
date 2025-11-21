import importlib.util
import sys
from pathlib import Path
import unittest
from unittest.mock import patch, call


class DummyResponse:
    def __init__(self, text: str):
        self.text = text


def load_module_with_patches(responses_map):
    """
    Load the player_stat module from source path while patching httpx.get
    to return predetermined responses based on URL. Returns the loaded module
    and a list of captured httpx.get calls for assertions.
    """
    captured_calls = []

    def fake_get(url, headers=None):
        captured_calls.append((url, headers))
        if url in responses_map:
            return DummyResponse(responses_map[url])
        raise AssertionError(f"Unexpected URL requested: {url}")

    module_path = Path(__file__).resolve().parents[1] / 'datas' / 'playerstats' / 'player_stat.py'
    spec = importlib.util.spec_from_file_location("player_stat_under_test", module_path)
    module = importlib.util.module_from_spec(spec)

    with patch("httpx.get", side_effect=fake_get):
        # Ensure a clean import each time
        if spec and spec.loader:
            spec.loader.exec_module(module)
        else:
            raise RuntimeError("Unable to load module spec")

    return module, captured_calls


class TestPlayerStat(unittest.TestCase):
    def test_extract_alphabet_links_from_commented_html(self):
        # Prepare responses: index page with commented alphabet, one alphabet page with commented tbody
        base_url = "https://www.basketball-reference.com/players/"
        a_page = "https://www.basketball-reference.com/players/a/"
        player_url = "https://www.basketball-reference.com/players/a/adamsst01.html"

        index_html = (
            '<html><body>\n'
            '<!-- <div class="section_content" id="div_alphabet">'
            '<ul class="alphabet"><li><a href="/players/a/">A</a></li></ul>'
            '</div> -->\n'
            '</body></html>'
        )
        a_page_html = (
            '<html><body>\n'
            '<!-- <tbody><tr><th><a href="/players/a/adamsst01.html">Steven Adams</a></th></tr></tbody> -->\n'
            '</body></html>'
        )

        module, calls = load_module_with_patches({
            base_url: index_html,
            a_page: a_page_html,
        })

        # Validate alphabet links are built correctly
        self.assertEqual(module.player_list, [a_page])
        # Validate player links are collected into main_list
        self.assertIn(player_url, module.main_list)

        # Ensure requests were made with headers containing a User-Agent
        self.assertGreaterEqual(len(calls), 2)
        for url, headers in calls:
            self.assertIsInstance(headers, dict)
            self.assertIn("User-Agent", headers)
            self.assertTrue(headers["User-Agent"].startswith("Mozilla/5.0"))

    def test_parse_non_commented_tbody(self):
        base_url = "https://www.basketball-reference.com/players/"
        a_page = "https://www.basketball-reference.com/players/a/"
        player_url = "https://www.basketball-reference.com/players/a/abdulka01.html"

        index_html = (
            '<html><body>\n'
            '<!-- <div class="section_content" id="div_alphabet">'
            '<ul class="alphabet"><li><a href="/players/a/">A</a></li></ul>'
            '</div> -->\n'
            '</body></html>'
        )
        # Non-commented tbody variant
        a_page_html = (
            '<html><body>\n'
            '<tbody><tr><th><a href="/players/a/abdulka01.html">Kareem Abdul-Jabbar</a></th></tr></tbody>\n'
            '</body></html>'
        )

        module, _ = load_module_with_patches({
            base_url: index_html,
            a_page: a_page_html,
        })

        self.assertIn(player_url, module.main_list)

    def test_harmadik_lepes_creates_directory_and_sleeps_per_player(self):
        base_url = "https://www.basketball-reference.com/players/"
        a_page = "https://www.basketball-reference.com/players/a/"
        # Provide two players to verify sleep is called twice
        players = [
            "https://www.basketball-reference.com/players/a/alpha01.html",
            "https://www.basketball-reference.com/players/a/beta02.html",
        ]

        index_html = (
            '<html><body>\n'
            '<!-- <div class="section_content" id="div_alphabet">'
            '<ul class="alphabet"><li><a href="/players/a/">A</a></li></ul>'
            '</div> -->\n'
            '</body></html>'
        )
        a_page_html = (
            '<html><body>\n'
            '<!-- <tbody>'
            '<tr><th><a href="/players/a/alpha01.html">Alpha</a></th></tr>'
            '<tr><th><a href="/players/a/beta02.html">Beta</a></th></tr>'
            '</tbody> -->\n'
            '</body></html>'
        )
        # Player pages content (not parsed by harmadik_lepes, but requested)
        player_html = "<html><body>Player</body></html>"

        responses = {base_url: index_html, a_page: a_page_html}
        for u in players:
            responses[u] = player_html

        module, _ = load_module_with_patches(responses)

        with patch("os.makedirs") as makedirs_mock, patch("time.sleep") as sleep_mock:
            # Instantiate harmadik_lepes to trigger directory creation and delays
            module.harmadik_lepes()

            makedirs_mock.assert_called_once_with("player_data", exist_ok=True)
            # Sleep called once per player in main_list
            self.assertEqual(sleep_mock.call_count, len(module.main_list))

    def test_handles_empty_alphabet_gracefully(self):
        base_url = "https://www.basketball-reference.com/players/"
        # Index page without the commented alphabet section
        index_html = "<html><body><div>No commented alphabet here</div></body></html>"

        module, calls = load_module_with_patches({
            base_url: index_html,
        })

        # No players/alphabet should be discovered
        self.assertEqual(module.player_list, [])
        self.assertEqual(module.main_list, [])
        # Only one request should have been made (the index page)
        self.assertEqual(len(calls), 1)

    def test_all_requests_include_headers(self):
        base_url = "https://www.basketball-reference.com/players/"
        a_page = "https://www.basketball-reference.com/players/a/"
        player_url = "https://www.basketball-reference.com/players/a/adamsst01.html"

        index_html = (
            '<html><body>\n'
            '<!-- <div class="section_content" id="div_alphabet">'
            '<ul class="alphabet"><li><a href="/players/a/">A</a></li></ul>'
            '</div> -->\n'
            '</body></html>'
        )
        a_page_html = (
            '<html><body>\n'
            '<!-- <tbody><tr><th><a href="/players/a/adamsst01.html">Steven Adams</a></th></tr></tbody> -->\n'
            '</body></html>'
        )
        player_html = "<html><body>Player</body></html>"

        module, calls = load_module_with_patches({
            base_url: index_html,
            a_page: a_page_html,
            player_url: player_html,
        })

        # Instantiate harmadik_lepes to produce an additional request per player
        with patch("os.makedirs"):
            with patch("time.sleep"):
                module.harmadik_lepes()

        # Verify each call had headers
        for url, headers in calls:
            self.assertIsNotNone(headers)
            self.assertIn("User-Agent", headers)


if __name__ == "__main__":
    unittest.main(verbosity=2)
