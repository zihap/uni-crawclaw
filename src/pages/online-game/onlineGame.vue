<template>
    <view class="game-container">
        <view class="game-header">
            <view class="round-info">
                <text class="round-label">回合</text>
                <text class="round-number">{{ onlineGameStore.currentRound }}/{{ onlineGameStore.maxRounds }}</text>
            </view>
            <view class="phase-info">
                <text class="phase-label">{{ phaseText }}</text>
            </view>
            <button
                    class="next-btn"
                    v-if="onlineGameStore.currentPhase !== 'settlement'"
                    @click="handleNextPhase"
                    :disabled="!onlineGameStore.isMyTurn"
            >
                下一阶段
            </button>
        </view>

        <view class="shrimp-draw-messages">
            <view v-for="msg in shrimpDrawMessages" :key="msg.id" class="shrimp-draw-msg">
                <text class="shrimp-draw-msg-text">{{ msg.text }}</text>
            </view>
        </view>

        <view v-if="isPlacementPhase" class="placement-banner">
            <view class="placement-info">
                <text class="placement-text">
                    {{ onlineGameStore.isMyTurn ? '轮到你放置里长' : `等待 ${currentPlacementPlayerName} 放置里长` }}
                </text>
                <text class="placement-hint"> 点击空闲的行动格放置里长 </text>
            </view>
        </view>

        <view class="players-bar">
            <view
                    v-for="(player, index) in playerStore.players"
                    :key="player.id"
                    :class="[
                    'player-item',
                    {
                        active: isCurrentPlacementPlayer(index),
                        'is-me': player.id === onlineGameStore.playerId,
                        starting: player.isStartingPlayer
                    }
                ]"
                    :style="getPlayerItemStyle(index)"
            >
                <view class="player-badge" v-if="player.isStartingPlayer">起始</view>
                <view class="player-badge me-badge" v-if="player.id === onlineGameStore.playerId">我</view>
                <text class="player-name">{{ player.name }}</text>
                <view class="player-stats">
                    <text class="stat">德:{{ player.de }}</text>
                    <text class="stat">望:{{ player.wang }}</text>
                    <text class="stat">金:{{ player.coins }}</text>
                    <text class="stat">里长:{{ player.liZhang }}</text>
                </view>
            </view>
        </view>

        <view class="main-board">
            <view class="board-section">
                <view class="section-header">
                    <text class="section-title">捕虾区</text>
                    <text class="section-desc">放置里长获取捕虾机会</text>
                </view>
                <view class="area-slots">
                    <view
                            v-for="i in 4"
                            :key="i"
                            :class="[
                            'slot',
                            {
                                occupied: isSlotOccupied('shrimp_catching', i - 1),
                                disabled: !canPlaceOnSlot('shrimp_catching', i - 1),
                                'is-mine': isMySlot('shrimp_catching', i - 1)
                            }
                        ]"
                            :style="getSlotStyle('shrimp_catching', i - 1)"
                            @click="handleSlotClick('shrimp_catching', i - 1)"
                    >
                        <view v-if="getSlotOccupantLabel('shrimp_catching', i - 1)" class="slot-occupant-badge">
                            {{ getSlotOccupantLabel('shrimp_catching', i - 1) }}
                        </view>
                        <text class="slot-number">{{ i }}号</text>
                        <text class="slot-desc">{{ getShrimpCatchingSlotDesc(i) }}</text>
                    </view>
                </view>
            </view>

            <view class="board-section">
                <view class="section-header">
                    <text class="section-title">海鲜市场</text>
                    <text class="section-desc">放置里长进行交易</text>
                </view>
                <view class="area-slots">
                    <view
                            v-for="i in 4"
                            :key="i"
                            :class="[
                            'slot',
                            {
                                occupied: isSlotOccupied('seafood_market', i - 1),
                                disabled: !canPlaceOnSlot('seafood_market', i - 1),
                                'is-mine': isMySlot('seafood_market', i - 1)
                            }
                        ]"
                            :style="getSlotStyle('seafood_market', i - 1)"
                            @click="handleSlotClick('seafood_market', i - 1)"
                    >
                        <view v-if="getSlotOccupantLabel('seafood_market', i - 1)" class="slot-occupant-badge">
                            {{ getSlotOccupantLabel('seafood_market', i - 1) }}
                        </view>
                        <text class="slot-number">{{ i }}号</text>
                        <text class="slot-desc">{{ getSeafoodMarketSlotDesc(i) }}</text>
                    </view>
                </view>
            </view>

            <view class="board-section">
                <view class="section-header">
                    <text class="section-title">养蛊区</text>
                    <text class="section-desc">放置里长培养龙虾</text>
                </view>
                <view class="area-slots">
                    <view
                            v-for="i in 4"
                            :key="i"
                            :class="[
                            'slot',
                            {
                                occupied: isSlotOccupied('breeding', i - 1),
                                disabled: !canPlaceOnSlot('breeding', i - 1),
                                'is-mine': isMySlot('breeding', i - 1)
                            }
                        ]"
                            :style="getSlotStyle('breeding', i - 1)"
                            @click="handleSlotClick('breeding', i - 1)"
                    >
                        <view v-if="getSlotOccupantLabel('breeding', i - 1)" class="slot-occupant-badge">
                            {{ getSlotOccupantLabel('breeding', i - 1) }}
                        </view>
                        <text class="slot-number">{{ i }}号</text>
                        <text class="slot-desc">{{ getBreedingSlotDesc(i) }}</text>
                    </view>
                </view>
            </view>

            <view class="board-section">
                <view class="section-header">
                    <text class="section-title">上供区</text>
                    <text class="section-desc">放置里长完成上供任务</text>
                </view>
                <view class="area-slots">
                    <view
                            v-for="i in 8"
                            :key="i"
                            :class="[
                            'slot',
                            {
                                occupied: isSlotOccupied('tribute', i - 1),
                                disabled: !canPlaceOnSlot('tribute', i - 1) || !isTributeSlotAvailable(i - 1),
                                'challenge-slot': i > 3 && i <= 6,
                                'is-mine': isMySlot('tribute', i - 1)
                            }
                        ]"
                            :style="getSlotStyle('tribute', i - 1)"
                            @click="handleSlotClick('tribute', i - 1)"
                    >
                        <view v-if="getSlotOccupantLabel('tribute', i - 1)" class="slot-occupant-badge">
                            {{ getSlotOccupantLabel('tribute', i - 1) }}
                        </view>
                        <text class="slot-number">{{ i }}号</text>
                        <text class="slot-desc">{{ getTributeSlotDesc(i) }}</text>
                    </view>
                </view>
            </view>

            <view class="board-section">
                <view class="section-header">
                    <text class="section-title">闹市区</text>
                    <text class="section-desc">放置里长执行闹市行动</text>
                </view>
                <view class="area-slots">
                    <view
                            v-for="i in 3"
                            :key="i"
                            :class="[
                            'slot',
                            {
                                occupied: isSlotOccupied('marketplace', i - 1),
                                disabled: !canPlaceOnSlot('marketplace', i - 1) || !isMarketplaceAvailable(i),
                                'is-mine': isMySlot('marketplace', i - 1)
                            }
                        ]"
                            :style="getSlotStyle('marketplace', i - 1)"
                            @click="handleSlotClick('marketplace', i - 1)"
                    >
                        <view v-if="getSlotOccupantLabel('marketplace', i - 1)" class="slot-occupant-badge">
                            {{ getSlotOccupantLabel('marketplace', i - 1) }}
                        </view>
                        <text class="slot-number">{{ i }}号</text>
                        <text class="slot-desc">{{ getMarketplaceSlotDesc(i) }}</text>
                    </view>
                </view>
            </view>
        </view>

        <view class="current-player-panel" v-if="onlineGameStore.myPlayer">
            <view class="panel-header">
                <text class="panel-title">{{ onlineGameStore.myPlayer.name }}的回合</text>
                <text class="lizhang-count"
                >里长: {{ onlineGameStore.myPlayer.headmen || onlineGameStore.myPlayer.liZhang || 0 }}
                </text
                >
            </view>
            <view class="panel-resources">
                <view class="resource-item">
                    <text class="resource-label">金币</text>
                    <text class="resource-value">{{
                            onlineGameStore.myPlayer.gold || onlineGameStore.myPlayer.coins || 0
                        }}
                    </text>
                </view>
                <view class="resource-item">
                    <text class="resource-label">海草</text>
                    <text class="resource-value">{{ onlineGameStore.myPlayer.seaweed || 0 }}</text>
                </view>
                <view class="resource-item">
                    <text class="resource-label">虾笼</text>
                    <text class="resource-value">{{ onlineGameStore.myPlayer.cages || 0 }}</text>
                </view>
                <view class="resource-item lobster-resource" @longpress="showLobsterList = true">
                    <text class="resource-label">龙虾</text>
                    <text class="resource-value">{{
                            onlineGameStore.myPlayer.lobsters?.length || onlineGameStore.myPlayer.titleCards?.length
                        }}
                    </text>
                </view>
                <view class="resource-item tribute-cards-item" @longpress="showTributeCards = true">
                    <text class="resource-label">上供卡</text>
                    <text class="resource-value">{{ onlineGameStore.myPlayer.tributeCards?.length || 0 }}</text>
                </view>
            </view>
        </view>

        <view v-if="showLobsterList" class="lobster-list-overlay" @click="showLobsterList = false">
            <view class="lobster-list-panel" @click.stop>
                <view class="lobster-list-header">
                    <text class="lobster-list-title"
                    >我的龙虾 ({{ onlineGameStore.myPlayer.lobsters?.length || 0 }})
                    </text
                    >
                    <text class="lobster-list-close" @click="showLobsterList = false">✕</text>
                </view>
                <view class="lobster-list-body">
                    <view v-if="onlineGameStore.myPlayer.lobsters?.length" class="lobster-list-grid">
                        <view
                                v-for="lobster in onlineGameStore.myPlayer.lobsters"
                                :key="lobster.id"
                                class="lobster-list-item"
                        >
                            <text class="lobster-list-icon">🦞</text>
                            <text class="lobster-list-grade">{{ getLobsterGradeName(lobster.grade) }}</text>
                            <text v-if="lobster.title" class="lobster-list-title-tag">{{ lobster.title.name }}</text>
                        </view>
                    </view>
                    <view v-else class="empty-list-hint">暂无龙虾</view>

                    <view v-if="onlineGameStore.myPlayer.titleCards?.length" class="title-cards-section">
                        <text class="title-cards-label">称号 ({{ onlineGameStore.myPlayer.titleCards?.length }})</text>
                        <view class="title-cards-grid">
                            <view
                                    v-for="card in onlineGameStore.myPlayer.titleCards"
                                    :key="card.id"
                                    class="title-card-item"
                            >
                                <text class="title-card-name">{{ card.name }}</text>
                                <text v-if="card.description" class="title-card-desc">{{ card.description }}</text>
                            </view>
                        </view>
                    </view>
                </view>
            </view>
        </view>

        <view v-if="showTributeCards" class="tribute-cards-overlay" @click="showTributeCards = false">
            <view class="tribute-cards-panel" @click.stop>
                <view class="tribute-cards-header">
                    <text class="tribute-cards-title"
                    >我的上供卡 ({{ onlineGameStore.myPlayer.tributeCards?.length }})
                    </text
                    >
                    <text class="tribute-cards-close" @click="showTributeCards = false">✕</text>
                </view>
                <view class="tribute-cards-body">
                    <view v-if="onlineGameStore.myPlayer.tributeCards?.length" class="tribute-cards-grid">
                        <view
                                v-for="card in onlineGameStore.myPlayer.tributeCards"
                                :key="card.id"
                                class="tribute-card-item"
                        >
                            <text class="tribute-card-name">{{ card.name }}</text>
                            <text v-if="card.effectDesc" class="tribute-card-desc">{{ card.effectDesc }}</text>
                        </view>
                    </view>
                    <view v-else class="empty-list-hint">暂无上供卡</view>
                </view>
            </view>
        </view>

        <view class="log-panel">
            <view class="log-header" @click="showLog = !showLog">
                <text class="log-title">游戏日志</text>
                <text class="log-toggle">{{ showLog ? '收起' : '展开' }}</text>
            </view>
            <view class="log-content" v-if="showLog">
                <view class="log-scroll">
                    <view
                            v-for="(log, index) in onlineGameStore.logs?.slice().reverse() || []"
                            :key="index"
                            :class="['log-item', log.type || 'info']"
                    >
                        <text class="log-text">{{ log.message }}</text>
                    </view>
                </view>
            </view>
        </view>

        <view class="modal-overlay" v-if="showSettlementModal && pendingSettlement?.areaType === 'shrimp_catching'">
            <view class="modal-content shrimp-modal">
                <view class="modal-header">
                    <view class="modal-title-group">
                        <text class="modal-title">{{ pendingSettlement?.player?.name }} 的捕虾行动</text>
                        <text class="modal-subtitle"
                        >剩余次数:
                            <text class="highlight">{{ pendingSettlement?.actionCount }}</text>
                        </text>
                    </view>
                </view>

                <view class="modal-body">
                    <view v-if="pendingSettlement?.step === 'waiting_confirm'" class="indicator-display">
                        <text class="indicator-icon">🎣</text>
                        <text class="indicator-text">确认继续捕虾？</text>
                    </view>

                    <view v-else class="indicator-display">
                        <text class="indicator-icon">🎣</text>
                        <text class="indicator-text">抽到了"龙虾或海草"，请选择：</text>
                    </view>

                    <view v-if="pendingSettlement?.step === 'waiting_confirm'" class="choice-buttons">
                        <button class="btn btn-choice" @click="confirmShrimpCatch">确认抽取</button>
                    </view>

                    <view v-else class="choice-buttons">
                        <button class="btn btn-choice" @click="chooseShrimpReward('lobster')">🦞 选择龙虾</button>
                        <button class="btn btn-choice" @click="chooseShrimpReward('seaweed')">🌿 选择海草</button>
                    </view>
                </view>

                <view class="modal-footer">
                    <button class="btn btn-secondary w-full" @click="skipSettlementAction">放弃剩余次数并结束</button>
                </view>
            </view>
        </view>

        <view class="modal-overlay" v-if="showSettlementModal && pendingSettlement?.areaType === 'seafood_market'">
            <view class="modal-content seafood-market-modal">
                <view class="modal-header">
                    <view class="modal-title-group">
                        <text class="modal-title">{{ pendingSettlement?.player?.name }} 的市场交易</text>
                        <text class="modal-subtitle"
                        >剩余行动次数:
                            <text class="highlight">{{ pendingSettlement?.actionCount }}</text>
                        </text>
                    </view>
                </view>

                <view class="market-display-board">
                    <view class="market-prices">
                        <text class="price-title">当前流通物价</text>
                        <view class="price-tags">
                            <text>龙虾买: {{ marketPrices.buyLobster }}金 / 卖: {{ marketPrices.sellLobster }}金</text>
                            <text>虾笼买: {{ marketPrices.buyCage }}金 / 卖: {{ marketPrices.sellCage }}金</text>
                            <text>海草买: {{ marketPrices.buySeaweed }}金 / 卖: {{ marketPrices.sellSeaweed }}金</text>
                        </view>
                    </view>
                </view>

                <view class="modal-body">
                    <view class="trade-grid">
                        <view class="trade-row">
                            <button
                                    class="btn btn-outline"
                                    @click="doSeafoodTrade('buy_lobster')"
                                    :disabled="!canBuyLobster"
                            >
                                买入龙虾 (-{{ marketPrices.buyLobster }}金)
                            </button>
                            <button
                                    class="btn btn-outline"
                                    @click="doSeafoodTrade('sell_lobster')"
                                    :disabled="!canSellLobster"
                            >
                                卖出龙虾 (+{{ marketPrices.sellLobster }}金)
                            </button>
                        </view>
                        <view class="trade-row">
                            <button class="btn btn-outline" @click="doSeafoodTrade('buy_cage')" :disabled="!canBuyCage">
                                买入虾笼 (-{{ marketPrices.buyCage }}金)
                            </button>
                            <button
                                    class="btn btn-outline"
                                    @click="doSeafoodTrade('sell_cage')"
                                    :disabled="!canSellCage"
                            >
                                卖出虾笼 (+{{ marketPrices.sellCage }}金)
                            </button>
                        </view>
                        <view class="trade-row">
                            <button
                                    class="btn btn-outline"
                                    @click="doSeafoodTrade('buy_seaweed')"
                                    :disabled="!canBuySeaweed"
                            >
                                买海草 (-{{ marketPrices.buySeaweed }}金)
                            </button>
                            <button
                                    class="btn btn-outline"
                                    @click="doSeafoodTrade('sell_seaweed')"
                                    :disabled="!canSellSeaweed"
                            >
                                卖海草 (+{{ marketPrices.sellSeaweed }}金)
                            </button>
                        </view>
                        <view class="trade-row">
                            <button class="btn btn-outline" @click="doSeafoodTrade('hire')" :disabled="!canHire">
                                雇佣头目 (-6金)
                            </button>
                        </view>
                    </view>
                </view>

                <view class="modal-footer">
                    <button class="btn btn-secondary w-full" @click="skipSettlementAction">放弃剩余次数并结束</button>
                </view>
            </view>
        </view>

        <view class="modal-overlay" v-if="showSettlementModal && pendingSettlement?.areaType === 'breeding'">
            <view class="modal-content breeding-modal">
                <view class="modal-header">
                    <view class="modal-title-group">
                        <text class="modal-title">{{ pendingSettlement?.player?.name }} 的培养行动</text>
                        <text class="modal-subtitle"
                        >剩余次数:
                            <text class="highlight">{{ pendingSettlement?.actionCount }}</text>
                        </text>
                    </view>
                </view>

                <view class="modal-body">
                    <view v-if="breedingState.lobsterIndex === -1" class="lobster-selection">
                        <text class="section-label">请选择要进行培养的龙虾：</text>
                        <view class="lobster-grid">
                            <view
                                    v-for="(lobster, index) in pendingSettlement?.player?.lobsters"
                                    :key="lobster.id"
                                    class="lobster-card"
                                    :class="{ 'max-royal': lobster.grade === LOBSTER_GRADES.ROYAL }"
                                    @click="lobster.grade !== LOBSTER_GRADES.ROYAL && selectLobsterForBreeding(index)"
                            >
                                <text class="lobster-icon">🦞</text>
                                <text class="lobster-grade">{{ getLobsterGradeName(lobster.grade) }}</text>
                                <text class="lobster-title" v-if="lobster.title">{{ lobster.title.name }}</text>
                                <view v-if="lobster.grade === LOBSTER_GRADES.ROYAL" class="max-grade-mask">已满级</view>
                            </view>
                        </view>
                        <view v-if="!pendingSettlement?.player?.lobsters?.length" class="empty-hint">
                            您目前没有任何龙虾。
                        </view>
                    </view>

                    <view v-else class="breeding-action-panel">
                        <view class="upgrade-path">
                            <view class="grade-box current">
                                <text>当前</text>
                                <text class="val">{{ getLobsterGradeName(targetLobster.grade) }}</text>
                            </view>
                            <text class="arrow">➔</text>
                            <view class="grade-box target">
                                <text>目标</text>
                                <text class="val highlight">{{ getLobsterGradeName(projectedGrade) }}</text>
                            </view>
                        </view>

                        <view class="options-group">
                            <view
                                    class="checkbox-wrapper"
                                    @click="toggleSeaweed"
                                    :class="{
                                    disabled:
                                        (pendingSettlement?.player?.seaweed < 1 && !breedingState.useSeaweed) ||
                                        !isSeaweedUseful
                                }"
                            >
                                <view class="custom-checkbox" :class="{ checked: breedingState.useSeaweed }"></view>
                                <text class="checkbox-text"
                                >消耗 1 海草 额外升一品 (拥有: {{ pendingSettlement?.player?.seaweed }})
                                </text>
                            </view>
                        </view>

                        <view v-if="isUpgradingToRoyal" class="royal-requirements animate-fade-in">
                            <text class="req-title">突破至皇家级需支付额外费用：</text>
                            <view class="cost-options">
                                <button
                                        class="cost-btn"
                                        :class="{ active: breedingState.royalCostType === 'cage' }"
                                        :disabled="pendingSettlement?.player?.cages < 1"
                                        @click="breedingState.royalCostType = 'cage'"
                                >
                                    🦞 1 虾笼 (拥有: {{ pendingSettlement?.player?.cages }})
                                </button>
                                <button
                                        class="cost-btn"
                                        :class="{ active: breedingState.royalCostType === 'coin' }"
                                        :disabled="pendingSettlement?.player?.coins < 3"
                                        @click="breedingState.royalCostType = 'coin'"
                                >
                                    🪙 3 金币 (拥有: {{ pendingSettlement?.player?.coins }})
                                </button>
                            </view>

                            <view class="req-title" style="margin-top: 1rem">请选择升级皇家奖励：</view>
                            <view class="reward-options">
                                <view
                                        class="custom-radio-wrap"
                                        :class="{ active: breedingState.royalRewardType === 'de' }"
                                        @click="breedingState.royalRewardType = 'de'"
                                >
                                    <view
                                            class="custom-radio"
                                            :class="{ checked: breedingState.royalRewardType === 'de' }"
                                    ></view>
                                    获得 1 德
                                </view>
                                <view
                                        class="custom-radio-wrap"
                                        :class="{ active: breedingState.royalRewardType === 'wang' }"
                                        @click="breedingState.royalRewardType = 'wang'"
                                >
                                    <view
                                            class="custom-radio"
                                            :class="{ checked: breedingState.royalRewardType === 'wang' }"
                                    ></view>
                                    获得 1 望
                                </view>
                            </view>

                            <view
                                    v-if="onlineGameStore.gameTitleCards && onlineGameStore.gameTitleCards.length > 0"
                                    class="title-selection"
                                    style="margin-top: 1rem"
                            >
                                <text class="req-title">请挑选一个霸气称号：</text>
                                <view class="title-cards">
                                    <view
                                            v-for="card in onlineGameStore.gameTitleCards"
                                            :key="card.id"
                                            class="title-card"
                                            :class="{ active: breedingState.selectedTitleId === card.id }"
                                            @click="breedingState.selectedTitleId = card.id"
                                    >
                                        {{ card.name }}
                                    </view>
                                </view>
                            </view>
                        </view>

                        <view class="modal-actions">
                            <button class="btn btn-ghost" @click="cancelBreedingAction">返回重选</button>
                            <button
                                    class="btn btn-primary"
                                    :disabled="!canConfirmBreeding"
                                    @click="confirmBreedingAction"
                            >
                                确认培养
                            </button>
                        </view>
                    </view>
                </view>

                <view class="modal-footer" v-if="breedingState.lobsterIndex === -1">
                    <button class="btn btn-secondary w-full" @click="skipSettlementAction">放弃剩余次数并结束</button>
                </view>
            </view>
        </view>

        <view class="modal-overlay" v-if="showSettlementModal && pendingSettlement?.areaType === 'marketplace'">
            <view class="modal-content marketplace-modal">
                <view class="modal-header">
                    <view class="modal-title-group">
                        <text class="modal-title">{{ pendingSettlement?.player?.name }} 的闹市行动</text>
                        <text class="modal-subtitle">请选择本回合尚未被执行的一张闹市卡</text>
                    </view>
                </view>

                <view class="modal-body">
                    <view class="marketplace-cards">
                        <view
                                v-for="(card, idx) in pendingSettlement?.availableCards"
                                :key="card.id || idx"
                                class="mp-card"
                                :class="{
                                used: card.usedThisRound,
                                selected: marketplaceState.selectedCard?.id === card.id
                            }"
                                @click="selectMarketplaceCard(card)"
                        >
                            <text class="mp-card-name">{{ card.name }}</text>
                            <text class="mp-card-desc">{{ card.description }}</text>
                            <view v-if="card.usedThisRound" class="used-mask">本回合已被使用</view>
                        </view>
                    </view>

                    <view
                            v-if="
                            marketplaceState.selectedCard &&
                            !marketplaceState.selectedCard.auto &&
                            marketplaceState.selectedCard.action?.type === 'exchange'
                        "
                            class="mp-options-panel animate-fade-in"
                    >
                        <text class="section-label">请选择执行方案：</text>
                        <view class="mp-options">
                            <view
                                    v-for="(opt, optIdx) in marketplaceState.selectedCard.action?.options || []"
                                    :key="optIdx"
                                    class="mp-option-btn"
                                    :class="{ active: marketplaceState.selectedOptionIndex === optIdx }"
                                    @click="marketplaceState.selectedOptionIndex = optIdx"
                            >
                                <view
                                        class="custom-radio"
                                        :class="{ checked: marketplaceState.selectedOptionIndex === optIdx }"
                                ></view>
                                <text class="option-text">{{ formatOptionText(opt) }}</text>
                            </view>
                        </view>
                        <text v-if="!canConfirmMarketplace" class="error-hint">资源不足，无法执行该方案</text>
                    </view>
                </view>

                <view class="modal-footer">
                    <view class="modal-actions">
                        <button class="btn btn-ghost" @click="skipSettlementAction">放弃行动</button>
                        <button
                                class="btn btn-primary"
                                :disabled="!marketplaceState.selectedCard || !canConfirmMarketplace"
                                @click="confirmMarketplaceAction"
                        >
                            确认执行
                        </button>
                    </view>
                </view>
            </view>
        </view>

        <LobsterSelect
                :visible="showArenaModal"
                :challenger="onlineGameStore.currentArenaBattle?.challenger"
                :defender="onlineGameStore.currentArenaBattle?.defender"
                :player-id="onlineGameStore.playerId"
                :room-id="onlineGameStore.roomId"
                @both-ready="handleBothReady"
        />

        <view v-if="showArenaReopen" class="arena-reopen-btn" @click="showArenaModal = true">
            <text>竞技场</text>
        </view>

        <view class="modal-overlay" v-if="pendingBattleBonusChoice">
            <view class="modal-content battle-bonus-modal">
                <view class="modal-header">
                    <text class="modal-title">战斗奖励选择</text>
                    <text class="modal-subtitle">你拥有战斗胜利光环，选择一项作为战斗奖励</text>
                </view>
                <view class="modal-body">
                    <view class="bonus-choices">
                        <view class="bonus-option" @click="chooseBattleBonus('coins')">
                            <text class="bonus-icon">🪙</text>
                            <text class="bonus-label">1 金币</text>
                        </view>
                        <view class="bonus-option" @click="chooseBattleBonus('seaweed')">
                            <text class="bonus-icon">🌿</text>
                            <text class="bonus-label">1 海草</text>
                        </view>
                        <view class="bonus-option" @click="chooseBattleBonus('lobster')">
                            <text class="bonus-icon">🦞</text>
                            <text class="bonus-label">1 普通龙虾</text>
                        </view>
                    </view>
                </view>
            </view>
        </view>

        <view class="modal-overlay" v-if="pendingSettlement?.areaType === 'tribute'">
            <view class="modal-content tribute-modal">
                <view class="modal-header">
                    <view class="modal-title-group">
                        <text class="modal-title">{{ pendingSettlement?.player?.name }} 的上供行动</text>
                        <text class="modal-subtitle">请选择一家酒楼并支付资源，或者选择裸交</text>
                    </view>
                </view>

                <view class="modal-body" v-if="!tributeState.isNakedMode && !tributeState.showLobsterPicker">
                    <view class="taverns-list">
                        <view v-for="tavern in getAvailableTaverns()" :key="tavern.id" class="tavern-box">
                            <view class="tavern-header">
                                <text class="tavern-name">🏮 {{ tavern.name }}</text>
                            </view>

                            <view v-if="tavern.cards.length === 0" class="empty-hint">上供卡已被抢空</view>

                            <view class="tribute-cards">
                                <view
                                        v-for="card in tavern.cards"
                                        :key="card.id"
                                        class="tribute-card"
                                        :class="{
                                        selected: tributeState.selectedCardIds.includes(card.id),
                                        disabled: isCardDisabled(tavern.id, card.id)
                                    }"
                                        @click="toggleCardSelect(tavern.id, card.id)"
                                >
                                    <view
                                            class="tribute-card-check"
                                            :class="{ checked: tributeState.selectedCardIds.includes(card.id) }"
                                    >
                                        <text v-if="tributeState.selectedCardIds.includes(card.id)">✓</text>
                                    </view>
                                    <text class="tc-name">{{ card.name }}</text>
                                    <text class="tc-desc">{{ card.effectDesc }}</text>
                                    <view class="tc-req">需求：{{ formatTributeReq(card.requirements) }}</view>
                                    <view class="tc-rew">奖励：{{ formatTributeRew(card.reward) }}</view>
                                </view>
                            </view>
                        </view>
                        <view v-if="getCompletedTaverns().length > 0" class="completed-taverns-section">
                            <view class="section-label">✅ 已完成上供的酒楼</view>
                            <view
                                    v-for="tavern in getCompletedTaverns()"
                                    :key="tavern.id"
                                    class="tavern-box completed-tavern"
                            >
                                <view class="tavern-header">
                                    <text class="tavern-name">🏮 {{ tavern.name }}</text>
                                    <text class="tavern-status">已完成</text>
                                </view>
                            </view>
                        </view>
                    </view>
                    <view v-if="tributeState.selectedCardIds.length > 0" class="selected-summary">
                        已选 {{ tributeState.selectedCardIds.length }} 张卡牌
                        <text v-if="!canConfirmTributeCards()" class="error-hint">，资源不足</text>
                    </view>
                </view>

                <view class="modal-body naked-mode-panel" v-else-if="tributeState.isNakedMode">
                    <view class="naked-intro">
                        <text class="warn-text">🔥 裸交模式 🔥</text>
                        <text class="sub-text">
                            如果你无法满足任何酒楼的卡牌要求，你可以选择献祭一只【三品及以上】的龙虾强行上供并抢夺一家酒楼的席位！
                        </text>
                    </view>

                    <view class="section-label">1. 请选择要强行献祭的龙虾：</view>
                    <view class="lobster-grid">
                        <view
                                v-for="lobster in getValidNakedLobsters(pendingSettlement?.player)"
                                :key="lobster.id"
                                class="lobster-card"
                                :class="{
                                selected:
                                    tributeState.nakedLobsterIndex ===
                                    getNakedLobsterGlobalIndex(lobster.id, pendingSettlement?.player)
                            }"
                                @click="
                                tributeState.nakedLobsterIndex = getNakedLobsterGlobalIndex(
                                    lobster.id,
                                    pendingSettlement?.player
                                )
                            "
                        >
                            <text class="lobster-icon">🦞</text>
                            <text class="lobster-grade">{{ getLobsterGradeName(lobster.grade) }}</text>
                            <text class="lobster-title" v-if="lobster.title">{{ lobster.title.name }}</text>
                        </view>
                        <view
                                v-for="tc in getValidNakedTitleCards(pendingSettlement?.player)"
                                :key="tc.id"
                                class="lobster-card title-card-lobster"
                                :class="{
                                selected:
                                    tributeState.nakedLobsterIndex ===
                                    getNakedLobsterGlobalIndex(tc.id, pendingSettlement?.player)
                            }"
                                @click="
                                tributeState.nakedLobsterIndex = getNakedLobsterGlobalIndex(
                                    tc.id,
                                    pendingSettlement?.player
                                )
                            "
                        >
                            <text class="lobster-icon">🏆</text>
                            <text class="lobster-grade">{{ tc.name }}</text>
                            <text class="lobster-title" v-if="tc.skill?.description">{{ tc.skill.description }}</text>
                        </view>
                    </view>
                    <view
                            v-if="
                            getValidNakedLobsters(pendingSettlement?.player).length === 0 &&
                            getValidNakedTitleCards(pendingSettlement?.player).length === 0
                        "
                            class="error-hint mt-2"
                    >
                        你连一只三品以上的龙虾都没有，怎么好意思裸交？
                    </view>

                    <view class="section-label mt-4">2. 请选择你要抢占席位的酒楼：</view>
                    <view class="tavern-select-grid">
                        <view
                                v-for="t in pendingSettlement?.taverns"
                                :key="t.id"
                                class="tavern-select-btn"
                                :class="{
                                active: tributeState.nakedTavernId === t.id,
                                disabled: isNakedTavernDisabled(t)
                            }"
                                @click="!isNakedTavernDisabled(t) && (tributeState.nakedTavernId = t.id)"
                        >
                            <text class="ts-name">{{ t.name }}</text>
                            <text class="ts-status">席位: {{ getTavernOccupantCount(t.id) }}/4</text>
                            <text v-if="isPlayerOccupiedTavern(t.id)" class="ts-lock">已占</text>
                        </view>
                    </view>

                    <view class="section-label mt-4">3. 请选择保底奖励：</view>
                    <view class="reward-options">
                        <view
                                class="custom-radio-wrap"
                                :class="{ active: tributeState.nakedRewardType === 'de' }"
                                @click="tributeState.nakedRewardType = 'de'"
                        >
                            <view
                                    class="custom-radio"
                                    :class="{ checked: tributeState.nakedRewardType === 'de' }"
                            ></view>
                            获得 1 德
                        </view>
                        <view
                                class="custom-radio-wrap"
                                :class="{ active: tributeState.nakedRewardType === 'wang' }"
                                @click="tributeState.nakedRewardType = 'wang'"
                        >
                            <view
                                    class="custom-radio"
                                    :class="{ checked: tributeState.nakedRewardType === 'wang' }"
                            ></view>
                            获得 1 望
                        </view>
                    </view>
                </view>

                <view v-if="tributeState.showLobsterPicker" class="modal-body lobster-picker-panel">
                    <view class="section-label">🦞 选择要上供的龙虾</view>
                    <view class="lobster-req-hint">
                        <text v-for="(req, grade) in getPendingCardLobsterReqs()" :key="grade" class="req-item">
                            需要 {{ req }} 只 {{ getLobsterGradeName(grade) }} 及以上
                        </text>
                    </view>
                    <view class="lobster-picker-grid">
                        <view
                                v-for="lobster in pendingSettlement?.player?.lobsters"
                                :key="lobster.id"
                                class="lobster-pick-card"
                                :class="{
                                selected: tributeState.selectedLobsterIds.includes(lobster.id),
                                disabled:
                                    !tributeState.selectedLobsterIds.includes(lobster.id) &&
                                    tributeState.selectedLobsterIds.length >= getTotalLobsterReqCount()
                            }"
                                @click="toggleLobsterSelect(lobster.id)"
                        >
                            <view
                                    class="lpd-check"
                                    :class="{ checked: tributeState.selectedLobsterIds.includes(lobster.id) }"
                            >
                                <text v-if="tributeState.selectedLobsterIds.includes(lobster.id)">✓</text>
                            </view>
                            <text class="lpd-icon">🦞</text>
                            <text class="lpd-grade">{{ getLobsterGradeName(lobster.grade) }}</text>
                            <text class="lpd-title" v-if="lobster.title">{{ lobster.title.name }}</text>
                        </view>
                        <view
                                v-for="tc in pendingSettlement?.player?.titleCards"
                                :key="tc.id"
                                class="lobster-pick-card title-card-pick"
                                :class="{
                                selected: tributeState.selectedLobsterIds.includes(tc.id),
                                disabled:
                                    !tributeState.selectedLobsterIds.includes(tc.id) &&
                                    tributeState.selectedLobsterIds.length >= getTotalLobsterReqCount()
                            }"
                                @click="toggleLobsterSelect(tc.id)"
                        >
                            <view
                                    class="lpd-check"
                                    :class="{ checked: tributeState.selectedLobsterIds.includes(tc.id) }"
                            >
                                <text v-if="tributeState.selectedLobsterIds.includes(tc.id)">✓</text>
                            </view>
                            <text class="lpd-icon">🏆</text>
                            <text class="lpd-grade">{{ tc.name }}</text>
                            <text class="lpd-title" v-if="tc.skill?.description">{{ tc.skill.description }}</text>
                        </view>
                    </view>
                    <view class="lobster-picker-count">
                        已选 {{ tributeState.selectedLobsterIds.length }} / {{ getTotalLobsterReqCount() }} 只
                    </view>
                    <view v-if="selectedLobstersHaveBonus" class="bonus-tribute-inline" style="margin-top: 1rem">
                        <view class="section-label">🌟 黄金鳌效果：选择额外奖励（必选）</view>
                        <view class="reward-options">
                            <view
                                    class="custom-radio-wrap"
                                    :class="{ active: tributeState.bonusTributeChoice === 'de' }"
                                    @click="tributeState.bonusTributeChoice = 'de'"
                            >
                                <view
                                        class="custom-radio"
                                        :class="{ checked: tributeState.bonusTributeChoice === 'de' }"
                                ></view>
                                额外获得 1 德
                            </view>
                            <view
                                    class="custom-radio-wrap"
                                    :class="{ active: tributeState.bonusTributeChoice === 'wang' }"
                                    @click="tributeState.bonusTributeChoice = 'wang'"
                            >
                                <view
                                        class="custom-radio"
                                        :class="{ checked: tributeState.bonusTributeChoice === 'wang' }"
                                ></view>
                                额外获得 1 望
                            </view>
                        </view>
                    </view>
                </view>

                <view class="modal-footer">
                    <view class="modal-actions" v-if="!tributeState.isNakedMode && !tributeState.showLobsterPicker">
                        <button class="btn btn-ghost" @click="tributeState.isNakedMode = true">强行裸交</button>
                        <button class="btn btn-secondary" @click="skipTributeAction">放弃上供</button>
                        <button
                                class="btn btn-primary"
                                :disabled="tributeState.selectedCardIds.length === 0 || !canConfirmTributeCards()"
                                @click="confirmTributeCards"
                        >
                            确认上供（{{ tributeState.selectedCardIds.length }}张）
                        </button>
                    </view>
                    <view class="modal-actions" v-else-if="tributeState.showLobsterPicker">
                        <button class="btn btn-ghost" @click="cancelLobsterSelection">取消</button>
                        <button
                                class="btn btn-warning"
                                :disabled="
                                tributeState.selectedLobsterIds.length < getTotalLobsterReqCount() ||
                                (selectedLobstersHaveBonus && !tributeState.bonusTributeChoice)
                            "
                                @click="confirmLobsterSelection"
                        >
                            确认选择
                        </button>
                    </view>
                    <view class="modal-actions" v-else>
                        <button class="btn btn-ghost" @click="tributeState.isNakedMode = false">返回卡牌列表</button>
                        <button
                                class="btn btn-warning"
                                :disabled="tributeState.nakedLobsterIndex === -1 || tributeState.nakedTavernId === ''"
                                @click="confirmNakedTribute"
                        >
                            确认献祭并抢席位
                        </button>
                    </view>
                </view>
            </view>
        </view>
    </view>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, reactive } from 'vue'
