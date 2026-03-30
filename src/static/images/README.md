《巨螯》微信小程序登录页 - 切图规范与存放目录

请美术同学或开发同学将切图放置于此目录 (src/static/images/) 中。
我们在 pages/index/index.vue 代码里已经写好了这些图片的绝对定位与层叠顺序（Z-index）。只要文件名对应正确，页面启动后图片将自动拼装成高品质 2.5D 视差效果！

需放入此文件夹的文件清单：

1. 场景背景

bg_ocean.jpg : 游戏全屏海底背景图，不需要透明底。（Z-index: 0）

2. 人物与角色图层（必须为透明底 PNG）

viking_left.png : 左侧维京勇士半身像。（Z-index: 10）

viking_right.png : 右侧维京勇士半身像。（Z-index: 10）

boss_shrimp.png : 中央熔岩霸王虾主体躯干，不包含巨螯。（Z-index: 20）

claw_ice.png : 左侧冰霜发光巨螯。（Z-index: 30）

claw_fire.png : 右侧熔岩发光巨螯。（Z-index: 30）

3. UI 界面层（必须为透明底 PNG）

logo.png : 屏幕上方的【巨螯】游戏Logo艺术字。

icon_setting.png : 右侧悬浮齿轮设置按钮。

icon_notice.png : 右侧悬浮卷轴公告按钮。

4. 底部资产小图标（必须为透明底 PNG）

icon_silver.png : 符文银

icon_anemone.png : 荧光海葵

icon_urn.png : 圣瓮

icon_box.png : 宝匣

提示：在图片缺失的情况下，页面预览会显示带有半透明底色的纯色圆形或方块，用以标识出占位位置。
