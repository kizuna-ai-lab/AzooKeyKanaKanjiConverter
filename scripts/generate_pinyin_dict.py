#!/usr/bin/env python3
"""
Generate Pinyin Dictionary for XiaoLiIME Hybrid Input Mode

This script creates a pinyin-to-kanji dictionary by:
1. Extracting kanji words from the existing Japanese dictionary (.loudstxt3 files)
2. Looking up Chinese pinyin using phrase-pinyin-data (words and characters)
3. Generating pinyin entries with correct multi-character word pronunciations

Data source: https://github.com/mozillazg/phrase-pinyin-data
- Provides word-level pinyin (handles multi-pronunciation characters correctly)
- Falls back to single-character pinyin for words not in the phrase dictionary

Usage:
    python generate_pinyin_dict.py [--output OUTPUT_DIR]
"""

import argparse
import re
import struct
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Optional


# Hiragana to romaji mapping
HIRAGANA_TO_ROMAJI = {
    'あ': 'a', 'い': 'i', 'う': 'u', 'え': 'e', 'お': 'o',
    'か': 'ka', 'き': 'ki', 'く': 'ku', 'け': 'ke', 'こ': 'ko',
    'さ': 'sa', 'し': 'shi', 'す': 'su', 'せ': 'se', 'そ': 'so',
    'た': 'ta', 'ち': 'chi', 'つ': 'tsu', 'て': 'te', 'と': 'to',
    'な': 'na', 'に': 'ni', 'ぬ': 'nu', 'ね': 'ne', 'の': 'no',
    'は': 'ha', 'ひ': 'hi', 'ふ': 'fu', 'へ': 'he', 'ほ': 'ho',
    'ま': 'ma', 'み': 'mi', 'む': 'mu', 'め': 'me', 'も': 'mo',
    'や': 'ya', 'ゆ': 'yu', 'よ': 'yo',
    'ら': 'ra', 'り': 'ri', 'る': 'ru', 'れ': 're', 'ろ': 'ro',
    'わ': 'wa', 'を': 'wo', 'ん': 'n',
    # Voiced (dakuten)
    'が': 'ga', 'ぎ': 'gi', 'ぐ': 'gu', 'げ': 'ge', 'ご': 'go',
    'ざ': 'za', 'じ': 'ji', 'ず': 'zu', 'ぜ': 'ze', 'ぞ': 'zo',
    'だ': 'da', 'ぢ': 'di', 'づ': 'du', 'で': 'de', 'ど': 'do',
    'ば': 'ba', 'び': 'bi', 'ぶ': 'bu', 'べ': 'be', 'ぼ': 'bo',
    'ぱ': 'pa', 'ぴ': 'pi', 'ぷ': 'pu', 'ぺ': 'pe', 'ぽ': 'po',
    # Small kana
    'ゃ': 'ya', 'ゅ': 'yu', 'ょ': 'yo',
    'ぁ': 'a', 'ぃ': 'i', 'ぅ': 'u', 'ぇ': 'e', 'ぉ': 'o',
    'っ': 'tt',  # Double consonant marker
}

