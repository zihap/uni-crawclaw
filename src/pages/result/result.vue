<template>
  <view class="result-container">
    <view class="result-header">
      <text class="result-title">游戏结束</text>
      <text class="result-subtitle">龙争虾斗</text>
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
