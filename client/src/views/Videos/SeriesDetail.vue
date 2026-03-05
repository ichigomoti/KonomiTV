<template>
    <div class="route-container">
        <HeaderBar />
        <main>
            <Navigation />
            <div class="series-detail-container-wrapper">
                <SPHeaderBar />
                <div class="series-detail-container">
                    <Breadcrumbs :crumbs="[
                        { name: 'ホーム', path: '/' },
                        { name: 'ビデオをみる', path: '/videos/' },
                        { name: 'シリーズ一覧', path: '/videos/series' },
                        { name: series ? series.title : '読み込み中…', path: '', disabled: true },
                    ]" />
                    <!-- ローディング中 -->
                    <div class="series-detail__loading" v-if="is_loading">
                        <Icon icon="line-md:loading-twotone-loop" width="50px" />
                    </div>
                    <!-- シリーズが見つからなかった場合 -->
                    <div class="series-detail__empty" v-else-if="!series">
                        <Icon class="series-detail__empty-icon" icon="fluent:video-clip-multiple-16-regular"
                            width="54px" height="54px" />
                        <h2>シリーズが見つかりません</h2>
                        <div class="series-detail__empty-submessage">
                            指定されたシリーズは存在しないか、<br class="d-sm-none">削除された可能性があります。
                        </div>
                    </div>
                    <!-- シリーズ詳細 -->
                    <template v-else>
                        <!-- シリーズヘッダー -->
                        <div class="series-detail__header">
                            <h2 class="series-detail__title">
                                <div v-ripple class="series-detail__title-back" @click="$router.back()">
                                    <Icon icon="fluent:chevron-left-12-filled" width="27px" />
                                </div>
                                <span class="series-detail__title-text">{{ series.title }}</span>
                                <div v-ripple class="series-detail__title-action" @click="openRenameDialog"
                                    v-ftooltip="'シリーズ名を編集'">
                                    <Icon icon="fluent:edit-16-regular" width="18px" />
                                </div>
                                <div v-ripple class="series-detail__title-action" @click="openAddProgramDialog"
                                    v-ftooltip="'番組を追加'">
                                    <Icon icon="fluent:add-16-regular" width="18px" />
                                </div>
                                <div v-ripple class="series-detail__title-action" @click="openMergeDialog"
                                    v-ftooltip="'シリーズを結合'">
                                    <Icon icon="fluent:merge-20-regular" width="18px" />
                                </div>
                                <div v-ripple class="series-detail__title-action series-detail__title-action--danger"
                                    @click="openDeleteDialog" v-ftooltip="'シリーズを削除'">
                                    <Icon icon="fluent:delete-16-regular" width="18px" />
                                </div>
                                <div class="series-detail__title-count">{{ totalEpisodeCount }}件</div>
                            </h2>
                        </div>
                        <!-- シリーズ概要情報 -->
                        <div class="series-detail__info" v-if="series.description || series.genres.length > 0">
                            <div class="series-detail__description" v-if="series.description">
                                {{ series.description }}
                            </div>
                            <div class="series-detail__genres" v-if="series.genres.length > 0">
                                <v-chip v-for="(genre, index) in series.genres" :key="index" size="small"
                                    variant="tonal" class="series-detail__genre-chip">
                                    {{ genre.major }}
                                    <template v-if="genre.middle"> / {{ genre.middle }}</template>
                                </v-chip>
                            </div>
                        </div>
                        <!-- 放送期間ごとのエピソードリスト -->
                        <div class="series-detail__periods">
                            <div class="series-detail__period" v-for="period in series.broadcast_periods"
                                :key="getPeriodKey(period)">
                                <!-- 放送期間が複数の場合のみ期間ヘッダーを表示 -->
                                <div class="series-detail__period-header" v-if="series.broadcast_periods.length > 1">
                                    <span class="series-detail__period-channel">{{ period.channel.name }}</span>
                                    <span class="series-detail__period-date">{{ formatDateRange(period) }}</span>
                                    <span class="series-detail__period-count">{{ period.recorded_programs.length }}件</span>
                                </div>
                                <!-- エピソードリスト: RecordedProgramList を再利用 -->
                                <RecordedProgramList
                                    :title="series.broadcast_periods.length > 1 ? '' : series.title"
                                    :programs="getSortedPrograms(period)"
                                    :total="period.recorded_programs.length"
                                    :hideHeader="true"
                                    :hideSort="true"
                                    :hidePagination="true"
                                    :showEmptyMessage="false"
                                    :isLoading="false"
                                    :forSeries="true"
                                    :seriesId="series.id"
                                    @removedFromSeries="handleProgramRemovedFromSeries" />
                            </div>
                        </div>
                    </template>
                </div>
            </div>
        </main>
    </div>

    <!-- シリーズ名変更ダイアログ -->
    <v-dialog max-width="550" v-model="show_rename_dialog">
        <v-card>
            <v-card-title class="d-flex justify-center pt-6 font-weight-bold">シリーズ名を変更</v-card-title>
            <v-card-text class="pt-4 pb-0">
                <v-text-field v-model="rename_title" label="シリーズ名" variant="outlined" density="comfortable"
                    hide-details @keydown.enter="renameSeries" autofocus />
            </v-card-text>
            <v-card-actions class="pt-4 px-6 pb-6">
                <v-spacer></v-spacer>
                <v-btn color="text" variant="text" @click="show_rename_dialog = false">
                    <Icon icon="fluent:dismiss-20-regular" width="18px" height="18px" />
                    <span class="ml-1">キャンセル</span>
                </v-btn>
                <v-btn class="px-3" color="primary" variant="flat" @click="renameSeries"
                    :disabled="!rename_title.trim() || rename_title.trim() === series?.title">
                    <Icon icon="fluent:checkmark-20-regular" width="18px" height="18px" />
                    <span class="ml-1">変更する</span>
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>

    <!-- 番組追加ダイアログ -->
    <v-dialog max-width="750" v-model="show_add_program_dialog" scrollable>
        <v-card>
            <v-card-title class="d-flex justify-center pt-6 font-weight-bold">番組を追加</v-card-title>
            <v-card-text class="pt-4 pb-0">
                <v-text-field v-model="add_program_query" label="番組を検索…" variant="outlined" density="comfortable"
                    hide-details clearable prepend-inner-icon="mdi-magnify" @update:model-value="onAddProgramQueryChanged" />
                <!-- 検索結果リスト -->
                <div class="add-program__results" v-if="add_program_results.length > 0">
                    <div class="add-program__item" v-for="program in add_program_results" :key="program.id">
                        <div class="add-program__thumbnail">
                            <img loading="lazy" :src="`${Utils.api_base_url}/videos/${program.id}/thumbnail`" />
                        </div>
                        <div class="add-program__info">
                            <div class="add-program__title">{{ program.title }}</div>
                            <div class="add-program__meta">
                                <span v-if="program.channel">{{ program.channel.name }}</span>
                                <span>{{ dayjs(program.start_time).format('YYYY/MM/DD HH:mm') }}</span>
                            </div>
                            <!-- 既にこのシリーズに追加済み -->
                            <v-chip v-if="isProgramInCurrentSeries(program)" size="x-small" color="primary"
                                variant="tonal" class="mt-1">追加済み</v-chip>
                        </div>
                        <div class="add-program__action">
                            <v-btn v-if="!isProgramInCurrentSeries(program)" color="primary" variant="flat"
                                size="small" :loading="adding_program_id === program.id"
                                @click="addProgramToSeries(program)">
                                追加
                            </v-btn>
                        </div>
                    </div>
                </div>
                <!-- 検索中の表示 -->
                <div class="add-program__loading" v-else-if="is_searching">
                    <Icon icon="line-md:loading-twotone-loop" width="36px" />
                </div>
                <!-- 検索結果なし -->
                <div class="add-program__empty" v-else-if="add_program_query && add_program_query.trim() && !is_searching">
                    <span>検索結果が見つかりませんでした。</span>
                </div>
            </v-card-text>
            <v-card-actions class="pt-4 px-6 pb-6">
                <v-spacer></v-spacer>
                <v-btn color="text" variant="text" @click="show_add_program_dialog = false">
                    <Icon icon="fluent:dismiss-20-regular" width="18px" height="18px" />
                    <span class="ml-1">閉じる</span>
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>

    <!-- シリーズ削除確認ダイアログ -->
    <v-dialog max-width="550" v-model="show_delete_dialog">
        <v-card>
            <v-card-title class="d-flex justify-center pt-6 font-weight-bold">シリーズを削除</v-card-title>
            <v-card-text class="pt-4 pb-0">
                <div class="text-center">
                    シリーズ「{{ series?.title }}」を削除しますか？<br>
                    シリーズに含まれる録画番組は削除されませんが、<br class="d-sm-none">シリーズとの紐付けが解除されます。
                </div>
            </v-card-text>
            <v-card-actions class="pt-4 px-6 pb-6">
                <v-spacer></v-spacer>
                <v-btn color="text" variant="text" @click="show_delete_dialog = false">
                    <Icon icon="fluent:dismiss-20-regular" width="18px" height="18px" />
                    <span class="ml-1">キャンセル</span>
                </v-btn>
                <v-btn class="px-3" color="error" variant="flat" @click="deleteSeries">
                    <Icon icon="fluent:delete-20-regular" width="18px" height="18px" />
                    <span class="ml-1">削除する</span>
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>

    <!-- シリーズマージ検索ダイアログ -->
    <v-dialog max-width="750" v-model="show_merge_dialog" scrollable>
        <v-card>
            <v-card-title class="d-flex justify-center pt-6 font-weight-bold">シリーズを結合</v-card-title>
            <v-card-text class="pt-4 pb-0">
                <v-text-field v-model="merge_target_query" label="マージ先シリーズを検索…" variant="outlined"
                    density="comfortable" hide-details clearable prepend-inner-icon="mdi-magnify"
                    @update:model-value="onMergeTargetQueryChanged" autofocus />
                <!-- 検索結果リスト -->
                <div class="merge-series__results" v-if="merge_target_results.length > 0">
                    <div class="merge-series__item" v-for="targetSeries in merge_target_results"
                        :key="targetSeries.id">
                        <div class="merge-series__info">
                            <div class="merge-series__title">{{ targetSeries.title }}</div>
                            <div class="merge-series__meta">
                                {{ getMergeTargetEpisodeCount(targetSeries) }}件
                            </div>
                        </div>
                        <v-btn color="primary" variant="flat" size="small"
                            @click="confirmMergeSeries(targetSeries)">
                            選択
                        </v-btn>
                    </div>
                </div>
                <!-- 検索中の表示 -->
                <div class="merge-series__loading" v-else-if="is_searching_merge_target">
                    <Icon icon="line-md:loading-twotone-loop" width="36px" />
                </div>
                <!-- 検索結果なし -->
                <div class="merge-series__empty"
                    v-else-if="merge_target_query && merge_target_query.trim() && !is_searching_merge_target">
                    <span>マージ先のシリーズが見つかりませんでした。</span>
                </div>
            </v-card-text>
            <v-card-actions class="pt-4 px-6 pb-6">
                <v-spacer></v-spacer>
                <v-btn color="text" variant="text" @click="show_merge_dialog = false">
                    <Icon icon="fluent:dismiss-20-regular" width="18px" height="18px" />
                    <span class="ml-1">閉じる</span>
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>

    <!-- シリーズマージ確認ダイアログ -->
    <v-dialog max-width="550" v-model="show_merge_confirm_dialog">
        <v-card>
            <v-card-title class="d-flex justify-center pt-6 font-weight-bold">シリーズを結合</v-card-title>
            <v-card-text class="pt-4 pb-0">
                <div class="text-center">
                    シリーズ「{{ series?.title }}」の全{{ totalEpisodeCount }}件を<br class="d-sm-none">
                    「{{ selected_merge_target?.title }}」にマージしますか？<br>
                    <span class="text-caption">マージ後、「{{ series?.title }}」は削除されます。</span>
                </div>
            </v-card-text>
            <v-card-actions class="pt-4 px-6 pb-6">
                <v-spacer></v-spacer>
                <v-btn color="text" variant="text" @click="show_merge_confirm_dialog = false">
                    <Icon icon="fluent:dismiss-20-regular" width="18px" height="18px" />
                    <span class="ml-1">キャンセル</span>
                </v-btn>
                <v-btn class="px-3" color="primary" variant="flat" @click="executeMergeSeries"
                    :loading="is_merging">
                    <Icon icon="fluent:merge-20-regular" width="18px" height="18px" />
                    <span class="ml-1">マージする</span>
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>
<script lang="ts" setup>