import { useOnlineGameStore, LOBSTER_GRADES } from '@stores/online-game.js'
import { usePlayerStore } from '@stores/player.js'
import { DEFAULT_SLOT_STYLE, getOccupiedSlotStyle, PLAYER_COLORS } from '@utils/slotConstants.js'
import { getLobsterGradeName, getNextLobsterGrade } from '@utils/gameUtils.js'
import LobsterSelect from './lobsterSelect.vue'
import socketModule from '@utils/socket.js'

const socketService = socketModule.socketService || socketModule
const onlineGameStore = useOnlineGameStore()
const playerStore = usePlayerStore()
const showLog = ref(false)
const showArenaModal = ref(false)
const showLobsterList = ref(false)
const showTributeCards = ref(false)

// ============ 结算阶段状态 ============
const pendingSettlement = computed(() => onlineGameStore.pendingSettlement)
// 强制监听 pendingSettlement 变化以确保响应式更新
const settlementActionCount = computed(() => pendingSettlement.value?.actionCount ?? 0)

// 战斗奖励选择状态
const pendingBattleBonusChoice = computed(() => onlineGameStore.pendingBattleBonusChoice)

watch(settlementActionCount, (newVal, oldVal) => {
    console.log('[Seafood Market] Action count changed:', oldVal, '->', newVal)
})
const showSettlementModal = computed(() => {
    return pendingSettlement.value !== null && onlineGameStore.currentPhase === 'settlement'
})

