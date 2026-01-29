#!/usr/bin/env python3
"""
Tests for generate_pinyin_dict.py

Focuses on kanji+hiragana mixed word support.
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from generate_pinyin_dict import (
    is_kanji,
    is_hiragana,
    generate_pinyin_for_word,
    HIRAGANA_TO_ROMAJI,
)


class TestIsHiragana(unittest.TestCase):
    """Tests for is_hiragana() function."""

    def test_basic_hiragana(self):
        """Basic hiragana characters should return True."""
        self.assertTrue(is_hiragana('あ'))
        self.assertTrue(is_hiragana('い'))
        self.assertTrue(is_hiragana('う'))
        self.assertTrue(is_hiragana('ん'))

    def test_voiced_hiragana(self):
        """Voiced hiragana (dakuten) should return True."""
        self.assertTrue(is_hiragana('が'))
        self.assertTrue(is_hiragana('ざ'))
        self.assertTrue(is_hiragana('だ'))
        self.assertTrue(is_hiragana('ば'))
        self.assertTrue(is_hiragana('ぱ'))

    def test_small_hiragana(self):
        """Small hiragana should return True."""
        self.assertTrue(is_hiragana('ゃ'))
        self.assertTrue(is_hiragana('ゅ'))
        self.assertTrue(is_hiragana('ょ'))
        self.assertTrue(is_hiragana('っ'))

    def test_kanji_returns_false(self):
        """Kanji should return False."""
        self.assertFalse(is_hiragana('厚'))
        self.assertFalse(is_hiragana('日'))
        self.assertFalse(is_hiragana('本'))

    def test_katakana_returns_false(self):
        """Katakana should return False."""
        self.assertFalse(is_hiragana('ア'))
        self.assertFalse(is_hiragana('イ'))
        self.assertFalse(is_hiragana('ン'))

    def test_ascii_returns_false(self):
        """ASCII characters should return False."""
        self.assertFalse(is_hiragana('a'))
        self.assertFalse(is_hiragana('A'))
        self.assertFalse(is_hiragana('1'))


class TestHiraganaToRomajiMapping(unittest.TestCase):
    """Tests for HIRAGANA_TO_ROMAJI mapping completeness."""

    def test_basic_vowels(self):
        """Basic vowel hiragana should be mapped."""
        self.assertEqual(HIRAGANA_TO_ROMAJI['あ'], 'a')
        self.assertEqual(HIRAGANA_TO_ROMAJI['い'], 'i')
        self.assertEqual(HIRAGANA_TO_ROMAJI['う'], 'u')
        self.assertEqual(HIRAGANA_TO_ROMAJI['え'], 'e')
        self.assertEqual(HIRAGANA_TO_ROMAJI['お'], 'o')

    def test_ka_row(self):
        """Ka-row hiragana should be mapped."""
        self.assertEqual(HIRAGANA_TO_ROMAJI['か'], 'ka')
        self.assertEqual(HIRAGANA_TO_ROMAJI['き'], 'ki')
        self.assertEqual(HIRAGANA_TO_ROMAJI['く'], 'ku')
        self.assertEqual(HIRAGANA_TO_ROMAJI['け'], 'ke')
        self.assertEqual(HIRAGANA_TO_ROMAJI['こ'], 'ko')

    def test_special_consonants(self):
        """Special consonant mappings should be correct."""
        self.assertEqual(HIRAGANA_TO_ROMAJI['し'], 'shi')
        self.assertEqual(HIRAGANA_TO_ROMAJI['ち'], 'chi')
        self.assertEqual(HIRAGANA_TO_ROMAJI['つ'], 'tsu')
        self.assertEqual(HIRAGANA_TO_ROMAJI['ふ'], 'fu')

    def test_n_character(self):
        """N character should be mapped."""
        self.assertEqual(HIRAGANA_TO_ROMAJI['ん'], 'n')

    def test_voiced_consonants(self):
        """Voiced consonants (dakuten) should be mapped."""
        self.assertEqual(HIRAGANA_TO_ROMAJI['が'], 'ga')
        self.assertEqual(HIRAGANA_TO_ROMAJI['じ'], 'ji')
        self.assertEqual(HIRAGANA_TO_ROMAJI['ず'], 'zu')
        self.assertEqual(HIRAGANA_TO_ROMAJI['ぢ'], 'di')
        self.assertEqual(HIRAGANA_TO_ROMAJI['づ'], 'du')

    def test_p_sounds(self):
        """P-sounds (handakuten) should be mapped."""
        self.assertEqual(HIRAGANA_TO_ROMAJI['ぱ'], 'pa')
        self.assertEqual(HIRAGANA_TO_ROMAJI['ぴ'], 'pi')
        self.assertEqual(HIRAGANA_TO_ROMAJI['ぷ'], 'pu')
        self.assertEqual(HIRAGANA_TO_ROMAJI['ぺ'], 'pe')
        self.assertEqual(HIRAGANA_TO_ROMAJI['ぽ'], 'po')

    def test_small_kana(self):
        """Small kana should be mapped."""
        self.assertEqual(HIRAGANA_TO_ROMAJI['ゃ'], 'ya')
        self.assertEqual(HIRAGANA_TO_ROMAJI['ゅ'], 'yu')
        self.assertEqual(HIRAGANA_TO_ROMAJI['ょ'], 'yo')
        self.assertEqual(HIRAGANA_TO_ROMAJI['っ'], 'tt')

    def test_small_vowels(self):
        """Small vowels should be mapped."""
        self.assertEqual(HIRAGANA_TO_ROMAJI['ぁ'], 'a')
        self.assertEqual(HIRAGANA_TO_ROMAJI['ぃ'], 'i')
        self.assertEqual(HIRAGANA_TO_ROMAJI['ぅ'], 'u')
        self.assertEqual(HIRAGANA_TO_ROMAJI['ぇ'], 'e')
        self.assertEqual(HIRAGANA_TO_ROMAJI['ぉ'], 'o')


class TestGeneratePinyinForWord(unittest.TestCase):
    """Tests for generate_pinyin_for_word() with mixed kanji+hiragana."""

    def setUp(self):
        """Sample character to pinyin mapping for tests."""
        self.char_to_pinyin = {
            '厚': 'hou',
            '手': 'shou',
            '分': 'fen',
            '日': 'ri',
            '本': 'ben',
            '語': 'yu',
            '食': 'shi',
            '飲': 'yin',
            '物': 'wu',
            '大': 'da',
            '小': 'xiao',
            '新': 'xin',
            '古': 'gu',
            '高': 'gao',
            '安': 'an',
            '揚': 'yang',
        }

    def test_pure_kanji_word(self):
        """Pure kanji words should work as before."""
        self.assertEqual(generate_pinyin_for_word('日本', self.char_to_pinyin), 'riben')
        self.assertEqual(generate_pinyin_for_word('日本語', self.char_to_pinyin), 'ribenyu')

    def test_kanji_with_trailing_hiragana(self):
        """Kanji + trailing hiragana (i-adjectives, verbs) should work."""
        # 厚い (atsui/thick) -> houi
        self.assertEqual(generate_pinyin_for_word('厚い', self.char_to_pinyin), 'houi')
        # 高い (takai/tall) -> gaoi
        self.assertEqual(generate_pinyin_for_word('高い', self.char_to_pinyin), 'gaoi')
        # 安い (yasui/cheap) -> ani
        self.assertEqual(generate_pinyin_for_word('安い', self.char_to_pinyin), 'ani')

    def test_kanji_with_middle_hiragana(self):
        """Kanji + middle hiragana + kanji should work."""
        # 食べ物 (tabemono/food) -> shibewu
        self.assertEqual(generate_pinyin_for_word('食べ物', self.char_to_pinyin), 'shibewu')
        # 飲み物 (nomimono/drink) -> yinmiwu
        self.assertEqual(generate_pinyin_for_word('飲み物', self.char_to_pinyin), 'yinmiwu')

    def test_kanji_with_suffix_hiragana(self):
        """Kanji + suffix hiragana should work."""
        # 厚め (atsume/thick-ish) -> houme
        self.assertEqual(generate_pinyin_for_word('厚め', self.char_to_pinyin), 'houme')
        # 厚さ (atsusa/thickness) -> housa
        self.assertEqual(generate_pinyin_for_word('厚さ', self.char_to_pinyin), 'housa')
        # 厚み (atsumi/thickness) -> houmi
        self.assertEqual(generate_pinyin_for_word('厚み', self.char_to_pinyin), 'houmi')

    def test_compound_with_hiragana(self):
        """Compound kanji words with hiragana should work."""
        # 手厚い (teatsui/hospitable) -> shouhoui
        self.assertEqual(generate_pinyin_for_word('手厚い', self.char_to_pinyin), 'shouhoui')
        # 分厚い (buatsui/bulky) -> fenhoui
        self.assertEqual(generate_pinyin_for_word('分厚い', self.char_to_pinyin), 'fenhoui')

    def test_long_hiragana_suffix(self):
        """Words with long hiragana suffixes should work."""
        # 厚かましい (atsukamashii/impudent) -> houkamashii
        self.assertEqual(generate_pinyin_for_word('厚かましい', self.char_to_pinyin), 'houkamashii')

    def test_hiragana_with_small_kana(self):
        """Words with small kana (っ, ゃ, etc.) should work."""
        # Test with っ: 厚っ -> houtt
        self.assertEqual(generate_pinyin_for_word('厚っ', self.char_to_pinyin), 'houtt')

    def test_pure_hiragana_returns_none(self):
        """Pure hiragana words should return None (must have kanji)."""
        self.assertIsNone(generate_pinyin_for_word('あいうえお', self.char_to_pinyin))
        self.assertIsNone(generate_pinyin_for_word('これ', self.char_to_pinyin))
        self.assertIsNone(generate_pinyin_for_word('する', self.char_to_pinyin))

    def test_katakana_returns_none(self):
        """Words with katakana should return None."""
        self.assertIsNone(generate_pinyin_for_word('カタカナ', self.char_to_pinyin))
        self.assertIsNone(generate_pinyin_for_word('厚イ', self.char_to_pinyin))  # Mixed with katakana

    def test_kanji_without_pinyin_returns_none(self):
        """Words with unmapped kanji should return None."""
        # 猫 is not in char_to_pinyin
        self.assertIsNone(generate_pinyin_for_word('猫', self.char_to_pinyin))
        self.assertIsNone(generate_pinyin_for_word('猫い', self.char_to_pinyin))

    def test_punctuation_returns_none(self):
        """Words with punctuation should return None."""
        self.assertIsNone(generate_pinyin_for_word('日本。', self.char_to_pinyin))
        self.assertIsNone(generate_pinyin_for_word('厚い！', self.char_to_pinyin))

    def test_empty_string_returns_none(self):
        """Empty string should return None."""
        self.assertIsNone(generate_pinyin_for_word('', self.char_to_pinyin))

    def test_voiced_hiragana_in_word(self):
        """Voiced hiragana (dakuten) in words should work."""
        # 厚げ -> houge (げ=ge)
        result = generate_pinyin_for_word('厚げ', self.char_to_pinyin)
        self.assertEqual(result, 'houge')

    def test_all_hiragana_rows(self):
        """Test various hiragana from different rows."""
        # Using 厚 as base kanji
        test_cases = [
            ('厚あ', 'houa'),
            ('厚か', 'houka'),
            ('厚さ', 'housa'),
            ('厚た', 'houta'),
            ('厚な', 'houna'),
            ('厚は', 'houha'),
            ('厚ま', 'houma'),
            ('厚や', 'houya'),
            ('厚ら', 'houra'),
            ('厚わ', 'houwa'),
            ('厚ん', 'houn'),
        ]
        for word, expected in test_cases:
            with self.subTest(word=word):
                self.assertEqual(generate_pinyin_for_word(word, self.char_to_pinyin), expected)


class TestIsKanji(unittest.TestCase):
    """Tests for is_kanji() function."""

    def test_common_kanji(self):
        """Common kanji should return True."""
        self.assertTrue(is_kanji('日'))
        self.assertTrue(is_kanji('本'))
        self.assertTrue(is_kanji('語'))
        self.assertTrue(is_kanji('厚'))

    def test_hiragana_returns_false(self):
        """Hiragana should return False."""
        self.assertFalse(is_kanji('あ'))
        self.assertFalse(is_kanji('い'))

    def test_katakana_returns_false(self):
        """Katakana should return False."""
        self.assertFalse(is_kanji('ア'))
        self.assertFalse(is_kanji('イ'))

    def test_ascii_returns_false(self):
        """ASCII should return False."""
        self.assertFalse(is_kanji('a'))
        self.assertFalse(is_kanji('1'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
