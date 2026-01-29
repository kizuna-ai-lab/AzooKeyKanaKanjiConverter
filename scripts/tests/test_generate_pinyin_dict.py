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
    lookup_phrase,
    to_simplified,
    HIRAGANA_TO_ROMAJI,
    TRAD_TO_SIMP,
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
        """Sample character and phrase to pinyin mappings for tests."""
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
            '築': 'zhu',
            '地': 'de',  # Note: default pronunciation is 'de', but '地' in '築地' should be 'di'
            '劇': 'ju',
            '場': 'chang',
            '東': 'dong',
            '京': 'jing',
            '学': 'xue',
            '银': 'yin',
            '行': 'xing',  # Note: default is 'xing', but in '银行' should be 'hang'
            '职': 'zhi',
            '员': 'yuan',
        }
        # Phrase-level pinyin for correct multi-pronunciation handling
        self.phrase_to_pinyin = {
            '日本': 'riben',
            '日本語': 'ribenyu',
            '築地': 'zhudi',  # 地 -> di (not de)
            '小劇場': 'xiaojuchang',
            '東京': 'dongjing',
            '東京大学': 'dongjingdaxue',
            '银行': 'yinhang',  # 行 -> hang (not xing)
        }
        self.max_phrase_len = 4  # Max length of phrases in test data

    def test_pure_kanji_word(self):
        """Pure kanji words should work with phrase lookup."""
        self.assertEqual(
            generate_pinyin_for_word('日本', self.phrase_to_pinyin, self.char_to_pinyin, self.max_phrase_len),
            'riben'
        )
        self.assertEqual(
            generate_pinyin_for_word('日本語', self.phrase_to_pinyin, self.char_to_pinyin, self.max_phrase_len),
            'ribenyu'
        )

    def test_kanji_with_trailing_hiragana(self):
        """Kanji + trailing hiragana (i-adjectives, verbs) should work."""
        # 厚い (atsui/thick) -> houi
        self.assertEqual(
            generate_pinyin_for_word('厚い', self.phrase_to_pinyin, self.char_to_pinyin, self.max_phrase_len),
            'houi'
        )
        # 高い (takai/tall) -> gaoi
        self.assertEqual(
            generate_pinyin_for_word('高い', self.phrase_to_pinyin, self.char_to_pinyin, self.max_phrase_len),
            'gaoi'
        )
        # 安い (yasui/cheap) -> ani
        self.assertEqual(
            generate_pinyin_for_word('安い', self.phrase_to_pinyin, self.char_to_pinyin, self.max_phrase_len),
            'ani'
        )

    def test_kanji_with_middle_hiragana(self):
        """Kanji + middle hiragana + kanji should work."""
        # 食べ物 (tabemono/food) -> shibewu
        self.assertEqual(
            generate_pinyin_for_word('食べ物', self.phrase_to_pinyin, self.char_to_pinyin, self.max_phrase_len),
            'shibewu'
        )
        # 飲み物 (nomimono/drink) -> yinmiwu
        self.assertEqual(
            generate_pinyin_for_word('飲み物', self.phrase_to_pinyin, self.char_to_pinyin, self.max_phrase_len),
            'yinmiwu'
        )

    def test_kanji_with_suffix_hiragana(self):
        """Kanji + suffix hiragana should work."""
        # 厚め (atsume/thick-ish) -> houme
        self.assertEqual(
            generate_pinyin_for_word('厚め', self.phrase_to_pinyin, self.char_to_pinyin, self.max_phrase_len),
            'houme'
        )
        # 厚さ (atsusa/thickness) -> housa
        self.assertEqual(
            generate_pinyin_for_word('厚さ', self.phrase_to_pinyin, self.char_to_pinyin, self.max_phrase_len),
            'housa'
        )
        # 厚み (atsumi/thickness) -> houmi
        self.assertEqual(
            generate_pinyin_for_word('厚み', self.phrase_to_pinyin, self.char_to_pinyin, self.max_phrase_len),
            'houmi'
        )

    def test_compound_with_hiragana(self):
        """Compound kanji words with hiragana should work."""
        # 手厚い (teatsui/hospitable) -> shouhoui
        self.assertEqual(
            generate_pinyin_for_word('手厚い', self.phrase_to_pinyin, self.char_to_pinyin, self.max_phrase_len),
            'shouhoui'
        )
        # 分厚い (buatsui/bulky) -> fenhoui
        self.assertEqual(
            generate_pinyin_for_word('分厚い', self.phrase_to_pinyin, self.char_to_pinyin, self.max_phrase_len),
            'fenhoui'
        )

    def test_long_hiragana_suffix(self):
        """Words with long hiragana suffixes should work."""
        # 厚かましい (atsukamashii/impudent) -> houkamashii
        self.assertEqual(
            generate_pinyin_for_word('厚かましい', self.phrase_to_pinyin, self.char_to_pinyin, self.max_phrase_len),
            'houkamashii'
        )

    def test_hiragana_with_small_kana(self):
        """Words with small kana (っ, ゃ, etc.) should work."""
        # Test with っ: 厚っ -> houtt
        self.assertEqual(
            generate_pinyin_for_word('厚っ', self.phrase_to_pinyin, self.char_to_pinyin, self.max_phrase_len),
            'houtt'
        )

    def test_pure_hiragana_returns_none(self):
        """Pure hiragana words should return None (must have kanji)."""
        self.assertIsNone(
            generate_pinyin_for_word('あいうえお', self.phrase_to_pinyin, self.char_to_pinyin, self.max_phrase_len)
        )
        self.assertIsNone(
            generate_pinyin_for_word('これ', self.phrase_to_pinyin, self.char_to_pinyin, self.max_phrase_len)
        )
        self.assertIsNone(
            generate_pinyin_for_word('する', self.phrase_to_pinyin, self.char_to_pinyin, self.max_phrase_len)
        )

    def test_katakana_returns_none(self):
        """Words with katakana should return None."""
        self.assertIsNone(
            generate_pinyin_for_word('カタカナ', self.phrase_to_pinyin, self.char_to_pinyin, self.max_phrase_len)
        )
        self.assertIsNone(
            generate_pinyin_for_word('厚イ', self.phrase_to_pinyin, self.char_to_pinyin, self.max_phrase_len)
        )

    def test_kanji_without_pinyin_returns_none(self):
        """Words with unmapped kanji should return None."""
        # 猫 is not in char_to_pinyin
        self.assertIsNone(
            generate_pinyin_for_word('猫', self.phrase_to_pinyin, self.char_to_pinyin, self.max_phrase_len)
        )
        self.assertIsNone(
            generate_pinyin_for_word('猫い', self.phrase_to_pinyin, self.char_to_pinyin, self.max_phrase_len)
        )

    def test_punctuation_returns_none(self):
        """Words with punctuation should return None."""
        self.assertIsNone(
            generate_pinyin_for_word('日本。', self.phrase_to_pinyin, self.char_to_pinyin, self.max_phrase_len)
        )
        self.assertIsNone(
            generate_pinyin_for_word('厚い！', self.phrase_to_pinyin, self.char_to_pinyin, self.max_phrase_len)
        )

    def test_empty_string_returns_none(self):
        """Empty string should return None."""
        self.assertIsNone(
            generate_pinyin_for_word('', self.phrase_to_pinyin, self.char_to_pinyin, self.max_phrase_len)
        )

    def test_voiced_hiragana_in_word(self):
        """Voiced hiragana (dakuten) in words should work."""
        # 厚げ -> houge (げ=ge)
        result = generate_pinyin_for_word('厚げ', self.phrase_to_pinyin, self.char_to_pinyin, self.max_phrase_len)
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
                self.assertEqual(
                    generate_pinyin_for_word(word, self.phrase_to_pinyin, self.char_to_pinyin, self.max_phrase_len),
                    expected
                )


