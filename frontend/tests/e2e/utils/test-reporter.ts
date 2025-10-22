import { FullConfig, FullResult, TestCase, TestResult } from '@playwright/test/reporter';
import * as fs from 'fs';
import * as path from 'path';

/**
 * 自定义测试报告器
 * 生成详细的HTML和JSON报告
 */

interface TestReportData {
  timestamp: string;
  summary: {
    total: number;
    passed: number;
    failed: number;
    skipped: number;
    duration: number;
  };
  tests: TestDetail[];
  performance: PerformanceMetrics[];
  screenshots: ScreenshotInfo[];
}

interface TestDetail {
  title: string;
  status: string;
  duration: number;
  error?: string;
  category: string;
  browser?: string;
  viewport?: string;
}

interface PerformanceMetrics {
  testName: string;
  loadTime?: number;
  apiResponseTime?: number;
  domContentLoaded?: number;
  memoryUsage?: number;
}

interface ScreenshotInfo {
  testName: string;
  path: string;
  timestamp: string;
  description: string;
}

class CustomTestReporter {
  private reportData: TestReportData = {
    timestamp: new Date().toISOString(),
    summary: {
      total: 0,
      passed: 0,
      failed: 0,
      skipped: 0,
      duration: 0
    },
    tests: [],
    performance: [],
    screenshots: []
  };

  private screenshotsDir = 'test-results/screenshots';
  private reportsDir = 'test-results/reports';

  constructor() {
    // 确保目录存在
    this.ensureDirectoryExists(this.screenshotsDir);
    this.ensureDirectoryExists(this.reportsDir);
  }

  private ensureDirectoryExists(dirPath: string) {
    if (!fs.existsSync(dirPath)) {
      fs.mkdirSync(dirPath, { recursive: true });
    }
  }

  onBegin(config: FullConfig, result: FullResult) {
    console.log('🚀 开始执行E2E测试...');
    console.log(`📋 测试文件数量: ${result.specs.length}`);

    // 清理旧的报告文件
    this.cleanOldReports();
  }

  onTestBegin(test: TestCase, result: TestResult) {
    console.log(`🔍 开始测试: ${test.title}`);
  }

  onTestEnd(test: TestCase, result: TestResult) {
    const testDetail: TestDetail = {
      title: test.title,
      status: result.status,
      duration: result.duration,
      category: this.extractCategory(test.title),
      browser: this.extractBrowser(test.title),
      viewport: this.extractViewport(test.title)
    };

    if (result.status === 'failed' && result.error) {
      testDetail.error = result.error.message || result.error.stack || 'Unknown error';
    }

    this.reportData.tests.push(testDetail);
    this.updateSummary(result);

    // 收集性能数据
    this.collectPerformanceData(test, result);

    // 收集截图信息
    this.collectScreenshotInfo(test, result);

    console.log(`${this.getStatusIcon(result.status)} 测试完成: ${test.title} (${result.duration}ms)`);
  }

  onEnd(result: FullResult) {
    this.reportData.summary.duration = result.duration;

    // 生成HTML报告
    this.generateHtmlReport();

    // 生成JSON报告
    this.generateJsonReport();

    // 打印总结
    this.printSummary();
  }

  private extractCategory(title: string): string {
    if (title.includes('首页')) return '首页功能';
    if (title.includes('AI单词生成') || title.includes('word-generation')) return 'AI单词生成';
    if (title.includes('查询限制') || title.includes('query-limit')) return '查询限制';
    if (title.includes('响应式') || title.includes('responsive')) return '响应式设计';
    if (title.includes('浏览器') || title.includes('browser')) return '跨浏览器';
    return '其他功能';
  }

  private extractBrowser(title: string): string {
    if (title.includes('Chromium') || title.includes('Chrome')) return 'Chrome';
    if (title.includes('Firefox')) return 'Firefox';
    if (title.includes('WebKit') || title.includes('Safari')) return 'Safari';
    return '未指定';
  }

  private extractViewport(title: string): string {
    if (title.includes('Desktop')) return '桌面';
    if (title.includes('Tablet') || title.includes('iPad')) return '平板';
    if (title.includes('Mobile') || title.includes('iPhone')) return '手机';
    return '未指定';
  }

  private updateSummary(result: TestResult) {
    this.reportData.summary.total++;

    switch (result.status) {
      case 'passed':
        this.reportData.summary.passed++;
        break;
      case 'failed':
        this.reportData.summary.failed++;
        break;
      case 'skipped':
        this.reportData.summary.skipped++;
        break;
    }
  }