import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import Breadcrumbs from '@/components/Breadcrumbs.vue';
import HeaderBar from '@/components/HeaderBar.vue';
import Navigation from '@/components/Navigation.vue';
import SPHeaderBar from '@/components/SPHeaderBar.vue';
import RecordedProgramList from '@/components/Videos/RecordedProgramList.vue';
import Message from '@/message';
import SeriesService, { ISeries, ISeriesBroadcastPeriod } from '@/services/Series';
import Videos, { IRecordedProgram } from '@/services/Videos';
import useUserStore from '@/stores/UserStore';
import Utils, { dayjs } from '@/utils';

// ルーター
const route = useRoute();
const router = useRouter();

// シリーズ情報
const series = ref<ISeries | null>(null);
const is_loading = ref(true);

// シリーズ名変更ダイアログ
const show_rename_dialog = ref(false);
const rename_title = ref('');

// 番組追加ダイアログ
const show_add_program_dialog = ref(false);
const add_program_query = ref('');
const add_program_results = ref<IRecordedProgram[]>([]);
const is_searching = ref(false);
const adding_program_id = ref<number | null>(null);
let search_debounce_timer: ReturnType<typeof setTimeout> | null = null;

// シリーズ削除ダイアログ
const show_delete_dialog = ref(false);

// シリーズマージダイアログ
const show_merge_dialog = ref(false);
const show_merge_confirm_dialog = ref(false);
const merge_target_query = ref('');
const merge_target_results = ref<ISeries[]>([]);
const selected_merge_target = ref<ISeries | null>(null);
const is_searching_merge_target = ref(false);
const is_merging = ref(false);
let merge_search_debounce_timer: ReturnType<typeof setTimeout> | null = null;