class TestSubwordMatching(unittest.TestCase):
    """Tests for maximum forward matching (subword matching) algorithm."""

    def setUp(self):
        """Sample data for subword matching tests."""
        self.char_to_pinyin = {
            '築': 'zhu',
            '地': 'de',  # Default pronunciation
            '小': 'xiao',
            '劇': 'ju',
            '場': 'chang',
            '東': 'dong',
            '京': 'jing',
            '大': 'da',
            '学': 'xue',
            '银': 'yin',
            '行': 'xing',  # Default pronunciation
            '职': 'zhi',
            '员': 'yuan',
        }
        self.phrase_to_pinyin = {
            '築地': 'zhudi',  # 地 -> di (correct for this context)
            '小劇場': 'xiaojuchang',
            '東京': 'dongjing',
            '東京大学': 'dongjingdaxue',
            '银行': 'yinhang',  # 行 -> hang (correct for bank)
        }
        self.max_phrase_len = 4

    def test_subword_matching_basic(self):
        """Test basic subword matching: 築地小劇場 -> zhudi + xiaojuchang."""
        # Without subword matching: zhudexiaojuchang (wrong: 地=de)
        # With subword matching: zhudixiaojuchang (correct: 築地=zhudi)
        result = generate_pinyin_for_word(
            '築地小劇場',
            self.phrase_to_pinyin,
            self.char_to_pinyin,
            self.max_phrase_len
        )
        self.assertEqual(result, 'zhudixiaojuchang')

    def test_subword_matching_bank(self):
        """Test subword matching for 银行职员 -> yinhang + zhiyuan."""
        # Without subword matching: yinxingzhiyuan (wrong: 行=xing)
        # With subword matching: yinhangzhiyuan (correct: 银行=yinhang)
        result = generate_pinyin_for_word(
            '银行职员',
            self.phrase_to_pinyin,
            self.char_to_pinyin,
            self.max_phrase_len
        )
        self.assertEqual(result, 'yinhangzhiyuan')

    def test_full_phrase_match_takes_priority(self):
        """Test that full phrase match is preferred over subword matching."""
        # 東京大学 should match as full phrase, not 東京 + 大 + 学
        result = generate_pinyin_for_word(
            '東京大学',
            self.phrase_to_pinyin,
            self.char_to_pinyin,
            self.max_phrase_len
        )
        self.assertEqual(result, 'dongjingdaxue')

    def test_longest_subword_preferred(self):
        """Test that longest matching subword is preferred."""
        # Add a shorter phrase that overlaps
        phrase_to_pinyin = self.phrase_to_pinyin.copy()
        phrase_to_pinyin['東'] = 'dong'  # Single char (should not be preferred)
        phrase_to_pinyin['東京'] = 'dongjing'  # Longer phrase (should be preferred)

        result = generate_pinyin_for_word(
            '東京大学',
            phrase_to_pinyin,
            self.char_to_pinyin,
            self.max_phrase_len
        )
        # Full match takes priority
        self.assertEqual(result, 'dongjingdaxue')

    def test_no_subword_match_falls_back_to_char(self):
        """Test fallback to character-by-character when no subword matches."""
        # Word not in phrase dict, no subwords match
        result = generate_pinyin_for_word(
            '大小',
            {},  # Empty phrase dict
            self.char_to_pinyin,
            self.max_phrase_len
        )
        self.assertEqual(result, 'daxiao')

    def test_partial_subword_match(self):
        """Test mixed subword and character matching."""
        # 築地大 = 築地 (zhudi) + 大 (da)
        result = generate_pinyin_for_word(
            '築地大',
            self.phrase_to_pinyin,
            self.char_to_pinyin,
            self.max_phrase_len
        )
        self.assertEqual(result, 'zhudida')


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


