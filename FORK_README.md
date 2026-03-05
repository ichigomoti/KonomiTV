# KonomiTV Custom Fork

[本家 KonomiTV](https://github.com/tsukumijima/KonomiTV) をベースに、シリーズ管理機能の大幅拡張・キャプチャギャラリー・ログイン必須設定など、いくつかのカスタム機能を追加したフォークです。

> **本家 KonomiTV について**: いろいろな場所とデバイスでテレビと録画を快適に見れる、モダンな Web ベースのソフトウェアです。
> 開発者: [tsukumijima](https://github.com/tsukumijima) / ライセンス: MIT

---

## 追加機能の概要

### 1. シリーズ自動グルーピング

録画番組のメタデータが解析されると、番組タイトルを自動解析してシリーズ（番組グループ）を自動的に作成します。

- **TitleParser**: 番組タイトルから作品名・話数・サブタイトルを高精度に抽出するパーサー
  - 「〇〇 第3話」「〇〇 #03 サブタイトル」「〇〇（5）」など多様なフォーマットに対応
  - 半角/全角・括弧の揺れなども正規化して正確にグルーピング
- **自動シリーズ作成**: 録画スキャン時に同一作品の番組を自動的にシリーズにまとめる
- **放送期間ごとの整理**: 同じシリーズでもチャンネルや放送期間が異なる場合は別ブロックとして表示

### 2. シリーズ手動管理

自動グルーピングで完全にまとめきれない場合に、手動でシリーズを整理できます。

| 機能 | 説明 |
|------|------|
| **シリーズ作成** | 任意の名前で空のシリーズを新規作成 |
| **シリーズ名変更** | 既存シリーズのタイトルを編集 |
| **番組追加** | 検索して任意の録画番組をシリーズに追加 |
| **番組除外** | シリーズから個別の番組を除外（録画自体は削除されない） |
| **シリーズ削除** | シリーズを削除（紐付け解除のみ、録画番組は残る） |

- 手動で編集したシリーズには `is_series_manually_edited` フラグが自動的にセットされ、次回の自動スキャンで上書きされることを防ぎます。

### 3. シリーズ結合（マージ）

分かれてしまったシリーズ同士を1つに統合できます。

- シリーズ詳細画面のマージボタンから、マージ先シリーズを検索して選択
- マージ元の全録画番組がマージ先に移動し、マージ元シリーズは自動削除
- マージ先シリーズに自動遷移

### 4. キャプチャギャラリー

テレビ視聴中・録画再生中にキャプチャした画像を一覧・検索・整理できるギャラリー機能を追加しました。

#### ギャラリー画面

- **グリッド表示**: デスクトップ 4列 / タブレット 3列 / スマートフォン 2列のレスポンシブレイアウト
- **ソート**: 新しい順 / 古い順の切り替え
- **検索**: ファイル名・番組タイトル・チャンネル名で横断検索
- **ライトボックス**: サムネイルクリックで拡大表示、メタデータ（画像サイズ・ファイルサイズ・撮影日時）も確認可能
- **ページネーション**: 1ページ36件ずつ表示

#### フォルダ管理

キャプチャを仮想フォルダで整理できます（ファイルの物理的な移動は行わず、DB 上のブックマークで管理）。

| 機能 | 説明 |
|------|------|
| **フォルダ作成** | 任意の名前でフォルダを新規作成 |
| **フォルダ名変更** | 右クリックメニューからフォルダ名を編集 |
| **フォルダ削除** | フォルダを削除（キャプチャ画像自体は残る） |
| **キャプチャ追加** | ギャラリーからキャプチャをフォルダに追加（複数選択対応） |
| **キャプチャ除外** | フォルダからキャプチャを除外（画像自体は削除されない） |
| **複数フォルダ所属** | 1つのキャプチャを複数のフォルダに入れられる（タグのような運用が可能） |

#### 一括操作

- 右クリックで選択モードに入り、複数キャプチャを一括選択
- 選択したキャプチャをまとめてフォルダに追加・フォルダから除外・削除

#### キャプチャ設定

設定画面（設定 → キャプチャ）から以下を設定可能:

- **保存モード**: ブラウザダウンロード / サーバーアップロード / 両方
- **字幕合成モード**: 映像のみ / 字幕合成 / 両方
- **ファイル名パターン**: TVTest 互換マクロ展開（`%date%`, `%channel-name%`, `%event-name%` など）
- **クリップボードコピー**: キャプチャ時にクリップボードにもコピー

#### EXIF メタデータ

キャプチャ画像の EXIF に番組情報（タイトル・チャンネル・放送日時・字幕テキストなど）が JSON 形式で埋め込まれます。ギャラリーでの検索やメタデータ表示に活用されます。

### 5. ログイン必須設定

KonomiTV にアクセスする際にログインを必須にするサーバー設定を追加しました。

- **設定画面**: サーバー設定 → 「ログインを必須にする」スイッチで ON/OFF
- **動作**: 有効時、未ログインユーザーはすべてのページでログイン画面にリダイレクトされる
- **リダイレクト対応**: ログイン後、元々アクセスしようとしていたページに自動的に戻る

### 6. モバイルレスポンシブ対応

シリーズ一覧・シリーズ詳細画面をスマートフォン縦画面で快適に使えるようにレイアウトを最適化しました。

- **シリーズ詳細**: タイトルとアクションボタンが2行に分かれて表示、エピソード件数も画面内に収まる
- **シリーズ一覧**: タイトル行とアクション行が2段に折り返し、「シリーズ一覧」テキストが改行されない

---

## 追加・拡張した API

### シリーズ関連

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/api/series` | シリーズ一覧取得（ソート・ページネーション対応） |
| GET | `/api/series/{series_id}` | シリーズ詳細取得 |
| GET | `/api/series/search` | シリーズ検索 |
| POST | `/api/series` | シリーズ新規作成 |
| PUT | `/api/series/{series_id}` | シリーズ名変更 |
| DELETE | `/api/series/{series_id}` | シリーズ削除 |
| POST | `/api/series/{series_id}/programs/{program_id}` | シリーズに番組追加 |
| DELETE | `/api/series/{series_id}/programs/{program_id}` | シリーズから番組除外 |
| POST | `/api/series/{source_id}/merge/{target_id}` | シリーズ結合（source → target） |

### キャプチャギャラリー関連

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/api/captures` | キャプチャ一覧取得（ソート・ページネーション・検索対応） |
| GET | `/api/captures/{filename}` | キャプチャ画像取得（サムネイル生成対応） |
| POST | `/api/captures` | キャプチャ画像アップロード |
| DELETE | `/api/captures/{filename}` | キャプチャ画像削除 |
| GET | `/api/captures/folders` | フォルダ一覧取得 |
| POST | `/api/captures/folders` | フォルダ新規作成 |
| PUT | `/api/captures/folders/{folder_id}` | フォルダ名変更・並び順変更 |
| DELETE | `/api/captures/folders/{folder_id}` | フォルダ削除（画像は残る） |
| GET | `/api/captures/folders/{folder_id}/captures` | フォルダ内キャプチャ一覧取得 |
| POST | `/api/captures/folders/{folder_id}/captures` | フォルダにキャプチャ追加 |
| DELETE | `/api/captures/folders/{folder_id}/captures` | フォルダからキャプチャ除外 |

---

## インストール方法

### 方法 A: 本家 KonomiTV からの移行（推奨）

既に本家 KonomiTV がインストール済みの場合、ソースコードを差し替えるだけで移行できます。

```bash
# 1. KonomiTV サーバーを停止する

# 2. このフォークのソースコードをダウンロード
git clone -b custom-features https://github.com/ichigomoti/KonomiTV.git KonomiTV-custom

# 3. サーバー側のソースを差し替え (既存の server/app/ を上書き)
#    ※ server/data/ や server/thirdparty/ は既存のものをそのまま使う
cp -r KonomiTV-custom/server/app/ <KonomiTVインストール先>/server/app/

# 4. クライアントをビルド
cd <KonomiTVインストール先>/client
cp -r KonomiTV-custom/client/src/ ./src/
cp KonomiTV-custom/client/package.json ./package.json
yarn install --ignore-engines
yarn build

# 5. DB マイグレーションを実行
cd <KonomiTVインストール先>/server
poetry run python -m aerich upgrade

# 6. KonomiTV サーバーを再起動
```

### 方法 B: 新規インストール

1. 本家 KonomiTV のインストーラーで通常通りインストール
2. 上記の「方法 A」の手順 2〜6 を実行してソースを差し替え

---

## 本家からのアップデート取り込み

本家 KonomiTV のマスターブランチに更新が来た場合、以下の手順で取り込めます。

```bash
cd KonomiTV-fork

# 本家の最新を取得
git fetch upstream

# 本家の更新を自分のブランチにマージ
git checkout custom-features
git merge upstream/master

# コンフリクト（競合）が発生した場合は手動で解消
# 解消後:
git add .
git commit -m "merge: upstream/master の変更を取り込み"
git push origin custom-features
```

---

## 変更ファイル一覧

<details>
<summary>クリックで展開</summary>

### サーバー側 (Python)

| ファイル | 変更内容 |
|---------|---------|
| `server/app/config.py` | `require_login` 設定フィールドの追加 |
| `server/app/metadata/TitleParser.py` | **[新規]** 番組タイトル解析パーサー |
| `server/app/metadata/RecordedScanTask.py` | シリーズ自動グルーピングロジックの追加 |
| `server/app/models/Series.py` | シリーズモデルの拡張 |
| `server/app/models/SeriesBroadcastPeriod.py` | 放送期間モデルの拡張 |
| `server/app/models/RecordedProgram.py` | `is_series_manually_edited` フラグ追加 |
| `server/app/routers/SeriesRouter.py` | シリーズ CRUD + マージ API の追加 |
| `server/app/routers/CapturesRouter.py` | キャプチャギャラリー API の拡張（フォルダ CRUD・検索・サムネイル） |
| `server/app/models/CaptureFolder.py` | **[新規]** キャプチャフォルダモデル |
| `server/app/models/CaptureBookmark.py` | **[新規]** キャプチャブックマーク（フォルダ紐付け）モデル |
| `server/app/schemas.py` | シリーズ・キャプチャ関連スキーマの追加 |
| `server/app/migrations/models/8_*.py` | **[新規]** シリーズ関連 DB マイグレーション |
| `server/app/migrations/models/9_*.py` | **[新規]** 追加マイグレーション |

### クライアント側 (TypeScript / Vue)

| ファイル | 変更内容 |
|---------|---------|
| `client/src/views/Videos/Series.vue` | **[新規]** シリーズ一覧ページ |
| `client/src/views/Videos/SeriesDetail.vue` | **[新規]** シリーズ詳細ページ (編集・マージ UI 含む) |
| `client/src/views/Captures.vue` | **[新規]** キャプチャギャラリーページ（一覧・検索・フォルダ・ライトボックス） |
| `client/src/views/Settings/Capture.vue` | **[新規]** キャプチャ設定ページ |
| `client/src/services/Captures.ts` | キャプチャ API クライアント（アップロード・フォルダ CRUD） |
| `client/src/services/Series.ts` | シリーズ API クライアント (CRUD + マージ) |
| `client/src/services/Settings.ts` | `require_login` フィールド追加 |
| `client/src/views/Settings/Server.vue` | ログイン必須設定の v-switch 追加 |
| `client/src/services/player/managers/CaptureManager.ts` | EXIF メタデータ埋め込み・サーバーアップロード対応 |
| `client/src/router/index.ts` | キャプチャギャラリールート追加・ログイン必須 `beforeEach` ガード追加 |
| `client/src/views/Login.vue` | リダイレクト対応 |
| `client/src/components/Videos/RecordedProgramList.vue` | シリーズ向け表示対応 |

</details>

---

## ライセンス

本家 KonomiTV と同じく [MIT License](License.txt) です。

Copyright (c) 2021-2026 [tsukumijima](https://github.com/tsukumijima) (本家)
カスタム機能の追加: [ichigomoti](https://github.com/ichigomoti)
