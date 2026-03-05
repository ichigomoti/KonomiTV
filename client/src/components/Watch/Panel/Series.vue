<template>
    <div class="series-container">
        <!-- ヘッダー: シリーズアイコンとタイトル -->
        <section class="series-header">
            <h2 class="series-header__title">
                <Icon class="series-header__title-icon" icon="fluent:video-clip-multiple-16-filled" height="18.5px" />
                <span class="series-header__title-text">シリーズ</span>
            </h2>
        </section>
        <!-- ローディング中 -->
        <div class="series-announce" v-if="is_loading">
            <Icon class="series-announce__icon" icon="line-md:loading-twotone-loop" width="45px" />
        </div>
        <!-- シリーズ情報がない場合の空状態 -->
        <div class="series-announce" v-else-if="!series">
            <Icon class="series-announce__icon" icon="fluent:video-clip-multiple-16-regular" width="45px" />
            <div class="series-announce__heading">シリーズ情報がありません</div>
            <div class="series-announce__text">
                この録画番組はシリーズに<br class="d-sm-none">紐付けられていません。
            </div>
        </div>
        <!-- シリーズのエピソードリスト -->
        <div class="series-content" v-else>
            <!-- シリーズ概要 -->
            <div class="series-info">
                <div class="series-info__title">{{ series.title }}</div>
                <div class="series-info__count">全 {{ totalEpisodeCount }} 件</div>
            </div>
            <!-- 放送期間ごとにグループ化したエピソードリスト -->
            <div class="series-period" v-for="period in series.broadcast_periods" :key="getPeriodKey(period)">
                <!-- 放送期間が複数の場合のみヘッダー表示 -->
                <div class="series-period__header" v-if="series.broadcast_periods.length > 1">
                    <span class="series-period__channel">{{ period.channel.name }}</span>
                    <span class="series-period__date">{{ formatDateRange(period) }}</span>
                </div>
                <!-- エピソードカード -->
                <router-link class="series-episode" v-for="program in getSortedPrograms(period)"
                    :key="program.id" :to="`/videos/watch/${program.id}`"
                    :class="{'series-episode--current': program.id === currentProgramId}">
                    <div class="series-episode__thumbnail">
                        <img :src="`${Utils.api_base_url}/videos/${program.id}/thumbnail`"
                            loading="lazy" />
                        <span class="series-episode__duration">{{ formatDuration(program.recorded_video.duration) }}</span>
                    </div>
                    <div class="series-episode__info">
                        <span class="series-episode__number" v-if="program.episode_number">
                            #{{ program.episode_number }}
                        </span>
                        <span class="series-episode__title">
                            {{ program.subtitle || program.title }}
                        </span>
                        <span class="series-episode__time">
                            {{ formatDate(program.start_time) }}
                        </span>
                    </div>
                </router-link>
            </div>
            <!-- シリーズ詳細ページへのリンク -->
            <router-link class="series-detail-link" :to="`/videos/series/${series.id}`">
                <Icon icon="fluent:open-16-filled" width="16px" class="mr-1" />
                シリーズの詳細を表示
            </router-link>
        </div>
    </div>
</template>
<script lang="ts" setup>

import { computed, ref, watch } from 'vue';

import SeriesService, { ISeries, ISeriesBroadcastPeriod } from '@/services/Series';
import { IRecordedProgram } from '@/services/Videos';
import usePlayerStore from '@/stores/PlayerStore';
import Utils, { dayjs } from '@/utils';

// プレイヤーストア
const playerStore = usePlayerStore();

// シリーズ情報
const series = ref<ISeries | null>(null);

// ローディング状態
const is_loading = ref(false);

// 現在再生中の録画番組 ID
const currentProgramId = computed(() => playerStore.recorded_program.id);

// シリーズ内の全エピソード数を算出する
const totalEpisodeCount = computed(() => {
    if (!series.value) return 0;
    return series.value.broadcast_periods.reduce(
        (sum, period) => sum + period.recorded_programs.length, 0,
    );
});

// 録画番組の series_id が変化したらシリーズ情報を再取得する
watch(() => playerStore.recorded_program.series_id, async (newSeriesId) => {
    if (newSeriesId === null || newSeriesId === undefined) {
        series.value = null;
        return;
    }
    is_loading.value = true;
    const result = await SeriesService.fetchSeries(newSeriesId);
    series.value = result;
    is_loading.value = false;
}, { immediate: true });

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

// 放送日時をフォーマットする
const formatDate = (dateStr: string): string => {
    return dayjs(dateStr).format('YYYY/MM/DD HH:mm');
};