class TestTraditionalToSimplified(unittest.TestCase):
    """Tests for traditional to simplified Chinese conversion."""

    def test_to_simplified_common_chars(self):
        """Test conversion of common traditional characters."""
        self.assertEqual(to_simplified('銀'), '银')
        self.assertEqual(to_simplified('東'), '东')
        self.assertEqual(to_simplified('國'), '国')
        self.assertEqual(to_simplified('學'), '学')
        self.assertEqual(to_simplified('電'), '电')

    def test_to_simplified_word(self):
        """Test conversion of entire words."""
        self.assertEqual(to_simplified('銀行'), '银行')
        self.assertEqual(to_simplified('東京'), '东京')
        self.assertEqual(to_simplified('電話'), '电话')

    def test_to_simplified_mixed(self):
        """Test conversion with mixed traditional and simplified."""
        # Characters already simplified or not in mapping should stay unchanged
        self.assertEqual(to_simplified('银行'), '银行')  # Already simplified
        self.assertEqual(to_simplified('東京大学'), '东京大学')

    def test_to_simplified_hiragana_unchanged(self):
        """Test that hiragana is not changed."""
        self.assertEqual(to_simplified('あいう'), 'あいう')
        self.assertEqual(to_simplified('銀行です'), '银行です')

    def test_lookup_phrase_traditional(self):
        """Test phrase lookup with traditional characters."""
        # Phrase dict uses simplified Chinese
        phrase_to_pinyin = {
            '银行': 'yinhang',
            '东京': 'dongjing',
        }

        # Looking up traditional should find simplified
        self.assertEqual(lookup_phrase('銀行', phrase_to_pinyin), 'yinhang')
        self.assertEqual(lookup_phrase('東京', phrase_to_pinyin), 'dongjing')

        # Looking up simplified should also work
        self.assertEqual(lookup_phrase('银行', phrase_to_pinyin), 'yinhang')

        # Non-existent should return None
        self.assertIsNone(lookup_phrase('不存在', phrase_to_pinyin))

    def test_generate_pinyin_with_traditional(self):
        """Test pinyin generation with traditional characters via simplified lookup."""
        char_to_pinyin = {
            '銀': 'yin',
            '行': 'xing',  # Default is wrong for 银行
            '員': 'yuan',
        }
        # Phrase dict uses simplified
        phrase_to_pinyin = {
            '银行': 'yinhang',  # Correct pronunciation
        }

        # 銀行 (traditional) should find 银行 (simplified) in phrase dict
        result = generate_pinyin_for_word('銀行', phrase_to_pinyin, char_to_pinyin, 10)
        self.assertEqual(result, 'yinhang')  # Not 'yinxing'

    def test_subword_matching_with_traditional(self):
        """Test subword matching with traditional characters."""
        char_to_pinyin = {
            '銀': 'yin',
            '行': 'xing',
            '職': 'zhi',
            '員': 'yuan',
        }
        phrase_to_pinyin = {
            '银行': 'yinhang',
        }

        # 銀行職員 should use 银行=yinhang from phrase dict
        result = generate_pinyin_for_word('銀行職員', phrase_to_pinyin, char_to_pinyin, 10)
        self.assertEqual(result, 'yinhangzhiyuan')


if __name__ == '__main__':
    unittest.main(verbosity=2)
