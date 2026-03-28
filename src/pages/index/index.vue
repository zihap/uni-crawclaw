<template>
  <view class="index-container">
    <view class="index-header">
      <text class="index-title">龙争虾斗</text>
      <text class="index-subtitle">桌游</text>
    </view>
    <view class="index-content">
      <view class="index-section">
        <text class="index-section-title">选择玩家数量</text>
        <view class="player-options">
          <view v-for="count in [2, 3, 4]" :key="count"
            :class="['player-option', { active: selectedPlayerCount === count }]" @click="selectPlayerCount(count)">
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
    }
  }
}
</script>