// ============ 捕虾抽取结果悬浮提示 ============
const SHRIMP_ITEM_EMOJI = { bubble: '🫧', lobster: '🦞', seaweed: '🌿', either: '❓' }
const getDrawnItemEmoji = (item) => SHRIMP_ITEM_EMOJI[item] || '🎣'
const shrimpDrawMessages = ref([])
let shrimpMsgId = 0

watch(
        () => pendingSettlement.value?.lastResult,
        (newResult) => {
            if (newResult && pendingSettlement.value?.areaType === 'shrimp_catching') {
                const id = ++shrimpMsgId
                const item = pendingSettlement.value?.lastItem || ''
                shrimpDrawMessages.value.push({id, text: `${getDrawnItemEmoji(item)} ${newResult}`})
                setTimeout(() => {
                    shrimpDrawMessages.value = shrimpDrawMessages.value.filter((m) => m.id !== id)
                }, 3000)
            }
        }
)

const breedingState = ref({
    lobsterIndex: -1,
    useSeaweed: false,
    royalCostType: '',
    selectedTitleId: '',
    royalRewardType: 'de'
})

const marketplaceState = ref({
    selectedCard: null,
    selectedOptionIndex: 0
})

watch(pendingSettlement, (newVal) => {
    if (!newVal || newVal.areaType !== 'breeding') {
        breedingState.value = {
            lobsterIndex: -1,
            useSeaweed: false,
            royalCostType: '',
            selectedTitleId: '',
            royalRewardType: 'de'
        }
    }
    if (!newVal || newVal.areaType !== 'marketplace') {
        marketplaceState.value = { selectedCard: null, selectedOptionIndex: 0 }
    }
})

