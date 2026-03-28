<template>
  <view class="container">
    <view class="header">
      <text class="title">龙争虾斗</text>
      <text class="subtitle">桌游</text>
    </view>
    <view class="content">
      <view class="section">
        <text class="section-title">选择玩家数量</text>
        <view class="player-options">
          <view v-for="count in [2, 3, 4]" :key="count"
            :class="['player-option', { active: selectedPlayerCount === count }]" @click="selectPlayerCount(count)">
            <text class="player-count">{{ count }}</text>
            <text class="player-label">名玩家</text>
          </view>
        </view>
      </view>

      <view class="section">
        <text class="section-title">游戏规则简介</text>
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

<style scoped>
.container {
  min-height: 100vh;
  padding: 1rem;
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%);
  display: flex;
  flex-direction: column;
  animation: fadeIn 0.8s ease-out;
}

.header {
  text-align: center;
  padding: 2rem 0;
  margin-bottom: 1rem;
}

.title {
  display: block;
  font-size: 2.5rem;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  margin-bottom: 0.5rem;
  animation: fadeIn 1s ease-out 0.2s both;
}

.subtitle {
  display: block;
  font-size: 1.125rem;
  color: rgba(255, 255, 255, 0.8);
  animation: fadeIn 1s ease-out 0.4s both;
}

.content {
  background: var(--background-light);
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  max-width: 600px;
  margin: 0 auto;
  flex: 1;
  animation: fadeIn 1s ease-out 0.6s both;
}

.section {
  margin-bottom: 1.5rem;
}

.section-title {
  display: block;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 1rem;
}

.player-options {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.player-option {
  flex: 1;
  padding: 1.5rem 0.75rem;
  border: 2px solid var(--border-color);
  border-radius: 0.75rem;
  text-align: center;
  transition: all 0.3s ease;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.player-option::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.1), transparent);
  transition: left 0.5s;
}

.player-option:hover::before {
  left: 100%;
}

.player-option:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.player-option.active {
  border-color: var(--primary-color);
  background: rgba(102, 126, 234, 0.1);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.player-count {
  display: block;
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
}

.player-label {
  display: block;
  font-size: 0.875rem;
  color: var(--text-muted);
}

.rules {
  background: var(--background-gray);
  border-radius: 0.75rem;
  padding: 1.25rem;
  margin-bottom: 1.5rem;
}

.rule-item {
  display: block;
  font-size: 0.9375rem;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 0.5rem;
  position: relative;
  padding-left: 1.25rem;
}

.rule-item::before {
  content: '•';
  position: absolute;
  left: 0;
  color: var(--primary-color);
  font-weight: bold;
}

.start-btn {
  width: 100%;
  height: 3.75rem;
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%);
  color: #fff;
  font-size: 1.25rem;
  font-weight: 600;
  border: none;
  border-radius: 1.875rem;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.start-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.start-btn:hover::before {
  left: 100%;
}

.start-btn:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
}

.start-btn:active {
  transform: translateY(0);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .container {
    padding: 1rem;
  }
  
  .header {
    padding: 1.5rem 0;
  }
  
  .title {
    font-size: 2rem;
  }
  
  .content {
    padding: 1.25rem;
  }
  
  .player-option {
    padding: 1.25rem 0.5rem;
  }
  
  .player-count {
    font-size: 1.5rem;
  }
  
  .start-btn {
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
</style>