# Traditional to Simplified Chinese character mapping
# Japanese uses traditional characters (or Shinjitai), but the phrase dictionary uses simplified
TRAD_TO_SIMP = {
    # Common characters that differ between traditional and simplified
    '銀': '银', '銀': '银', '東': '东', '國': '国', '國': '国',
    '學': '学', '會': '会', '經': '经', '業': '业', '電': '电',
    '車': '车', '機': '机', '場': '场', '開': '开', '關': '关',
    '門': '门', '間': '间', '時': '时', '書': '书', '長': '长',
    '張': '张', '馬': '马', '魚': '鱼', '鳥': '鸟', '龍': '龙',
    '風': '风', '飛': '飞', '體': '体', '頭': '头', '臉': '脸',
    '見': '见', '視': '视', '觀': '观', '說': '说', '話': '话',
    '語': '语', '讀': '读', '認': '认', '識': '识', '記': '记',
    '計': '计', '設': '设', '許': '许', '論': '论', '議': '议',
    '護': '护', '報': '报', '發': '发', '對': '对', '專': '专',
    '導': '导', '將': '将', '廣': '广', '當': '当', '準': '准',
    '進': '进', '過': '过', '運': '运', '還': '还', '連': '连',
    '選': '选', '達': '达', '遠': '远', '邊': '边', '這': '这',
    '裡': '里', '裏': '里', '處': '处', '號': '号', '線': '线',
    '紅': '红', '綠': '绿', '結': '结', '給': '给', '統': '统',
    '繼': '继', '續': '续', '織': '织', '終': '终', '練': '练',
    '總': '总', '約': '约', '紙': '纸', '級': '级', '細': '细',
    '納': '纳', '組': '组', '經': '经', '繩': '绑', '緊': '紧',
    '縣': '县', '區': '区', '醫': '医', '藥': '药', '農': '农',
    '寫': '写', '實': '实', '寶': '宝', '審': '审', '宮': '宫',
    '賣': '卖', '買': '买', '質': '质', '貨': '货', '責': '责',
    '貴': '贵', '費': '费', '資': '资', '賞': '赏', '賀': '贺',
    '貿': '贸', '財': '财', '貧': '贫', '販': '贩', '購': '购',
    '賊': '贼', '貸': '贷', '賴': '赖', '賢': '贤', '賤': '贱',
    '勞': '劳', '動': '动', '勸': '劝', '務': '务', '勝': '胜',
    '勢': '势', '團': '团', '園': '园', '圖': '图', '圍': '围',
    '點': '点', '黨': '党', '聽': '听', '聲': '声', '聯': '联',
    '職': '职', '陽': '阳', '陰': '阴', '際': '际', '隊': '队',
    '階': '阶', '險': '险', '雜': '杂', '難': '难', '雲': '云',
    '電': '电', '霧': '雾', '靈': '灵', '靜': '静', '鐵': '铁',
    '錢': '钱', '鋼': '钢', '錄': '录', '鏡': '镜', '針': '针',
    '鑒': '鉴', '錯': '错', '鍵': '键', '鎮': '镇', '鐘': '钟',
    '門': '门', '開': '开', '閉': '闭', '關': '关', '閱': '阅',
    '闘': '斗', '鬥': '斗', '鬪': '斗',
    '佛': '佛', '價': '价', '個': '个', '傳': '传', '備': '备',
    '優': '优', '儀': '仪', '億': '亿', '僅': '仅', '傷': '伤',
    '倉': '仓', '創': '创', '劃': '划', '劇': '剧', '則': '则',
    '剛': '刚', '別': '别', '刪': '删', '劉': '刘', '勵': '励',
    '華': '华', '衛': '卫', '廳': '厅', '廠': '厂', '壓': '压',
    '雙': '双', '變': '变', '叢': '丛', '葉': '叶', '號': '号',
    '臺': '台', '喬': '乔', '嚴': '严', '囑': '嘱', '聯': '联',
    '戰': '战', '戲': '戏', '戀': '恋', '態': '态', '愛': '爱',
    '憶': '忆', '懷': '怀', '惡': '恶', '慶': '庆', '應': '应',
    '憲': '宪', '懸': '悬', '懼': '惧', '戶': '户', '擔': '担',
    '據': '据', '擁': '拥', '擊': '击', '擬': '拟', '擴': '扩',
    '摯': '挚', '撐': '撑', '損': '损', '換': '换', '搶': '抢',
    '擇': '择', '撫': '抚', '搗': '捣', '撲': '扑', '擺': '摆',
    '攝': '摄', '攬': '揽', '攜': '携', '攻': '攻', '敗': '败',
    '敘': '叙', '數': '数', '斷': '断', '條': '条', '極': '极',
    '構': '构', '標': '标', '棟': '栋', '橋': '桥', '機': '机',
    '檔': '档', '檢': '检', '權': '权', '歐': '欧', '歲': '岁',
    '歷': '历', '殘': '残', '殺': '杀', '毀': '毁', '氣': '气',
    '氫': '氢', '決': '决', '況': '况', '沒': '没', '濟': '济',
    '濃': '浓', '測': '测', '減': '减', '溫': '温', '滅': '灭',
    '準': '准', '滿': '满', '漢': '汉', '漸': '渐', '潔': '洁',
    '潛': '潜', '潰': '溃', '滬': '沪', '濟': '济', '濱': '滨',
    '瀏': '浏', '灣': '湾', '災': '灾', '燈': '灯', '燃': '燃',
    '爺': '爷', '爾': '尔', '牆': '墙', '猶': '犹', '獨': '独',
    '獲': '获', '獎': '奖', '獻': '献', '環': '环', '現': '现',
    '產': '产', '異': '异', '疊': '叠', '療': '疗', '發': '发',
    '盜': '盗', '監': '监', '鹽': '盐', '盡': '尽', '眾': '众',
    '睜': '睁', '瞭': '了', '礎': '础', '祿': '禄', '禮': '礼',
    '稅': '税', '穩': '稳', '種': '种', '積': '积', '競': '竞',
    '筆': '笔', '節': '节', '範': '范', '築': '筑', '篤': '笃',
    '簡': '简', '籠': '笼', '類': '类', '粵': '粤', '絕': '绝',
    '絲': '丝', '編': '编', '緒': '绪', '練': '练', '繁': '繁',
    '縮': '缩', '繪': '绘', '義': '义', '習': '习', '翻': '翻',
    '耐': '耐', '聖': '圣', '職': '职', '腦': '脑', '腸': '肠',
    '膠': '胶', '膽': '胆', '臨': '临', '舉': '举', '舊': '旧',
    '舖': '铺', '艦': '舰', '艱': '艰', '芻': '刍', '範': '范',
    '莊': '庄', '華': '华', '萬': '万', '葛': '葛', '蒙': '蒙',
    '蓋': '盖', '蔣': '蒋', '藍': '蓝', '藝': '艺', '蘇': '苏',
    '處': '处', '虛': '虚', '號': '号', '蟲': '虫', '蠟': '蜡',
    '術': '术', '衛': '卫', '裝': '装', '製': '制', '複': '复',
    '褲': '裤', '親': '亲', '覺': '觉', '訊': '讯', '訓': '训',
    '記': '记', '訪': '访', '設': '设', '評': '评', '詞': '词',
    '詢': '询', '試': '试', '詩': '诗', '話': '话', '該': '该',
    '詳': '详', '誌': '志', '認': '认', '誠': '诚', '語': '语',
    '誤': '误', '說': '说', '課': '课', '調': '调', '談': '谈',
    '請': '请', '論': '论', '諸': '诸', '謀': '谋', '謂': '谓',
    '講': '讲', '謝': '谢', '謹': '谨', '證': '证', '識': '识',
    '譜': '谱', '警': '警', '議': '议', '譯': '译', '護': '护',
    '讓': '让', '讀': '读', '變': '变', '豐': '丰', '貝': '贝',
    '負': '负', '貢': '贡', '貪': '贪', '貫': '贯', '責': '责',
    '貯': '贮', '貳': '贰', '貴': '贵', '貶': '贬', '貸': '贷',
    '費': '费', '貿': '贸', '賀': '贺', '賁': '贲', '賃': '赁',
    '賄': '贿', '資': '资', '賈': '贾', '賊': '贼', '賓': '宾',
    '賜': '赐', '賞': '赏', '賠': '赔', '賢': '贤', '賣': '卖',
    '賤': '贱', '賦': '赋', '質': '质', '賬': '账', '賴': '赖',
    '賺': '赚', '購': '购', '賽': '赛', '贅': '赘', '贈': '赠',
    '贊': '赞', '贏': '赢', '贓': '赃', '趙': '赵', '趕': '赶',
    '趨': '趋', '跡': '迹', '跨': '跨', '跳': '跳', '踐': '践',
    '踴': '踊', '蹟': '迹', '軀': '躯', '車': '车', '軌': '轨',
    '軍': '军', '軒': '轩', '軟': '软', '較': '较', '載': '载',
    '輔': '辅', '輕': '轻', '輛': '辆', '輝': '辉', '輩': '辈',
    '輪': '轮', '輸': '输', '轄': '辖', '轉': '转', '轍': '辙',
    '轟': '轰', '辦': '办', '辭': '辞', '農': '农', '迴': '回',
    '逕': '径', '這': '这', '過': '过', '達': '达', '違': '违',
    '遙': '遥', '遜': '逊', '遞': '递', '遠': '远', '適': '适',
    '遲': '迟', '遷': '迁', '選': '选', '遺': '遗', '還': '还',
    '邁': '迈', '邊': '边', '邏': '逻', '郵': '邮', '鄉': '乡',
    '鄭': '郑', '鄰': '邻', '醜': '丑', '醫': '医', '醬': '酱',
    '釀': '酿', '釋': '释', '針': '针', '鈴': '铃', '鉀': '钾',
    '鉅': '钜', '鉛': '铅', '鉢': '钵', '鉤': '钩', '銅': '铜',
    '銘': '铭', '銳': '锐', '銷': '销', '鋁': '铝', '鋒': '锋',
    '鋪': '铺', '鋼': '钢', '錄': '录', '錘': '锤', '錢': '钱',
    '錦': '锦', '錨': '锚', '錫': '锡', '錯': '错', '鍊': '链',
    '鍋': '锅', '鍵': '键', '鍾': '钟', '鎖': '锁', '鎮': '镇',
    '鏡': '镜', '鏢': '镖', '鐘': '钟', '鐵': '铁', '鑄': '铸',
    '鑑': '鉴', '鑒': '鉴', '鑰': '钥', '鑽': '钻', '長': '长',
    '門': '门', '閃': '闪', '閉': '闭', '開': '开', '閏': '闰',
    '閑': '闲', '間': '间', '閘': '闸', '閣': '阁', '閥': '阀',
    '閱': '阅', '闆': '板', '闈': '闱', '闊': '阔', '闌': '阑',
    '闔': '阖', '闘': '斗', '關': '关', '闡': '阐', '防': '防',
    '阮': '阮', '陣': '阵', '陰': '阴', '陳': '陈', '陸': '陆',
    '陽': '阳', '隊': '队', '階': '阶', '隔': '隔', '際': '际',
    '隨': '随', '險': '险', '隱': '隐', '隻': '只', '雖': '虽',
    '雙': '双', '雜': '杂', '雞': '鸡', '離': '离', '難': '难',
    '雲': '云', '電': '电', '霧': '雾', '露': '露', '靈': '灵',
    '青': '青', '靜': '静', '靠': '靠', '頁': '页', '頂': '顶',
    '項': '项', '順': '顺', '須': '须', '頌': '颂', '預': '预',
    '頑': '顽', '頒': '颁', '領': '领', '頗': '颇', '頭': '头',
    '頰': '颊', '頸': '颈', '頻': '频', '頹': '颓', '顆': '颗',
    '題': '题', '額': '额', '顏': '颜', '願': '愿', '類': '类',
    '顧': '顾', '顯': '显', '風': '风', '颱': '台', '飄': '飘',
    '飛': '飞', '飢': '饥', '飲': '饮', '飼': '饲', '飽': '饱',
    '飾': '饰', '餃': '饺', '養': '养', '餐': '餐', '餘': '余',
    '餅': '饼', '餓': '饿', '館': '馆', '餞': '饯', '餡': '馅',
    '饅': '馒', '饑': '饥', '首': '首', '馬': '马', '駁': '驳',
    '駐': '驻', '駕': '驾', '駛': '驶', '駝': '驼', '駿': '骏',
    '騎': '骑', '騙': '骗', '騷': '骚', '驅': '驱', '驗': '验',
    '驚': '惊', '體': '体', '髮': '发', '鬆': '松', '鬥': '斗',
    '鬧': '闹', '鬱': '郁', '魚': '鱼', '魯': '鲁', '鮮': '鲜',
    '鯨': '鲸', '鰭': '鳍', '鱗': '鳞', '鳥': '鸟', '鳳': '凤',
    '鴉': '鸦', '鴕': '鸵', '鴻': '鸿', '鵑': '鹃', '鵝': '鹅',
    '鷗': '鸥', '鷹': '鹰', '鸚': '鹦', '鹹': '咸', '鹿': '鹿',
    '麥': '麦', '麵': '面', '麼': '么', '黃': '黄', '黑': '黑',
    '點': '点', '黨': '党', '鼓': '鼓', '鼠': '鼠', '齊': '齐',
    '齒': '齿', '齡': '龄', '龍': '龙', '龜': '龟',
    # Japanese specific (Shinjitai)
    '駅': '驿', '桜': '樱', '芸': '艺', '売': '卖', '読': '读',
    '単': '单', '営': '营', '実': '实', '写': '写', '学': '学',
    '挙': '举', '覚': '觉', '観': '观', '気': '气', '戦': '战',
    '県': '县', '対': '对', '図': '图', '変': '变', '応': '应',
    '医': '医', '歴': '历', '旧': '旧', '帰': '归', '広': '广',
    '悪': '恶', '画': '画', '発': '发', '鉄': '铁', '塩': '盐',
}