// 録画時間 (秒) を MM:SS or H:MM:SS 形式にフォーマットする
const formatDuration = (durationSec: number): string => {
    const hours = Math.floor(durationSec / 3600);
    const minutes = Math.floor((durationSec % 3600) / 60);
    const seconds = Math.floor(durationSec % 60);
    if (hours > 0) {
        return `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }
    return `${minutes}:${String(seconds).padStart(2, '0')}`;
};

</script>
<style lang="scss" scoped>

.series-container {
    display: flex;
    flex-direction: column;
    height: 100%;
    padding-left: 16px;
    padding-right: 16px;
    overflow-y: auto;
    @include tablet-vertical {
        margin-top: 20px;
        padding-left: 24px;
        padding-right: 24px;
    }
    @include smartphone-horizontal {
        margin-top: 12px;
    }
    @include smartphone-vertical {
        margin-top: 14px;
    }
}

// ヘッダー (Comment.vue のヘッダーパターンに準拠)
.series-header {
    display: flex;
    align-items: center;
    flex-shrink: 0;
    min-height: 32px;
    margin-bottom: 12px;

    &__title {
        display: flex;
        align-items: center;
        font-size: 18.5px;
        font-weight: bold;
    }

    &__title-icon {
        flex-shrink: 0;
        margin-right: 8px;
    }

    &__title-text {
        flex-shrink: 0;
    }
}

// 空状態・ローディング表示
.series-announce {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    flex-grow: 1;
    padding-top: 30px;
    padding-bottom: 40px;

    &__icon {
        color: rgb(var(--v-theme-text-darken-1));
    }

    &__heading {
        margin-top: 12px;
        font-size: 17px;
        font-weight: bold;
        text-align: center;
    }

    &__text {
        margin-top: 6px;
        font-size: 13.5px;
        color: rgb(var(--v-theme-text-darken-1));
        text-align: center;
        line-height: 1.65;
    }
}

// シリーズ概要情報
.series-info {
    display: flex;
    align-items: center;
    margin-bottom: 12px;

    &__title {
        font-size: 15px;
        font-weight: bold;
        flex: 1;
        min-width: 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    &__count {
        flex-shrink: 0;
        margin-left: 8px;
        font-size: 13px;
        color: rgb(var(--v-theme-text-darken-1));
    }
}

// 放送期間ごとのグループ
.series-period {
    & + .series-period {
        margin-top: 16px;
    }

    &__header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
        padding: 6px 0;
        border-bottom: 1px solid rgb(var(--v-theme-background-lighten-2));
    }

    &__channel {
        font-size: 13px;
        font-weight: bold;
    }

    &__date {
        font-size: 12px;
        color: rgb(var(--v-theme-text-darken-1));
    }
}

// エピソードカード
.series-episode {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 6px 4px;
    border-radius: 6px;
    text-decoration: none;
    color: rgb(var(--v-theme-text));
    transition: background-color 0.15s ease;
    cursor: pointer;

    &:hover {
        background-color: rgb(var(--v-theme-background-lighten-2));
    }

    // 現在再生中のエピソードをハイライト
    &--current {
        border-left: 3px solid rgb(var(--v-theme-primary));
        padding-left: 5px;
        background-color: rgba(var(--v-theme-primary), 0.08);

        &:hover {
            background-color: rgba(var(--v-theme-primary), 0.12);
        }
    }

    &__thumbnail {
        position: relative;
        flex-shrink: 0;
        width: 120px;
        aspect-ratio: 16 / 9;
        border-radius: 4px;
        overflow: hidden;
        background: linear-gradient(150deg, rgb(var(--v-theme-gray)), rgb(var(--v-theme-background-lighten-2)));

        img {
            display: block;
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
    }

    &__duration {
        position: absolute;
        bottom: 3px;
        right: 3px;
        padding: 1px 4px;
        border-radius: 3px;
        background: rgba(0, 0, 0, 0.7);
        color: #ffffff;
        font-size: 11px;
        font-weight: 600;
        line-height: 1.4;
    }

    &__info {
        display: flex;
        flex-direction: column;
        gap: 2px;
        min-width: 0;
        flex: 1;
    }

    &__number {
        font-size: 12px;
        font-weight: bold;
        color: rgb(var(--v-theme-primary));
    }

    &__title {
        font-size: 13px;
        font-weight: 500;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    &__time {
        font-size: 11.5px;
        color: rgb(var(--v-theme-text-darken-1));
    }
}

// シリーズ詳細ページへのリンク
.series-detail-link {
    display: flex;
    align-items: center;
    justify-content: center;
    margin-top: 16px;
    margin-bottom: 16px;
    padding: 10px;
    border-radius: 8px;
    background: rgb(var(--v-theme-background-lighten-2));
    color: rgb(var(--v-theme-primary));
    font-size: 13.5px;
    font-weight: 600;
    text-decoration: none;
    transition: opacity 0.15s ease;

    &:hover {
        opacity: 0.8;
    }
}

</style>