// シリーズ内の全エピソード数を算出する
const totalEpisodeCount = computed(() => {
    if (!series.value) return 0;
    return series.value.broadcast_periods.reduce(
        (sum, period) => sum + period.recorded_programs.length, 0,
    );
});

// ==================== データ取得 ====================

// シリーズ情報を取得する
const fetchSeries = async () => {
    const seriesId = parseInt(route.params.series_id as string);
    if (isNaN(seriesId)) {
        is_loading.value = false;
        return;
    }
    const result = await SeriesService.fetchSeries(seriesId);
    series.value = result;
    is_loading.value = false;
};

// ==================== ユーティリティ関数 ====================

// 放送期間のユニークキーを生成する
const getPeriodKey = (period: ISeriesBroadcastPeriod): string => {
    return `${period.channel.id}-${period.start_date}-${period.end_date}`;
};

// 放送期間内のエピソードを episode_number の数値順 → start_time 順にソートする
const getSortedPrograms = (period: ISeriesBroadcastPeriod): IRecordedProgram[] => {
    return [...period.recorded_programs].sort((a, b) => {
        // episode_number がある場合は数値比較
        if (a.episode_number !== null && b.episode_number !== null) {
            const numA = parseFloat(a.episode_number);
            const numB = parseFloat(b.episode_number);
            if (!isNaN(numA) && !isNaN(numB)) {
                return numA - numB;
            }
        }
        // episode_number がない場合は start_time 順
        return dayjs(a.start_time).unix() - dayjs(b.start_time).unix();
    });
};

