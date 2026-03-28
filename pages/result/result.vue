<template>
  <view class="result-container">
    <view class="result-header">
      <text class="title">游戏结束</text>
      <text class="subtitle">龙争虾斗</text>
    </view>

    <view class="result-content">
      <view class="rankings">
        <view v-for="(player, index) in sortedPlayers" :key="player.id"
          :class="['rank-item', { first: index === 0, second: index === 1, third: index === 2 }]">
          <view class="rank-badge">
            <text class="rank-number">{{ index + 1 }}</text>
          </view>
          <view class="player-info">
            <text class="player-name">{{ player.name }}</text>
            <view class="player-score">
              <text class="score-label">总得分:</text>
              <text class="score-value">{{ gameStore.calculateTotalScore(player) }}</text>
            </view>
          </view>
          <view class="player-details">
            <view class="detail-item">
              <text class="detail-label">德</text>
              <text class="detail-value">{{ player.de }}</text>
            </view>
            <view class="detail-item">
              <text class="detail-label">望</text>
              <text class="detail-value">{{ player.wang }}</text>
            </view>
            <view class="detail-item">
              <text class="detail-label">金币</text>
              <text class="detail-value">{{ player.coins }}</text>
            </view>
          </view>
        </view>
      </view>

      <view class="winner-section" v-if="sortedPlayers.length > 0">
        <text class="winner-title">恭喜</text>
        <text class="winner-name">{{ sortedPlayers[0].name }}</text>
        <text class="winner-desc">获得胜利!</text>
      </view>

      <button class="restart-btn" @click="restartGame">再来一局</button>
      <button class="home-btn" @click="goHome">返回首页</button>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { useGameStore } from '@stores/game.js'

const gameStore = useGameStore()

const sortedPlayers = computed(() => {
  return gameStore.getSortedPlayers()
})

const restartGame = () => {
  gameStore.initGame(gameStore.players.length)
  uni.navigateTo({
    url: '/pages/game/game'
  })
}

const goHome = () => {
  uni.redirectTo({
    url: '/pages/index/index'
  })
}
</script>

<style scoped>
.result-container {
  min-height: 100vh;
  padding: 1.25rem;
  background: linear-gradient(135deg, var(--secondary-light) 0%, var(--secondary-color) 100%);
  display: flex;
  flex-direction: column;
  animation: fadeIn 0.8s ease-out;
}

.result-header {
  text-align: center;
  padding: 1.875rem 0;
  margin-bottom: 1rem;
}

.title {
  display: block;
  font-size: 2.5rem;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  margin-bottom: 0.3125rem;
  animation: fadeIn 1s ease-out 0.2s both;
}

.subtitle {
  display: block;
  font-size: 1.125rem;
  color: rgba(255, 255, 255, 0.9);
  animation: fadeIn 1s ease-out 0.4s both;
}

.result-content {
  background: var(--background-light);
  border-radius: 1.25rem;
  padding: 1.875rem;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  max-width: 600px;
  margin: 0 auto;
  flex: 1;
  animation: fadeIn 1s ease-out 0.6s both;
}

.rankings {
  margin-bottom: 1.5625rem;
}

.rank-item {
  display: flex;
  align-items: center;
  padding: 1.25rem;
  background: var(--background-gray);
  border-radius: 0.9375rem;
  margin-bottom: 0.9375rem;
  border: 2px solid transparent;
  transition: all 0.3s ease;
  animation: slideUp 0.5s ease-out;
}

.rank-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.rank-item.first {
  background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
  border-color: #ffd700;
  box-shadow: 0 4px 16px rgba(255, 215, 0, 0.3);
}

.rank-item.second {
  background: linear-gradient(135deg, #c0c0c0 0%, #e8e8e8 100%);
  border-color: #c0c0c0;
  box-shadow: 0 4px 16px rgba(192, 192, 192, 0.3);
}

.rank-item.third {
  background: linear-gradient(135deg, #cd7f32 0%, #daa06d 100%);
  border-color: #cd7f32;
  box-shadow: 0 4px 16px rgba(205, 127, 50, 0.3);
}

.rank-badge {
  width: 3.125rem;
  height: 3.125rem;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 0.9375rem;
  flex-shrink: 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.rank-number {
  font-size: 1.375rem;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.player-info {
  flex: 1;
  margin-right: 1rem;
}

.player-name {
  display: block;
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.player-score {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.score-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.score-value {
  font-size: 1.375rem;
  font-weight: 700;
  color: var(--primary-color);
}

.player-details {
  display: flex;
  gap: 0.9375rem;
  flex-shrink: 0;
}

.detail-item {
  text-align: center;
  padding: 0.625rem 0.9375rem;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 0.5rem;
  transition: all 0.3s ease;
}

.detail-item:hover {
  background: rgba(255, 255, 255, 0.8);
  transform: translateY(-2px);
}

.detail-label {
  display: block;
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-bottom: 0.1875rem;
}

.detail-value {
  display: block;
  font-size: 0.9375rem;
  font-weight: 700;
  color: var(--text-primary);
}

.winner-section {
  text-align: center;
  padding: 1.5625rem 0;
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%);
  border-radius: 0.9375rem;
  margin-bottom: 1.5625rem;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
  animation: pulse 2s infinite;
}

.winner-title {
  display: block;
  font-size: 1.125rem;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 0.5rem;
}

.winner-name {
  display: block;
  font-size: 1.75rem;
  font-weight: 700;
  color: #fff;
  margin: 0.5rem 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.winner-desc {
  display: block;
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.9);
  margin-top: 0.5rem;
}

.restart-btn {
  width: 100%;
  height: 3.75rem;
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%);
  color: #fff;
  font-size: 1.25rem;
  font-weight: 600;
  border: none;
  border-radius: 1.875rem;
  margin-bottom: 0.9375rem;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.restart-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.restart-btn:hover::before {
  left: 100%;
}

.restart-btn:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
}

.restart-btn:active {
  transform: translateY(0);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.home-btn {
  width: 100%;
  height: 3.75rem;
  background: var(--background-gray);
  color: var(--text-primary);
  font-size: 1.125rem;
  font-weight: 600;
  border: 1px solid var(--border-color);
  border-radius: 1.875rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.home-btn:hover {
  background: var(--border-color);
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.home-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .result-container {
    padding: 1rem;
  }
  
  .result-header {
    padding: 1.5rem 0;
  }
  
  .title {
    font-size: 2rem;
  }
  
  .result-content {
    padding: 1.5rem;
  }
  
  .rank-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
    padding: 1rem;
  }
  
  .player-details {
    width: 100%;
    justify-content: space-between;
  }
  
  .winner-name {
    font-size: 1.5rem;
  }
  
  .restart-btn,
  .home-btn {
    height: 3.5rem;
    font-size: 1.125rem;
  }
}

/* 动画效果 */
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

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulse {
  0% {
    transform: scale(1);
    box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
  }
  50% {
    transform: scale(1.02);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
  }
  100% {
    transform: scale(1);
    box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
  }
}
</style>
