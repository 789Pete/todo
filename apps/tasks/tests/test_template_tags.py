from apps.tasks.templatetags.task_tags import badge_text_color


class TestBadgeTextColor:
    """Tests for the badge_text_color template filter."""

    # All 8 palette colors have luminance > 0.179 → dark text (#000000)
    def test_yellow_returns_dark_text(self):
        assert badge_text_color("#F7DC6F") == "#000000"

    def test_mint_returns_dark_text(self):
        assert badge_text_color("#98D8C8") == "#000000"

    def test_sky_blue_returns_dark_text(self):
        assert badge_text_color("#85C1E2") == "#000000"

    def test_orange_returns_dark_text(self):
        assert badge_text_color("#FFA07A") == "#000000"

    def test_red_returns_dark_text(self):
        assert badge_text_color("#FF6B6B") == "#000000"

    def test_teal_returns_dark_text(self):
        assert badge_text_color("#4ECDC4") == "#000000"

    def test_blue_returns_dark_text(self):
        assert badge_text_color("#45B7D1") == "#000000"

    def test_purple_returns_dark_text(self):
        assert badge_text_color("#BB8FCE") == "#000000"

    # Dark colors need white text (luminance <= 0.179)
    def test_pure_black_returns_white_text(self):
        assert badge_text_color("#000000") == "#ffffff"

    def test_dark_navy_returns_white_text(self):
        # #1a237e dark navy: very low luminance
        assert badge_text_color("#1a237e") == "#ffffff"

    def test_dark_green_returns_white_text(self):
        # #1B5E20 dark green: very low luminance
        assert badge_text_color("#1B5E20") == "#ffffff"

    # Bright colors need dark text
    def test_pure_white_returns_dark_text(self):
        assert badge_text_color("#FFFFFF") == "#000000"

    # Edge cases
    def test_without_hash_prefix(self):
        # lstrip('#') handles missing prefix
        assert badge_text_color("F7DC6F") == "#000000"

    def test_invalid_color_returns_white(self):
        # Short/invalid hex falls back to white
        assert badge_text_color("#FFF") == "#ffffff"
