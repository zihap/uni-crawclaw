<template>
    <view class="index-container">
        <view class="scanline"></view>
        <view class="grid-bg"></view>
        <view class="index-header">
            <view class="title-decoration"></view>
            <text class="index-title">龙争虾斗</text>
            <text class="index-subtitle">德策放置桌游</text>
            <view class="title-decoration"></view>
        </view>
        <view class="index-content">
            <view class="index-section">
                <text class="index-section-title">选择玩家数量</text>
                <view class="player-options">
                    <view
                        v-for="count in [2, 3, 4]"
                        :key="count"
                        :class="['player-option', { active: selectedPlayerCount === count }]"
                        @click="selectPlayerCount(count)"
                    >
                        <text class="player-count">{{ count }}</text>
                        <text class="player-label">名玩家</text>
                    </view>
                </view>
            </view>

            <view class="index-section">
                <text class="index-section-title">游戏规则简介</text>
                <view class="rules">
                    <text class="rule-item">共5个回合，每回合分为4个阶段</text>
                    <text class="rule-item">通过放置里长获取资源和行动</text>
                    <text class="rule-item">德值 × 望值 + 额外分数 = 总得分</text>
                    <text class="rule-item">总得分最高者获胜</text>
                </view>
            </view>

            <button class="start-btn" @click="startGame">开始游戏</button>
            <button class="online-btn" @click="goToLobby">联机对战</button>
        </view>
    </view>
</template>

<script>
import { useGameStore } from '@stores/game.js'

export default {
    data() {
        return {
            selectedPlayerCount: 2
        }
    },
    computed: {
        gameStore() {
            return useGameStore()
        }
    },
    methods: {
        selectPlayerCount(count) {
            this.selectedPlayerCount = count
        },
        startGame() {
            this.gameStore.initGame(this.selectedPlayerCount)
            uni.navigateTo({
                url: '/pages/game/game'
            })
        },
        goToLobby() {
            uni.navigateTo({
                url: '/pages/lobby/lobby'
            })
        }
    }
}
</script>

<style scoped>
.index-container {
    min-height: 100vh;
    padding: 1rem;
    background: #0a0a1a;
    display: flex;
    flex-direction: column;
    position: relative;
    overflow: hidden;
}

