


import re
import unicodedata
from dataclasses import dataclass


@dataclass
class TitleParseResult:
    """
    番組タイトルの解析結果を格納するデータクラス

    Attributes:
        series_title: シリーズ名 (タイトルから抽出したシリーズ名、または正規化後のタイトル全体)
        episode_number: 話数 (話数パターンが見つからなかった場合は None)
        subtitle: サブタイトル (存在しない場合は None)
    """
    series_title: str | None
    episode_number: str | None
    subtitle: str | None


class TitleParser:
    """
    番組タイトルからシリーズ名・話数・サブタイトルを抽出するユーティリティクラス

    日本のテレビ番組の EPG タイトルには、放送局が付加するメタ情報や話数・サブタイトルが
    様々なパターンで含まれている。このクラスは Komorebi (Android TV クライアント) の
    TitleNormalizer を参考に、EPG 特有のノイズを除去した上でシリーズのグループ化に
    必要な情報を抽出する。SCRenamePy のパターンも参考にしている。

    設計方針:
        Komorebi と同様の「決定論的な正規化 → 完全一致グルーピング」アプローチを採用する。
        ファジーマッチングは使わず、正規化パターンを十分に網羅することで、
        同一シリーズが常に同じ series_title に正規化されることを保証する。

    前処理 (正規化) の流れ:
        1. Unicode NFKC 正規化: 全角英数字→半角、互換文字の正規化
        2. EPG 放送タグの除去: [字], (二), 【新】, ［再］ など5種類の括弧スタイルに対応
        3. ジャンルプレフィックスの除去: アニメ「...」, アニメ・, アニメA・, 【連続テレビ小説】 等
        4. 放送枠プレフィックス/サフィックスの除去: <ノイタミナ>, AnichU, 【ANiMAZiNG！！！】 等
        5. スペース正規化・トリム

    話数抽出の流れ:
        正規化後のタイトルから、エピソード番号/サブタイトル区切りパターンを検出し、
        最初にマッチした位置でタイトルを切断してシリーズ名とする。

    話数パターンが見つからなかった場合でも、正規化後のタイトル全体を series_title として返す。
    これにより話数を持たない番組 (バラエティ・ニュース・スポーツ等) も同じタイトルの
    番組同士でシリーズとしてグループ化できる。

    対応パターン例:
        - 「[新]アニメA・番組名 #3「サブタイトル」[字]」 → series_title="番組名", episode_number="3"
        - 「<ノイタミナ>番組名 Season2 #04[字][解]」 → series_title="番組名 Season2", episode_number="4"
        - 「アニメ アルネの事件簿 Teil 9」 → series_title="アルネの事件簿", episode_number="9"
        - 「【連続テレビ小説】ばけばけ(98)第20週「サブタイトル」」 → series_title="ばけばけ", episode_number="98"
        - 「番組名 ★第3話「サブタイトル」」 → series_title="番組名", episode_number="3"
        - 「アニメ・彼女、お借りします4期▼第2話 サブタイトル」 → series_title="彼女、お借りします4期", episode_number="2"
        - 「バラエティ番組B」 → series_title="バラエティ番組B", episode_number=None
    """

    # ==================== 前処理 (正規化) 用パターン ====================

    # EPG 放送タグ: 番組の属性情報を示すタグを5種類の括弧スタイルで除去する
    # 対象: 字, 二, デ, 解, 多, S, 新, 終, 再, 無, SS, HV, P, W, 手, 初, 生, N, H,
    #       複, 双, 別, カ, 英, 韓, 中, 天, 擬, 吹, 撮, 録, 問, 画, 前, 後, 編, 回,
    #       全, 話, 映, CC, OP, B, S1, S2, S3, MV, D, 演, 移, 他, 収, 販, PPV,
    #       配, 料, 無料, 3D, 2K, 4K, 8K, HDR, SD, HC, 5.1, 7.1 など
    # Komorebi の TitleNormalizer.TAGS_PATTERN を参考に、網羅的にカバーする
    _BROADCAST_TAG_MARKS = (
        '字|二|デ|解|多|S|新|終|再|無|SS|HV|P|W|手|初|生|N|H|複|双|別|'
        'カ|英|韓|中|天|擬|吹|撮|録|問|画|前|後|編|回|全|話|映|CC|OP|B|'
        'S1|S2|S3|MV|D|演|移|他|収|販|PPV|配|料|無料|'
        '3D|2K|4K|8K|HDR|SD|HC|5\\.1|7\\.1|22\\.2|'
        '60P|120P|d|Hi-Res|Lossless|SHV|UHD|VOD'
    )
    BROADCAST_TAG_PATTERN = re.compile(
        # [字], [新], [4K], [5.1] など半角角括弧
        rf'\[(?:{_BROADCAST_TAG_MARKS})\]|'
        # (字), (二), (再) など半角丸括弧 (一部のみ: 誤検出を避けるため)
        r'\((字|二|デ|解|多|新|終|再|無|S)\)|'
        # （字）,（再）など全角丸括弧 (一部のみ)
        r'（(字|二|デ|解|多|新|終|再|無|S)）|'
        # 【新】, 【終】, 【無料】 など隅付き括弧
        r'【(新|終|再|初|字|二|デ|解|無料|生|録)】|'
        # ［新］, ［終］ など全角角括弧
        r'［(新|終|再|初|字|二|デ|解|無料|生|録)］'
    )

    # ジャンルプレフィックス (括弧型):
    #   「アニメ「番組名」」「映画「番組名」」のように、ジャンル名+括弧で番組名を囲む形式
    #   括弧の内側の文字列を抽出してジャンルプレフィックスを除去する
    GENRE_PREFIX_BRACKET_PATTERN = re.compile(
        r'^(?:映画|アニメ|連続テレビ小説|土曜ドラマ|ドラマ|特別番組|特番|新番組|最終回)'
        r'[「『](.*?)[」』]$'
    )

    # ジャンルプレフィックス (スペース型):
    #   「アニメ 番組名」のように、ジャンル名+スペースで区切る形式
    #   ジャンル名を除去してスペース以降の部分を残す
    GENRE_PREFIX_SPACE_PATTERN = re.compile(
        r'^(?:映画|アニメ|連続テレビ小説|土曜ドラマ|ドラマ|特別番組|特番|新番組|最終回)[\s]+'
    )

    # NHK の番組枠プレフィックス (隅付き括弧型):
    #   「【連続テレビ小説】番組名」「【夜ドラ】番組名」のように、番組枠名を隅付き括弧で囲む形式
    #   ※ 【推しの子】のように番組名そのものに使われるケースがあるため、
    #   既知の番組枠名のみを対象とする
    NHK_SLOT_PREFIX_PATTERN = re.compile(
        r'^【(?:連続テレビ小説|大河ドラマ|夜ドラ|よるドラ|土曜ドラマ|ドラマ10|アニメ)】\s*'
    )

    # 放送枠プレフィックス (山括弧):
    #   <ノイタミナ>, <アニメギルド> など放送枠名を示す山括弧プレフィックス
    #   半角山括弧 <> と全角山括弧 ＜＞ のみ除去する
    ANGLE_BRACKET_PREFIX_PATTERN = re.compile(r'^(?:<[^>]+>|＜[^＞]+＞)\s*')

    # 放送枠プレフィックス (中黒区切り):
    #   「アニメA・番組名」「アニメ・番組名」のような放送枠名・中黒区切りのプレフィックスを除去する
    SLOT_PREFIX_PATTERN = re.compile(r'^アニメ[A-Za-z]?・\s*')

    # 放送枠サフィックス:
    #   「番組名 AnichU」「番組名【ANiMAZiNG！！！】」「番組名 【アニメイズム】」のような放送枠サフィックスを除去する
    SLOT_SUFFIX_PATTERN = re.compile(
        r'\s*(?:AnichU|【ANiMAZiNG[!！]+】|【アニメイズム】)\s*$'
    )

    # ==================== エピソード番号・サブタイトル区切り検出用パターン ====================
    # Komorebi の EPISODE_SUBTITLE_PATTERN を参考に、エピソード番号やサブタイトルの
    # 開始位置を検出するパターンを定義する。最初にマッチした位置でタイトルを切断して
    # シリーズ名を抽出する (Komorebi と同じアプローチ)。

    # 漢数字を含む数値パターン (Komorebi の NUM 定数を参考)
    # 半角数字・全角数字・漢数字のいずれかにマッチする
    _NUM = r'[0-9０-９一二三四五六七八九十百千万零]+'

    # エピソード番号・サブタイトルの開始位置を検出するパターン (優先度順)
    # スペースの後に続くエピソード表記を検出する (タイトル本体の数字を誤検出しないようスペース必須)
    # re.search で最初のマッチ位置を取得し、そこでタイトルを切断する
    EPISODE_SUBTITLE_PATTERN = re.compile(
        # ---- スペースの後に続くエピソード表記 (スペース部分から切断) ----
        # 第N話, 第N回, 第N幕 (漢数字対応)
        rf'(?:[\s])(?:第{_NUM}[話回幕]?)'
        # N話, N回, N幕 (「第」なし、漢数字対応)
        rf'|(?:[\s])(?:{_NUM}[話回幕])'
        # #N, ##N (ハッシュ付き話数)
        rf'|(?:[\s])(?:#{{1,2}}{_NUM})'
        # ★第N話, ★#N (★区切り)
        rf'|(?:[\s])★\s*(?:第{_NUM}[話回幕]?|#{_NUM})'
        # (N), （N） (括弧付き話数 — スペース後)
        rf'|(?:[\s])(?:\({_NUM}\)|（{_NUM}）)'
        # EP.N, EPN, Episode N (英語表記)
        rf'|(?:[\s])(?:EP\.?\s*{_NUM}|Episode\s*{_NUM})'
        # Teil N (ドイツ語表記 — アルネの事件簿等)
        rf'|(?:[\s])(?:Teil\s*{_NUM})'
        # N投目, N本目 などの特殊カウンタ (Turkey! 等)
        rf'|(?:[\s])(?:{_NUM}(?:投目|本目|局目|戦目))'
        # 第N部 (パート)
        rf'|(?:[\s])第{_NUM}[部]'
        # ---- スペース不要のパターン ----
        # (N) 括弧付き話数 (スペースなし — 【連続テレビ小説】ばけばけ(98) 等)
        rf'|\({_NUM}\)'
        # #N (スペースなし — 番組名#3 のケース)
        rf'|#\d+'
        # ---- サブタイトル区切り文字 (スペースの後に括弧や記号で始まるサブタイトル) ----
        r'|(?:[\s])(?:[「『【＜〈])'
        # ▽, ▼ (NHKニュースのサブタイトル区切り)
        r'|[▽▼]'
        # ---- 末尾の裸の数字 (スペースの後) ----
        rf'|(?:[\s]){_NUM}$',
        re.IGNORECASE,
    )

    # エピソード番号を抽出するための個別パターン (マッチした部分文字列から話数を取得するために使用)
    # EPISODE_SUBTITLE_PATTERN でマッチした文字列に対して適用し、話数とサブタイトルを抽出する
    # サブタイトルの共通パターン (括弧で囲まれたサブタイトル、または残りのテキスト全体)
    # 括弧付き: 「サブタイトル」『サブタイトル』
    # 括弧なし: スペース区切りで残りのテキスト全体 (エピソード番号の後に続くテキスト)
    _SUBTITLE = r'(?:[「『](?P<subtitle>.+?)[」』]|(?P<subtitle_raw>.+))'

    EPISODE_EXTRACT_PATTERNS: list[re.Pattern[str]] = [
        # ★ 区切りで話数がある場合 (例: 「 ★第1話「バイト1日目」」)
        re.compile(
            r'^\s*★\s*(?:第(?P<episode>\d+(?:\.\d+)?)(?:話|回|夜)?|#(?P<episode2>\d+(?:\.\d+)?))'
            rf'\s*{_SUBTITLE}?\s*$'
        ),
        # 「第N話」「第N回」「第N夜」形式
        re.compile(
            r'^\s*第(?P<episode>\d+(?:\.\d+)?)(?:話|回|幕|夜)?'
            rf'\s*{_SUBTITLE}?\s*$'
        ),
        # 漢数字「第一話」「第二回」形式
        re.compile(
            r'^\s*第(?P<kanji_episode>[一二三四五六七八九十百千万零]+)(?:話|回|幕|夜)?'
            rf'\s*{_SUBTITLE}?\s*$'
        ),
        # 「#N」「##N」形式
        re.compile(
            r'^\s*#{1,2}(?P<episode>\d+(?:\.\d+)?)'
            r'(?:\s*-\s*#\d+(?:\.\d+)?)?'  # #01-#06 のような範囲指定は無視
            rf'\s*{_SUBTITLE}?\s*$'
        ),
        # 「(N)」「（N）」形式
        re.compile(
            r'^\s*[（(](?P<episode>\d+)[)）]'
            r'(?:\s*第\d+週)?'  # 連続テレビ小説の「(98)第20週」形式
            rf'\s*{_SUBTITLE}?\s*$'
        ),
        # 「EP.N」「Episode N」形式
        re.compile(
            r'^\s*(?:Episode\s+|Ep\.?\s*)(?P<episode>\d+(?:\.\d+)?)'
            rf'\s*{_SUBTITLE}?\s*$',
            re.IGNORECASE,
        ),
        # 「Teil N」形式 (ドイツ語)
        re.compile(
            r'^\s*Teil\s+(?P<episode>\d+(?:\.\d+)?)'
            rf'\s*{_SUBTITLE}?\s*$',
            re.IGNORECASE,
        ),
        # 「N投目」「N本目」形式
        re.compile(
            r'^\s*(?P<episode>\d+)(?:投目|本目|局目|戦目)'
            rf'\s*{_SUBTITLE}?\s*$'
        ),
        # 「N話」「N回」「N幕」形式 (「第」なし)
        re.compile(
            r'^\s*(?P<episode>\d+(?:\.\d+)?)(?:話|回|幕)'
            rf'\s*{_SUBTITLE}?\s*$'
        ),
        # 第N部
        re.compile(
            r'^\s*第(?P<episode>\d+)部\s*$'
        ),
        # サブタイトルのみ (括弧区切り)
        re.compile(
            r'^\s*[「『【＜〈](?P<subtitle>.+?)[」』】＞〉]?\s*$'
        ),
        # ▽▼ 以降のテキストをサブタイトルとして抽出
        re.compile(
            r'^\s*[▽▼]\s*(?P<subtitle>.+)\s*$'
        ),
    ]

    # ==================== 漢数字変換テーブル ====================

    _KANJI_TO_INT: dict[str, int] = {
        '零': 0, '一': 1, '二': 2, '三': 3, '四': 4,
        '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
        '十': 10, '百': 100, '千': 1000, '万': 10000,
    }

    # ==================== 類似タイトルマージ用パターン ====================

    # 類似タイトルの判定時に「別のシリーズ」とみなす差分パターン
    # 短いタイトルが長いタイトルの前方一致である場合、差分がこのパターンにマッチすると別シリーズとみなす
    # 例: 「ニュース」と「ニュース7」→ 差分「7」は数字のみなので別シリーズ
    # 例: 「ドラマA」と「ドラマA2」→ 差分「2」は数字のみなので別シリーズ (シーズン違い)
    DISTINCT_SUFFIX_PATTERN = re.compile(
        r'^'
        r'(?:'
        r'\d+(?:\.\d+)?'           # 数字のみ (例: "7", "2024", "3.5")
        r'|[IVXLCDM]+'            # ローマ数字 (例: "II", "III")
        r'|[A-Z]'                 # 1文字のアルファベット (例: "Z", "S")
        r'|[Ⅰ-Ⅻ]'               # ローマ数字記号 (例: "Ⅱ")
        r'|\([^)]+\)'             # 丸括弧で囲まれた注記 (例: "(岩手)", "(第2期)")
        r'|（[^）]+）'             # 全角丸括弧で囲まれた注記 (例: "（岩手）")
        r'|SP'                    # スペシャル略称 (例: "SP")
        r')'
        r'$'
    )

    @staticmethod
    def _kanjiToInt(kanji_str: str) -> int:
        """
        漢数字文字列を整数に変換する

        「一」→1, 「十二」→12, 「二十三」→23, 「百二十三」→123 などに対応する。
        万・千・百・十の位取りに基づく日本語の漢数字表記を解析する。

        Args:
            kanji_str: 漢数字文字列 (例: "十二", "二十三")

        Returns:
            int: 変換後の整数値
        """

        result = 0
        current = 0

        for char in kanji_str:
            value = TitleParser._KANJI_TO_INT.get(char, 0)
            if value >= 10:
                # 位取り文字 (十, 百, 千, 万) の場合
                if current == 0:
                    current = 1  # 「十」= 10 (暗黙の1)
                result += current * value
                current = 0
            else:
                # 数字 (一〜九, 零) の場合
                current = value

        # 最後の端数を加算 (例: 「十二」の「二」)
        result += current
        return result

    @staticmethod
    def _cleanTitle(title: str) -> str:
        """
        EPG タイトルから番組属性タグ・放送枠プレフィックス等のノイズを除去し、正規化したタイトルを返す

        Komorebi の TitleNormalizer.extractDisplayTitle() を参考にした正規化パイプライン:
            1. Unicode NFKC 正規化: 全角英数字→半角、互換文字の正規化
            2. 放送タグの除去: [字], (二), 【新】, ［再］ など5種類の括弧スタイル
            3. ジャンルプレフィックスの除去: アニメ「...」, アニメ , 【連続テレビ小説】 等
            4. 放送枠プレフィックス/サフィックスの除去: <ノイタミナ>, アニメA・, AnichU 等
            5. スペース正規化: 連続スペース→1つに統一

        Args:
            title: 正規化対象の EPG タイトル文字列

        Returns:
            str: 正規化後のタイトル文字列
        """

        # ステップ1: Unicode NFKC 正規化
        # 全角英数字→半角、全角スペース→半角スペース、互換文字の統一
        # これにより「番組名７」と「番組名7」が同一視されるようになる
        cleaned = unicodedata.normalize('NFKC', title.strip())

        # ステップ2: 放送タグの除去
        # [字], [新], [4K], (二), 【終】, ［再］ など5種類の括弧スタイルのタグを除去
        cleaned = TitleParser.BROADCAST_TAG_PATTERN.sub('', cleaned)

        # ステップ3: ジャンルプレフィックスの除去
        # NHK 番組枠: 【連続テレビ小説】, 【夜ドラ】 など隅付き括弧の番組枠名
        cleaned = TitleParser.NHK_SLOT_PREFIX_PATTERN.sub('', cleaned)
        # 括弧型: 「アニメ「番組名」」→「番組名」を抽出
        trimmed = cleaned.strip()
        bracket_match = TitleParser.GENRE_PREFIX_BRACKET_PATTERN.match(trimmed)
        if bracket_match:
            cleaned = bracket_match.group(1)
        else:
            # スペース型: 「アニメ 番組名」→「番組名」を抽出
            cleaned = TitleParser.GENRE_PREFIX_SPACE_PATTERN.sub('', trimmed)

        # ステップ4: 放送枠プレフィックスの除去
        # 山括弧: <ノイタミナ>, ＜放送枠名＞
        cleaned = TitleParser.ANGLE_BRACKET_PREFIX_PATTERN.sub('', cleaned)
        # 中黒区切り: アニメA・, アニメ・
        cleaned = TitleParser.SLOT_PREFIX_PATTERN.sub('', cleaned)

        # ステップ5: 放送枠サフィックスの除去
        # AnichU, 【ANiMAZiNG！！！】, 【アニメイズム】 など
        cleaned = TitleParser.SLOT_SUFFIX_PATTERN.sub('', cleaned)

        # ステップ6: スペースの正規化
        # 連続スペースを1つに統一
        cleaned = re.sub(r' {2,}', ' ', cleaned)

        # ステップ7: 先頭・末尾の不要な記号やスペースを除去
        cleaned = cleaned.strip()
        cleaned = re.sub(r'^[\s・-]+|[\s・-]+$', '', cleaned)

        return cleaned.strip()

    @staticmethod
    def parse(title: str) -> TitleParseResult:
        """
        番組タイトルを解析し、シリーズ名・話数・サブタイトルを抽出する

        Komorebi の extractDisplayTitle() と同様のアプローチで、
        正規化後のタイトルからエピソード番号/サブタイトルの開始位置を検出し、
        そこでタイトルを切断してシリーズ名を取得する。

        Args:
            title: 解析対象の番組タイトル文字列

        Returns:
            TitleParseResult: 解析結果を格納したデータクラス
                - series_title: シリーズ名 (常に非 None。タイトルが空の場合のみ None)
                - episode_number: 話数文字列 (先頭のゼロは除去される / 話数パターンがない場合は None)
                - subtitle: サブタイトル (存在しない場合は None)
        """

        # タイトルが空の場合は解析不能
        if not title or not title.strip():
            return TitleParseResult(series_title=None, episode_number=None, subtitle=None)

        # 前処理: EPG タイトルの正規化を行う
        cleaned_title = TitleParser._cleanTitle(title)

        # 前処理後にタイトルが空になった場合は解析不能
        if not cleaned_title:
            return TitleParseResult(series_title=None, episode_number=None, subtitle=None)

        # エピソード番号/サブタイトルの開始位置を検出する
        # EPISODE_SUBTITLE_PATTERN で最初にマッチした位置でタイトルを切断する
        match = TitleParser.EPISODE_SUBTITLE_PATTERN.search(cleaned_title)

        if match is None:
            # どのパターンにもマッチしなかった場合:
            # 正規化後のタイトル全体をシリーズ名として返す
            # これにより話数を持たない番組（バラエティ・ニュース・スポーツ等）も
            # 同じタイトル同士でシリーズとしてグループ化できる
            # 放送枠サフィックスの最終除去も適用する
            final_title = TitleParser.SLOT_SUFFIX_PATTERN.sub('', cleaned_title).strip()
            if not final_title:
                return TitleParseResult(series_title=None, episode_number=None, subtitle=None)
            return TitleParseResult(
                series_title=final_title,
                episode_number=None,
                subtitle=None,
            )

        # マッチ位置でタイトルを切断し、シリーズ名と残りの部分に分割する
        series_title = cleaned_title[:match.start()].strip()
        remainder = cleaned_title[match.start():].strip()

        # シリーズ名に残っている放送枠サフィックスを追加で除去する
        series_title = TitleParser.SLOT_SUFFIX_PATTERN.sub('', series_title).strip()

        # シリーズ名が空になった場合、タイトル全体をシリーズ名として扱う
        if not series_title:
            final_title = TitleParser.SLOT_SUFFIX_PATTERN.sub('', cleaned_title).strip()
            if not final_title:
                return TitleParseResult(series_title=None, episode_number=None, subtitle=None)
            return TitleParseResult(
                series_title=final_title,
                episode_number=None,
                subtitle=None,
            )

        # 残りの部分からエピソード番号とサブタイトルを抽出する
        episode_number: str | None = None
        subtitle: str | None = None

        for extract_pattern in TitleParser.EPISODE_EXTRACT_PATTERNS:
            extract_match = extract_pattern.match(remainder)
            if extract_match is None:
                continue

            groups = extract_match.groupdict()

            # 漢数字のエピソード番号を処理
            kanji_episode = groups.get('kanji_episode')
            if kanji_episode is not None:
                episode_number = str(TitleParser._kanjiToInt(kanji_episode))
            else:
                # 通常の数字エピソード番号
                episode_str = groups.get('episode') or groups.get('episode2')
                if episode_str is not None:
                    if '.' in episode_str:
                        episode_number = episode_str
                    else:
                        # 先頭ゼロを除去 (例: "03" → "3")
                        episode_number = str(int(episode_str))

            # サブタイトルを取得 (括弧付き subtitle が優先、なければ括弧なし subtitle_raw)
            sub = groups.get('subtitle') or groups.get('subtitle_raw')
            if sub is not None:
                sub = sub.strip()
                if sub:
                    subtitle = sub

            break

        # 先頭・末尾の不要な記号やスペースをシリーズ名から除去
        series_title = re.sub(r'^[\s・-]+|[\s・-]+$', '', series_title)

        if not series_title:
            return TitleParseResult(series_title=None, episode_number=None, subtitle=None)

        return TitleParseResult(
            series_title=series_title,
            episode_number=episode_number,
            subtitle=subtitle,
        )

    @staticmethod
    def buildSimilarTitleMapping(series_titles: list[str]) -> dict[str, str]:
        """
        シリーズタイトルのリストから、類似タイトルのマッピングを構築する

        前方一致で短いタイトルが長いタイトルに含まれる場合に、長いタイトルを短いタイトルに
        マージする。ただし、差分が数字のみ・ローマ数字・1文字アルファベットなど
        「シーズン番号や別番組を示す接尾辞」に該当する場合はマージしない。

        例 (マージされる):
            - 「番組A 〜特別編〜」→「番組A」にマージ
            - 「番組A スペシャル」→「番組A」にマージ
        例 (マージされない):
            - 「ニュース7」は「ニュース」にマージされない (差分が数字のみ)
            - 「ドラマA2」は「ドラマA」にマージされない (差分が数字のみ)
            - 「番組Z」は「番組」にマージされない (差分が1文字アルファベット)

        Args:
            series_titles: 全ユニークなシリーズタイトルのリスト

        Returns:
            dict[str, str]: 長いタイトル → マージ先の短いタイトルのマッピング
                マージ対象でないタイトルはマッピングに含まれない
        """

        # タイトルを長さの短い順にソートする
        # 短いタイトルから順に処理することで、最も短い (= 最も基本的な) タイトルが代表名になる
        sorted_titles = sorted(set(series_titles), key=len)
        merge_map: dict[str, str] = {}

        for i, short_title in enumerate(sorted_titles):
            # 既に他のタイトルにマージされている場合はスキップ
            if short_title in merge_map:
                continue
            # 短すぎるタイトルは前方一致で誤マージしやすいため対象外とする
            # 例: 2文字の「映画」が「映画館へ行こう」にマージされるのを防ぐ
            if len(short_title) < 3:
                continue
            for j in range(i + 1, len(sorted_titles)):
                long_title = sorted_titles[j]
                # 既に他のタイトルにマージされている場合はスキップ
                if long_title in merge_map:
                    continue
                # 前方一致チェック: 長いタイトルが短いタイトルで始まるか
                if not long_title.startswith(short_title):
                    continue
                # 差分部分を取得する (短いタイトルより後の部分)
                suffix = long_title[len(short_title):]
                # 差分の前後の空白を除去する
                suffix_stripped = suffix.strip()
                # 差分が空の場合はまったく同じタイトルなのでスキップ (ここには到達しないはず)
                if not suffix_stripped:
                    continue
                # 差分が「別シリーズを示す接尾辞」に該当する場合はマージしない
                if TitleParser.DISTINCT_SUFFIX_PATTERN.match(suffix_stripped):
                    continue
                # 差分の先頭がスペースや記号でなく、短いタイトルと差分が連結している場合:
                # 短いタイトルの最後が漢字/カタカナ/ひらがなで、差分の先頭も漢字/カタカナ/ひらがなの場合、
                # 単語の途中で切れている可能性が高いためマージしない
                # 例: 「相棒」と「相棒season」→ 差分「season」はアルファベットなのでOK→マージ
                # 例: 「報道」と「報道特集」→ 差分「特集」の先頭が日本語→単語途中の可能性→マージしない
                if suffix == suffix_stripped:  # 差分の前にスペースがない場合
                    # 短いタイトルの末尾文字を取得
                    last_char = short_title[-1]
                    first_suffix_char = suffix_stripped[0]
                    # 短いタイトル末尾と差分先頭の両方が日本語文字の場合、単語の途中で切れている可能性がある
                    if (re.match(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', last_char) and
                        re.match(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', first_suffix_char)):
                        continue
                # ここまで到達した場合、長いタイトルを短いタイトルにマージする
                merge_map[long_title] = short_title

        return merge_map
