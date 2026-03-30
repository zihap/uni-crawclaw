# CSS样式重构实施指南

## 项目概述

本指南详细说明了如何将项目中的内联CSS样式系统性地重构为现代化的独立CSS文件系统。

## 重构目标

1. **提高可维护性** - 集中管理样式，减少重复代码
2. **增强一致性** - 使用设计令牌确保视觉统一
3. **支持响应式** - 移动优先的响应式设计
4. **优化性能** - 减少CSS文件大小，提高加载速度
5. **提升体验** - 添加流畅的动画和过渡效果

## 文件结构

```
src/styles/
├── tokens/                    # 设计令牌
│   ├── colors.css            # 颜色系统（支持暗黑主题）
│   ├── typography.css        # 排版系统
│   ├── spacing.css           # 间距系统
│   ├── shadows.css           # 阴影系统
│   └── animations.css        # 动画系统
├── core/                      # 核心样式
│   ├── reset.css             # CSS重置
│   ├── base.css              # 基础样式和工具类
│   └── responsive.css        # 响应式框架
├── components/                # 组件样式
│   ├── buttons.css           # 按钮组件
│   └── cards.css             # 卡片组件
├── index.css                  # 主入口文件
└── REFACTORING_GUIDE.md       # 本指南
```

## 样式迁移步骤

### 第一步：引入新样式系统

在 `App.vue` 中已引入：

```css
@import './styles/index.css';
@import './styles/core/responsive.css';
```

### 第二步：替换颜色变量

**旧写法：**

```css
background: var(--primary-color);
color: var(--text-primary);
```

**新写法：**

```css
background: var(--color-primary);
color: var(--color-text-primary);
```

### 第三步：使用组件类

**按钮组件：**

```html
<!-- 旧写法 -->
<button class="start-btn">开始</button>

<!-- 新写法 -->
<button class="btn btn-primary btn-lg">开始</button>
```

**卡片组件：**

```html
<!-- 旧写法 -->
<view class="content">
    <!-- 内容 -->
</view>

<!-- 新写法 -->
<view class="card card-interactive">
    <view class="card-body">
        <!-- 内容 -->
    </view>
</view>
```

### 第四步：使用工具类

**布局：**

```html
<view class="flex items-center justify-between gap-4">
    <!-- 内容 -->
</view>
```

**间距：**

```html
<view class="p-4 px-6 py-8">
    <!-- 内容 -->
</view>
```

**文本：**

```html
<text class="text-lg font-semibold text-primary"> 标题文本 </text>
```

### 第五步：添加动画效果

```html
<view class="animate-slide-up delay-200">
    <!-- 内容 -->
</view>
```

## 兼容性处理

### 1. CSS变量降级

所有CSS变量都有降级值：

```css
color: var(--color-text-primary, #171717);
```

### 2. 浏览器前缀

使用Autoprefixer自动添加浏览器前缀。

### 3. 响应式断点

- sm: 640px
- md: 768px
- lg: 1024px
- xl: 1280px
- 2xl: 1536px

### 4. 安全区域适配

```css
.safe-area-top {
    padding-top: env(safe-area-inset-top);
}

.safe-area-bottom {
    padding-bottom: env(safe-area-inset-bottom);
}
```

## 质量验证标准

### 1. 视觉一致性检查

- [ ] 所有颜色使用设计令牌
- [ ] 间距遵循4px网格系统
- [ ] 字体大小使用排版比例尺
- [ ] 阴影使用预定义变量

### 2. 响应式检查

- [ ] 移动端（<640px）显示正常
- [ ] 平板端（768px-1024px）显示正常
- [ ] 桌面端（>1024px）显示正常
- [ ] 横竖屏切换正常

### 3. 交互检查

- [ ] 按钮hover效果正常
- [ ] 卡片悬浮效果正常
- [ ] 过渡动画流畅
- [ ] 焦点状态可见

### 4. 性能检查

- [ ] 首屏加载时间 < 3秒
- [ ] 无样式闪烁（FOUC）
- [ ] 动画帧率 > 60fps
- [ ] 内存占用合理

### 5. 可访问性检查

- [ ] 颜色对比度符合WCAG标准
- [ ] 支持键盘导航
- [ ] 支持屏幕阅读器
- [ ] 支持高对比度模式

## 迁移示例

### 首页迁移示例

**迁移前：**

```vue
<template>
    <view class="container">
        <view class="header">
            <text class="title">龙争虾斗</text>
        </view>
    </view>
</template>

<style scoped>
.container {
    min-height: 100vh;
    padding: 1rem;
    background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%);
}
.header {
    text-align: center;
    padding: 2rem 0;
}
.title {
    font-size: 2.5rem;
    font-weight: 700;
    color: #fff;
}
</style>
```

**迁移后：**

```vue
<template>
    <view
        class="min-h-screen p-4 flex flex-col items-center justify-center"
        style="background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%)"
    >
        <view class="text-center py-8 animate-fade-in">
            <text class="text-5xl font-bold text-inverse">龙争虾斗</text>
        </view>
    </view>
</template>
```

## 注意事项

1. **逐步迁移** - 不要一次性修改所有文件，分页面逐步迁移
2. **测试验证** - 每次修改后都要进行测试
3. **保留备份** - 修改前备份原始文件
4. **团队协作** - 确保团队成员了解新的样式系统
5. **文档更新** - 及时更新相关文档

## 后续优化

1. 添加更多组件样式（表单、导航、模态框等）
2. 实现主题切换功能
3. 优化CSS文件大小（使用PurgeCSS）
4. 添加CSS自定义属性polyfill支持
5. 实现设计系统文档站点

## 参考资料

- [Modern CSS Reset](https://piccalil.li/blog/a-modern-css-reset/)
- [CSS Custom Properties](https://developer.mozilla.org/en-US/docs/Web/CSS/--*)
- [Responsive Design](https://developer.mozilla.org/en-US/docs/Learn/CSS/CSS_layout/Responsive_Design)
- [CSS Animations](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Animations/Using_CSS_animations)