// ============ 海鲜市场价格计算 ============
const marketPrices = computed(() => {
    const lobsterCount = pendingSettlement.value?.marketLobsterCount ?? 4
    const base = Math.min(lobsterCount, 8)
    return {
        buyLobster: 2 + Math.floor(base / 2),
        sellLobster: Math.max(1, 4 - Math.floor(base / 2)),
        buyCage: 3,
        sellCage: 2,
        buySeaweed: 2 + Math.floor(base / 4),
        sellSeaweed: Math.max(1, 3 - Math.floor(base / 4))
    }
})

const canBuyLobster = computed(() => {
    const player = pendingSettlement.value?.player
    return (
            player &&
            player.coins >= marketPrices.value.buyLobster &&
            (pendingSettlement.value?.marketLobsterCount ?? 0) > 0
    )
})

const canSellLobster = computed(() => {
    const player = pendingSettlement.value?.player
    return (
            player &&
            player.lobsters &&
            player.lobsters.length > 0 &&
            (pendingSettlement.value?.marketLobsterCount ?? 0) < 8
    )
})

const canBuyCage = computed(() => {
    const player = pendingSettlement.value?.player
    return player && player.coins >= marketPrices.value.buyCage
})

const canSellCage = computed(() => {
    const player = pendingSettlement.value?.player
    return player && player.cages > 0
})

const canBuySeaweed = computed(() => {
    const player = pendingSettlement.value?.player
    return player && player.coins >= marketPrices.value.buySeaweed
})

const canSellSeaweed = computed(() => {
    const player = pendingSettlement.value?.player
    return player && player.seaweed >= 1
})

const canHire = computed(() => {
    const player = pendingSettlement.value?.player
    return player && player.coins >= 6
})

// ============ 养蛊区计算属性 ============
const targetLobster = computed(() => {
    if (breedingState.value.lobsterIndex === -1) return null
    const player = pendingSettlement.value?.player
    return player?.lobsters?.[breedingState.value.lobsterIndex]
})

const isSeaweedUseful = computed(() => {
    if (!targetLobster.value) return false
    return targetLobster.value.grade !== LOBSTER_GRADES.GRADE1 && targetLobster.value.grade !== LOBSTER_GRADES.ROYAL
})

const projectedGrade = computed(() => {
    if (!targetLobster.value) return null
    let grade = getNextLobsterGrade(targetLobster.value.grade)
    console.log(
            '[Seaweed] base grade:',
            grade,
            'target:',
            targetLobster.value.grade,
            'useSeaweed:',
            breedingState.value.useSeaweed
    )
    if (breedingState.value.useSeaweed) {
        // 海草额外+1品
        const seaweedGrades = {
            [LOBSTER_GRADES.GRADE3]: LOBSTER_GRADES.GRADE2,
            [LOBSTER_GRADES.GRADE2]: LOBSTER_GRADES.GRADE1
        }
        console.log('[Seaweed] seaweedGrades map:', JSON.stringify(seaweedGrades))
        console.log('[Seaweed] looking up grade:', grade, 'result:', seaweedGrades[grade])
        grade = seaweedGrades[grade] || getNextLobsterGrade(grade)
        console.log('[Seaweed] final grade:', grade)
    }
    return grade
})

const isUpgradingToRoyal = computed(() => {
    return (
            targetLobster.value &&
            targetLobster.value.grade !== LOBSTER_GRADES.ROYAL &&
            projectedGrade.value === LOBSTER_GRADES.ROYAL
    )
})

const canConfirmBreeding = computed(() => {
    if (!targetLobster.value) return false
    if (breedingState.value.useSeaweed && (pendingSettlement.value?.player?.seaweed ?? 0) < 1) return false
    if (isUpgradingToRoyal.value) {
        const player = pendingSettlement.value?.player
        if (breedingState.value.royalCostType === 'cage' && (player?.cages ?? 0) < 1) return false
        if (breedingState.value.royalCostType === 'coin' && (player?.coins ?? 0) < 3) return false
        if (onlineGameStore.gameTitleCards?.length > 0 && !breedingState.value.selectedTitleId) return false
    }
    return true
})

// ============ 闹市区计算属性 ============
const canConfirmMarketplace = computed(() => {
    if (!marketplaceState.value.selectedCard) return false
    const card = marketplaceState.value.selectedCard
    const player = pendingSettlement.value?.player
    if (!player) return false

    if (!card.auto && card.action?.type === 'exchange') {
        const options = card.action?.options || []
        const opt = options[marketplaceState.value.selectedOptionIndex]
        if (!opt || !opt.cost) return false

        for (const [resType, resAmount] of Object.entries(opt.cost)) {
            if (resType === 'lobsters') {
                if ((player.lobsters?.length ?? 0) < resAmount) return false
            } else {
                if ((player[resType] ?? 0) < resAmount) return false
            }
        }
    }
    return true
})

// ============ 计算属性 ============
const isPlacementPhase = computed(() => onlineGameStore.currentPhase === 'placement')

const currentPlacementPlayerName = computed(() => {
    const player = playerStore.players[onlineGameStore.currentPlayerIndex]
    return player?.name || '未知'
})

const phaseText = computed(() => `${onlineGameStore.phaseText}阶段`)

const arenaBattleQueue = computed(() => onlineGameStore.arenaBattleQueue)

const showArenaReopen = computed(
        () => onlineGameStore.arenaPhase !== 'idle' && !showArenaModal.value && arenaBattleQueue.value.length > 0
)

// ============ 样式方法 ============

const getPlayerItemStyle = (playerId) => {
    if (!isCurrentPlacementPlayer(playerId)) return {}
    const color = PLAYER_COLORS[playerId]
    if (!color) return {}
    return {
        borderColor: color.bg,
        boxShadow: `0 0 10px ${color.bg}40`
    }
}

const getSlotStyle = (area, slotIndex) => {
    const occupant = onlineGameStore.getSlotOccupant(area, slotIndex)
    if (occupant != null) {
        const style = getOccupiedSlotStyle(occupant)
        return {
            background: style.background,
            borderColor: style.borderColor,
            opacity: style.opacity,
            color: style.color
        }
    }
    return {
        background: DEFAULT_SLOT_STYLE.background,
        opacity: isPlacementPhase.value ? 1 : 0.6
    }
}

// ============ 状态查询 ============

const isSlotOccupied = (area, slotIndex) => onlineGameStore.isSlotOccupied(area, slotIndex)

const getSlotOccupantLabel = (area, slotIndex) => {
    const occupant = onlineGameStore.getSlotOccupant(area, slotIndex)
    return occupant != null ? getOccupiedSlotStyle(occupant).playerLabel : null
}

const canPlaceOnSlot = (area, slotIndex) => {
    if (!isPlacementPhase.value) return false
    if (!onlineGameStore.isMyTurn) return false
    if (isSlotOccupied(area, slotIndex)) return false
    if (
            onlineGameStore.lastPlacement &&
            String(onlineGameStore.lastPlacement.playerId) === String(onlineGameStore.playerId)
    )
        return false
    return true
}

const isMySlot = (area, slotIndex) => {
    if (!isPlacementPhase.value) return false
    if (!onlineGameStore.isMyTurn) return false
    const occupant = onlineGameStore.getSlotOccupant(area, slotIndex)
    return occupant !== null && String(occupant) === String(onlineGameStore.playerId)
}

const isCurrentPlacementPlayer = (playerId) => isPlacementPhase.value && onlineGameStore.currentPlayerIndex === playerId

const isMarketplaceAvailable = (slotIndex) => onlineGameStore.currentRound >= slotIndex + 1