// 放送期間の日付範囲をフォーマットする
const formatDateRange = (period: ISeriesBroadcastPeriod): string => {
    const start = dayjs(period.start_date).format('YYYY/MM/DD');
    const end = dayjs(period.end_date).format('YYYY/MM/DD');
    return `${start} 〜 ${end}`;
};

// ==================== シリーズ編集 ====================

// シリーズ名変更ダイアログを開く
const openRenameDialog = () => {
    if (!series.value) return;
    rename_title.value = series.value.title;
    show_rename_dialog.value = true;
};

// シリーズ名を変更する
const renameSeries = async () => {
    if (!series.value || !rename_title.value.trim()) return;
    const trimmedTitle = rename_title.value.trim();
    if (trimmedTitle === series.value.title) return;

    show_rename_dialog.value = false;
    const result = await SeriesService.updateSeries(series.value.id, trimmedTitle);
    if (result !== null) {
        // 更新後のシリーズ情報でローカル state を更新
        series.value = result;
        Message.success('シリーズ名を変更しました。');
    }
};

// ==================== 番組追加 ====================

// 番組追加ダイアログを開く
const openAddProgramDialog = () => {
    add_program_query.value = '';
    add_program_results.value = [];
    is_searching.value = false;
    show_add_program_dialog.value = true;
};