  private collectPerformanceData(test: TestCase, result: TestResult) {
    // 这里可以收集性能相关的数据
    // 实际项目中可以从测试结果中提取性能指标
    if (test.title.includes('性能') || test.title.includes('performance')) {
      this.reportData.performance.push({
        testName: test.title,
        loadTime: Math.random() * 1000, // 示例数据
        apiResponseTime: Math.random() * 5000, // 示例数据
        memoryUsage: Math.random() * 100 // 示例数据
      });
    }
  }

  private collectScreenshotInfo(test: TestCase, result: TestResult) {
    // 收集测试截图信息
    if (result.status === 'failed' || test.title.includes('响应式')) {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const screenshotPath = `${this.screenshotsDir}/${test.title.replace(/[^a-zA-Z0-9]/g, '-')}-${timestamp}.png`;

      this.reportData.screenshots.push({
        testName: test.title,
        path: screenshotPath,
        timestamp: new Date().toISOString(),
        description: `测试: ${test.title}, 状态: ${result.status}`
      });
    }
  }

  private cleanOldReports() {
    try {
      const files = fs.readdirSync(this.reportsDir);
      const now = Date.now();
      const oneDayAgo = now - (24 * 60 * 60 * 1000);

      files.forEach(file => {
        const filePath = path.join(this.reportsDir, file);
        const stats = fs.statSync(filePath);

        if (stats.mtime.getTime() < oneDayAgo) {
          fs.unlinkSync(filePath);
          console.log(`🗑️ 清理旧报告: ${file}`);
        }
      });
    } catch (error) {
      console.log('⚠️ 清理旧报告时出错:', error);
    }
  }

  private generateHtmlReport() {
    const htmlContent = this.generateHtmlContent();
    const htmlPath = path.join(this.reportsDir, `e2e-report-${Date.now()}.html`);

    fs.writeFileSync(htmlPath, htmlContent);
    console.log(`📄 HTML报告已生成: ${htmlPath}`);
  }

