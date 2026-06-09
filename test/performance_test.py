"""
数字农业平台 - Python性能测试脚本
使用多线程模拟并发请求，测试登录接口性能
"""
import requests
import time
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from collections import defaultdict

# 配置
BASE_URL = "http://127.0.0.1:8000/api/auth/login/"
LOGIN_DATA = {"username": "admin", "password": "admin123"}
RESULTS_DIR = r"e:\PyCharm 2025.2.1.1\pythonProjects\Digital Agriculture\results"

# 测试场景
TEST_SCENARIOS = [
    {"name": "10并发", "threads": 10, "duration": 30},
    {"name": "50并发", "threads": 50, "duration": 30},
    {"name": "100并发", "threads": 100, "duration": 30},
    {"name": "200并发", "threads": 200, "duration": 30},
    {"name": "500并发", "threads": 500, "duration": 30},
]


class LoadTester:
    def __init__(self, base_url, login_data):
        self.base_url = base_url
        self.login_data = login_data
        self.results = []
        self.lock = threading.Lock()
        self.running = False
        self.start_time = None

    def make_request(self):
        """发送单个请求并记录结果"""
        start = time.time()
        try:
            response = requests.post(
                self.base_url,
                json=self.login_data,
                timeout=30
            )
            elapsed = int((time.time() - start) * 1000)  # 毫秒
            success = response.status_code == 200
            return {
                "timestamp": time.time(),
                "elapsed": elapsed,
                "status_code": response.status_code,
                "success": success,
                "error": None if success else response.text[:100]
            }
        except Exception as e:
            elapsed = int((time.time() - start) * 1000)
            return {
                "timestamp": time.time(),
                "elapsed": elapsed,
                "status_code": 0,
                "success": False,
                "error": str(e)[:100]
            }

    def worker(self, worker_id, duration):
        """工作线程：持续发送请求直到超时"""
        local_results = []
        end_time = time.time() + duration

        while time.time() < end_time and self.running:
            result = self.make_request()
            result["worker_id"] = worker_id
            local_results.append(result)

        with self.lock:
            self.results.extend(local_results)

        return len(local_results)

    def run_load_test(self, num_threads, duration):
        """运行负载测试"""
        print(f"\n{'='*60}")
        print(f"开始测试: {num_threads}并发, 持续{duration}秒")
        print(f"{'='*60}")

        self.results = []
        self.running = True
        self.start_time = time.time()

        request_count = 0

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(self.worker, i, duration)
                for i in range(num_threads)
            ]

            # 等待所有任务完成
            for future in as_completed(futures):
                request_count += future.result()

        self.running = False
        elapsed_total = time.time() - self.start_time

        # 计算统计数据
        return self.analyze_results(elapsed_total)

    def analyze_results(self, total_time):
        """分析测试结果"""
        if not self.results:
            return None

        # 提取响应时间
        response_times = [r["elapsed"] for r in self.results]
        response_times.sort()

        total_requests = len(self.results)
        success_count = sum(1 for r in self.results if r["success"])
        error_count = total_requests - success_count

        # 计算百分位数
        def percentile(data, p):
            if not data:
                return 0
            k = (len(data) - 1) * p / 100
            f = int(k)
            c = min(f + 1, len(data) - 1)
            return data[f] + (data[c] - data[f]) * (k - f)

        # 按时间段分组计算RPS
        time_buckets = defaultdict(int)
        for r in self.results:
            bucket = int((r["timestamp"] - self.start_time) // 1)  # 1秒桶
            time_buckets[bucket] += 1

        rps_values = list(time_buckets.values())
        max_rps = max(rps_values) if rps_values else 0
        avg_rps = sum(rps_values) / len(rps_values) if rps_values else 0

        return {
            "total_requests": total_requests,
            "success_count": success_count,
            "error_count": error_count,
            "success_rate": (success_count / total_requests * 100) if total_requests > 0 else 0,
            "error_rate": (error_count / total_requests * 100) if total_requests > 0 else 0,
            "rps": total_requests / total_time,
            "max_rps": max_rps,
            "avg_rps": avg_rps,
            "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
            "min_response_time": min(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "p50": percentile(response_times, 50),
            "p90": percentile(response_times, 90),
            "p95": percentile(response_times, 95),
            "p99": percentile(response_times, 99),
            "total_time": total_time,
        }


def generate_html_report(results, scenarios):
    """生成HTML报告"""
    # 计算总结数据
    total_requests_all = sum(r["total_requests"] for r in results)
    avg_success_rate = sum(r["success_rate"] for r in results) / len(results) if results else 0
    peak_rps = max(r["max_rps"] for r in results) if results else 0

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>数字农业平台 - 性能测试报告</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{ color: white; margin-bottom: 30px; text-align: center; text-shadow: 2px 2px 4px rgba(0,0,0,0.2); }}
        .subtitle {{ color: rgba(255,255,255,0.9); text-align: center; margin-bottom: 30px; font-size: 1.1em; }}
        .summary {{ background: white; border-radius: 16px; padding: 30px; margin-bottom: 30px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }}
        .summary h2 {{ color: #333; margin-bottom: 20px; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }}
        .metric {{ text-align: center; padding: 25px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; color: white; }}
        .metric-value {{ font-size: 2.5em; font-weight: bold; }}
        .metric-label {{ font-size: 0.95em; opacity: 0.9; margin-top: 8px; }}
        .chart-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(450px, 1fr)); gap: 30px; margin-bottom: 30px; }}
        .chart-card {{ background: white; border-radius: 16px; padding: 25px; box-shadow: 0 10px 40px rgba(0,0,0,0.15); }}
        .chart-card h3 {{ color: #333; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 3px solid; border-image: linear-gradient(135deg, #667eea, #764ba2) 1; }}
        .data-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 0.9em; }}
        .data-table th, .data-table td {{ padding: 12px 8px; text-align: center; border: 1px solid #e0e0e0; }}
        .data-table th {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; font-weight: 600; }}
        .data-table tr:nth-child(even) {{ background: #f8f9fa; }}
        .data-table tr:hover {{ background: #e8f0fe; }}
        .success {{ color: #34a853; font-weight: bold; }}
        .warning {{ color: #fbbc04; font-weight: bold; }}
        .error {{ color: #ea4335; font-weight: bold; }}
        .highlight {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }}
        .footer {{ text-align: center; margin-top: 30px; color: rgba(255,255,255,0.8); font-size: 0.9em; }}
        .footer a {{ color: white; }}
        @media (max-width: 768px) {{ .chart-grid {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
    <div class="container">
        <h1>数字农业平台 - 性能测试报告</h1>
        <p class="subtitle">测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <div class="summary">
            <h2>测试摘要</h2>
            <div class="summary-grid">
                <div class="metric">
                    <div class="metric-value">{len(results)}</div>
                    <div class="metric-label">测试场景数</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{total_requests_all:,}</div>
                    <div class="metric-label">总请求数</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{avg_success_rate:.1f}%</div>
                    <div class="metric-label">平均成功率</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{peak_rps:.0f}</div>
                    <div class="metric-label">峰值RPS</div>
                </div>
            </div>
        </div>

        <div class="chart-grid">
            <div class="chart-card">
                <h3>并发数 vs 吞吐量 (RPS)</h3>
                <canvas id="rpsChart"></canvas>
            </div>
            <div class="chart-card">
                <h3>并发数 vs 响应时间 (ms)</h3>
                <canvas id="responseChart"></canvas>
            </div>
            <div class="chart-card">
                <h3>并发数 vs 错误率 (%)</h3>
                <canvas id="errorChart"></canvas>
            </div>
            <div class="chart-card">
                <h3>成功率分布</h3>
                <canvas id="successChart"></canvas>
            </div>
        </div>

        <div class="chart-card">
            <h3>详细测试数据</h3>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>并发数</th>
                        <th>总请求</th>
                        <th>成功率</th>
                        <th>RPS</th>
                        <th>峰值RPS</th>
                        <th>平均(ms)</th>
                        <th>P50(ms)</th>
                        <th>P90(ms)</th>
                        <th>P95(ms)</th>
                        <th>P99(ms)</th>
                        <th>最大(ms)</th>
                    </tr>
                </thead>
                <tbody>
"""

    for i, r in enumerate(results):
        rate_class = 'success' if r['error_rate'] < 1 else ('warning' if r['error_rate'] < 5 else 'error')
        html += f"""
                    <tr>
                        <td class="highlight">{scenarios[i]['threads']}</td>
                        <td>{r['total_requests']:,}</td>
                        <td class="{rate_class}">{r['success_rate']:.1f}%</td>
                        <td>{r['rps']:.1f}</td>
                        <td>{r['max_rps']:.0f}</td>
                        <td>{r['avg_response_time']:.0f}</td>
                        <td>{r['p50']:.0f}</td>
                        <td>{r['p90']:.0f}</td>
                        <td>{r['p95']:.0f}</td>
                        <td>{r['p99']:.0f}</td>
                        <td>{r['max_response_time']:.0f}</td>
                    </tr>
"""

    html += """                </tbody>
            </table>
        </div>

        <div class="footer">
            <p>报告生成时间: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
            <p>测试工具: Python LoadTester | 被测系统: 数字农业平台登录接口</p>
        </div>
    </div>

    <script>
        const results = """ + json.dumps(results, ensure_ascii=False) + """;
        const threads = """ + json.dumps([s['threads'] for s in scenarios]) + """;

        // 通用图表配置
        const chartOptions = {
            responsive: true,
            maintainAspectRatio: true,
            plugins: { legend: { position: 'top' } }
        };

        // RPS Chart
        new Chart(document.getElementById('rpsChart'), {
            type: 'line',
            data: {
                labels: threads.map(t => t + '并发'),
                datasets: [
                    {
                        label: '平均RPS',
                        data: results.map(r => r.rps),
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: '峰值RPS',
                        data: results.map(r => r.max_rps),
                        borderColor: '#34a853',
                        backgroundColor: 'rgba(52, 168, 83, 0.1)',
                        fill: true,
                        tension: 0.4
                    }
                ]
            },
            options: {
                ...chartOptions,
                scales: {
                    y: { beginAtZero: true, title: { display: true, text: 'RPS (请求/秒)' } }
                }
            }
        });

        // Response Time Chart
        new Chart(document.getElementById('responseChart'), {
            type: 'line',
            data: {
                labels: threads.map(t => t + '并发'),
                datasets: [
                    { label: '平均', data: results.map(r => r.avg_response_time), borderColor: '#667eea', tension: 0.4 },
                    { label: 'P50', data: results.map(r => r.p50), borderColor: '#34a853', tension: 0.4, borderDash: [5, 5] },
                    { label: 'P90', data: results.map(r => r.p90), borderColor: '#fbbc04', tension: 0.4, borderDash: [5, 5] },
                    { label: 'P99', data: results.map(r => r.p99), borderColor: '#ea4335', tension: 0.4, borderDash: [5, 5] }
                ]
            },
            options: {
                ...chartOptions,
                scales: {
                    y: { beginAtZero: true, title: { display: true, text: '响应时间 (ms)' } }
                }
            }
        });

        // Error Rate Chart
        new Chart(document.getElementById('errorChart'), {
            type: 'bar',
            data: {
                labels: threads.map(t => t + '并发'),
                datasets: [{
                    label: '错误率 (%)',
                    data: results.map(r => r.error_rate),
                    backgroundColor: results.map(r =>
                        r.error_rate < 1 ? 'rgba(52, 168, 83, 0.8)' :
                        r.error_rate < 5 ? 'rgba(251, 188, 4, 0.8)' :
                        'rgba(234, 67, 53, 0.8)'
                    ),
                    borderColor: results.map(r =>
                        r.error_rate < 1 ? '#34a853' :
                        r.error_rate < 5 ? '#fbbc04' :
                        '#ea4335'
                    ),
                    borderWidth: 2
                }]
            },
            options: {
                ...chartOptions,
                scales: {
                    y: { beginAtZero: true, title: { display: true, text: '错误率 (%)' } }
                }
            }
        });

        // Success Rate Chart
        new Chart(document.getElementById('successChart'), {
            type: 'doughnut',
            data: {
                labels: ['成功', '失败'],
                datasets: [{
                    data: [
                        results.reduce((sum, r) => sum + r.success_count, 0),
                        results.reduce((sum, r) => sum + r.error_count, 0)
                    ],
                    backgroundColor: ['#34a853', '#ea4335'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    </script>
</body>
</html>"""

    return html


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # 首先测试接口是否可用
    print("检查登录接口...")
    try:
        response = requests.post(BASE_URL, json=LOGIN_DATA, timeout=5)
        if response.status_code == 200:
            print(f"登录接口正常: {response.status_code}")
        else:
            print(f"登录接口异常: {response.status_code}")
            return
    except Exception as e:
        print(f"无法连接服务器: {e}")
        return

    print("\n" + "="*60)
    print("数字农业平台 - 性能测试")
    print("="*60)

    tester = LoadTester(BASE_URL, LOGIN_DATA)
    results = []

    for scenario in TEST_SCENARIOS:
        # 运行测试
        stats = tester.run_load_test(scenario["threads"], scenario["duration"])

        if stats:
            results.append(stats)

            # 打印结果
            print(f"\n  总请求数: {stats['total_requests']:,}")
            print(f"  成功率: {stats['success_rate']:.2f}%")
            print(f"  RPS: {stats['rps']:.1f} req/s")
            print(f"  峰值RPS: {stats['max_rps']:.0f} req/s")
            print(f"  平均响应: {stats['avg_response_time']:.0f}ms")
            print(f"  P50: {stats['p50']:.0f}ms")
            print(f"  P90: {stats['p90']:.0f}ms")
            print(f"  P95: {stats['p95']:.0f}ms")
            print(f"  P99: {stats['p99']:.0f}ms")
            print(f"  最大响应: {stats['max_response_time']:.0f}ms")
        else:
            print(f"\n  测试失败!")

        # 等待3秒再进行下一轮测试
        print("\n等待3秒...")
        time.sleep(3)

    # 生成HTML报告
    if results:
        report_path = os.path.join(RESULTS_DIR, 'performance_report.html')
        html_report = generate_html_report(results, TEST_SCENARIOS)

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_report)

        print("\n" + "="*60)
        print("所有测试完成!")
        print(f"报告已生成: {report_path}")
        print("="*60)

        # 保存JSON结果
        json_path = os.path.join(RESULTS_DIR, 'test_results.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({"scenarios": TEST_SCENARIOS, "results": results}, f, ensure_ascii=False, indent=2)
        print(f"JSON数据: {json_path}")


if __name__ == '__main__':
    main()
