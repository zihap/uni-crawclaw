<template>
    <view class="result-container">
        <view class="bg-overlay"></view>

        <view class="winner-section animate-fade-down" v-if="winner">
            <view class="crown-icon">👑</view>
            <view class="winner-avatar-wrap">
                <image class="winner-avatar" src="/static/images/player1_default.png" mode="aspectFill"/>
            </view>
            <text class="winner-name">{{ winner.name }}</text>
            <text class="winner-title">最终胜利</text>
            <text class="winner-score">{{ winner.totalScore }} 分</text>
        </view>

        <scroll-view scroll-y class="leaderboard-section animate-fade-up">
            <view class="leaderboard-title">对局结算排行榜</view>
            <view v-for="(player, index) in sortedPlayers" :key="player.id" class="player-card">
                <view class="player-row" @click="toggleExpand(player.id)">
                    <view class="rank-badge" :class="`rank-${index + 1}`">{{ index + 1 }}</view>
                    <image class="player-avatar" src="/static/images/player2_default.png" mode="aspectFill"/>
                    <text class="player-name">{{ player.name }}</text>
                    <view class="score-wrap">
                        <text class="total-score">{{ player.totalScore }}</text>
                        <text class="expand-icon" :class="{ expanded: expandedRows[player.id] }">▼</text>
                    </view>
                </view>

                <view class="score-details" v-if="expandedRows[player.id]">
                    <view class="detail-item">
                        <text class="detail-label">1. 核心乘积分</text>
                        <text class="detail-formula">
                            (德{{ player.deTrack.value }} * 望{{ player.wangTrack.value }}
                            + 德突破奖励{{ player.deTrack.bonus }}
                            + 望突破奖励{{ player.wangTrack.bonus }}
                            = {{ player.coreScore }})
                        </text>
                    </view>

                    <view class="detail-item">
                        <text class="detail-label">2. 进贡席位分</text>
                        <text class="detail-formula">
                            ({{ player.tavernDetails.join(' + ') }} = {{ player.tavernTotal }})
                        </text>
                    </view>

                    <view class="detail-item">
                        <text class="detail-label">3. 资源转换分</text>
                        <text class="detail-formula">
                            (金币折算{{ player.res.coins }}
                            + 海草折算{{ player.res.seaweed }}
                            + 虾笼折算{{ player.res.cages }}
                            + 龙虾折算{{ player.res.lobsters }}
                            = {{ player.resTotal }})
                        </text>
                    </view>
                </view>
            </view>
        </scroll-view>

        <view class="actions animate-fade-up">
            <button class="btn-return" @click="returnToLobby">返回大厅</button>
        </view>
    </view>
</template>

<script setup>
import {ref, computed, onMounted} from 'vue'

const sortedPlayers = ref([])
const winner = computed(() => sortedPlayers.value[0])
const expandedRows = ref({})

// 德望双轨刻度映射 (0-15下标 共16个)
const VALUE_MAP = [1, 2, 3, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 9, 10]

// 突破奖励规则映射
const getBreakthroughBonus = (idx) => {
    if (idx >= 14) return 5 // 达到第三个 9
    if (idx >= 13) return 4 // 达到第二个 9
    if (idx >= 11) return 3 // 达到第二个 8
    if (idx >= 9) return 2  // 达到第二个 7
    if (idx >= 7) return 1  // 达到第二个 6
    return 0
}

// 获取双轨具体数值
const getTrackData = (val) => {
    // 限制边界 0~15
    const idx = Math.min(Math.max(val || 0, 0), 15)
    return {
        raw: val,
        value: VALUE_MAP[idx],
        bonus: getBreakthroughBonus(idx)
    }
}

const toggleExpand = (id) => {
    expandedRows.value[id] = !expandedRows.value[id]
}

const returnToLobby = () => {
    uni.reLaunch({url: '/pages/lobby/lobby'})
}

const calculatePlayerScore = (player, taverns) => {
    // 1. 核心乘积分
    const deTrack = getTrackData(player.de)
    const wangTrack = getTrackData(player.wang)
    const coreScore = (deTrack.value * wangTrack.value) + deTrack.bonus + wangTrack.bonus

    // 2. 进贡席位分
    let tavernTotal = 0
    const tavernDetails = []
    ;(taverns || []).forEach(t => {
        const rank = (t.occupants || []).indexOf(player.id)
        // 顺位分：第一名3分，第二名2分，第三名1分，第四名0分
        const pts = rank !== -1 && rank < 4 ? [3, 2, 1, 0][rank] : 0
        tavernDetails.push(pts)
        tavernTotal += pts
    })
    // 补齐显示，如果没有占满6个祭坛，前端显示补0
    while (tavernDetails.length < 6) tavernDetails.push(0)

    // 3. 资源转换分
    const coinsScore = Math.floor((player.coins || 0) / 2)
    const seaweedScore = Math.floor((player.seaweed || 0) / 3)
    const cagesScore = (player.cages || 0) * 2

    let lobstersScore = 0
    ;(player.lobsters || []).forEach(l => {
        if (l.grade === 'normal') lobstersScore += 1
        else if (l.grade === 'grade3') lobstersScore += 2
        else if (l.grade === 'grade2') lobstersScore += 3
        else if (l.grade === 'grade1') lobstersScore += 5
        else if (l.grade === 'royal') lobstersScore += 8
    })

    // 未绑定的单独称号卡（被视为神器献祭价值）算作8分
    ;(player.titleCards || []).forEach(tc => {
        lobstersScore += 8
    })

    const resTotal = coinsScore + seaweedScore + cagesScore + lobstersScore
    const totalScore = coreScore + tavernTotal + resTotal + (player.bonusPoints || 0)

    return {
        ...player,
        deTrack,
        wangTrack,
        coreScore,
        tavernDetails,
        tavernTotal,
        res: {coins: coinsScore, seaweed: seaweedScore, cages: cagesScore, lobsters: lobstersScore},
        resTotal,
        totalScore
    }
}

