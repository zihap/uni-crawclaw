/**
 * 日志工具类
 * 用于统一管理和记录应用日志
 */

class Logger {
  constructor() {
    this.logs = []
    this.maxLogs = 1000
  }

  info(message, data = null) {
    this._log('info', message, data)
  }

  warn(message, data = null) {
    this._log('warn', message, data)
  }

  error(message, data = null) {
    this._log('error', message, data)
  }

  debug(message, data = null) {
    this._log('debug', message, data)
  }

  _log(level, message, data) {
    const logEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      data
    }

    this.logs.push(logEntry)

    if (this.logs.length > this.maxLogs) {
      this.logs.shift()
    }

    // 在开发环境下输出到控制台
    // #ifdef H5
    const colors = {
      info: '#2196F3',
      warn: '#FF9800',
      error: '#F44336',
      debug: '#4CAF50'
    }
    console.log(
      `%c[${level.toUpperCase()}] %s`,
      `color: ${colors[level]}; font-weight: bold;`,
      message,
      data || ''
    )
    // #endif

    // 非H5平台使用普通console
    // #ifndef H5
    console.log(`[${level.toUpperCase()}]`, message, data || '')
    // #endif
  }

  getLogs(level = null) {
    if (level) {
      return this.logs.filter(log => log.level === level)
    }
    return this.logs
  }

  clearLogs() {
    this.logs = []
  }

  exportLogs() {
    return JSON.stringify(this.logs, null, 2)
  }
}

export const logger = new Logger()

/**
 * 带错误捕获的异步执行函数
 * @param {Function} fn - 要执行的异步函数
 * @param {string} errorMessage - 错误提示信息
 * @returns {Promise} 执行结果
 */
export const tryCatch = async (fn, errorMessage = '操作失败') => {
  try {
    return await fn()
  } catch (error) {
    logger.error(errorMessage, error)
    uni.showToast({
      title: errorMessage,
      icon: 'none',
      duration: 2000
    })
    throw error
  }
}

/**
 * 安全执行函数
 * @param {Function} fn - 要执行的函数
 * @param {*} fallbackValue - 出错时的返回值
 * @param {string} errorMessage - 错误信息
 * @returns {*} 执行结果或fallbackValue
 */
export const safeExecute = (fn, fallbackValue = null, errorMessage = '执行出错') => {
  try {
    const result = fn()
    if (result instanceof Promise) {
      return result.catch(error => {
        logger.error(errorMessage, error)
        return fallbackValue
      })
    }
    return result
  } catch (error) {
    logger.error(errorMessage, error)
    return fallbackValue
  }
}