// 検索クエリが変更された時 (300ms デバウンス)
const onAddProgramQueryChanged = () => {
    if (search_debounce_timer) {
        clearTimeout(search_debounce_timer);
    }
    const query = add_program_query.value?.trim() || '';
    if (!query) {
        add_program_results.value = [];
        is_searching.value = false;
        return;
    }
    is_searching.value = true;
    search_debounce_timer = setTimeout(async () => {
        const result = await Videos.searchVideos(query);
        if (result) {
            add_program_results.value = result.recorded_programs;
        }
        is_searching.value = false;
    }, 300);
};

// 番組がこのシリーズに既に含まれているかチェック
const isProgramInCurrentSeries = (program: IRecordedProgram): boolean => {
    if (!series.value) return false;
    return program.series_id === series.value.id;
};

// 番組をシリーズに追加する
const addProgramToSeries = async (program: IRecordedProgram) => {
    if (!series.value) return;
    adding_program_id.value = program.id;
    const result = await SeriesService.addProgramToSeries(series.value.id, program.id);
    adding_program_id.value = null;
    if (result !== null) {
        // 更新後のシリーズ情報でローカル state を更新
        series.value = result;
        // 検索結果内の番組の series_id を更新して「追加済み」チップを表示する
        const idx = add_program_results.value.findIndex(p => p.id === program.id);
        if (idx !== -1) {
            add_program_results.value[idx].series_id = series.value.id;
        }
        Message.success('番組をシリーズに追加しました。');
    }
};

// ==================== シリーズ削除 ====================

// シリーズ削除ダイアログを開く
const openDeleteDialog = () => {
    show_delete_dialog.value = true;
};

// シリーズを削除する
const deleteSeries = async () => {
    if (!series.value) return;
    show_delete_dialog.value = false;
    const success = await SeriesService.deleteSeries(series.value.id);
    if (success) {
        Message.success('シリーズを削除しました。');
        router.push('/videos/series');
    }
};

// ==================== シリーズ結合 (マージ) ====================

// マージダイアログを開く
const openMergeDialog = () => {
    merge_target_query.value = '';
    merge_target_results.value = [];
    selected_merge_target.value = null;
    is_searching_merge_target.value = false;
    show_merge_dialog.value = true;
};

// マージ先シリーズの検索クエリが変更された時 (300ms デバウンス)
const onMergeTargetQueryChanged = () => {
    if (merge_search_debounce_timer) {
        clearTimeout(merge_search_debounce_timer);
    }
    const query = merge_target_query.value?.trim() || '';
    if (!query) {
        merge_target_results.value = [];
        is_searching_merge_target.value = false;
        return;
    }
    is_searching_merge_target.value = true;
    merge_search_debounce_timer = setTimeout(async () => {
        const result = await SeriesService.searchSeries(query);
        if (result) {
            // 自分自身のシリーズを検索結果から除外する
            merge_target_results.value = result.series_list.filter(
                s => s.id !== series.value?.id,
            );
        }
        is_searching_merge_target.value = false;
    }, 300);
};