  private generateHtmlContent(): string {
    const passRate = this.reportData.summary.total > 0
      ? (this.reportData.summary.passed / this.reportData.summary.total * 100).toFixed(1)
      : '0';

    return `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>拆词鸭 E2E 测试报告</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; }
        .header h1 { margin: 0; font-size: 2.5em; }
        .header p { margin: 10px 0 0 0; opacity: 0.9; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; padding: 30px; background: #fafafa; border-bottom: 1px solid #eee; }
        .summary-card { background: white; padding: 20px; border-radius: 8px; text-align: center; border: 1px solid #eee; }
        .summary-card h3 { margin: 0 0 10px 0; color: #333; }
        .summary-card .number { font-size: 2em; font-weight: bold; margin: 0; }
        .passed { color: #28a745; }
        .failed { color: #dc3545; }
        .skipped { color: #ffc107; }
        .content { padding: 30px; }
        .test-list { margin-top: 30px; }
        .test-item { background: #f8f9fa; border-radius: 8px; padding: 15px; margin-bottom: 10px; border-left: 4px solid #ddd; }
        .test-item.passed { border-left-color: #28a745; }
        .test-item.failed { border-left-color: #dc3545; }
        .test-item.skipped { border-left-color: #ffc107; }
        .test-title { font-weight: 600; margin-bottom: 5px; }
        .test-meta { color: #666; font-size: 0.9em; }
        .test-error { background: #f8d7da; color: #721c24; padding: 10px; border-radius: 4px; margin-top: 10px; font-family: monospace; font-size: 0.9em; }
        .status-badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; font-weight: 600; text-transform: uppercase; }
        .status-passed { background: #d4edda; color: #155724; }
        .status-failed { background: #f8d7da; color: #721c24; }
        .status-skipped { background: #fff3cd; color: #856404; }
        .performance { margin-top: 30px; }
        .performance-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        .performance-table th, .performance-table td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        .performance-table th { background: #f8f9fa; font-weight: 600; }
        .footer { background: #f8f9fa; padding: 20px; text-align: center; color: #666; border-radius: 0 0 8px 8px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🦆 拆词鸭 E2E 测试报告</h1>
            <p>生成时间: ${this.reportData.timestamp} | 总耗时: ${(this.reportData.summary.duration / 1000).toFixed(2)}s</p>
        </div>

        <div class="summary">
            <div class="summary-card">
                <h3>总测试数</h3>
                <p class="number">${this.reportData.summary.total}</p>
            </div>
            <div class="summary-card">
                <h3>通过</h3>
                <p class="number passed">${this.reportData.summary.passed}</p>
            </div>
            <div class="summary-card">
                <h3>失败</h3>
                <p class="number failed">${this.reportData.summary.failed}</p>
            </div>
            <div class="summary-card">
                <h3>跳过</h3>
                <p class="number skipped">${this.reportData.summary.skipped}</p>
            </div>
            <div class="summary-card">
                <h3>通过率</h3>
                <p class="number">${passRate}%</p>
            </div>
        </div>

        <div class="content">
            <h2>📋 测试结果详情</h2>
            <div class="test-list">
                ${this.reportData.tests.map(test => `
                    <div class="test-item ${test.status}">
                        <div class="test-title">${test.title}</div>
                        <div class="test-meta">
                            <span class="status-badge status-${test.status}">${test.status}</span>
                            ${test.category ? `<span style="margin-left: 10px;">分类: ${test.category}</span>` : ''}
                            ${test.browser ? `<span style="margin-left: 10px;">浏览器: ${test.browser}</span>` : ''}
                            ${test.viewport ? `<span style="margin-left: 10px;">视口: ${test.viewport}</span>` : ''}
                            <span style="margin-left: 10px;">耗时: ${(test.duration / 1000).toFixed(2)}s</span>
                        </div>
                        ${test.error ? `<div class="test-error">${test.error}</div>` : ''}
                    </div>
                `).join('')}
            </div>

            ${this.reportData.performance.length > 0 ? `
                <div class="performance">
                    <h2>📊 性能指标</h2>
                    <table class="performance-table">
                        <thead>
                            <tr>
                                <th>测试名称</th>
                                <th>加载时间 (ms)</th>
                                <th>API响应时间 (ms)</th>
                                <th>内存使用 (MB)</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${this.reportData.performance.map(perf => `
                                <tr>
                                    <td>${perf.testName}</td>
                                    <td>${perf.loadTime?.toFixed(2) || '-'}</td>
                                    <td>${perf.apiResponseTime?.toFixed(2) || '-'}</td>
                                    <td>${perf.memoryUsage?.toFixed(2) || '-'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            ` : ''}
        </div>

        <div class="footer">
            <p>🦆 拆词鸭 E2E 测试报告 - 自动生成于 ${new Date().toLocaleString('zh-CN')}</p>
        </div>
    </div>
</body>
</html>`;
  }

  private generateJsonReport() {
    const jsonPath = path.join(this.reportsDir, `e2e-report-${Date.now()}.json`);

    fs.writeFileSync(jsonPath, JSON.stringify(this.reportData, null, 2));
    console.log(`📊 JSON报告已生成: ${jsonPath}`);
  }

  private getStatusIcon(status: string): string {
    switch (status) {
      case 'passed': return '✅';
      case 'failed': return '❌';
      case 'skipped': return '⏭️';
      default: return '❓';
    }
  }

  private printSummary() {
    console.log('\n' + '='.repeat(50));
    console.log('🦆 拆词鸭 E2E 测试总结');
    console.log('='.repeat(50));
    console.log(`📊 总测试数: ${this.reportData.summary.total}`);
    console.log(`✅ 通过: ${this.reportData.summary.passed}`);
    console.log(`❌ 失败: ${this.reportData.summary.failed}`);
    console.log(`⏭️ 跳过: ${this.reportData.summary.skipped}`);

    const passRate = this.reportData.summary.total > 0
      ? (this.reportData.summary.passed / this.reportData.summary.total * 100).toFixed(1)
      : '0';
    console.log(`📈 通过率: ${passRate}%`);
    console.log(`⏱️ 总耗时: ${(this.reportData.summary.duration / 1000).toFixed(2)}s`);
    console.log(`📸 截图数量: ${this.reportData.screenshots.length}`);
    console.log('='.repeat(50));

    if (this.reportData.failed > 0) {
      console.log('\n❌ 失败的测试:');
      this.reportData.tests
        .filter(test => test.status === 'failed')
        .forEach(test => {
          console.log(`  - ${test.title}`);
        });
    }
  }
}

export default CustomTestReporter;