def to_simplified(text: str) -> str:
    """Convert traditional/Japanese characters to simplified Chinese."""
    return ''.join(TRAD_TO_SIMP.get(c, c) for c in text)


def download_phrase_pinyin_data(output_dir: Path) -> tuple[Path, Path]:
    """
    Download pinyin data files from GitHub.

    Returns (phrase_file, char_file) paths.

    Data sources:
    - phrase-pinyin-data: word/phrase level pinyin (handles multi-pronunciation correctly)
    - pinyin-data: single character pinyin (fallback for characters not in phrase dict)
    """
    # Word/phrase pinyin (large_pinyin.txt ~9MB, contains phrases from multiple sources)
    phrase_file = output_dir / "large_pinyin.txt"
    phrase_url = "https://raw.githubusercontent.com/mozillazg/phrase-pinyin-data/master/large_pinyin.txt"

    # Single character pinyin from pinyin-data repository
    # pinyin.txt contains character -> pinyin mappings with most common pronunciation
    char_file = output_dir / "char_pinyin.txt"
    char_url = "https://raw.githubusercontent.com/mozillazg/pinyin-data/master/pinyin.txt"

    downloads = [
        ("large_pinyin.txt", phrase_file, phrase_url),
        ("char_pinyin.txt", char_file, char_url),
    ]

    for filename, filepath, url in downloads:
        if filepath.exists():
            print(f"{filename} already exists at {filepath}")
            continue

        print(f"Downloading {filename} from {url}...")

        try:
            result = subprocess.run(
                ['curl', '-L', '-A', 'Mozilla/5.0', '-o', str(filepath), url],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                raise Exception(f"curl failed: {result.stderr}")
            print(f"Downloaded {filename}")
        except Exception as e:
            print(f"Error downloading {filename}: {e}")
            print(f"Please manually download from {url}")
            sys.exit(1)

    return phrase_file, char_file


def remove_tone_marks(pinyin: str) -> str:
    """Remove pinyin tone marks and convert to base letters."""
    tone_map = {
        'ā': 'a', 'á': 'a', 'ǎ': 'a', 'à': 'a',
        'ē': 'e', 'é': 'e', 'ě': 'e', 'è': 'e',
        'ī': 'i', 'í': 'i', 'ǐ': 'i', 'ì': 'i',
        'ō': 'o', 'ó': 'o', 'ǒ': 'o', 'ò': 'o',
        'ū': 'u', 'ú': 'u', 'ǔ': 'u', 'ù': 'u',
        'ǖ': 'v', 'ǘ': 'v', 'ǚ': 'v', 'ǜ': 'v', 'ü': 'v',
        'ń': 'n', 'ň': 'n', 'ǹ': 'n',
        'ḿ': 'm',
    }
    result = pinyin.lower()
    for tone, base in tone_map.items():
        result = result.replace(tone, base)
    # Also remove numeric tone markers (1-5)
    result = re.sub(r'[1-5]', '', result)
    return result


def load_phrase_pinyin(phrase_file: Path) -> tuple[dict[str, str], int]:
    """
    Load word/phrase to pinyin mapping from phrase-pinyin-data.

    Format: 词语: pīn yīn
    Returns tuple of (dict mapping word -> pinyin (without tones, spaces removed), max phrase length)
    """
    phrase_to_pinyin = {}
    max_len = 0

    print(f"Loading phrase pinyin from {phrase_file}...")

    with open(phrase_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or ': ' not in line:
                continue

            # Format: "词语: pīn yīn"
            parts = line.split(': ', 1)
            if len(parts) != 2:
                continue

            phrase, pinyin_with_tones = parts
            # Remove tone marks and spaces
            pinyin_clean = remove_tone_marks(pinyin_with_tones.replace(' ', ''))
            phrase_to_pinyin[phrase] = pinyin_clean
            max_len = max(max_len, len(phrase))

    print(f"Loaded {len(phrase_to_pinyin)} phrase-to-pinyin mappings, max length: {max_len}")
    return phrase_to_pinyin, max_len


def load_char_pinyin(char_file: Path) -> dict[str, str]:
    """
    Load single character to pinyin mapping from mozillazg/pinyin-data.

    This file contains the most commonly used pronunciation for each character,
    which is better than Unihan's arbitrary first pronunciation.

    Format: U+XXXX: pīn1,pīn2,...  # 字
    Returns dict mapping char -> pinyin (without tones)
    """
    char_to_pinyin = {}

    print(f"Loading character pinyin from {char_file}...")

    with open(char_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Format: U+XXXX: pīn1,pīn2,...  # 字
            if not line.startswith('U+'):
                continue

            # Split by colon to get codepoint and pinyin part
            if ': ' not in line:
                continue

            codepoint_part, rest = line.split(': ', 1)

            # Remove comment if present
            if '#' in rest:
                pinyin_part = rest.split('#')[0].strip()
            else:
                pinyin_part = rest.strip()

            # Convert codepoint to character
            try:
                codepoint = int(codepoint_part[2:], 16)
                char = chr(codepoint)
            except (ValueError, OverflowError):
                continue

            # Take first pronunciation if multiple (comma-separated)
            first_pinyin = pinyin_part.split(',')[0].strip()
            pinyin_clean = remove_tone_marks(first_pinyin)

            if pinyin_clean:
                char_to_pinyin[char] = pinyin_clean

    print(f"Loaded {len(char_to_pinyin)} character-to-pinyin mappings")
    return char_to_pinyin


def is_kanji(char: str) -> bool:
    """Check if a character is a CJK ideograph (kanji)."""
    try:
        name = unicodedata.name(char, '')
        return 'CJK' in name or 'IDEOGRAPH' in name
    except:
        # Fallback: check Unicode ranges for CJK
        cp = ord(char)
        return (
            (0x4E00 <= cp <= 0x9FFF) or   # CJK Unified Ideographs
            (0x3400 <= cp <= 0x4DBF) or   # CJK Extension A
            (0x20000 <= cp <= 0x2A6DF) or # CJK Extension B
            (0x2A700 <= cp <= 0x2B73F) or # CJK Extension C
            (0x2B740 <= cp <= 0x2B81F) or # CJK Extension D
            (0xF900 <= cp <= 0xFAFF) or   # CJK Compatibility Ideographs
            (0x2F800 <= cp <= 0x2FA1F)    # CJK Compatibility Supplement
        )


def is_hiragana(char: str) -> bool:
    """Check if character is hiragana."""
    return 0x3040 <= ord(char) <= 0x309F


def parse_loudstxt3(filepath: Path) -> list[tuple[str, str, int, int, int, float]]:
    """
    Parse a .loudstxt3 file and extract dictionary entries.

    Returns list of (ruby, word, lcid, rcid, mid, score) tuples.
    """
    entries = []

    try:
        with open(filepath, 'rb') as f:
            data = f.read()

        if len(data) < 2:
            return entries

        # Header: UInt16 count
        count = struct.unpack('<H', data[0:2])[0]

        if count == 0:
            return entries

        # Offsets: count * UInt32
        header_size = 2 + count * 4
        if len(data) < header_size:
            return entries

        offsets = []
        for i in range(count):
            offset = struct.unpack('<I', data[2 + i*4 : 2 + i*4 + 4])[0]
            offsets.append(offset)

        # Parse each entry
        for i in range(count):
            start = offsets[i]
            end = offsets[i+1] if i+1 < count else len(data)

            if start >= len(data) or end > len(data) or start >= end:
                continue

            entry_data = data[start:end]
            if len(entry_data) < 2:
                continue

            # Entry format: UInt16 row_count, then rows, then text
            row_count = struct.unpack('<H', entry_data[0:2])[0]

            if row_count == 0:
                continue

            # Each row: lcid(2) + rcid(2) + mid(2) + score(4) = 10 bytes
            rows_size = row_count * 10
            if len(entry_data) < 2 + rows_size:
                continue

            rows = []
            for j in range(row_count):
                row_start = 2 + j * 10
                lcid = struct.unpack('<H', entry_data[row_start:row_start+2])[0]
                rcid = struct.unpack('<H', entry_data[row_start+2:row_start+4])[0]
                mid = struct.unpack('<H', entry_data[row_start+4:row_start+6])[0]
                score = struct.unpack('<f', entry_data[row_start+6:row_start+10])[0]
                rows.append((lcid, rcid, mid, score))

            # Text area: ruby\tword1\tword2\t...
            text_start = 2 + rows_size
            text_data = entry_data[text_start:]

            try:
                text = text_data.decode('utf-8')
                parts = text.split('\t')
                if len(parts) >= 1:
                    ruby = parts[0]
                    words = parts[1:] if len(parts) > 1 else [ruby]

                    for idx, word in enumerate(words):
                        if idx < len(rows):
                            lcid, rcid, mid, score = rows[idx]
                            # Empty word means same as ruby
                            actual_word = word if word else ruby
                            entries.append((ruby, actual_word, lcid, rcid, mid, score))
            except:
                pass

    except Exception as e:
        pass

    return entries


def extract_japanese_dictionary(dict_dir: Path) -> list[tuple[str, str, int, int, int, float]]:
    """
    Extract all entries from the Japanese dictionary .loudstxt3 files.

    Returns list of (ruby, word, lcid, rcid, mid, score) tuples.
    """
    entries = []

    loudstxt3_files = list(dict_dir.glob("*.loudstxt3"))
    # Exclude pinyin files
    loudstxt3_files = [f for f in loudstxt3_files if not f.name.startswith("pinyin")]

    print(f"Found {len(loudstxt3_files)} Japanese dictionary files")

    for i, filepath in enumerate(loudstxt3_files):
        if i % 50 == 0:
            print(f"  Processing file {i+1}/{len(loudstxt3_files)}...")

        file_entries = parse_loudstxt3(filepath)
        entries.extend(file_entries)

    print(f"Extracted {len(entries)} entries from Japanese dictionary")
    return entries


def lookup_phrase(phrase: str, phrase_to_pinyin: dict[str, str]) -> Optional[str]:
    """
    Look up a phrase in the dictionary, trying both original and simplified forms.

    Returns pinyin if found, None otherwise.
    """
    # Try original form first
    if phrase in phrase_to_pinyin:
        return phrase_to_pinyin[phrase]

    # Try simplified Chinese form
    simplified = to_simplified(phrase)
    if simplified != phrase and simplified in phrase_to_pinyin:
        return phrase_to_pinyin[simplified]

    return None


def generate_pinyin_for_word(
    word: str,
    phrase_to_pinyin: dict[str, str],
    char_to_pinyin: dict[str, str],
    max_phrase_len: int = 20
) -> Optional[str]:
    """
    Generate pinyin for a word using maximum forward matching algorithm.

    Algorithm:
    1. If entire word is in phrase dictionary, return directly
    2. Otherwise, scan from left to right, matching longest subword in phrase dictionary
    3. Unmatched characters fall back to single-character lookup

    Note: Both traditional (Japanese) and simplified Chinese forms are tried
    when looking up in the phrase dictionary.

    Example:
        "築地小劇場" not in dictionary
        → Match "築地" (zhudi) + "小劇場" (xiaojuchang)
        → Result: "zhudixiaojuchang"

    - Kanji: converted to pinyin
    - Hiragana: converted to romaji
    - Other characters: skip word

    Returns None if word cannot be converted.
    """
    # Must contain at least one kanji to be useful
    if not any(is_kanji(c) for c in word):
        return None

    # Fast path: entire word in phrase dictionary (try both traditional and simplified)
    pinyin = lookup_phrase(word, phrase_to_pinyin)
    if pinyin:
        return pinyin

    # Maximum forward matching algorithm
    result = []
    pos = 0

    while pos < len(word):
        matched = False

        # Try matching longest subword first (from max_phrase_len down to 2)
        max_len = min(len(word) - pos, max_phrase_len)
        for length in range(max_len, 1, -1):
            candidate = word[pos:pos + length]
            # Try both traditional and simplified forms
            pinyin = lookup_phrase(candidate, phrase_to_pinyin)
            if pinyin:
                result.append(pinyin)
                pos += length
                matched = True
                break

        # Single character fallback
        if not matched:
            char = word[pos]
            if char in char_to_pinyin:
                # Kanji with pinyin mapping
                result.append(char_to_pinyin[char])
            elif is_hiragana(char) and char in HIRAGANA_TO_ROMAJI:
                # Hiragana converted to romaji
                result.append(HIRAGANA_TO_ROMAJI[char])
            elif is_kanji(char):
                # Kanji without pinyin mapping - skip entire word
                return None
            else:
                # Other characters (katakana, punctuation) - skip entire word
                return None
            pos += 1

    return ''.join(result) if result else None


def generate_pinyin_entries(
    japanese_entries: list[tuple[str, str, int, int, int, float]],
    phrase_to_pinyin: dict[str, str],
    char_to_pinyin: dict[str, str],
    max_phrase_len: int = 20
) -> list[tuple[str, str, int, int, int, float]]:
    """
    Generate pinyin dictionary entries from Japanese dictionary entries.

    For each Japanese entry with kanji word:
    1. Look up pinyin using maximum forward matching (subword matching)
    2. Create new entry with pinyin as key, kanji as value
    3. Keep the entry with the best (highest) score for each (pinyin, word) pair
    """
    # Track best entry for each (pinyin, word) pair
    best_entries: dict[tuple[str, str], tuple[str, str, int, int, int, float]] = {}

    print("Generating pinyin entries from Japanese dictionary...")
    phrase_hits = 0
    subword_hits = 0
    char_hits = 0

    # Process Japanese dictionary entries
    for ruby, word, lcid, rcid, mid, score in japanese_entries:
        # Only process words that contain kanji
        if not any(is_kanji(c) for c in word):
            continue

        # Categorize match type for stats
        if word in phrase_to_pinyin:
            match_type = 'phrase'
        else:
            match_type = 'other'

        # Generate pinyin for the word
        pinyin = generate_pinyin_for_word(word, phrase_to_pinyin, char_to_pinyin, max_phrase_len)

        if pinyin and pinyin.isascii() and pinyin.islower():
            key = (pinyin, word)
            # Adjust score (cap at -5.0)
            adjusted_score = min(score, -5.0)

            # Keep entry with best (highest/least negative) score
            if key not in best_entries or adjusted_score > best_entries[key][5]:
                best_entries[key] = (pinyin, word, lcid, rcid, mid, adjusted_score)

            # Track stats
            if match_type == 'phrase':
                phrase_hits += 1
            else:
                # Check if subword matching was used (word not in phrase dict but has multi-char submatches)
                # Simple heuristic: if any 2+ char substring is in phrase dict
                has_subword = any(
                    word[i:i+l] in phrase_to_pinyin
                    for i in range(len(word))
                    for l in range(2, len(word) - i + 1)
                    if i + l <= len(word)
                )
                if has_subword:
                    subword_hits += 1
                else:
                    char_hits += 1

    pinyin_entries = list(best_entries.values())
    print(f"Generated {len(pinyin_entries)} pinyin entries from Japanese dictionary")
    print(f"  - Full phrase matches: {phrase_hits}")
    print(f"  - Subword matches: {subword_hits}")
    print(f"  - Character-only matches: {char_hits}")
    print(f"Total pinyin entries: {len(pinyin_entries)}")

    return pinyin_entries


def write_tsv(entries: list[tuple], output_file: Path):
    """Write entries to TSV format."""
    print(f"Writing {len(entries)} entries to {output_file}...")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# pinyin\tword\tlcid\trcid\tmid\tvalue\n")
        for pinyin, word, lcid, rcid, mid, value in sorted(entries, key=lambda x: (x[0], x[1])):
            f.write(f"{pinyin}\t{word}\t{lcid}\t{rcid}\t{mid}\t{value}\n")

    print(f"Written TSV to {output_file}")


def build_louds_dictionary(
    tsv_file: Path,
    output_dir: Path,
    char_id_file: Path
):
    """Build LOUDS dictionary files from TSV."""

    print(f"Building LOUDS dictionary...")
    print(f"  TSV file: {tsv_file}")
    print(f"  Output dir: {output_dir}")
    print(f"  CharID file: {char_id_file}")

    output_dir.mkdir(parents=True, exist_ok=True)

    swift_script = f'''
import Foundation

// Load charID mapping
let charIDPath = "{char_id_file}"
let charIDString = try! String(contentsOfFile: charIDPath, encoding: .utf8)
var char2UInt8: [Character: UInt8] = [:]
for (index, char) in charIDString.enumerated() {{
    char2UInt8[char] = UInt8(index)
}}

// Ensure lowercase letters are mapped
let letters = "abcdefghijklmnopqrstuvwxyz"
for (i, c) in letters.enumerated() {{
    if char2UInt8[c] == nil {{
        char2UInt8[c] = UInt8(164 + i)
    }}
}}

// Parse TSV file
struct Entry {{
    var pinyin: String
    var word: String
    var lcid: Int
    var rcid: Int
    var mid: Int
    var value: Float
}}

var entries: [Entry] = []
let tsvPath = "{tsv_file}"
let tsvContent = try! String(contentsOfFile: tsvPath, encoding: .utf8)
for line in tsvContent.split(separator: "\\n") {{
    if line.hasPrefix("#") {{ continue }}
    let parts = line.split(separator: "\\t", omittingEmptySubsequences: false)
    if parts.count >= 6 {{
        let entry = Entry(
            pinyin: String(parts[0]),
            word: String(parts[1]),
            lcid: Int(parts[2])!,
            rcid: Int(parts[3])!,
            mid: Int(parts[4])!,
            value: Float(parts[5])!
        )
        entries.append(entry)
    }}
}}

print("Loaded \\(entries.count) entries from TSV")

// Build trie structure
class TrieNode {{
    var children: [UInt8: TrieNode] = [:]
    var entries: [Entry] = []
}}

let root = TrieNode()

for entry in entries {{
    var node = root
    for char in entry.pinyin {{
        guard let id = char2UInt8[char] else {{
            continue
        }}
        if node.children[id] == nil {{
            node.children[id] = TrieNode()
        }}
        node = node.children[id]!
    }}
    node.entries.append(entry)
}}

// BFS to build LOUDS structure
var bits: [Bool] = [true, false]
var nodeChars: [UInt8] = [0, 0]

struct QueueItem {{
    var node: TrieNode
    var char: UInt8
}}

var queue: [QueueItem] = root.children.sorted {{ $0.key < $1.key }}.map {{ QueueItem(node: $0.value, char: $0.key) }}
bits.append(contentsOf: [Bool](repeating: true, count: queue.count))
bits.append(false)

var nodeIndex = 2
var nodeToIndex: [ObjectIdentifier: Int] = [:]
var indexToEntries: [Int: [Entry]] = [:]

while !queue.isEmpty {{
    var nextQueue: [QueueItem] = []
    for item in queue {{
        nodeToIndex[ObjectIdentifier(item.node)] = nodeIndex
        nodeChars.append(item.char)
        if !item.node.entries.isEmpty {{
            indexToEntries[nodeIndex] = item.node.entries
        }}

        let children = item.node.children.sorted {{ $0.key < $1.key }}
        bits.append(contentsOf: [Bool](repeating: true, count: children.count))
        bits.append(false)

        for (childChar, childNode) in children {{
            nextQueue.append(QueueItem(node: childNode, char: childChar))
        }}
        nodeIndex += 1
    }}
    queue = nextQueue
}}

print("Built LOUDS trie with \\(nodeIndex) nodes")

// Write LOUDS file
func makeLOUDSData(bits: [Bool]) -> Data {{
    let unit = 64
    let paddedCount = ((bits.count + unit - 1) / unit) * unit
    var data = Data()
    var value: UInt64 = 0
    var idxInUnit = 0
    for b in bits {{
        if b {{
            value |= (1 << (unit - idxInUnit - 1))
        }}
        idxInUnit += 1
        if idxInUnit == unit {{
            var v = value
            data.append(Data(bytes: &v, count: 8))
            value = 0
            idxInUnit = 0
        }}
    }}
    if idxInUnit != 0 {{
        while idxInUnit < unit {{
            value |= (1 << (unit - idxInUnit - 1))
            idxInUnit += 1
        }}
        var v = value
        data.append(Data(bytes: &v, count: 8))
    }}
    return data
}}

let outputDir = "{output_dir}"
let loudsData = makeLOUDSData(bits: bits)
try! loudsData.write(to: URL(fileURLWithPath: outputDir + "/pinyin.louds"))
print("Written pinyin.louds")

let charsData = Data(nodeChars)
try! charsData.write(to: URL(fileURLWithPath: outputDir + "/pinyin.loudschars2"))
print("Written pinyin.loudschars2")

// Write loudstxt3 files (sharded)
let shardShift = 11
let entriesPerShard = 1 << shardShift
let localMask = entriesPerShard - 1

var shards: [Int: [(local: Int, ruby: String, rows: [(word: String, lcid: Int, rcid: Int, mid: Int, score: Float)])]] = [:]

for (nodeIdx, nodeEntries) in indexToEntries {{
    let shard = nodeIdx >> shardShift
    let local = nodeIdx & localMask
    let ruby = nodeEntries.first!.pinyin
    let rows = nodeEntries.map {{ ($0.word, $0.lcid, $0.rcid, $0.mid, $0.value) }}
    shards[shard, default: []].append((local: local, ruby: ruby, rows: rows))
}}

for (shard, items) in shards.sorted(by: {{ $0.key < $1.key }}) {{
    var payloads: [Data] = Array(repeating: {{
        var z: UInt16 = 0
        return Data(bytes: &z, count: 2)
    }}(), count: entriesPerShard)

    for item in items {{
        var d = Data()
        var count = UInt16(item.rows.count)
        d.append(Data(bytes: &count, count: 2))
        for row in item.rows {{
            var lcid = UInt16(row.lcid)
            var rcid = UInt16(row.rcid)
            var mid = UInt16(row.mid)
            var score = Float32(row.score)
            d.append(Data(bytes: &lcid, count: 2))
            d.append(Data(bytes: &rcid, count: 2))
            d.append(Data(bytes: &mid, count: 2))
            d.append(Data(bytes: &score, count: 4))
        }}
        let text = ([item.ruby] + item.rows.map {{ $0.word == item.ruby ? "" : $0.word }}).joined(separator: "\\t")
        d.append(text.data(using: .utf8)!)
        payloads[item.local] = d
    }}

    var result = Data()
    var count16 = UInt16(entriesPerShard)
    result.append(Data(bytes: &count16, count: 2))

    var offset: UInt32 = 2 + UInt32(entriesPerShard) * 4
    for i in 0..<entriesPerShard {{
        result.append(Data(bytes: &offset, count: 4))
        offset += UInt32(payloads[i].count)
    }}

    for p in payloads {{
        result.append(p)
    }}

    try! result.write(to: URL(fileURLWithPath: outputDir + "/pinyin\\(shard).loudstxt3"))
}}

print("Written \\(shards.count) loudstxt3 shard files")
print("Dictionary build complete!")
'''

    script_file = output_dir / "build_pinyin_dict.swift"
    with open(script_file, 'w', encoding='utf-8') as f:
        f.write(swift_script)

    print(f"Running Swift script to build dictionary...")
    result = subprocess.run(
        ['swift', str(script_file)],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"Error building dictionary:")
        print(result.stderr)
        sys.exit(1)

    print(result.stdout)
    script_file.unlink()


def main():
    parser = argparse.ArgumentParser(
        description="Generate Pinyin Dictionary from Japanese Dictionary"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path(__file__).parent.parent / "Sources" / "KanaKanjiConverterModuleWithDefaultDictionary" / "PinyinDictionary" / "louds",
        help="Output directory for pinyin dictionary files"
    )
    parser.add_argument(
        "--dict-dir", "-d",
        type=Path,
        default=Path(__file__).parent.parent / "Sources" / "KanaKanjiConverterModuleWithDefaultDictionary" / "azooKey_dictionary_storage" / "Dictionary" / "louds",
        help="Source directory containing Japanese dictionary files (.loudstxt3)"
    )
    parser.add_argument(
        "--tsv-only",
        action="store_true",
        help="Only generate TSV file, skip LOUDS building"
    )

    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    # Step 1: Download phrase-pinyin-data (replaces Unihan for better multi-pronunciation handling)
    phrase_file, char_file = download_phrase_pinyin_data(args.output.parent)

    # Step 2: Load pinyin data
    phrase_to_pinyin, max_phrase_len = load_phrase_pinyin(phrase_file)
    char_to_pinyin = load_char_pinyin(char_file)

    # Step 3: Extract entries from Japanese dictionary
    japanese_entries = extract_japanese_dictionary(args.dict_dir)

    # Step 4: Generate pinyin entries (using maximum forward matching for subword matching)
    pinyin_entries = generate_pinyin_entries(japanese_entries, phrase_to_pinyin, char_to_pinyin, max_phrase_len)

    # Step 5: Write TSV
    tsv_file = args.output / "pinyin_dictionary.tsv"
    write_tsv(pinyin_entries, tsv_file)

    # Step 6: Build LOUDS dictionary
    if not args.tsv_only:
        char_id_file = args.dict_dir / "charID.chid"
        build_louds_dictionary(tsv_file, args.output, char_id_file=char_id_file)

    print("\nDone! Dictionary files created:")
    print(f"  - {args.output}/pinyin.louds")
    print(f"  - {args.output}/pinyin.loudschars2")
    print(f"  - {args.output}/pinyin*.loudstxt3")


if __name__ == "__main__":
    main()