// マージ先シリーズの全エピソード数を算出する
const getMergeTargetEpisodeCount = (targetSeries: ISeries): number => {
    return targetSeries.broadcast_periods.reduce(
        (sum, period) => sum + period.recorded_programs.length, 0,
    );
};

// マージ先シリーズを選択して確認ダイアログを表示する
const confirmMergeSeries = (targetSeries: ISeries) => {
    selected_merge_target.value = targetSeries;
    show_merge_dialog.value = false;
    show_merge_confirm_dialog.value = true;
};

// マージを実行する
const executeMergeSeries = async () => {
    if (!series.value || !selected_merge_target.value) return;
    is_merging.value = true;
    const result = await SeriesService.mergeSeries(series.value.id, selected_merge_target.value.id);
    is_merging.value = false;
    if (result !== null) {
        show_merge_confirm_dialog.value = false;
        Message.success('シリーズをマージしました。');
        // マージ先のシリーズ詳細ページに遷移する
        router.push(`/videos/series/${selected_merge_target.value.id}`);
    }
};

// ==================== シリーズから番組除外 ====================

// シリーズから番組が除外された時の処理
const handleProgramRemovedFromSeries = async () => {
    if (!series.value) return;

    // シリーズ情報を再取得して最新の状態を反映する
    const result = await SeriesService.fetchSeries(series.value.id);
    if (result === null) {
        // シリーズが削除された場合 (全番組が除外された)、シリーズ一覧に戻る
        Message.show('シリーズ内の番組がなくなったため、シリーズ一覧に戻ります。');
        router.push('/videos/series');
        return;
    }
    series.value = result;
};

// ==================== 初期化 ====================

onMounted(async () => {
    // 事前にログイン状態を同期
    const userStore = useUserStore();
    await userStore.fetchUser();

    // シリーズ情報を取得
    await fetchSeries();
});

</script>
<style lang="scss" scoped>

.series-detail-container-wrapper {
    display: flex;
    flex-direction: column;
    width: 100%;
}