const isTributeSlotAvailable = (slotIndex) => {
    if (slotIndex === 2) {
        return onlineGameStore.currentRound >= 4
    }
    return true
}

// ============ 行动格描述 ============

const getShrimpCatchingSlotDesc = (i) => {
    const descs = ['1虾笼,夺起始,1次捕虾', '1虾笼,2次捕虾', '1金币,3次捕虾', '4次捕虾']
    return descs[i - 1]
}

const getSeafoodMarketSlotDesc = (i) => {
    const descs = ['1金币,2次交易', '3次交易', '1金币,3次交易', '2金币,3次交易']
    return descs[i - 1]
}

const getBreedingSlotDesc = (i) => {
    const descs = ['1草,1次培养', '2次培养', '1金币,2次培养', '3次培养']
    return descs[i - 1]
}

const getTributeSlotDesc = (i) => {
    if (i <= 3) {
        return i === 3 ? '第4回合可用,1次上供' : '1次上供'
    } else if (i <= 6) {
        return `挑战${i - 3}号位,1次上供`
    } else {
        return '1次上供'
    }
}

const getMarketplaceSlotDesc = (i) => {
    const descs = ['第2回合可用,1次闹市', '1金币,第3回合可用,1次闹市', '2金币,第4回合可用,1次闹市']
    return descs[i - 1]
}

// ============ 交互处理 ============

const showToast = (message, icon = 'none') => {
    uni.showToast({ title: message, icon, duration: 2000 })
}

const handleSlotClick = (area, slotIndex) => {
    if (!isPlacementPhase.value) {
        showToast('当前不是工放阶段，无法放置里长')
        return
    }
    if (!onlineGameStore.isMyTurn) {
        showToast('不是你的回合')
        return
    }
    if (isSlotOccupied(area, slotIndex)) {
        const occupant = onlineGameStore.getSlotOccupant(area, slotIndex)
        if (String(occupant) === String(onlineGameStore.playerId)) {
            onlineGameStore.cancelHeadmanAction()
        } else {
            const occupantPlayer = playerStore.players.find((p) => p.id === occupant)
            showToast(`该行动格已被${occupantPlayer?.name || '未知玩家'}占用`)
        }
        return
    }
    if (area === 'marketplace' && !isMarketplaceAvailable(slotIndex + 1)) {
        showToast(`第${slotIndex + 1}号格子需第${slotIndex + 2}回合才可用`)
        return
    }
    if (area === 'tribute' && !isTributeSlotAvailable(slotIndex)) {
        showToast('第3号格子需第4回合才可用')
        return
    }
    if (!canPlaceOnSlot(area, slotIndex)) {
        showToast('请先点击"下一阶段"结束当前回合')
        return
    }
    onlineGameStore.sendGameAction('placeHeadman', { areaIndex: area, slotIndex })
}

const handleNextPhase = () => {
    if (!onlineGameStore.isMyTurn) {
        showToast('不是你的回合')
        return
    }
    if (onlineGameStore.currentPhase === 'placement') {
        onlineGameStore.sendGameAction('nextPlayer', {})
    } else if (onlineGameStore.currentPhase === 'settlement') {
        onlineGameStore.sendGameAction('nextArea', {})
    }
}

// ============ 结算阶段交互处理 ============

const skipSettlementAction = () => {
    onlineGameStore.sendSettlementAction('skip')
    onlineGameStore.clearPendingSettlement()
}

// --- 捕虾区 ---
const confirmShrimpCatch = () => {
    onlineGameStore.sendSettlementAction('confirm')
}

const chooseShrimpReward = (choice) => {
    onlineGameStore.sendSettlementAction('choose_either', { choice })
}

// --- 海鲜市场 ---
const doSeafoodTrade = (actionType) => {
    onlineGameStore.sendSettlementAction(actionType)
}

// --- 养蛊区 ---
const selectLobsterForBreeding = (index) => {
    breedingState.value.lobsterIndex = index
    breedingState.value.useSeaweed = false
    breedingState.value.royalCostType = ''
    breedingState.value.selectedTitleId = ''
    breedingState.value.royalRewardType = 'de'
}

const toggleSeaweed = () => {
    console.log(
            '[toggleSeaweed] before:',
            breedingState.value.useSeaweed,
            'seaweed:',
            pendingSettlement.value?.player?.seaweed
    )
    if (!isSeaweedUseful.value) {
        showToast('已达满级，无需消耗海草')
        return
    }
    const player = pendingSettlement.value?.player
    if ((player?.seaweed ?? 0) >= 1 || breedingState.value.useSeaweed) {
        breedingState.value.useSeaweed = !breedingState.value.useSeaweed
        console.log('[toggleSeaweed] after:', breedingState.value.useSeaweed)
    } else {
        showToast('海草数量不足')
    }
}

const cancelBreedingAction = () => {
    breedingState.value.lobsterIndex = -1
}

const confirmBreedingAction = () => {
    if (!canConfirmBreeding.value) return
    const player = pendingSettlement.value?.player
    const lobster = targetLobster.value
    if (!player || !lobster) return

    onlineGameStore.sendSettlementAction('cultivateLobster', {
        lobsterIndex: breedingState.value.lobsterIndex,
        useSeaweed: breedingState.value.useSeaweed,
        royalCostType: isUpgradingToRoyal.value ? breedingState.value.royalCostType : null,
        royalRewardType: isUpgradingToRoyal.value ? breedingState.value.royalRewardType : null,
        selectedTitleId: isUpgradingToRoyal.value ? breedingState.value.selectedTitleId : null
    })

    breedingState.value.lobsterIndex = -1
    breedingState.value.useSeaweed = false
    breedingState.value.royalCostType = ''
    breedingState.value.selectedTitleId = ''
    breedingState.value.royalRewardType = 'de'
}

// --- 闹市区 ---
const selectMarketplaceCard = (card) => {
    if (card.usedThisRound) return
    marketplaceState.value.selectedCard = card
    marketplaceState.value.selectedOptionIndex = 0
}

const formatOptionText = (opt) => {
    if (!opt || !opt.cost || !opt.reward) return ''
    const nameMap = { coins: '金币', seaweed: '海草', cages: '虾笼', lobsters: '龙虾', de: '德', wang: '望' }
    const costStrs = Object.entries(opt.cost).map(([k, v]) => `${v} ${nameMap[k] || k}`)
    const rewardStrs = Object.entries(opt.reward).map(([k, v]) => `${v} ${nameMap[k] || k}`)
    return `消耗 ${costStrs.join(' 和 ')} ➔ 获得 ${rewardStrs.join(' 和 ')}`
}

const confirmMarketplaceAction = () => {
    if (!canConfirmMarketplace.value) return
    const card = marketplaceState.value.selectedCard
    const optionIndex = marketplaceState.value.selectedOptionIndex
    const availableCards = pendingSettlement.value?.availableCards || []
    const cardIndex = availableCards.findIndex((c) => c.id === card.id)

    onlineGameStore.sendSettlementAction('executeDowntownAction', {
        cardIndex,
        optionIndex
    })

    marketplaceState.value.selectedCard = null
    marketplaceState.value.selectedOptionIndex = 0
}

// ============ 上供区逻辑 ============

const tributeState = reactive({
    isNakedMode: false,
    nakedLobsterIndex: -1,
    nakedTavernId: '',
    nakedRewardType: 'de',
    bonusTributeChoice: '',
    showLobsterPicker: false,
    pendingCardSubmit: null,
    selectedLobsterIds: [],
    selectedTavernId: null,
    selectedCardIds: []
})

watch(
        pendingSettlement,
        (newVal) => {
            if (!newVal || newVal.areaType !== 'tribute') {
                tributeState.isNakedMode = false
                tributeState.nakedLobsterIndex = -1
                tributeState.nakedTavernId = ''
                tributeState.nakedRewardType = 'de'
                tributeState.bonusTributeChoice = ''
                tributeState.showLobsterPicker = false
                tributeState.pendingCardSubmit = null
                tributeState.selectedLobsterIds = []
                tributeState.selectedTavernId = null
                tributeState.selectedCardIds = []
            }
        },
        {immediate: true}
)

const formatTributeReq = (req) => {
    if (!req) return '无'
    const parts = []
    if (req.coins) parts.push(`${req.coins}金币`)
    if (req.seaweed) parts.push(`${req.seaweed}海草`)
    if (req.cages) parts.push(`${req.cages}虾笼`)
    if (req.lobsters) {
        for (const [grade, count] of Object.entries(req.lobsters)) {
            parts.push(`${count}只${grade}龙虾`)
        }
    }
    return parts.length > 0 ? parts.join(' + ') : '无'
}

const formatTributeRew = (rew) => {
    if (!rew) return '无'
    const parts = []
    if (rew.de) parts.push(`${rew.de}德`)
    if (rew.wang) parts.push(`${rew.wang}望`)
    return parts.length > 0 ? parts.join(' + ') : '无'
}

const checkTributeReq = (req, player) => {
    if (!player || !req) return false
    if ((player.coins ?? 0) < (req.coins ?? 0)) return false
    if ((player.seaweed ?? 0) < (req.seaweed ?? 0)) return false
    if ((player.cages ?? 0) < (req.cages ?? 0)) return false

    if (req.lobsters) {
        const gradeValues = { normal: 0, grade3: 1, grade2: 2, grade1: 3, royal: 4 }
        let tempLobsters = [...(player.lobsters || []), ...(player.titleCards || [])]
        for (const [gradeKey, count] of Object.entries(req.lobsters)) {
            let foundCount = 0
            for (let i = 0; i < count; i++) {
                const reqGradeVal = gradeValues[gradeKey] ?? 0
                const matchIdx = tempLobsters.findIndex((l) => {
                    if (l.name && !l.grade) return 4 >= reqGradeVal
                    const lv = l.title ? 4 : (gradeValues[l.grade] ?? 0)
                    return lv >= reqGradeVal
                })
                if (matchIdx !== -1) {
                    foundCount++
                    tempLobsters.splice(matchIdx, 1)
                }
            }
            if (foundCount < count) return false
        }
    }
    return true
}

const getValidNakedLobsters = (player) => {
    if (!player || !player.lobsters) return []
    const gradeValues = { normal: 0, grade3: 1, grade2: 2, grade1: 3, royal: 4 }
    return player.lobsters.filter((l) => (gradeValues[l.grade] ?? 0) >= 1)
}

const getValidNakedTitleCards = (player) => {
    if (!player || !player.titleCards) return []
    return player.titleCards
}

const getNakedLobsterGlobalIndex = (lobsterId, player) => {
    const lobsters = getValidNakedLobsters(player)
    const idx = lobsters.findIndex((l) => l.id === lobsterId)
    if (idx !== -1) return idx
    const titleCards = getValidNakedTitleCards(player)
    const tcIdx = titleCards.findIndex((tc) => tc.id === lobsterId)
    if (tcIdx !== -1) return lobsters.length + tcIdx
    return -1
}

const isNakedTavernDisabled = (tavern) => {
    const player = pendingSettlement.value?.player
    const occupiedThisRound = tavern.occupants?.includes(player?.id)
    const completedBefore = player?.tavernCompletions?.[tavern.id] !== undefined
    return occupiedThisRound || completedBefore
}

const getTavernOccupantCount = (tavernId) => {
    const players = playerStore.players || []
    return players.filter((p) => p.tavernCompletions?.[tavernId] !== undefined).length
}

const isPlayerOccupiedTavern = (tavernId) => {
    const player = pendingSettlement.value?.player
    return player?.tavernCompletions?.[tavernId] !== undefined
}

const selectedLobstersHaveBonus = computed(() => {
    const player = pendingSettlement.value?.player
    if (!player || !player.titleCards) return false
    const bonusCardIds = player.titleCards.filter((tc) => tc.skill?.bonusTribute === true).map((tc) => tc.id)
    return tributeState.selectedLobsterIds.some((id) => bonusCardIds.includes(id))
})

const getAvailableTaverns = () => {
    const taverns = pendingSettlement.value?.taverns || []
    const player = pendingSettlement.value?.player
    const tavernCompletions = player?.tavernCompletions || {}
    return taverns.filter((t) => {
        const occupiedThisRound = t.occupants?.includes(player?.id)
        const completedBefore = Object.prototype.hasOwnProperty.call(tavernCompletions, t.id)
        return !occupiedThisRound && !completedBefore
    })
}