onMounted(() => {
    const pages = getCurrentPages()
    const options = pages[pages.length - 1].options || {}

    if (options.gameState) {
        try {
            const gameState = JSON.parse(decodeURIComponent(options.gameState))
            const rawPlayers = gameState.players || []
            const taverns = gameState.taverns || []

            // 计算全员得分并降序
            const processed = rawPlayers.map(p => calculatePlayerScore(p, taverns))
            processed.sort((a, b) => b.totalScore - a.totalScore)

            sortedPlayers.value = processed
            // 默认展开第一名
            if (processed.length > 0) expandedRows.value[processed[0].id] = true
        } catch (e) {
            console.error('Failed to parse game state in result.vue:', e)
        }
    }
})
</script>

<style scoped>
.result-container {
    min-height: 100vh;
    background-color: #0a0a1a;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 40px 20px 100px;
    position: relative;
    overflow-x: hidden;
}

.bg-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: radial-gradient(circle at 50% 20%, #1a1a3a 0%, #0a0a1a 80%);
    z-index: 0;
}

.winner-section, .leaderboard-section, .actions {
    position: relative;
    z-index: 1;
    width: 100%;
}

.winner-section {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-bottom: 40px;
}

.crown-icon {
    font-size: 50px;
    margin-bottom: -15px;
    z-index: 2;
    animation: float 2s ease-in-out infinite;
}

.winner-avatar-wrap {
    width: 100px;
    height: 100px;
    border-radius: 50%;
    padding: 4px;
    background: linear-gradient(135deg, #ffd700, #ff8c00);
    box-shadow: 0 0 30px rgba(255, 215, 0, 0.4);
    margin-bottom: 15px;
}

.winner-avatar {
    width: 100%;
    height: 100%;
    border-radius: 50%;
    background-color: #1a1a2e;
}

.winner-name {
    font-size: 24px;
    font-weight: bold;
    color: #fff;
    text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
}

.winner-title {
    font-size: 14px;
    color: #ffd700;
    margin: 5px 0 10px;
    letter-spacing: 2px;
}

.winner-score {
    font-size: 32px;
    font-weight: 900;
    color: #4ecdc4;
    text-shadow: 0 0 15px rgba(78, 205, 196, 0.6);
}

.leaderboard-title {
    color: #a0a0b0;
    font-size: 14px;
    margin-bottom: 15px;
    text-align: center;
    letter-spacing: 1px;
}

.leaderboard-section {
    max-height: 55vh;
    width: 100%;
}

.player-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(78, 205, 196, 0.2);
    border-radius: 12px;
    margin-bottom: 12px;
    overflow: hidden;
    transition: all 0.3s;
}

.player-row {
    display: flex;
    align-items: center;
    padding: 15px;
    position: relative;
}

.player-row:active {
    background: rgba(255, 255, 255, 0.1);
}

.rank-badge {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: #333;
    color: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: bold;
    margin-right: 12px;
}

.rank-1 {
    background: linear-gradient(135deg, #ffd700, #ff8c00);
    box-shadow: 0 0 10px rgba(255, 215, 0, 0.5);
    color: #000;
}

.rank-2 {
    background: linear-gradient(135deg, #e0e0e0, #999);
    box-shadow: 0 0 10px rgba(224, 224, 224, 0.5);
    color: #000;
}

.rank-3 {
    background: linear-gradient(135deg, #cd7f32, #8b4513);
    box-shadow: 0 0 10px rgba(205, 127, 50, 0.5);
    color: #fff;
}

.player-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background-color: #2a2a3e;
    margin-right: 12px;
}

.player-name {
    flex: 1;
    color: #fff;
    font-size: 16px;
    font-weight: 500;
}

.score-wrap {
    display: flex;
    align-items: center;
}

.total-score {
    color: #4ecdc4;
    font-size: 20px;
    font-weight: bold;
    margin-right: 10px;
}

.expand-icon {
    color: #666;
    font-size: 12px;
    transition: transform 0.3s;
}

.expand-icon.expanded {
    transform: rotate(180deg);
    color: #4ecdc4;
}

.score-details {
    padding: 0 15px 15px;
    background: rgba(0, 0, 0, 0.2);
    border-top: 1px dashed rgba(255, 255, 255, 0.05);
}

.detail-item {
    margin-top: 10px;
    display: flex;
    flex-direction: column;
}

.detail-label {
    color: #ffd700;
    font-size: 13px;
    margin-bottom: 4px;
}

.detail-formula {
    color: #a0a0b0;
    font-size: 12px;
    line-height: 1.4;
}

.actions {
    position: fixed;
    bottom: 30px;
    left: 20px;
    right: 20px;
}

.btn-return {
    background: linear-gradient(135deg, #4ecdc4, #3ba89f);
    color: #0a0a1a;
    font-weight: bold;
    border-radius: 25px;
    padding: 12px;
    text-align: center;
    box-shadow: 0 0 15px rgba(78, 205, 196, 0.3);
}

@keyframes float {
    0%, 100% {
        transform: translateY(0);
    }
    50% {
        transform: translateY(-10px);
    }
}

.animate-fade-down {
    animation: fadeDown 0.6s ease-out;
}

.animate-fade-up {
    animation: fadeUp 0.6s ease-out backwards;
}

@keyframes fadeDown {
    from {
        opacity: 0;
        transform: translateY(-20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes fadeUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
</style>