.series-detail-container {
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

// ローディング表示
.series-detail__loading {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 60px 0;
    color: rgb(var(--v-theme-text-darken-1));
}

// 空状態
.series-detail__empty {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    padding: 60px 0;

    &-icon {
        color: rgb(var(--v-theme-text-darken-1));
    }

    h2 {
        margin-top: 12px;
        font-size: 21px;
        @include smartphone-vertical {
            font-size: 19px;
        }
    }

    &-submessage {
        margin-top: 8px;
        color: rgb(var(--v-theme-text-darken-1));
        font-size: 15px;
        text-align: center;
        @include smartphone-vertical {
            font-size: 13px;
            line-height: 1.65;
        }
    }
}

// ヘッダー (RecordedProgramList のヘッダーパターンに準拠)
.series-detail__header {
    display: flex;
    align-items: center;
    @include smartphone-vertical {
        padding: 0px 8px;
    }
}

.series-detail__title {
    display: flex;
    align-items: center;
    position: relative;
    // 親の .series-detail__header が display: flex のため、min-width: 0 がないと
    // タイトルテキストの長さに引きずられて親コンテナからはみ出してしまう
    min-width: 0;
    font-size: 24px;
    font-weight: 700;
    padding-top: 8px;
    padding-bottom: 20px;
    @include smartphone-vertical {
        font-size: 22px;
        padding-bottom: 16px;
        // スマホ縦画面ではアクションボタンを2行目に折り返す
        flex-wrap: wrap;
        row-gap: 4px;
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

    &-text {
        flex: 1;
        min-width: 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        @include smartphone-vertical {
            // 戻るボタンの分を除いた幅を確保し、アクションボタンを次の行に折り返す
            flex-basis: calc(100% - 40px);
        }
    }

    &-action {
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        width: 32px;
        height: 32px;
        margin-left: 4px;
        border-radius: 50%;
        color: rgb(var(--v-theme-text-darken-1));
        cursor: pointer;
        transition: color 0.15s ease;
        @include smartphone-vertical {
            // スマホ縦画面ではタッチしやすいように少し大きくする
            width: 36px;
            height: 36px;
        }
        &:hover {
            color: rgb(var(--v-theme-text));
        }
        &--danger:hover {
            color: rgb(var(--v-theme-error));
        }
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
        @include smartphone-vertical {
            // 2行目で右端に配置
            margin-left: auto;
            padding-top: 0;
        }
    }
}

// シリーズ概要情報
.series-detail__info {
    margin-bottom: 16px;
    @include smartphone-vertical {
        padding: 0px 8px;
    }
}

.series-detail__description {
    font-size: 14px;
    color: rgb(var(--v-theme-text-darken-1));
    line-height: 1.65;
    margin-bottom: 12px;
}

.series-detail__genres {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}

.series-detail__genre-chip {
    font-size: 12px !important;
}

// 放送期間ごとのエピソードリスト
.series-detail__periods {
    display: flex;
    flex-direction: column;
    gap: 24px;
}

.series-detail__period {
    &-header {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 0;
        margin-bottom: 4px;
        border-bottom: 1px solid rgb(var(--v-theme-background-lighten-2));
        @include smartphone-vertical {
            padding: 8px 8px;
        }
    }

    &-channel {
        font-size: 15px;
        font-weight: bold;
    }

    &-date {
        font-size: 13px;
        color: rgb(var(--v-theme-text-darken-1));
    }

    &-count {
        margin-left: auto;
        font-size: 13px;
        color: rgb(var(--v-theme-text-darken-1));
    }
}

// 番組追加ダイアログ内のスタイル
.add-program__results {
    display: flex;
    flex-direction: column;
    margin-top: 16px;
    max-height: 400px;
    overflow-y: auto;
}

.add-program__item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 4px;
    border-bottom: 1px solid rgb(var(--v-theme-background-lighten-2));
    @include smartphone-vertical {
        gap: 8px;
    }
}

.add-program__thumbnail {
    flex-shrink: 0;
    width: 100px;
    aspect-ratio: 16 / 9;
    border-radius: 4px;
    overflow: hidden;
    background: linear-gradient(150deg, rgb(var(--v-theme-gray)), rgb(var(--v-theme-background-lighten-2)));
    @include smartphone-vertical {
        width: 80px;
    }

    img {
        display: block;
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
}

.add-program__info {
    flex: 1;
    min-width: 0;
}

.add-program__title {
    font-size: 13.5px;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    @include smartphone-vertical {
        font-size: 12.5px;
        white-space: normal;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
    }
}

.add-program__meta {
    display: flex;
    gap: 8px;
    font-size: 12px;
    color: rgb(var(--v-theme-text-darken-1));
    margin-top: 2px;
}

.add-program__action {
    flex-shrink: 0;
}

.add-program__loading {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 32px 0;
    color: rgb(var(--v-theme-text-darken-1));
}

.add-program__empty {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 32px 0;
    font-size: 14px;
    color: rgb(var(--v-theme-text-darken-1));
}

// シリーズマージダイアログ内のスタイル
.merge-series__results {
    display: flex;
    flex-direction: column;
    margin-top: 16px;
    max-height: 400px;
    overflow-y: auto;
}

.merge-series__item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 4px;
    border-bottom: 1px solid rgb(var(--v-theme-background-lighten-2));
}

.merge-series__info {
    flex: 1;
    min-width: 0;
}

.merge-series__title {
    font-size: 14px;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.merge-series__meta {
    font-size: 12px;
    color: rgb(var(--v-theme-text-darken-1));
    margin-top: 2px;
}

.merge-series__loading {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 32px 0;
    color: rgb(var(--v-theme-text-darken-1));
}

.merge-series__empty {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 32px 0;
    font-size: 14px;
    color: rgb(var(--v-theme-text-darken-1));
}

</style>