const getCompletedTaverns = () => {
    const taverns = pendingSettlement.value?.taverns || []
    const player = pendingSettlement.value?.player
    const tavernCompletions = player?.tavernCompletions || {}
    return taverns.filter((t) => {
        const occupiedThisRound = t.occupants?.includes(player?.id)
        const completedBefore = Object.prototype.hasOwnProperty.call(tavernCompletions, t.id)
        return occupiedThisRound || completedBefore
    })
}

const findCardById = (cardId) => {
    for (const tavern of pendingSettlement.value?.taverns || []) {
        const card = tavern.cards?.find((c) => c.id === cardId)
        if (card) return { ...card, tavernId: tavern.id }
    }
    return null
}

const isCardDisabled = (tavernId, cardId) => {
    if (tributeState.selectedCardIds.includes(cardId)) return false
    if (tributeState.selectedCardIds.length > 0) {
        const firstCard = findCardById(tributeState.selectedCardIds[0])
        if (firstCard && firstCard.tavernId !== tavernId) return true
    }
    return false
}

const toggleCardSelect = (tavernId, cardId) => {
    const idx = tributeState.selectedCardIds.indexOf(cardId)
    if (idx > -1) {
        tributeState.selectedCardIds.splice(idx, 1)
        if (tributeState.selectedCardIds.length === 0) {
            tributeState.selectedTavernId = null
        }
        return
    }
    if (tributeState.selectedCardIds.length >= 2) return
    if (tributeState.selectedCardIds.length > 0) {
        const firstCard = findCardById(tributeState.selectedCardIds[0])
        if (firstCard && firstCard.tavernId !== tavernId) return
    }
    tributeState.selectedCardIds.push(cardId)
    tributeState.selectedTavernId = tavernId
}

const canConfirmTributeCards = () => {
    if (tributeState.selectedCardIds.length === 0) return false
    const player = pendingSettlement.value?.player
    if (!player) return false
    let totalReq = { coins: 0, seaweed: 0, cages: 0, lobsters: {} }
    for (const cardId of tributeState.selectedCardIds) {
        const cardInfo = findCardById(cardId)
        if (!cardInfo) return false
        const req = cardInfo.requirements || {}
        totalReq.coins += req.coins || 0
        totalReq.seaweed += req.seaweed || 0
        totalReq.cages += req.cages || 0
        if (req.lobsters) {
            for (const [grade, count] of Object.entries(req.lobsters)) {
                totalReq.lobsters[grade] = (totalReq.lobsters[grade] || 0) + count
            }
        }
    }
    if ((player.coins ?? 0) < totalReq.coins) return false
    if ((player.seaweed ?? 0) < totalReq.seaweed) return false
    if ((player.cages ?? 0) < totalReq.cages) return false
    if (Object.keys(totalReq.lobsters).length > 0) {
        const gradeValues = { normal: 0, grade3: 1, grade2: 2, grade1: 3, royal: 4 }
        let tempLobsters = [...(player.lobsters || []), ...(player.titleCards || [])]
        for (const [gradeKey, count] of Object.entries(totalReq.lobsters)) {
            let foundCount = 0
            for (let i = 0; i < count; i++) {
                const reqGradeVal = gradeValues[gradeKey] ?? 0
                const matchIdx = tempLobsters.findIndex((l) => {
                    if (l.name && !l.grade) return 4 >= reqGradeVal
                    const lv = l.title ? 4 : (gradeValues[l.grade] ?? 0)
                    return lv >= reqGradeVal
                })
                if (matchIdx !== -1) {
                    foundCount++
                    tempLobsters.splice(matchIdx, 1)
                }
            }
            if (foundCount < count) return false
        }
    }
    return true
}

const confirmTributeCards = () => {
    if (!canConfirmTributeCards()) return
    const hasLobsterReq = tributeState.selectedCardIds.some((cardId) => {
        const cardInfo = findCardById(cardId)
        return cardInfo?.requirements?.lobsters && Object.keys(cardInfo.requirements.lobsters).length > 0
    })
    if (hasLobsterReq) {
        tributeState.showLobsterPicker = true
        tributeState.pendingCardSubmit = {
            tavernId: tributeState.selectedTavernId,
            cardIds: [...tributeState.selectedCardIds]
        }
        tributeState.selectedLobsterIds = []
        return
    }
    submitMultiTributeCards()
}

const submitMultiTributeCards = () => {
    const payload = {
        isNaked: false,
        tavernId: tributeState.selectedTavernId,
        cardIds: [...tributeState.selectedCardIds]
    }
    if (tributeState.selectedLobsterIds.length > 0) {
        payload.selectedLobsterIds = tributeState.selectedLobsterIds
    }
    if (selectedLobstersHaveBonus.value && tributeState.bonusTributeChoice) {
        payload.bonusTributeChoice = tributeState.bonusTributeChoice
    }
    onlineGameStore.sendSettlementAction('submitTribute', payload)
    tributeState.selectedCardIds = []
    tributeState.selectedTavernId = null
    tributeState.selectedLobsterIds = []
    tributeState.bonusTributeChoice = ''
}

const confirmLobsterSelection = () => {
    if (!tributeState.pendingCardSubmit) return
    submitMultiTributeCards()
    tributeState.showLobsterPicker = false
    tributeState.pendingCardSubmit = null
    tributeState.selectedLobsterIds = []
}

const cancelLobsterSelection = () => {
    tributeState.showLobsterPicker = false
    tributeState.pendingCardSubmit = null
    tributeState.selectedLobsterIds = []
}

const toggleLobsterSelect = (lobsterId) => {
    const idx = tributeState.selectedLobsterIds.indexOf(lobsterId)
    if (idx > -1) {
        tributeState.selectedLobsterIds.splice(idx, 1)
    } else {
        const maxCount = getTotalLobsterReqCount()
        if (tributeState.selectedLobsterIds.length >= maxCount) {
            return
        }
        tributeState.selectedLobsterIds.push(lobsterId)
    }
    if (!selectedLobstersHaveBonus.value) {
        tributeState.bonusTributeChoice = ''
    }
}

const getPendingCardLobsterReqs = () => {
    if (!tributeState.pendingCardSubmit) return {}
    const cardIds = tributeState.pendingCardSubmit.cardIds || [tributeState.pendingCardSubmit.cardId]
    const totalReqs = {}
    for (const cardId of cardIds) {
        const cardInfo = findCardById(cardId)
        if (cardInfo?.requirements?.lobsters) {
            for (const [grade, count] of Object.entries(cardInfo.requirements.lobsters)) {
                totalReqs[grade] = (totalReqs[grade] || 0) + count
            }
        }
    }
    return totalReqs
}

const getTotalLobsterReqCount = () => {
    const reqs = getPendingCardLobsterReqs()
    return Object.values(reqs).reduce((sum, count) => sum + count, 0)
}

const hasNakedBonusTribute = () => {
    const player = pendingSettlement.value?.player
    if (!player) return false
    if (tributeState.nakedLobsterIndex === -1) return false
    const lobsters = getValidNakedLobsters(player)
    const titleCards = getValidNakedTitleCards(player)
    const bonusCardIds = (player.titleCards || []).filter((tc) => tc.skill?.bonusTribute === true).map((tc) => tc.id)
    if (tributeState.nakedLobsterIndex < lobsters.length) {
        return false
    }
    const tcIndex = tributeState.nakedLobsterIndex - lobsters.length
    if (tcIndex >= 0 && tcIndex < titleCards.length) {
        return bonusCardIds.includes(titleCards[tcIndex].id)
    }
    return false
}

const confirmNakedTribute = () => {
    if (tributeState.nakedLobsterIndex === -1 || tributeState.nakedTavernId === '') return
    const payload = {
        isNaked: true,
        tavernId: tributeState.nakedTavernId,
        nakedLobsterIndex: tributeState.nakedLobsterIndex,
        nakedRewardType: tributeState.nakedRewardType
    }
    if (hasNakedBonusTribute() && tributeState.bonusTributeChoice) {
        payload.bonusTributeChoice = tributeState.bonusTributeChoice
    }
    onlineGameStore.sendSettlementAction('submitTribute', payload)
    onlineGameStore.clearPendingSettlement()
}

const skipTributeAction = () => {
    onlineGameStore.sendSettlementAction('skip')
    onlineGameStore.clearPendingSettlement()
}

// 战斗奖励选择
const chooseBattleBonus = (choice) => {
    onlineGameStore.sendBattleBonusChoice(choice)
}

// ============ 竞技场逻辑 ============

const checkBattleAvailability = () => {
    const battle = onlineGameStore.currentArenaBattle
    if (!battle) return { available: true }

    const challengerAvailable = onlineGameStore.getAvailableLobstersForBattle(battle.challenger?.id).length > 0
    const defenderAvailable = onlineGameStore.getAvailableLobstersForBattle(battle.defender?.id).length > 0

    if (!defenderAvailable && challengerAvailable) {
        return { available: false, reason: 'defender_no_lobster', battle }
    }
    if (!challengerAvailable) {
        return { available: false, reason: 'challenger_no_lobster', battle }
    }
    return { available: true }
}

const skipCurrentBattle = (reason, battle) => {
    if (reason === 'defender_no_lobster') {
        showToast(`${battle.defender?.name} 无可用龙虾，${battle.challenger?.name} 获胜并交换位置`)
        socketService._send('clientBattleAction', {
            action_type: 'noLobsterForfeit',
            challengeSlot: battle.slotIndex
        })
    } else {
        showToast(`${battle.challenger?.name} 无可用龙虾，跳过本场战斗`)
    }

    onlineGameStore.arenaBattleQueue.shift()
    if (onlineGameStore.arenaBattleQueue.length > 0) {
        onlineGameStore.setCurrentArenaBattle(0)
    }
}

const shouldShowArena = () => {
    if (arenaBattleQueue.value.length === 0) return false
    if (onlineGameStore.currentPhase !== 'settlement') return false
    if (onlineGameStore.arenaPhase !== 'idle') return false

    // 如果有非上供区的 pending settlement，优先显示结算UI
    const pending = onlineGameStore.pendingSettlement
    if (pending && pending.areaType && pending.areaType !== 'tribute') {
        return false
    }

    const check = checkBattleAvailability()
    if (!check.available) {
        skipCurrentBattle(check.reason, check.battle)
        return false
    }
    return true
}

const openArenaModal = () => {
    onlineGameStore.setCurrentArenaBattle(0)
    showArenaModal.value = true
}

watch(
        arenaBattleQueue,
        () => {
            if (shouldShowArena()) openArenaModal()
        },
        {deep: true}
)

watch(
        () => onlineGameStore.currentPhase,
        () => {
            if (shouldShowArena()) openArenaModal()
        }
)

const buildArenaPlayerData = (player, selectedLobster, defaultColor) => ({
    id: player.id,
    name: player.name,
    lobsterId: selectedLobster.id,
    lobsterGrade: selectedLobster.grade,
    lobsterName: selectedLobster.name || getLobsterGradeName(selectedLobster.grade),
    lobsterDesc: selectedLobster.description,
    lobsterSkill: selectedLobster.skill,
    color: PLAYER_COLORS[player.id]?.bg || defaultColor
})

const navigateToArena = (player1Data, player2Data) => {
    if (onlineGameStore.arenaBattleQueue.length > 0) {
        onlineGameStore.arenaBattleQueue.shift()
    }

    const storageKey = `arenaBattleQueue_${onlineGameStore.roomId}`
    uni.setStorageSync(storageKey, onlineGameStore.arenaBattleQueue)

    const battle = onlineGameStore.currentArenaBattle
    const url = `/pages/arena/arena?player1=${encodeURIComponent(JSON.stringify(player1Data))}&player2=${encodeURIComponent(JSON.stringify(player2Data))}&roomId=${onlineGameStore.roomId}&playerId=${onlineGameStore.playerId}&challengeSlot=${battle?.slotIndex}`

    uni.navigateTo({ url })
}

const handleBothReady = ({ challenger, defender, challengerLobster, defenderLobster }) => {
    showArenaModal.value = false
    onlineGameStore.setArenaPhase('idle')

    const player1Data = buildArenaPlayerData(challenger, challengerLobster, '#FF6B6B')
    const player2Data = buildArenaPlayerData(defender, defenderLobster, '#4ECDC4')

    navigateToArena(player1Data, player2Data)
}

// ============ 生命周期 ============

const parsePageOptions = () => {
    const pages = getCurrentPages()
    return pages[pages.length - 1].options || {}
}

const restoreArenaQueue = (roomId) => {
    const storageKey = `arenaBattleQueue_${roomId}`
    const savedQueue = uni.getStorageSync(storageKey)
    if (savedQueue?.length > 0) {
        onlineGameStore.arenaBattleQueue = savedQueue
        uni.removeStorageSync(storageKey)
        return true
    }
    return false
}

