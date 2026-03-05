# KonomiTV Custom Fork

[本家 KonomiTV](https://github.com/tsukumijima/KonomiTV) をベースに、シリーズ管理機能の大幅拡張やログイン必須設定など、いくつかのカスタム機能を追加したフォークです。

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

### 4. ログイン必須設定

KonomiTV にアクセスする際にログインを必須にするサーバー設定を追加しました。

- **設定画面**: サーバー設定 → 「ログインを必須にする」スイッチで ON/OFF
- **動作**: 有効時、未ログインユーザーはすべてのページでログイン画面にリダイレクトされる
- **リダイレクト対応**: ログイン後、元々アクセスしようとしていたページに自動的に戻る

### 5. モバイルレスポンシブ対応

シリーズ一覧・シリーズ詳細画面をスマートフォン縦画面で快適に使えるようにレイアウトを最適化しました。

- **シリーズ詳細**: タイトルとアクションボタンが2行に分かれて表示、エピソード件数も画面内に収まる
- **シリーズ一覧**: タイトル行とアクション行が2段に折り返し、「シリーズ一覧」テキストが改行されない

---

## シリーズ関連の API

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
| `server/app/schemas.py` | シリーズ関連スキーマの追加 |
| `server/app/migrations/models/8_*.py` | **[新規]** シリーズ関連 DB マイグレーション |
| `server/app/migrations/models/9_*.py` | **[新規]** 追加マイグレーション |

### クライアント側 (TypeScript / Vue)

| ファイル | 変更内容 |
|---------|---------|
| `client/src/views/Videos/Series.vue` | **[新規]** シリーズ一覧ページ |
| `client/src/views/Videos/SeriesDetail.vue` | **[新規]** シリーズ詳細ページ (編集・マージ UI 含む) |
| `client/src/services/Series.ts` | シリーズ API クライアント (CRUD + マージ) |
| `client/src/services/Settings.ts` | `require_login` フィールド追加 |
| `client/src/views/Settings/Server.vue` | ログイン必須設定の v-switch 追加 |
| `client/src/router/index.ts` | ログイン必須時の `beforeEach` ガード追加 |
| `client/src/views/Login.vue` | リダイレクト対応 |
| `client/src/components/Videos/RecordedProgramList.vue` | シリーズ向け表示対応 |

</details>

---

## ライセンス

本家 KonomiTV と同じく [MIT License](License.txt) です。

Copyright (c) 2021-2026 [tsukumijima](https://github.com/tsukumijima) (本家)
カスタム機能の追加: [ichigomoti](https://github.com/ichigomoti)
