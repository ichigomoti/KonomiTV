<template>
    <div class="route-container">
        <HeaderBar />
        <main>
            <Navigation />
            <div class="series-list-container-wrapper">
                <SPHeaderBar />
                <div class="series-list-container">
                    <Breadcrumbs :crumbs="[
                        { name: 'ホーム', path: '/' },
                        { name: 'ビデオをみる', path: '/videos/' },
                        { name: 'シリーズ一覧', path: '/videos/series', disabled: true },
                    ]" />
                    <!-- ヘッダー: タイトル・件数・ソート -->
                    <div class="series-list__header">
                        <h2 class="series-list__title">
                            <div v-ripple class="series-list__title-back" @click="$router.back()">
                                <Icon icon="fluent:chevron-left-12-filled" width="27px" />
                            </div>
                            <span class="series-list__title-text">シリーズ一覧</span>
                            <div class="series-list__title-count">{{ total }}件</div>
                        </h2>
                        <div class="series-list__actions">
                            <v-btn class="series-list__create-btn" color="primary" variant="flat" size="small"
                                @click="openCreateDialog">
                                <Icon icon="fluent:add-20-regular" width="18px" height="18px" />
                                <span class="ml-1">シリーズを作成</span>
                            </v-btn>
                            <v-select class="series-list__sort" color="primary" bg-color="background-lighten-1"
                                variant="solo" density="comfortable" hide-details
                                :items="sort_options" v-model="sort_order"
                                @update:model-value="updateSortOrder">
                            </v-select>
                        </div>
                    </div>
                    <!-- シリーズカードグリッド -->
                    <div class="series-list__grid"
                        :class="{
                            'series-list__grid--loading': is_loading,
                            'series-list__grid--empty': total === 0 && !is_loading,
                        }">
                        <!-- 空状態 -->
                        <div class="series-list__empty"
                            :class="{'series-list__empty--show': total === 0 && !is_loading}">
                            <div class="series-list__empty-content">
                                <Icon class="series-list__empty-icon" icon="fluent:video-clip-multiple-16-regular"
                                    width="54px" height="54px" />
                                <h2>シリーズがありません</h2>
                                <div class="series-list__empty-submessage">
                                    録画番組のメタデータが解析されると、<br class="d-sm-none">シリーズが自動的に作成されます。
                                </div>
                            </div>
                        </div>
                        <!-- カードリスト -->
                        <div class="series-list__grid-content">
                            <router-link class="series-card" v-for="s in series_list" :key="s.id"
                                :to="`/videos/series/${s.id}`">
                                <div class="series-card__thumbnail">
                                    <img v-if="getLatestProgram(s)" loading="lazy"
                                        :src="`${Utils.api_base_url}/videos/${getLatestProgram(s)!.id}/thumbnail`" />
                                    <span class="series-card__episode-badge">
                                        {{ getTotalEpisodeCount(s) }}件
                                    </span>
                                </div>
                                <div class="series-card__content">
                                    <span class="series-card__title">{{ s.title }}</span>
                                    <span class="series-card__description" v-if="s.description">
                                        {{ s.description }}
                                    </span>
                                    <div class="series-card__meta">
                                        <span class="series-card__channel" v-if="getLatestPeriod(s)">
                                            {{ getLatestPeriod(s)!.channel.name }}
                                        </span>
                                        <span class="series-card__genres" v-if="s.genres.length > 0">
                                            {{ s.genres.map(g => g.major).join(' / ') }}
                                        </span>
                                    </div>
                                </div>
                            </router-link>
                        </div>
                    </div>
                    <!-- ページネーション -->
                    <div class="series-list__pagination" v-if="total > 0 && !is_loading">
                        <v-pagination v-model="current_page" active-color="primary" density="comfortable"
                            :length="Math.ceil(total / 30)" :total-visible="Utils.isSmartphoneVertical() ? 5 : 7"
                            @update:model-value="updatePage">
                        </v-pagination>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <!-- シリーズ作成ダイアログ -->
    <v-dialog max-width="550" v-model="show_create_dialog">
        <v-card>
            <v-card-title class="d-flex justify-center pt-6 font-weight-bold">シリーズを作成</v-card-title>
            <v-card-text class="pt-4 pb-0">
                <v-text-field v-model="create_title" label="シリーズ名" variant="outlined" density="comfortable"
                    hide-details @keydown.enter="createSeries" autofocus />
            </v-card-text>
            <v-card-actions class="pt-4 px-6 pb-6">
                <v-spacer></v-spacer>
                <v-btn color="text" variant="text" @click="show_create_dialog = false">
                    <Icon icon="fluent:dismiss-20-regular" width="18px" height="18px" />
                    <span class="ml-1">キャンセル</span>
                </v-btn>
                <v-btn class="px-3" color="primary" variant="flat" @click="createSeries"
                    :disabled="!create_title.trim()">
                    <Icon icon="fluent:add-20-regular" width="18px" height="18px" />
                    <span class="ml-1">作成する</span>
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>
<script lang="ts" setup>

import { onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import Breadcrumbs from '@/components/Breadcrumbs.vue';
import HeaderBar from '@/components/HeaderBar.vue';
import Navigation from '@/components/Navigation.vue';
import SPHeaderBar from '@/components/SPHeaderBar.vue';
import Message from '@/message';
import SeriesService, { ISeries, ISeriesBroadcastPeriod } from '@/services/Series';
import useUserStore from '@/stores/UserStore';
import Utils from '@/utils';

// ルーター
const route = useRoute();
const router = useRouter();

// シリーズのリスト
const series_list = ref<ISeries[]>([]);
const total = ref(0);
const is_loading = ref(true);

// 現在のページ番号
const current_page = ref(1);

// シリーズ作成ダイアログ
const show_create_dialog = ref(false);
const create_title = ref('');

// ソート順
const sort_order = ref<'desc' | 'asc'>('desc');
const sort_options = [
    { title: '新しい順', value: 'desc' as const },
    { title: '古い順', value: 'asc' as const },
];

// ==================== データ取得 ====================

// シリーズ一覧を取得する
const fetchSeries = async () => {
    const result = await SeriesService.fetchSeriesList(sort_order.value, current_page.value);
    if (result) {
        series_list.value = result.series_list;
        total.value = result.total;
    }
    is_loading.value = false;
};

// ==================== ユーティリティ ====================

// シリーズの最新放送期間を取得する
const getLatestPeriod = (s: ISeries): ISeriesBroadcastPeriod | null => {
    if (s.broadcast_periods.length === 0) return null;
    return s.broadcast_periods[s.broadcast_periods.length - 1];
};

// シリーズの最新エピソード (サムネイル用) を取得する
const getLatestProgram = (s: ISeries) => {
    const period = getLatestPeriod(s);
    if (!period || period.recorded_programs.length === 0) return null;
    return period.recorded_programs[period.recorded_programs.length - 1];
};

// シリーズの全エピソード数を算出する
const getTotalEpisodeCount = (s: ISeries): number => {
    return s.broadcast_periods.reduce(
        (sum, period) => sum + period.recorded_programs.length, 0,
    );
};

// ==================== シリーズ作成 ====================

// シリーズ作成ダイアログを開く
const openCreateDialog = () => {
    create_title.value = '';
    show_create_dialog.value = true;
};

// シリーズを作成する
const createSeries = async () => {
    if (!create_title.value.trim()) return;
    show_create_dialog.value = false;
    const result = await SeriesService.createSeries(create_title.value.trim());
    if (result !== null) {
        Message.success('シリーズを作成しました。');
        // 作成したシリーズの詳細画面に遷移
        router.push(`/videos/series/${result.id}`);
    }
};

// ==================== ページ / ソート更新 ====================

// ページを更新する
const updatePage = async (page: number) => {
    current_page.value = page;
    is_loading.value = true;
    await router.replace({
        query: {
            ...route.query,
            page: page.toString(),
        },
    });
};

// ソート順を更新する
const updateSortOrder = async () => {
    current_page.value = 1;
    is_loading.value = true;
    await router.replace({
        query: {
            ...route.query,
            order: sort_order.value,
            page: '1',
        },
    });
};

// ==================== ルート変更の監視 ====================

// クエリパラメータが変更されたらシリーズを再取得する
watch(() => route.query, async (newQuery) => {
    if (newQuery.page) {
        current_page.value = parseInt(newQuery.page as string);
    }
    if (newQuery.order) {
        sort_order.value = newQuery.order as 'desc' | 'asc';
    }
    await fetchSeries();
}, { deep: true });

// ==================== 初期化 ====================

onMounted(async () => {
    // 事前にログイン状態を同期
    const userStore = useUserStore();
    await userStore.fetchUser();

    // クエリパラメータから初期値を設定
    if (route.query.page) {
        current_page.value = parseInt(route.query.page as string);
    }
    if (route.query.order) {
        sort_order.value = route.query.order as 'desc' | 'asc';
    }

    // シリーズ一覧を取得
    await fetchSeries();
});

</script>
<style lang="scss" scoped>

.series-list-container-wrapper {
    display: flex;
    flex-direction: column;
    width: 100%;
}

.series-list-container {
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100%;
    padding: 20px;
    margin: 0 auto;
    min-width: 0;
    max-width: 1000px;
    @include smartphone-horizontal {
        padding: 16px 20px !important;
    }
    @include smartphone-horizontal-short {
        padding: 16px 16px !important;
    }
    @include smartphone-vertical {
        padding: 16px 8px !important;
        padding-top: 8px !important;
    }
}

// ヘッダー (RecordedProgramList のヘッダーパターンに準拠)
.series-list__header {
    display: flex;
    align-items: center;
    @include smartphone-vertical {
        // スマホ縦画面ではタイトル行とアクション行を2段に折り返す
        flex-wrap: wrap;
        padding: 0px 8px;
    }
}

.series-list__title {
    display: flex;
    align-items: center;
    position: relative;
    // 親の .series-list__header が display: flex のため、min-width: 0 がないと
    // タイトルテキストの長さに引きずられて親コンテナからはみ出してしまう
    min-width: 0;
    font-size: 24px;
    font-weight: 700;
    padding-top: 8px;
    padding-bottom: 20px;
    @include smartphone-vertical {
        font-size: 22px;
        padding-bottom: 8px;
    }

    &-text {
        white-space: nowrap;
    }

    &-back {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
        margin-right: 4px;
        margin-left: -6px;
        border-radius: 50%;
        cursor: pointer;
    }

    &-count {
        display: flex;
        align-items: center;
        flex-shrink: 0;
        padding-top: 8px;
        margin-left: 12px;
        font-size: 14px;
        font-weight: 400;
        color: rgb(var(--v-theme-text-darken-1));
    }
}

.series-list__actions {
    display: flex;
    align-items: center;
    margin-left: auto;
    @include smartphone-vertical {
        // 2段目に配置し、右端に寄せる
        padding-bottom: 12px;
    }
    :deep(.v-field) {
        padding-right: 4px !important;
    }
    :deep(.v-field__input) {
        padding-left: 12px !important;
        padding-right: 0px !important;
    }
}

.series-list__create-btn {
    margin-right: 8px;
    font-size: 13px;
    @include smartphone-vertical {
        margin-right: 6px;
    }
}

.series-list__sort {
    width: 103px;
    :deep(.v-field__input) {
        font-size: 14px !important;
        padding-top: 6px !important;
        padding-bottom: 6px !important;
        min-height: unset !important;
    }
}

// シリーズカードグリッド
.series-list__grid {
    position: relative;
    width: 100%;
    background: rgb(var(--v-theme-background-lighten-1));
    border-radius: 8px;
    overflow: hidden;

    &--loading {
        .series-list__grid-content {
            visibility: hidden;
            opacity: 0;
        }
    }
    &--empty {
        min-height: 200px;
    }
}

.series-list__grid-content {
    display: flex;
    flex-direction: column;
    transition: visibility 0.2s ease, opacity 0.2s ease;
}

// 空状態
.series-list__empty {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    padding-top: 28px;
    padding-bottom: 40px;
    flex-grow: 1;
    visibility: hidden;
    opacity: 0;
    transition: visibility 0.2s ease, opacity 0.2s ease;

    &--show {
        visibility: visible;
        opacity: 1;
    }

    &-content {
        text-align: center;

        .series-list__empty-icon {
            color: rgb(var(--v-theme-text-darken-1));
        }

        h2 {
            font-size: 21px;
            @include smartphone-vertical {
                font-size: 19px !important;
                text-align: center;
            }
        }

        .series-list__empty-submessage {
            margin-top: 8px;
            color: rgb(var(--v-theme-text-darken-1));
            font-size: 15px;
            @include smartphone-vertical {
                font-size: 13px !important;
                text-align: center;
                line-height: 1.65;
            }
        }
    }
}

// シリーズカード (RecordedProgram.vue の横長カードパターンに準拠)
.series-card {
    display: flex;
    width: 100%;
    height: 125px;
    padding: 0px 16px;
    text-decoration: none;
    color: rgb(var(--v-theme-text));
    cursor: pointer;
    transition: background-color 0.15s ease;
    @include smartphone-vertical {
        height: auto;
        padding: 0px 9px;
    }

    &:hover {
        background-color: rgb(var(--v-theme-background-lighten-2));
    }

    & + .series-card {
        border-top: 1px solid rgb(var(--v-theme-background));
    }

    &__thumbnail {
        position: relative;
        flex-shrink: 0;
        width: 178px;
        aspect-ratio: 16 / 9;
        margin: 12px 0;
        border-radius: 5px;
        overflow: hidden;
        background: linear-gradient(150deg, rgb(var(--v-theme-gray)), rgb(var(--v-theme-background-lighten-2)));
        @include smartphone-vertical {
            width: 130px;
            margin: 9px 0;
        }

        img {
            display: block;
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
    }

    &__episode-badge {
        position: absolute;
        bottom: 4px;
        right: 4px;
        padding: 2px 6px;
        border-radius: 4px;
        background: rgba(0, 0, 0, 0.75);
        color: #ffffff;
        font-size: 11.5px;
        font-weight: 600;
    }

    &__content {
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 4px;
        padding: 12px 14px;
        min-width: 0;
        flex: 1;
        @include smartphone-vertical {
            padding: 9px 10px;
        }
    }

    &__title {
        font-size: 15px;
        font-weight: bold;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        @include smartphone-vertical {
            font-size: 14px;
            white-space: normal;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
        }
    }

    &__description {
        font-size: 13px;
        color: rgb(var(--v-theme-text-darken-1));
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        @include smartphone-vertical {
            display: none;
        }
    }

    &__meta {
        display: flex;
        gap: 8px;
        font-size: 12.5px;
        color: rgb(var(--v-theme-text-darken-1));
    }

    &__channel {
        font-weight: 500;
    }
}

// ページネーション
.series-list__pagination {
    display: flex;
    justify-content: center;
    margin-top: 24px;
    @include smartphone-vertical {
        margin-top: 20px;
    }
}

</style>