const prepareNextArenaBattle = () => {
    if (onlineGameStore.arenaBattleQueue.length === 0) return

    const nextBattle = onlineGameStore.arenaBattleQueue[0]
    const challenger = playerStore.getPlayerById(nextBattle.challengerId)
    const defender = playerStore.getPlayerById(nextBattle.defenderId)

    if (!challenger || !defender) return

    onlineGameStore.setArenaPhase('idle')
    onlineGameStore.resetArenaBattleState()

    showArenaModal.value = true
}

const initGameState = (options) => {
    if (options.gameState) {
        try {
            const gs = JSON.parse(decodeURIComponent(options.gameState))
            onlineGameStore.updateGameState(gs)
        } catch {
            // ignore parse errors
        }
    }
}

onMounted(() => {
    const options = parsePageOptions()
    const roomId = options.roomId || uni.getStorageSync('roomId') || ''
    const playerId = parseInt(options.playerId) || uni.getStorageSync('playerId')

    if (!roomId || playerId === null) {
        uni.redirectTo({ url: '/pages/lobby/lobby' })
        return
    }

    // 先恢复队列，再初始化（避免 initOnlineMode 清空队列）
    const hadQueue = restoreArenaQueue(roomId)

    initGameState(options)
    onlineGameStore.initOnlineMode(roomId, playerId)

    setTimeout(() => {
        if (onlineGameStore.arenaBattleQueue.length > 0) {
            prepareNextArenaBattle()
        }
    }, 500)
})

onUnmounted(() => {
    onlineGameStore.cleanupListeners()
})
</script>

<style scoped>
.arena-reopen-btn {
    position: fixed;
    bottom: 120px;
    right: 20px;
    background: linear-gradient(135deg, #e94560, #c23152);
    color: #fff;
    padding: 12px 20px;
    border-radius: 24px;
    font-size: 15px;
    font-weight: bold;
    z-index: 999;
    box-shadow: 0 0 20px rgba(233, 69, 96, 0.5),
    0 4px 12px rgba(0, 0, 0, 0.3);
    animation: arena-pulse 2s ease-in-out infinite;
    border: 1px solid rgba(233, 69, 96, 0.4);
}

@keyframes arena-pulse {
    0%,
    100% {
        transform: scale(1);
        box-shadow: 0 0 20px rgba(233, 69, 96, 0.5),
        0 4px 12px rgba(0, 0, 0, 0.3);
    }
    50% {
        transform: scale(1.08);
        box-shadow: 0 0 30px rgba(233, 69, 96, 0.7),
        0 4px 12px rgba(0, 0, 0, 0.3);
    }
}

.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(10, 10, 26, 0.9);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    backdrop-filter: blur(8px);
}

.modal-content {
    background: #1a1a2e;
    border-radius: 16px;
    width: 90%;
    max-width: 500px;
    max-height: 80vh;
    overflow-y: auto;
    box-shadow: 0 0 40px rgba(0, 0, 0, 0.6),
    0 0 20px rgba(78, 205, 196, 0.1);
    border: 1px solid rgba(78, 205, 196, 0.2);
    position: relative;
}

