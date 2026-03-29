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
	/* 引入现代化样式系统 */
	@import './styles/index.css';

	/* 每个页面公共css */
	page {
		font-family: var(--font-family-base);
		-webkit-font-smoothing: antialiased;
		-moz-osx-font-smoothing: grayscale;
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

  /* #ifdef MP-WEIXIN */
  view, text, button, image, navigator, input, textarea, cover-view, cover-image {
    box-sizing: border-box;
  }
  page {
    margin: 0;
    padding: 0;
  }
  /* #endif */
</style>
