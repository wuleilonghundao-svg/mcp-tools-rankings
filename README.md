MCP 工具项目排行（近三个月）

项目目标
- 聚焦 Model Context Protocol（MCP）相关项目：客户端、服务端、工具集、生态插件。
- 输出两个榜单：
  - 总分排行（综合星标、近90天增长、活跃度等）
  - 近三个月飙升榜（按近90天新增星标排序）
- 若项目近90天无更新，则在榜单上标注为“收集”。

工作方式
- 通过 GitHub API 检索 MCP 相关项目（多个查询组合去重）。
- 计算指标：总星标、近90天新增星、最后活跃天数等；给出综合评分。
- 生成 `README.md` 榜单和 `data/latest.json` 结构化数据。
- GitHub Actions 每日运行自动更新。

本地运行
- Python 3.10+
- `pip install -r requirements.txt`
- 设置 `GITHUB_TOKEN`（推荐）提升速率限制
- 运行：`python -m mcp_rank.generate`

配置
- 见 `mcp_rank/config.yml`，可调整搜索关键字、Top N、权重与时间窗口（默认90天）。

输出
- README：两个榜单（总分、飙升）与基础说明
- data/latest.json：包含各项目的详细指标与得分