.modal-content::before {
    content: '';
    position: absolute;
    top: -1px;
    left: 15%;
    right: 15%;
    height: 2px;
    background: linear-gradient(90deg, transparent, #4ecdc4, transparent);
    border-radius: 50%;
}

.modal-header {
    padding: 20px;
    border-bottom: 1px solid rgba(78, 205, 196, 0.15);
}

.modal-title-group {
    display: flex;
    flex-direction: column;
    align-items: center;
}

.modal-title {
    color: #fff;
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 8px;
    text-shadow: 0 0 10px rgba(78, 205, 196, 0.3);
}

.modal-subtitle {
    color: #a0a0b0;
    font-size: 14px;
}

.modal-subtitle .highlight {
    color: #4ecdc4;
    font-weight: bold;
    text-shadow: 0 0 8px rgba(78, 205, 196, 0.3);
}

.modal-body {
    padding: 20px;
}

.modal-footer {
    padding: 16px 20px;
    border-top: 1px solid rgba(78, 205, 196, 0.15);
}

.modal-actions {
    display: flex;
    gap: 12px;
    justify-content: space-between;
}

.btn {
    padding: 12px 20px;
    border-radius: 8px;
    font-size: 14px;
    border: none;
    cursor: pointer;
    transition: all 0.2s;
}

.btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.btn-primary {
    background: linear-gradient(135deg, #4ecdc4, #3ba89f);
    color: #0a0a1a;
    font-weight: bold;
    box-shadow: 0 0 15px rgba(78, 205, 196, 0.3);
}

.btn-primary:active {
    box-shadow: 0 0 25px rgba(78, 205, 196, 0.5);
    transform: scale(0.98);
}

.btn-secondary {
    background: rgba(255, 255, 255, 0.08);
    color: #a0a0b0;
    border: 1px solid rgba(255, 255, 255, 0.15);
}

.btn-ghost {
    background: transparent;
    color: #a0a0b0;
    border: 1px solid rgba(255, 255, 255, 0.15);
}

.btn-outline {
    background: transparent;
    color: #4ecdc4;
    border: 1px solid rgba(78, 205, 196, 0.4);
    padding: 10px 16px;
    font-size: 13px;
}

.btn-outline:disabled {
    opacity: 0.4;
    border-color: rgba(78, 205, 196, 0.2);
    color: rgba(78, 205, 196, 0.3);
}

.w-full {
    width: 100%;
}

.shrimp-modal .indicator-display {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 20px 0;
}

.shrimp-modal .indicator-icon {
    font-size: 48px;
    margin-bottom: 16px;
}

.shrimp-modal .indicator-text {
    color: #fff;
    font-size: 16px;
    text-align: center;
}

.shrimp-draw-messages {
    position: fixed;
    top: 10%;
    left: 50%;
    transform: translateX(-50%);
    z-index: 9999;
    pointer-events: none;
    width: 70%;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0;
}

.shrimp-draw-msg {
    padding: 4rpx 40rpx;
    background: transparent;
    width: 100%;
    animation: shrimpDrawFadeIn 0.3s ease-out;
}

.shrimp-draw-msg-text {
    font-size: 22rpx;
    font-weight: 600;
    color: #e2c38f;
    text-align: center;
    text-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.8),
    0 0 20rpx rgba(0, 0, 0, 0.5);
    font-family: 'Georgia', 'Times New Roman', serif;
    white-space: normal;
    word-wrap: break-word;
}

@keyframes shrimpDrawFadeIn {
    from {
        opacity: 0;
        transform: translateY(-10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.shrimp-modal .choice-buttons {
    display: flex;
    gap: 16px;
    margin-top: 20px;
}

.shrimp-modal .btn-choice {
    flex: 1;
    background: rgba(78, 205, 196, 0.08);
    color: #fff;
    padding: 16px;
    font-size: 16px;
    border: 2px solid rgba(78, 205, 196, 0.3);
    border-radius: 8px;
}

.shrimp-modal .btn-choice:active {
    border-color: #4ecdc4;
    background: rgba(78, 205, 196, 0.15);
}

.seafood-market-modal .market-display-board {
    padding: 16px 20px;
    background: rgba(78, 205, 196, 0.05);
    border-bottom: 1px solid rgba(78, 205, 196, 0.1);
}

.seafood-market-modal .price-title {
    color: #4ecdc4;
    font-size: 14px;
    font-weight: bold;
    display: block;
    margin-bottom: 8px;
    text-shadow: 0 0 8px rgba(78, 205, 196, 0.3);
}

.seafood-market-modal .price-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.seafood-market-modal .price-tags text {
    color: #a0a0b0;
    font-size: 12px;
    background: rgba(78, 205, 196, 0.08);
    padding: 4px 8px;
    border-radius: 4px;
    border: 1px solid rgba(78, 205, 196, 0.1);
}

.seafood-market-modal .trade-grid {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.seafood-market-modal .trade-row {
    display: flex;
    gap: 12px;
}

.seafood-market-modal .trade-row .btn {
    flex: 1;
}

.breeding-modal .lobster-selection {
    display: flex;
    flex-direction: column;
}

.breeding-modal .section-label {
    color: #a0a0b0;
    font-size: 14px;
    margin-bottom: 12px;
}

.breeding-modal .lobster-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
}

.breeding-modal .lobster-card {
    background: rgba(78, 205, 196, 0.05);
    border: 1px solid rgba(78, 205, 196, 0.15);
    border-radius: 8px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    overflow: hidden;
    transition: all 0.2s;
}

.breeding-modal .lobster-card:active:not(.max-royal) {
    border-color: #4ecdc4;
    background: rgba(78, 205, 196, 0.1);
}

.breeding-modal .lobster-card.max-royal {
    opacity: 0.6;
}

.breeding-modal .lobster-icon {
    font-size: 32px;
    margin-bottom: 8px;
}

.breeding-modal .lobster-grade {
    color: #4ecdc4;
    font-size: 12px;
    font-weight: bold;
    text-shadow: 0 0 8px rgba(78, 205, 196, 0.3);
}

.breeding-modal .lobster-title {
    color: #ffd700;
    font-size: 11px;
    margin-top: 4px;
}

.breeding-modal .max-grade-mask {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #666;
    font-size: 14px;
    font-weight: bold;
}

.breeding-modal .empty-hint {
    color: #666;
    text-align: center;
    padding: 20px;
}

.breeding-modal .breeding-action-panel {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.breeding-modal .upgrade-path {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
}

.breeding-modal .grade-box {
    display: flex;
    flex-direction: column;
    align-items: center;
    background: rgba(78, 205, 196, 0.08);
    padding: 8px 16px;
    border-radius: 8px;
    border: 1px solid rgba(78, 205, 196, 0.15);
}

.breeding-modal .grade-box text {
    color: #a0a0b0;
    font-size: 11px;
}

.breeding-modal .grade-box .val {
    color: #fff;
    font-size: 14px;
    font-weight: bold;
    margin-top: 4px;
}

.breeding-modal .grade-box .val.highlight {
    color: #4ecdc4;
    text-shadow: 0 0 8px rgba(78, 205, 196, 0.3);
}

.breeding-modal .arrow {
    color: #4ecdc4;
    font-size: 20px;
    text-shadow: 0 0 10px rgba(78, 205, 196, 0.4);
}

.breeding-modal .options-group {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.breeding-modal .checkbox-wrapper {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background: rgba(78, 205, 196, 0.05);
    border-radius: 8px;
    border: 1px solid rgba(78, 205, 196, 0.1);
}

.breeding-modal .checkbox-wrapper.disabled {
    opacity: 0.5;
}

.breeding-modal .custom-checkbox {
    width: 18px;
    height: 18px;
    border: 2px solid rgba(255, 255, 255, 0.2);
    border-radius: 4px;
}

.breeding-modal .custom-checkbox.checked {
    background: #4ecdc4;
    border-color: #4ecdc4;
    box-shadow: 0 0 8px rgba(78, 205, 196, 0.4);
}

.breeding-modal .checkbox-text {
    color: #a0a0b0;
    font-size: 13px;
}

.breeding-modal .royal-requirements {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 12px;
    background: rgba(255, 215, 0, 0.08);
    border-radius: 8px;
    border: 1px solid rgba(255, 215, 0, 0.25);
}

.breeding-modal .req-title {
    color: #ffd700;
    font-size: 13px;
    font-weight: bold;
    text-shadow: 0 0 8px rgba(255, 215, 0, 0.3);
}

.breeding-modal .cost-options {
    display: flex;
    gap: 8px;
}

.breeding-modal .cost-btn {
    flex: 1;
    padding: 10px;
    background: rgba(255, 255, 255, 0.05);
    color: #a0a0b0;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 8px;
    font-size: 12px;
}

.breeding-modal .cost-btn.active {
    background: rgba(78, 205, 196, 0.15);
    border-color: #4ecdc4;
    color: #4ecdc4;
    box-shadow: 0 0 10px rgba(78, 205, 196, 0.2);
}

.breeding-modal .cost-btn:disabled {
    opacity: 0.4;
}

.breeding-modal .modal-actions {
    display: flex;
    gap: 12px;
}

/* 添加皇家龙虾奖励选择和称号选择的样式支持 */
.title-cards {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.title-card {
    padding: 8px 12px;
    background: rgba(255, 215, 0, 0.05);
    border: 1px solid rgba(255, 215, 0, 0.2);
    border-radius: 8px;
    color: #ffd700;
    font-size: 12px;
    transition: all 0.2s;
}

.title-card.active {
    background: rgba(255, 215, 0, 0.2);
    border-color: #ffd700;
    box-shadow: 0 0 10px rgba(255, 215, 0, 0.4);
}

.marketplace-modal .marketplace-cards {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
}

.marketplace-modal .mp-card {
    background: rgba(78, 205, 196, 0.05);
    border: 1px solid rgba(78, 205, 196, 0.15);
    border-radius: 8px;
    padding: 12px;
    position: relative;
    overflow: hidden;
    transition: all 0.2s;
}

.marketplace-modal .mp-card:active:not(.used) {
    border-color: #4ecdc4;
    background: rgba(78, 205, 196, 0.1);
}

.marketplace-modal .mp-card.selected {
    border-color: #4ecdc4;
    background: rgba(78, 205, 196, 0.15);
    box-shadow: 0 0 15px rgba(78, 205, 196, 0.2);
}

.marketplace-modal .mp-card.used {
    opacity: 0.5;
}

.marketplace-modal .mp-card-name {
    color: #fff;
    font-size: 14px;
    font-weight: bold;
    display: block;
    margin-bottom: 4px;
}

.marketplace-modal .mp-card-desc {
    color: #666;
    font-size: 11px;
    display: block;
}

.marketplace-modal .used-mask {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #666;
    font-size: 12px;
    font-weight: bold;
}

.marketplace-modal .mp-options-panel {
    margin-top: 16px;
    padding: 12px;
    background: rgba(78, 205, 196, 0.05);
    border-radius: 8px;
    border: 1px solid rgba(78, 205, 196, 0.1);
}

.marketplace-modal .mp-options {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 8px;
}

.marketplace-modal .mp-option-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 12px;
    background: rgba(78, 205, 196, 0.05);
    border: 1px solid rgba(78, 205, 196, 0.15);
    border-radius: 8px;
}

.marketplace-modal .mp-option-btn.active {
    border-color: #4ecdc4;
    background: rgba(78, 205, 196, 0.15);
    box-shadow: 0 0 10px rgba(78, 205, 196, 0.15);
}

.marketplace-modal .custom-radio {
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255, 255, 255, 0.2);
    border-radius: 50%;
}

.marketplace-modal .custom-radio.checked {
    border-color: #4ecdc4;
    background: #4ecdc4;
    box-shadow: 0 0 8px rgba(78, 205, 196, 0.4);
}

.marketplace-modal .option-text {
    color: #a0a0b0;
    font-size: 12px;
}

.marketplace-modal .error-hint {
    color: #e94560;
    font-size: 12px;
    margin-top: 8px;
    display: block;
    text-shadow: 0 0 8px rgba(233, 69, 96, 0.3);
}

.animate-fade-in {
    animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.tribute-modal {
    background: #1a1a2e;
    border-radius: 16px;
    width: 90%;
    max-width: 500px;
    max-height: 85vh;
    overflow-y: auto;
    border: 1px solid rgba(78, 205, 196, 0.2);
    box-shadow: 0 0 40px rgba(0, 0, 0, 0.6);
}

.tribute-modal .modal-header {
    padding: 20px;
    border-bottom: 1px solid rgba(78, 205, 196, 0.15);
}

.tribute-modal .modal-title-group {
    display: flex;
    flex-direction: column;
    align-items: center;
}

.tribute-modal .modal-title {
    color: #fff;
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 8px;
    text-shadow: 0 0 10px rgba(78, 205, 196, 0.3);
}

.tribute-modal .modal-subtitle {
    color: #a0a0b0;
    font-size: 14px;
    text-align: center;
}

.tribute-modal .modal-body {
    padding: 16px;
    max-height: 60vh;
    overflow-y: auto;
}

.tribute-modal .taverns-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.tribute-modal .tavern-box {
    background: rgba(78, 205, 196, 0.05);
    border-radius: 12px;
    padding: 12px;
    border: 1px solid rgba(78, 205, 196, 0.1);
}

.tribute-modal .tavern-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}

.tribute-modal .tavern-name {
    color: #ffd700;
    font-size: 15px;
    font-weight: bold;
    text-shadow: 0 0 8px rgba(255, 215, 0, 0.3);
}

.tribute-modal .tavern-status {
    color: #4ecdc4;
    font-size: 12px;
}

.tribute-modal .empty-hint {
    color: #666;
    font-size: 13px;
    text-align: center;
    padding: 10px;
}

.tribute-modal .tribute-cards {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.tribute-modal .tribute-card {
    background: rgba(78, 205, 196, 0.05);
    border-radius: 8px;
    padding: 10px;
    border: 1px solid rgba(78, 205, 196, 0.1);
}

.tribute-modal .tc-name {
    color: #fff;
    font-size: 14px;
    font-weight: bold;
}

.tribute-modal .tc-desc {
    color: #a0a0b0;
    font-size: 12px;
    display: block;
    margin: 4px 0;
}

.tribute-modal .tc-req,
.tribute-modal .tc-rew {
    color: #666;
    font-size: 11px;
}

.tribute-modal .btn-sm {
    padding: 8px 16px;
    font-size: 12px;
}

.tribute-modal .mt-2 {
    margin-top: 8px;
}

.tribute-modal .naked-intro {
    background: rgba(233, 69, 96, 0.1);
    border: 1px solid rgba(233, 69, 96, 0.25);
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 16px;
}

.tribute-modal .warn-text {
    color: #e94560;
    font-size: 16px;
    font-weight: bold;
    display: block;
    margin-bottom: 8px;
    text-shadow: 0 0 10px rgba(233, 69, 96, 0.4);
}

.tribute-modal .sub-text {
    color: #a0a0b0;
    font-size: 13px;
    line-height: 1.5;
}

.tribute-modal .section-label {
    color: #a0a0b0;
    font-size: 13px;
    font-weight: bold;
    margin-bottom: 8px;
}

.tribute-modal .mt-4 {
    margin-top: 16px;
}

.tribute-modal .lobster-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.tribute-modal .lobster-card {
    background: rgba(78, 205, 196, 0.05);
    border-radius: 8px;
    padding: 10px;
    text-align: center;
    border: 2px solid transparent;
    min-width: 70px;
    transition: all 0.2s;
}

.tribute-modal .lobster-card.selected {
    border-color: #4ecdc4;
    background: rgba(78, 205, 196, 0.15);
    box-shadow: 0 0 12px rgba(78, 205, 196, 0.3);
}

.tribute-modal .lobster-icon {
    font-size: 24px;
    display: block;
}

.tribute-modal .lobster-grade {
    color: #fff;
    font-size: 12px;
    display: block;
}

.tribute-modal .lobster-title {
    color: #ffd700;
    font-size: 10px;
    display: block;
}

.tribute-modal .tavern-select-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.tribute-modal .tavern-select-btn {
    background: rgba(78, 205, 196, 0.05);
    border-radius: 8px;
    padding: 10px;
    text-align: center;
    border: 2px solid transparent;
    min-width: 80px;
    transition: all 0.2s;
}

.tribute-modal .tavern-select-btn.active {
    border-color: #4ecdc4;
    background: rgba(78, 205, 196, 0.15);
    box-shadow: 0 0 12px rgba(78, 205, 196, 0.2);
}

.tribute-modal .tavern-select-btn.disabled {
    opacity: 0.4;
}

.tribute-modal .ts-name {
    color: #fff;
    font-size: 13px;
    display: block;
}

.tribute-modal .ts-status {
    color: #666;
    font-size: 11px;
    display: block;
}

.tribute-modal .ts-lock {
    color: #e94560;
    font-size: 10px;
    display: block;
}

.tribute-modal .reward-options {
    display: flex;
    gap: 12px;
}

.tribute-modal .custom-radio-wrap {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 12px;
    background: rgba(78, 205, 196, 0.05);
    border-radius: 8px;
    border: 2px solid transparent;
    color: #a0a0b0;
    font-size: 13px;
    transition: all 0.2s;
}

.tribute-modal .custom-radio-wrap.active {
    border-color: #4ecdc4;
    background: rgba(78, 205, 196, 0.15);
    color: #4ecdc4;
    box-shadow: 0 0 12px rgba(78, 205, 196, 0.2);
}

.tribute-modal .custom-radio {
    width: 18px;
    height: 18px;
    border-radius: 50%;
    border: 2px solid rgba(255, 255, 255, 0.2);
    margin-right: 8px;
}

.tribute-modal .custom-radio.checked {
    background: #4ecdc4;
    border-color: #4ecdc4;
    box-shadow: 0 0 8px rgba(78, 205, 196, 0.4);
}

.tribute-modal .bonus-tribute-section {
    padding: 12px 20px;
    background: rgba(255, 215, 0, 0.05);
    border-top: 1px solid rgba(255, 215, 0, 0.15);
    border-bottom: 1px solid rgba(255, 215, 0, 0.15);
}

.tribute-modal .bonus-tribute-section .section-label {
    font-size: 14px;
    color: #ffd700;
    font-weight: bold;
    margin-bottom: 10px;
    text-align: center;
    display: block;
}

.tribute-modal .modal-footer {
    padding: 16px 20px;
    border-top: 1px solid rgba(78, 205, 196, 0.15);
}

.tribute-modal .modal-actions {
    display: flex;
    gap: 12px;
    justify-content: space-between;
}

.tribute-modal .error-hint {
    color: #e94560;
    font-size: 12px;
    text-align: center;
    padding: 8px;
}

.tribute-modal .lobster-picker-panel {
    padding: 12px 20px;
}

.tribute-modal .lobster-req-hint {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 12px;
}

.tribute-modal .lobster-req-hint .req-item {
    background: rgba(255, 107, 107, 0.15);
    color: #ff6b6b;
    font-size: 12px;
    padding: 4px 10px;
    border-radius: 12px;
    display: inline-block;
}

.tribute-modal .lobster-picker-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 10px;
    max-height: 400px;
    overflow-y: auto;
}

.tribute-modal .lobster-pick-card {
    background: rgba(78, 205, 196, 0.05);
    border: 2px solid rgba(78, 205, 196, 0.15);
    border-radius: 10px;
    padding: 10px 8px;
    text-align: center;
    cursor: pointer;
    min-width: 0;
    position: relative;
    transition: all 0.2s;
}

.tribute-modal .lobster-pick-card.selected {
    border-color: #4ecdc4;
    background: rgba(78, 205, 196, 0.15);
    box-shadow: 0 0 12px rgba(78, 205, 196, 0.3);
}

.tribute-modal .lobster-pick-card.title-card-pick {
    border-color: rgba(255, 215, 0, 0.3);
    background: rgba(255, 215, 0, 0.05);
}

.tribute-modal .lobster-pick-card.title-card-pick.selected {
    border-color: #ffd700;
    background: rgba(255, 215, 0, 0.15);
    box-shadow: 0 0 12px rgba(255, 215, 0, 0.3);
}

.tribute-modal .lpd-check {
    position: absolute;
    top: -6px;
    right: -6px;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: rgba(100, 100, 100, 0.8);
    color: #fff;
    font-size: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.tribute-modal .lpd-check.checked {
    background: #4ecdc4;
    box-shadow: 0 0 8px rgba(78, 205, 196, 0.5);
}

.tribute-modal .lpd-icon {
    font-size: 32px;
    display: block;
}

.tribute-modal .lpd-grade {
    color: #fff;
    font-size: 14px;
    display: block;
    margin-top: 2px;
}

.tribute-modal .lpd-title {
    color: #ffd700;
    font-size: 12px;
    display: block;
    margin-top: 2px;
}

.tribute-modal .lobster-picker-count {
    text-align: center;
    color: #a0a0b0;
    font-size: 13px;
    margin-top: 10px;
}

.tribute-modal .btn-warning {
    background: linear-gradient(135deg, #e94560, #c23152);
    color: #fff;
    font-weight: bold;
    box-shadow: 0 0 15px rgba(233, 69, 96, 0.3);
}

.tribute-modal .btn-warning:active {
    box-shadow: 0 0 25px rgba(233, 69, 96, 0.5);
    transform: scale(0.98);
}

.tribute-modal .btn-warning:disabled {
    opacity: 0.5;
}

.tribute-modal .error-hint {
    color: #e94560;
    font-size: 12px;
    text-shadow: 0 0 8px rgba(233, 69, 96, 0.3);
}
</style>