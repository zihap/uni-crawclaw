<script>
	export default {
		onLaunch: function() {
			console.log('App Launch')
		},
		onShow: function() {
			console.log('App Show')
		},
		onHide: function() {
			console.log('App Hide')
		}
	}
</script>

<style>
	/* 引入全局CSS变量 */
	@import './styles/variables.css';

	/* 每个页面公共css */
	page {
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
		-webkit-font-smoothing: antialiased;
		-moz-osx-font-smoothing: grayscale;
	}

	/* 重置默认样式 */
	* {
		box-sizing: border-box;
	}

	/* 隐藏滚动条但保留滚动功能 */
	::-webkit-scrollbar {
		width: 0;
		height: 0;
		background: transparent;
	}

	/* 按钮重置 */
	button {
		margin: 0;
		padding: 0;
		background: none;
		border: none;
		font-size: inherit;
		line-height: inherit;
	}

	button::after {
		border: none;
	}

	/* 文本重置 */
	text {
		display: inline-block;
	}

	/* 图片重置 */
	image {
		display: block;
		width: 100%;
		height: auto;
	}

	/* 安全区域适配 */
	.safe-area-bottom {
		padding-bottom: constant(safe-area-inset-bottom);
		padding-bottom: env(safe-area-inset-bottom);
	}

	.safe-area-top {
		padding-top: constant(safe-area-inset-top);
		padding-top: env(safe-area-inset-top);
	}
</style>