.grid-bg {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background:
        linear-gradient(rgba(78, 205, 196, 0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(78, 205, 196, 0.04) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
    z-index: 0;
}

.scanline {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 200px;
    background: linear-gradient(to bottom, transparent, rgba(233, 69, 96, 0.04), transparent);
    animation: scanline 8s linear infinite;
    pointer-events: none;
    z-index: 1;
}

@keyframes scanline {
    0% {
        transform: translateY(-200px);
    }
    100% {
        transform: translateY(100vh);
    }
}

.index-header {
    text-align: center;
    padding: 2rem 0;
    margin-bottom: 1rem;
    position: relative;
    z-index: 2;
}

.title-decoration {
    display: block;
    width: 100px;
    height: 2px;
    background: linear-gradient(90deg, transparent, #e94560, transparent);
    margin: 0 auto 12px;
    box-shadow: 0 0 10px rgba(233, 69, 96, 0.5);
}

.index-title {
    display: block;
    font-size: 2.5rem;
    font-weight: 700;
    color: #fff;
    text-shadow:
        0 0 15px rgba(233, 69, 96, 0.6),
        0 0 30px rgba(233, 69, 96, 0.3),
        0 0 60px rgba(233, 69, 96, 0.15);
    margin-bottom: 0.5rem;
    letter-spacing: 4px;
    animation: titleGlow 3s ease-in-out infinite;
}

@keyframes titleGlow {
    0%,
    100% {
        text-shadow:
            0 0 15px rgba(233, 69, 96, 0.6),
            0 0 30px rgba(233, 69, 96, 0.3),
            0 0 60px rgba(233, 69, 96, 0.15);
    }
    50% {
        text-shadow:
            0 0 20px rgba(233, 69, 96, 0.8),
            0 0 40px rgba(233, 69, 96, 0.5),
            0 0 80px rgba(233, 69, 96, 0.25);
    }
}

.index-subtitle {
    display: block;
    font-size: 1.125rem;
    color: #4ecdc4;
    text-shadow: 0 0 10px rgba(78, 205, 196, 0.4);
    letter-spacing: 6px;
}

.index-content {
    background: #1a1a2e;
    border-radius: 1rem;
    padding: 1.5rem;
    box-shadow:
        0 0 40px rgba(0, 0, 0, 0.5),
        0 0 20px rgba(78, 205, 196, 0.05);
    max-width: 600px;
    margin: 0 auto;
    flex: 1;
    animation: fadeIn 1s ease-out 0.6s both;
    position: relative;
    z-index: 2;
    border: 1px solid rgba(78, 205, 196, 0.15);
}

.index-content::before {
    content: '';
    position: absolute;
    top: -1px;
    left: 15%;
    right: 15%;
    height: 2px;
    background: linear-gradient(90deg, transparent, #4ecdc4, transparent);
    border-radius: 50%;
}

.index-section {
    margin-bottom: 1.5rem;
}

.index-section-title {
    display: block;
    font-size: 1.25rem;
    font-weight: 600;
    color: #fff;
    margin-bottom: 1rem;
    text-shadow: 0 0 8px rgba(78, 205, 196, 0.3);
}

.player-options {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.5rem;
}

.player-option {
    flex: 1;
    padding: 1.5rem 0.75rem;
    border: 2px solid rgba(78, 205, 196, 0.15);
    border-radius: 0.75rem;
    text-align: center;
    transition: all 0.3s ease;
    cursor: pointer;
    position: relative;
    overflow: hidden;
    background: #16213e;
}

.player-option::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(78, 205, 196, 0.08), transparent);
    transition: left 0.5s;
}

.player-option:hover::before {
    left: 100%;
}

.player-option:hover {
    transform: translateY(-4px);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
    border-color: rgba(78, 205, 196, 0.3);
}

.player-option.active {
    border-color: #e94560;
    background: linear-gradient(135deg, rgba(233, 69, 96, 0.15), rgba(233, 69, 96, 0.05));
    box-shadow: 0 0 20px rgba(233, 69, 96, 0.2);
}

.player-count {
    display: block;
    font-size: 1.75rem;
    font-weight: 700;
    color: #fff;
    margin-bottom: 0.25rem;
}

.player-option.active .player-count {
    color: #e94560;
    text-shadow: 0 0 10px rgba(233, 69, 96, 0.4);
}

.player-label {
    display: block;
    font-size: 0.875rem;
    color: #a0a0b0;
}

.rules {
    background: #16213e;
    border-radius: 0.75rem;
    padding: 1.25rem;
    margin-bottom: 1.5rem;
    border: 1px solid rgba(78, 205, 196, 0.1);
}

.rule-item {
    display: block;
    font-size: 0.9375rem;
    color: #a0a0b0;
    line-height: 1.6;
    margin-bottom: 0.5rem;
    position: relative;
    padding-left: 1.25rem;
}

.rule-item::before {
    content: '▸';
    position: absolute;
    left: 0;
    color: #4ecdc4;
    font-weight: bold;
    text-shadow: 0 0 8px rgba(78, 205, 196, 0.4);
}

.start-btn {
    width: 100%;
    height: 3.75rem;
    background: linear-gradient(135deg, #e94560 0%, #c23152 100%);
    color: #fff;
    font-size: 1.25rem;
    font-weight: 600;
    border: none;
    border-radius: 1.875rem;
    cursor: pointer;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
    box-shadow:
        0 0 20px rgba(233, 69, 96, 0.4),
        0 4px 12px rgba(0, 0, 0, 0.3);
    margin-bottom: 1rem;
}

.start-btn::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.15), transparent);
    transition: left 0.5s;
}

.start-btn:hover::before {
    left: 100%;
}

.start-btn:hover {
    transform: translateY(-4px);
    box-shadow:
        0 0 30px rgba(233, 69, 96, 0.6),
        0 8px 24px rgba(0, 0, 0, 0.3);
}

.start-btn:active {
    transform: translateY(0);
    box-shadow:
        0 0 20px rgba(233, 69, 96, 0.4),
        0 4px 12px rgba(0, 0, 0, 0.3);
}

.online-btn {
    width: 100%;
    height: 3.75rem;
    background: transparent;
    color: #4ecdc4;
    font-size: 1.25rem;
    font-weight: 600;
    border: 2px solid rgba(78, 205, 196, 0.4);
    border-radius: 1.875rem;
    cursor: pointer;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
    box-shadow: 0 0 15px rgba(78, 205, 196, 0.1);
}

.online-btn:hover {
    transform: translateY(-4px);
    background: rgba(78, 205, 196, 0.1);
    border-color: #4ecdc4;
    box-shadow:
        0 0 25px rgba(78, 205, 196, 0.3),
        0 8px 24px rgba(0, 0, 0, 0.3);
}

.online-btn:active {
    transform: translateY(0);
    box-shadow: 0 0 15px rgba(78, 205, 196, 0.1);
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@media (max-width: 768px) {
    .index-container {
        padding: 1rem;
    }

    .index-header {
        padding: 1.5rem 0;
    }

    .index-title {
        font-size: 2rem;
    }

    .index-content {
        padding: 1.25rem;
    }

    .player-option {
        padding: 1.25rem 0.5rem;
    }

    .player-count {
        font-size: 1.5rem;
    }

    .start-btn,
    .online-btn {
        height: 3.5rem;
        font-size: 1.125rem;
    }
}
</style>
