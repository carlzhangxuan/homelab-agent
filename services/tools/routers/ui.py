from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from config import settings
from store import store

router = APIRouter()

_PAGE = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Homelab</title>
  <style>
    :root {
      --bg: #111;
      --fg: #eee;
      --muted: #666;
      --accent: #7df;
      --ok: #4f4;
      --warn: #fc4;
      --err: #f44;
      --warm: #f84;
      --line: #222;
      --line-bright: #333;
      --panel: #1a1a1a;
    }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", monospace;
           background: var(--bg); color: var(--fg); padding: 2rem; margin: 0; }
    h1 { color: var(--accent); margin: 0 0 0.5rem 0; font-weight: 600; }
    .bar { display: flex; justify-content: space-between; align-items: center;
           margin-bottom: 1.5rem; color: var(--muted); font-size: 0.85rem; }
    table { border-collapse: collapse; width: 100%; font-variant-numeric: tabular-nums; }
    th { text-align: left; color: var(--accent); padding: 0.5rem 1rem;
         border-bottom: 1px solid var(--line-bright); font-weight: 500; font-size: 0.85rem;
         text-transform: uppercase; letter-spacing: 0.05em; }
    td { padding: 0.6rem 1rem; border-bottom: 1px solid var(--line); }
    td.host { font-weight: 600; }
    td.host .ip { color: var(--muted); font-weight: normal; margin-left: 0.6rem; font-size: 0.85rem; }
    td.status .online    { color: var(--ok); }
    td.status .offline   { color: var(--err); }
    td.status .working   { color: var(--warn); }
    td.status .unknown   { color: var(--muted); }
    td.status .spinner { display: inline-block; width: 0.6rem; margin-left: 0.3rem; }
    td.na { color: var(--muted); }
    td.actions { white-space: nowrap; text-align: right; }

    button {
      background: transparent;
      color: var(--fg);
      border: 1px solid var(--line-bright);
      padding: 0.35rem 0.9rem;
      border-radius: 999px;
      cursor: pointer;
      margin: 0 3px;
      font-family: inherit;
      font-size: 0.8rem;
      font-weight: 500;
      transition: background 0.15s, color 0.15s, border-color 0.15s, transform 0.08s;
    }
    button:hover:not(:disabled) { transform: translateY(-1px); }
    button:active:not(:disabled) { transform: translateY(0); }
    button:disabled { opacity: 0.4; cursor: not-allowed; }
    button.wake     { border-color: #2a5a2a; color: var(--ok); }
    button.wake:hover:not(:disabled)     { background: #1a3a1a; border-color: var(--ok); }
    button.shutdown { border-color: #5a3a1a; color: var(--warm); }
    button.shutdown:hover:not(:disabled) { background: #3a2512; border-color: var(--warm); }

    #toast {
      position: fixed; bottom: 2rem; right: 2rem;
      min-width: 14rem; max-width: 28rem;
      padding: 0.7rem 1.1rem;
      border-radius: 6px;
      font-family: inherit; font-size: 0.85rem;
      opacity: 0;
      transform: translateY(8px);
      transition: opacity 0.2s, transform 0.2s;
      pointer-events: none;
      box-shadow: 0 4px 14px rgba(0,0,0,0.4);
    }
    #toast.show { opacity: 1; transform: translateY(0); }
    #toast.info { background: #1a2a3a; border: 1px solid var(--accent); color: var(--accent); }
    #toast.ok   { background: #1a3a1a; border: 1px solid var(--ok);     color: var(--ok); }
    #toast.warn { background: #3a2f1a; border: 1px solid var(--warn);   color: var(--warn); }
    #toast.err  { background: #3a1a1a; border: 1px solid var(--err);    color: var(--err); }

    @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }
    .pulse { animation: pulse 1s ease-in-out infinite; }

    .sections { margin-top: 2rem; display: flex; flex-direction: column; gap: 1.5rem; }
    .sections h2 {
      color: var(--muted); font-size: 0.75rem; font-weight: 500;
      text-transform: uppercase; letter-spacing: 0.08em;
      margin: 0 0 0.8rem 0;
      padding-bottom: 0.4rem;
      border-bottom: 1px solid var(--line);
    }
    .link-group {
      display: flex; align-items: center; gap: 0.5rem;
      margin-bottom: 0.5rem;
    }
    .link-group .label {
      color: var(--fg); font-size: 0.85rem;
      min-width: 14rem;
    }
    .repo-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(16rem, 1fr));
      gap: 0.5rem 0.8rem;
    }
    a.link, button.link {
      color: var(--accent); background: transparent;
      border: 1px solid var(--line-bright); border-radius: 999px;
      padding: 0.3rem 0.8rem; font-family: inherit; font-size: 0.8rem;
      cursor: pointer; text-decoration: none;
      transition: background 0.15s, border-color 0.15s;
      display: inline-block;
    }
    a.link:hover, button.link:hover { background: #1a2a3a; border-color: var(--accent); }
    a.link.sub { font-size: 0.75rem; padding: 0.2rem 0.6rem; color: var(--muted); }
    a.link.sub:hover { color: var(--accent); }
    a.repo {
      display: block;
      padding: 0.5rem 0.9rem;
      border: 1px solid var(--line-bright); border-radius: 6px;
      color: var(--fg); text-decoration: none;
      font-size: 0.85rem;
      transition: background 0.15s, border-color 0.15s;
    }
    a.repo:hover { background: var(--panel); border-color: var(--accent); }
    a.repo .repo-name { color: var(--accent); font-weight: 500; }
    a.repo .repo-org { color: var(--muted); font-size: 0.75rem; margin-left: 0.4rem; }

    .roadmap-wrap {
      margin-top: 1rem;
      border: 1px solid var(--line-bright);
      border-radius: 8px;
      background: var(--panel);
      padding: 0.9rem;
      width: 100%;
      box-sizing: border-box;
    }
    .roadmap-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 0.8rem;
      margin-bottom: 0.8rem;
      flex-wrap: wrap;
    }
    .roadmap-meta { color: var(--muted); font-size: 0.8rem; }
    .roadmap-tabs, .roadmap-filters {
      display: flex;
      gap: 0.45rem;
      flex-wrap: wrap;
    }
    button.roadmap-tab, button.roadmap-filter {
      border-radius: 999px;
      padding: 0.25rem 0.7rem;
      font-size: 0.75rem;
      border: 1px solid var(--line-bright);
      background: #131313;
      color: var(--muted);
    }
    button.roadmap-tab.active, button.roadmap-filter.active {
      border-color: var(--accent);
      color: var(--accent);
      background: #142230;
    }
    .roadmap-page {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(24rem, 1fr));
      gap: 0.8rem;
      margin-top: 0.8rem;
      max-height: 72vh;
      overflow-y: auto;
      overflow-x: hidden;
      align-content: start;
      padding-right: 0.35rem;
    }
    .roadmap-card {
      border: 1px solid var(--line-bright);
      border-radius: 8px;
      background: #141414;
      overflow: hidden;
    }
    .roadmap-card-head {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.6rem 0.8rem;
      border-bottom: 1px solid var(--line);
      background: #181818;
    }
    .roadmap-pri {
      font-size: 0.7rem;
      border: 1px solid var(--line-bright);
      border-radius: 999px;
      padding: 0.08rem 0.45rem;
      color: var(--warn);
    }
    .roadmap-title {
      font-size: 0.82rem;
      color: var(--fg);
      font-weight: 600;
      margin: 0;
      line-height: 1.4;
    }
    .roadmap-count {
      margin-left: auto;
      color: var(--muted);
      font-size: 0.75rem;
    }
    .roadmap-items {
      list-style: none;
      margin: 0;
      padding: 0.25rem 0.7rem 0.6rem;
    }
    .roadmap-items li {
      display: flex;
      align-items: flex-start;
      gap: 0.45rem;
      padding: 0.28rem 0;
      border-bottom: 1px dashed #242424;
      font-size: 0.78rem;
      line-height: 1.45;
      color: #ddd;
    }
    .roadmap-items li:last-child { border-bottom: none; }
    .roadmap-dot {
      width: 0.35rem;
      height: 0.35rem;
      border-radius: 50%;
      margin-top: 0.33rem;
      background: var(--accent);
      flex: 0 0 auto;
    }
    .roadmap-tag {
      margin-left: 0.35rem;
      color: var(--muted);
      font-size: 0.7rem;
      border: 1px solid var(--line-bright);
      border-radius: 999px;
      padding: 0.02rem 0.36rem;
      white-space: nowrap;
    }
    .roadmap-items a {
      color: var(--accent);
      text-decoration: none;
      margin-left: 0.3rem;
      font-size: 0.72rem;
    }
    .progress-panel {
      margin-top: 0.9rem;
      border: 1px solid var(--line-bright);
      border-radius: 8px;
      background: #141414;
      padding: 0.8rem;
    }
    .progress-title {
      margin: 0 0 0.6rem 0;
      color: #93c5fd;
      font-size: 0.82rem;
      font-weight: 600;
      letter-spacing: 0.02em;
    }
    .progress-list {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(20rem, 1fr));
      gap: 0.7rem;
    }
    .progress-row {
      border: 1px solid #2a2a2a;
      border-radius: 8px;
      background: #121212;
      padding: 0.55rem 0.65rem;
    }
    .progress-row-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.55rem;
      margin-bottom: 0.4rem;
    }
    .progress-name {
      color: var(--fg);
      font-size: 0.74rem;
      line-height: 1.3;
    }
    .progress-pct {
      color: var(--muted);
      font-size: 0.72rem;
      min-width: 2.6rem;
      text-align: right;
    }
    .progress-slider {
      width: 100%;
      appearance: none;
      -webkit-appearance: none;
      height: 0.42rem;
      border-radius: 999px;
      background: linear-gradient(90deg, var(--slider-color, #f59e0b) 0%, var(--slider-color, #f59e0b) var(--pct, 0%), #2a2a2a var(--pct, 0%), #2a2a2a 100%);
      outline: none;
      cursor: pointer;
    }
    .progress-slider::-webkit-slider-thumb {
      -webkit-appearance: none;
      appearance: none;
      width: 0.9rem;
      height: 0.9rem;
      border-radius: 50%;
      border: 2px solid #0f0f0f;
      background: var(--slider-color, #f59e0b);
      box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.06);
    }
    .progress-slider::-moz-range-thumb {
      width: 0.9rem;
      height: 0.9rem;
      border-radius: 50%;
      border: 2px solid #0f0f0f;
      background: var(--slider-color, #f59e0b);
      box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.06);
    }
    .strategy-wrap {
      margin-top: 0.9rem;
      border: 1px solid var(--line-bright);
      border-radius: 8px;
      background: #141414;
      padding: 0.9rem;
    }
    .strategy-title {
      margin: 0 0 0.55rem 0;
      color: #a78bfa;
      font-size: 0.9rem;
      font-weight: 600;
    }
    .strategy-list {
      list-style: none;
      margin: 0;
      padding: 0;
      display: flex;
      flex-direction: column;
      gap: 0.45rem;
    }
    .strategy-list li {
      font-size: 0.8rem;
      line-height: 1.55;
      color: #d6d6d6;
      border-left: 2px solid #2a2a2a;
      padding-left: 0.55rem;
    }
    .strategy-list strong {
      color: var(--fg);
      font-weight: 600;
    }
    .strategy-list a {
      color: var(--accent);
      text-decoration: none;
      margin-left: 0.2rem;
    }
    .strategy-list a:hover {
      text-decoration: underline;
    }
    .burnout-wrap {
      margin-top: 0.9rem;
      border: 1px solid var(--line-bright);
      border-radius: 8px;
      background: #13161d;
      padding: 0.9rem;
    }
    .burnout-title {
      margin: 0 0 0.55rem 0;
      color: #7dd3fc;
      font-size: 0.9rem;
      font-weight: 600;
    }
    .burnout-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(18rem, 1fr));
      gap: 0.65rem;
      margin-bottom: 0.75rem;
    }
    .burnout-card {
      border: 1px solid #2a3341;
      border-radius: 8px;
      background: #10141a;
      padding: 0.6rem 0.65rem;
    }
    .burnout-card h4 {
      margin: 0 0 0.35rem 0;
      font-size: 0.8rem;
      color: #c7d2fe;
      font-weight: 600;
    }
    .burnout-card ul {
      margin: 0;
      padding-left: 1rem;
      color: #cbd5e1;
      font-size: 0.76rem;
      line-height: 1.5;
    }
    .burnout-ratio {
      margin: 0;
      font-size: 0.78rem;
      color: #d1d5db;
      line-height: 1.55;
      border-top: 1px dashed #2a3341;
      padding-top: 0.6rem;
    }
    .burnout-ratio strong { color: var(--fg); }
  </style>
</head>
<body>
  <h1>Homelab</h1>
  <div class="bar">
    <span>auto-refresh every <span id="refresh-s">5</span>s · <span id="last-refresh">just now</span></span>
    <span id="activity"></span>
  </div>
  <div id="toast"></div>
  <table>
    <tr>
      <th>Host</th><th>Status</th><th>CPU%</th><th>CPU°C</th>
      <th>Mem%</th><th>GPU°C</th><th>GPU W</th><th>SSD°C</th><th>BAT%</th><th>Actions</th>
    </tr>
    {rows}
  </table>
  <div class="sections">
    <section>
      <h2>Services</h2>
      <div class="link-group">
        <span class="label">Grafana · homelab-overview</span>
        <a class="link sub" href="http://192.168.10.32:3001/d/homelab-overview/homelab-overview?orgId=1&amp;from=now-5m&amp;to=now&amp;timezone=browser&amp;refresh=5s" target="_blank">LAN</a>
        <a class="link sub" href="http://100.75.243.9:3001/d/homelab-overview/homelab-overview?orgId=1&amp;from=now-5m&amp;to=now&amp;timezone=browser&amp;refresh=5s" target="_blank">Tailscale</a>
      </div>
      <div class="link-group">
        <span class="label">TensorBoard</span>
        <a class="link sub" href="http://192.168.10.32:6006/?darkMode=true#timeseries" target="_blank">LAN</a>
        <a class="link sub" href="http://100.75.243.9:6006/?darkMode=true#timeseries" target="_blank">Tailscale</a>
      </div>
      <div class="link-group">
        <span class="label">titanX volume</span>
        <button class="link sub" onclick="copyPath('file:///Volumes/titanX')">file:///Volumes/titanX</button>
      </div>
    </section>
    <section>
      <h2>Repositories</h2>
      <div class="repo-grid">
        <a class="repo" href="https://github.com/carlzhangxuan/auto-research" target="_blank">
          <span class="repo-name">auto-research</span><span class="repo-org">carlzhangxuan</span>
        </a>
        <a class="repo" href="https://github.com/carlzhangxuan/homelab-experiments" target="_blank">
          <span class="repo-name">homelab-experiments</span><span class="repo-org">carlzhangxuan</span>
        </a>
        <a class="repo" href="https://github.com/carlzhangxuan/homelab-agent" target="_blank">
          <span class="repo-name">homelab-agent</span><span class="repo-org">carlzhangxuan</span>
        </a>
        <a class="repo" href="https://github.com/carlzhangxuan/homelab-init" target="_blank">
          <span class="repo-name">homelab-init</span><span class="repo-org">carlzhangxuan</span>
        </a>
        <a class="repo" href="https://github.com/carlzhangxuan/research-notes" target="_blank">
          <span class="repo-name">research-notes</span><span class="repo-org">carlzhangxuan</span>
        </a>
        <a class="repo" href="https://github.com/carlzhangxuan/ai-notes" target="_blank">
          <span class="repo-name">ai-notes</span><span class="repo-org">carlzhangxuan</span>
        </a>
        <a class="repo" href="https://github.com/GDP-lab/flow_bedrock" target="_blank">
          <span class="repo-name">flow_bedrock</span><span class="repo-org">GDP-lab</span>
        </a>
        <a class="repo" href="https://github.com/carlzhangxuan/carlzhangxuan.github.io" target="_blank">
          <span class="repo-name">carlzhangxuan.github.io</span><span class="repo-org">carlzhangxuan</span>
        </a>
      </div>
    </section>
    <section>
      <h2>Roadmap</h2>
      <div class="roadmap-wrap">
        <div class="roadmap-head">
          <div id="roadmap-tabs" class="roadmap-tabs"></div>
          <div id="roadmap-filters" class="roadmap-filters"></div>
        </div>
        <div id="roadmap-meta" class="roadmap-meta"></div>
        <div id="roadmap-page" class="roadmap-page"></div>
      </div>
      <div id="project-progress" class="progress-panel"></div>
      <div class="strategy-wrap">
        <h3 class="strategy-title">💡 战略要点</h3>
        <ul class="strategy-list">
          <li><strong>交叉 = 最大杠杆:</strong> <a href="https://github.com/vllm-project/vllm-omni/issues/2136" target="_blank">vLLM-Omni</a> Q2 路线含 diffusion serving。你同时做 vLLM + diffusion，贡献 PR 或写深度分析 → 面试直接差异化。</li>
          <li><strong>Anthropic agent 4 篇必读:</strong> Building Effective Agents / Context Engineering / Writing Tools / Long-Running Harnesses → 你的 agent 对标这些 pattern。</li>
          <li><strong>面试不是 LeetCode:</strong> CodeSignal = 90min 系统构建 (4级加约束); Onsite = system design (inference serving / distributed training / eval) + AI safety。</li>
          <li><strong>P0 完成 → 立刻输出:</strong> README / 图 / benchmark CSV / blog 草稿 / demo。Blog = 英语 + portfolio + 面试素材三合一。</li>
        </ul>
      </div>
      <div class="burnout-wrap">
        <h3 class="burnout-title">🛡 防 Burn Out 指南</h3>
        <div class="burnout-grid">
          <article class="burnout-card">
            <h4>执行结构</h4>
            <ul>
              <li>主线只保留 1 条: Agent + vLLM / inference infra</li>
              <li>副线只保留 1 条: Diffusion / Flow 稳定积累</li>
              <li>保温线: 英语表达 + system design + leetcode</li>
            </ul>
          </article>
          <article class="burnout-card">
            <h4>日上限规则</h4>
            <ul>
              <li>深度工程任务: 每天最多 1 块</li>
              <li>深度理论任务: 每天最多 1 块</li>
              <li>面试准备: 每天 45-60 分钟</li>
              <li>晚上不做新重设计, 只整理/阅读</li>
            </ul>
          </article>
          <article class="burnout-card">
            <h4>风险信号</h4>
            <ul>
              <li>黄色: TODO 快速增长, Done 变少, 切换太频繁</li>
              <li>红色: 连续几天不想开项目, 只刷资料不动手</li>
              <li>到黄色立刻减负, 不靠意志硬顶</li>
            </ul>
          </article>
          <article class="burnout-card">
            <h4>硬规则</h4>
            <ul>
              <li>任何时刻只允许两个开放工程问题</li>
              <li>每天有产出, 但不要求四线齐推</li>
              <li>每周至少一个可见成果和一次回顾</li>
            </ul>
          </article>
        </div>
        <p class="burnout-ratio"><strong>当前建议负载比例:</strong> 50% Agent + Inference Infra · 25% Diffusion · 15% 英语/项目表达 · 10% LeetCode/System Design</p>
      </div>
    </section>
  </div>
  <script>
    const REFRESH_MS = 5000;
    const SHUTDOWN_TIMEOUT_MS = 120000;
    const POLL_MS = 5000;

    const ROADMAP_TRACKS = {
      vllm: {
        name: 'vLLM / Inference Infra',
        icon: '⚡',
        sections: [
          {
            title: '建 inference-lab repo + 跑通 baseline',
            priority: 'P0',
            items: [
              { text: '建 inference-lab repo，统一 benchmark harness v1', tag: '实战', link: null },
              { text: '统一指标体系: TTFT / decode tok·s⁻¹ / prompt len / concurrency / GPU mem / batch size', tag: '实战', link: null },
              { text: '5090 Docker 环境跑通 HF Transformers baseline (generate + 采集指标)', tag: '实战', link: null },
              { text: '跑通 vLLM 0.19.x baseline (同模型同 prompt，对照 HF)', tag: '实战', link: null },
              { text: '做一次 HF vs vLLM 对照表 → 写进 README', tag: '输出', link: null }
            ]
          },
          {
            title: '核心论文 & 源码精读',
            priority: 'P0',
            items: [
              { text: 'PagedAttention (Kwon et al. 2023) — 虚拟内存 KV cache 管理', tag: '论文', link: 'https://arxiv.org/abs/2309.06180' },
              { text: 'Orca / Continuous Batching (Yu et al. 2022) — iteration-level scheduling', tag: '论文', link: 'https://www.usenix.org/conference/osdi22/presentation/yu' },
              { text: 'FlashAttention 1 & 2 (Dao et al.) — IO-aware tiling, kernel 优化', tag: '论文', link: 'https://github.com/Dao-AILab/flash-attention' },
              { text: 'vLLM V1 源码链路: Scheduler → KV Cache Manager → Model Runner', tag: '源码', link: 'https://docs.vllm.ai/en/latest/' },
              { text: 'vLLM PagedAttention 设计页精读', tag: '源码', link: 'https://docs.vllm.ai/en/latest/design/kernel/paged_attention.html' }
            ]
          },
          {
            title: '验证高级特性 + 量化',
            priority: 'P1',
            items: [
              { text: '验证 Prefix Caching — 和 agent workload 高度相关', tag: '实验', link: 'https://docs.vllm.ai/en/latest/features/automatic_prefix_caching.html' },
              { text: '验证 Chunked Prefill — 长 prompt 场景', tag: '实验', link: null },
              { text: '量化对比: FP8 / NVFP4 / AWQ / GPTQ 在 5090 上 throughput & latency', tag: '实验', link: null },
              { text: 'Speculative Decoding (Leviathan 2023; Chen 2023) — draft-verify 流程', tag: '论文', link: 'https://arxiv.org/abs/2302.01318' }
            ]
          },
          {
            title: '进阶 & 面试加分',
            priority: 'P2',
            items: [
              { text: 'Model Runner V2 (MRV2) — piecewise CUDA graphs, async scheduling', tag: '源码', link: 'https://github.com/vllm-project/vllm/issues/39749' },
              { text: 'Disaggregated Serving: Prefill-Decode 分离架构 (PD disagg)', tag: '架构', link: null },
              { text: 'MoE 推理: Expert Parallelism, EPLB', tag: '架构', link: null },
              { text: 'Blog:「5090 上 vLLM 推理全链路实测」', tag: '输出', link: null }
            ]
          }
        ]
      },
      diffusion: {
        name: 'Diffusion / Flow',
        icon: '🌊',
        sections: [
          {
            title: '术语表 + 经典精读 (依赖顺序)',
            priority: 'P0',
            items: [
              { text: '写统一术语表: score / x0-pred / epsilon-pred / velocity / probability path / ODE·SDE / sampler·solver·NFE', tag: '输出', link: null },
              { text: 'DDPM (Ho et al. 2020) — 从零实现 forward/reverse, CIFAR-10 训练', tag: '复现', link: 'https://arxiv.org/abs/2006.11239' },
              { text: 'DDIM (Song et al. 2021) — deterministic sampling, eta, skip steps', tag: '复现', link: 'https://arxiv.org/abs/2010.02502' },
              { text: 'Score-SDE (Song et al. 2021) — SDE/ODE 统一, score matching ↔ DDPM', tag: '论文', link: 'https://arxiv.org/abs/2011.13456' }
            ]
          },
          {
            title: '最小实验 + 可视化',
            priority: 'P0',
            items: [
              { text: '做一个 2D toy 实验: Swiss Roll / 双月形 → 可视化 trajectory', tag: '实验', link: null },
              { text: '画一张 diffusion → flow 的连续关系图', tag: '输出', link: null },
              { text: '最小 notebook: DDPM objective vs FM objective 对比', tag: '实验', link: null }
            ]
          },
          {
            title: 'DiT + 现代方向 + Blog',
            priority: 'P1',
            items: [
              { text: 'EDM (Karras et al. 2022) — design space, preconditioning, noise schedule', tag: '论文', link: 'https://arxiv.org/abs/2206.00364' },
              { text: 'DiT (Peebles & Xie 2023) — Transformer 替代 UNet, adaLN-Zero', tag: '复现', link: 'https://arxiv.org/abs/2212.09748' },
              { text: 'Latent Diffusion (Rombach et al. 2022) — VAE + UNet in latent space', tag: '论文', link: 'https://arxiv.org/abs/2112.10752' },
              { text: '写 Blog:「From Diffusion to Flow」(英文)', tag: '输出', link: null }
            ]
          },
          {
            title: '前沿跟踪 (暂缓)',
            priority: 'P2',
            items: [
              { text: 'MeanFlow (Geng, He et al. 2025) — average velocity, 1-step', tag: '论文', link: 'https://arxiv.org/abs/2505.13447' },
              { text: 'Consistency Models (Song et al. 2023) — self-consistency, 1-step 蒸馏', tag: '论文', link: 'https://arxiv.org/abs/2303.01469' },
              { text: 'Diffusion Language Models survey (VILA-Lab)', tag: '阅读', link: 'https://github.com/VILA-Lab/Awesome-DLMs' },
              { text: 'vLLM-Omni diffusion serving: 训练好的 DiT 接入 vLLM', tag: '交叉', link: 'https://github.com/vllm-project/vllm-omni/issues/2136' }
            ]
          }
        ]
      },
      agent: {
        name: 'Agent / Runtime',
        icon: '🤖',
        sections: [
          {
            title: 'Coding Agent 完善 + Run 记录',
            priority: 'P0',
            items: [
              { text: '给现有 coding agent 加: run state / logs / artifact store / failure reason', tag: '开发', link: null },
              { text: '统一 task schema + 输入/输出 contract', tag: '设计', link: null },
              { text: 'Cross-repo: 先支持最小 happy path (两个 repo 联动)', tag: '开发', link: null },
              { text: '加一个人工确认节点 (human-in-the-loop)', tag: '开发', link: null }
            ]
          },
          {
            title: 'Training Agent 闭环',
            priority: 'P0',
            items: [
              { text: '串一次 spec → model search → Docker train → result eval 闭环', tag: '开发', link: null },
              { text: 'Agent core loop: 不用 LangChain, 自己 tool-use + state machine', tag: '开发', link: null },
              { text: 'Mac mini control → 5090 exec: task dispatch + monitoring', tag: '基建', link: null },
              { text: 'Task queue: 先 SQLite MVP (simple wins)', tag: '设计', link: null }
            ]
          },
          {
            title: 'Agent → 部署闭环 + Eval',
            priority: 'P1',
            items: [
              { text: '训练后自动量化 + vLLM deploy + benchmark', tag: '开发', link: null },
              { text: 'Cloudflare Tunnel (api.omegaterm.xyz) 暴露 API', tag: '基建', link: null },
              { text: '加 retry / rollback 规则', tag: '开发', link: null },
              { text: '设计 trace 结构 → run viewer 或日志页', tag: '开发', link: null }
            ]
          },
          {
            title: '参考文献 & 架构灵感',
            priority: 'P2',
            items: [
              { text: 'Anthropic — Building Effective Agents (必读首篇)', tag: '阅读', link: 'https://www.anthropic.com/research/building-effective-agents' },
              { text: 'Anthropic — Effective Context Engineering for AI Agents', tag: '阅读', link: 'https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents' },
              { text: 'MCP 官方规格 (2025-11-25 revision)', tag: '阅读', link: 'https://modelcontextprotocol.io/specification/2025-11-25' },
              { text: 'SWE-bench (Princeton) — coding agent eval 标准', tag: '阅读', link: 'https://github.com/princeton-nlp/SWE-bench' }
            ]
          }
        ]
      },
      interview: {
        name: '面试准备',
        icon: '🎯',
        sections: [
          {
            title: 'Anthropic 面试流程 + 叙事',
            priority: 'P0',
            items: [
              { text: '研究面试流程: Recruiter → CodeSignal OA → Technical → Onsite', tag: '准备', link: 'https://igotanoffer.com/en/advice/anthropic-interview-process' },
              { text: 'CodeSignal OA: 90min 4级递进, 练 modular code + 逐级加约束', tag: '刷题', link: null },
              { text: '准备 Why Anthropic 叙事', tag: '叙事', link: null },
              { text: 'Constitutional AI 论文精读', tag: '知识', link: 'https://arxiv.org/abs/2212.08073' }
            ]
          },
          {
            title: '4 个英文项目故事卡 (90s + 3min)',
            priority: 'P0',
            items: [
              { text: 'Story 1: Tell me about yourself (完整主线叙事)', tag: '叙事', link: null },
              { text: 'Story 2: Homelab + inference infra', tag: '叙事', link: null },
              { text: 'Story 3: Coding/cross-repo agent', tag: '叙事', link: null },
              { text: 'Story 4: Diffusion/flow research + training pipeline', tag: '叙事', link: null }
            ]
          },
          {
            title: '系统设计 × 4 模板',
            priority: 'P1',
            items: [
              { text: '设计 LLM Inference Service: batch scheduler, KV cache, autoscaling', tag: '系统', link: null },
              { text: '设计 Model Training Orchestration: parallelism, checkpointing', tag: '系统', link: null },
              { text: '设计 Agent Runtime with Tools + Human Review', tag: '系统', link: null },
              { text: '设计 Evaluation Pipeline: A/B, online/offline, safety guardrails', tag: '系统', link: null }
            ]
          },
          {
            title: 'LeetCode + Coding',
            priority: 'P1',
            items: [
              { text: '每天 1-2 题 Medium: 图/树/DP/滑动窗口, Python', tag: '刷题', link: 'https://leetcode.com/' },
              { text: 'KV store 实现 (加约束: persistence → compression → concurrency)', tag: '刷题', link: null },
              { text: 'Async URL parser + domain counter → scale to 100K rps', tag: '刷题', link: null },
              { text: 'Token generator: scale to 100K rps (分布式 latency)', tag: '刷题', link: null }
            ]
          }
        ]
      }
    };

    const ROADMAP_STATE = {
      track: 'vllm',
      priority: 'all'
    };

    let _busy = 0;
    let _toastTimer = null;
    let _lastRefresh = Date.now();

    function toast(msg, type, persist) {
      const el = document.getElementById('toast');
      el.textContent = msg;
      el.className = 'show ' + (type || 'info');
      if (_toastTimer) clearTimeout(_toastTimer);
      if (!persist) {
        _toastTimer = setTimeout(() => { el.className = ''; }, 4000);
      }
    }

    function setActivity() {
      const el = document.getElementById('activity');
      el.textContent = _busy > 0 ? (_busy + ' action' + (_busy === 1 ? '' : 's') + ' in progress') : '';
      el.className = _busy > 0 ? 'pulse' : '';
    }

    function startBusy(host, label) {
      _busy++;
      setActivity();
      const row = document.getElementById('row-' + host);
      if (row) {
        const statusCell = row.querySelector('td.status');
        statusCell.innerHTML = '<span class="working pulse">' + label + '</span>';
        row.querySelectorAll('button').forEach(b => b.disabled = true);
      }
    }

    function endBusy() {
      _busy = Math.max(0, _busy - 1);
      setActivity();
      if (_busy === 0) location.reload();
    }

    async function postOrThrow(url, body) {
      const options = {method: 'POST'};
      if (body !== undefined) {
        options.headers = {'Content-Type': 'application/json'};
        options.body = JSON.stringify(body);
      }
      const resp = await fetch(url, options);
      if (!resp.ok) {
        let msg = resp.status + ' ' + resp.statusText;
        try {
          const data = await resp.json();
          if (data && data.detail) msg = data.detail;
        } catch (_) {}
        throw new Error(msg);
      }
      try { return await resp.json(); } catch (_) { return {}; }
    }

    async function copyPath(path) {
      try {
        await navigator.clipboard.writeText(path);
        toast('Copied — paste into address bar', 'ok');
      } catch (e) {
        toast('Copy failed: ' + e.message, 'err');
      }
    }

    async function getHostOnline(host) {
      try {
        const resp = await fetch('/homelab/metrics/' + host, {cache: 'no-store'});
        if (!resp.ok) return null;
        const data = await resp.json();
        return data.online === true;
      } catch (_) { return null; }
    }

    async function wake(host) {
      startBusy(host, 'waking...');
      toast('Waking ' + host + '...', 'info', true);
      try {
        const result = await postOrThrow('/homelab/wake/' + host,
                                         {wait_timeout_s: 90, poll_interval_s: 5});
        if (result && result.already_online) {
          toast(host + ' was already online', 'ok');
        } else if (result && result.online) {
          const s = result.elapsed_s !== undefined ? (' in ~' + result.elapsed_s + 's') : '';
          toast(host + ' is online' + s, 'ok');
        } else if (result && result.detail) {
          toast(result.detail, 'warn');
        } else {
          toast('Wake sent: ' + host, 'ok');
        }
      } catch (e) {
        toast('Wake failed: ' + e.message, 'err');
      } finally {
        endBusy();
      }
    }

    async function shutdown(host) {
      const sudoPassword = prompt('Shutdown ' + host +
        '\\nEnter sudo password (leave blank for passwordless sudo):', '');
      if (sudoPassword === null) return;
      startBusy(host, 'shutting down...');
      toast('Sending shutdown to ' + host + '...', 'info', true);
      const startedAt = Date.now();
      try {
        await postOrThrow('/homelab/shutdown/' + host, {sudo_password: sudoPassword});
        toast('Shutdown sent to ' + host + ', waiting for offline...', 'info', true);
        while (Date.now() - startedAt < SHUTDOWN_TIMEOUT_MS) {
          await new Promise(r => setTimeout(r, POLL_MS));
          const online = await getHostOnline(host);
          if (online === false) {
            const s = Math.round((Date.now() - startedAt) / 1000);
            toast(host + ' is offline (~' + s + 's)', 'ok');
            return;
          }
        }
        toast(host + ' still online after ' +
              Math.round(SHUTDOWN_TIMEOUT_MS / 1000) + 's', 'warn');
      } catch (e) {
        toast('Shutdown failed: ' + e.message, 'err');
      } finally {
        endBusy();
      }
    }

    function updateRefreshLabel() {
      const el = document.getElementById('last-refresh');
      const s = Math.round((Date.now() - _lastRefresh) / 1000);
      el.textContent = s <= 0 ? 'just now' : s + 's ago';
    }

    function escHtml(input) {
      return String(input)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
    }

    function roadmapSections() {
      const track = ROADMAP_TRACKS[ROADMAP_STATE.track];
      if (!track) return [];
      if (ROADMAP_STATE.priority === 'all') return track.sections;
      return track.sections.filter(s => s.priority === ROADMAP_STATE.priority);
    }

    function progressStorageKey(trackKey, sectionTitle) {
      return 'roadmap_progress::' + trackKey + '::' + sectionTitle;
    }

    function readProgress(trackKey, sectionTitle) {
      const key = progressStorageKey(trackKey, sectionTitle);
      const raw = localStorage.getItem(key);
      const n = Number(raw);
      if (!Number.isFinite(n)) return 0;
      return Math.max(0, Math.min(100, Math.round(n)));
    }

    function writeProgress(trackKey, sectionTitle, value) {
      const key = progressStorageKey(trackKey, sectionTitle);
      localStorage.setItem(key, String(value));
    }

    function progressColorClass(value) {
      if (value >= 100) return '#06b6d4';
      if (value >= 70) return '#22c55e';
      if (value >= 40) return '#f59e0b';
      return '#ef4444';
    }

    function renderProgressPanel(sections) {
      const panelEl = document.getElementById('project-progress');
      if (!panelEl) return;

      if (!sections.length) {
        panelEl.innerHTML = '<h3 class="progress-title">项目进度 Slider</h3><div class="roadmap-meta">当前筛选无项目</div>';
        return;
      }

      panelEl.innerHTML =
        '<h3 class="progress-title">项目进度 Slider</h3>' +
        '<div class="progress-list">' +
        sections.map((sec) => {
          const p = readProgress(ROADMAP_STATE.track, sec.title || '');
          const color = progressColorClass(p);
          return (
            '<article class="progress-row">' +
            '<div class="progress-row-top">' +
            '<div class="progress-name">' + escHtml(sec.title || '') + '</div>' +
            '<div class="progress-pct">' + p + '%</div>' +
            '</div>' +
            '<input class="progress-slider" type="range" min="0" max="100" step="1" value="' + p + '" style="--pct: ' + p + '%; --slider-color: ' + color + ';" data-progress-track="' + escHtml(ROADMAP_STATE.track) + '" data-progress-title="' + escHtml(sec.title || '') + '" />' +
            '</article>'
          );
        }).join('') +
        '</div>';

      panelEl.querySelectorAll('.progress-slider').forEach((sliderEl) => {
        sliderEl.addEventListener('input', () => {
          let v = Number(sliderEl.value);
          if (!Number.isFinite(v)) v = 0;
          v = Math.max(0, Math.min(100, Math.round(v)));
          sliderEl.value = String(v);

          const color = progressColorClass(v);
          sliderEl.style.setProperty('--pct', v + '%');
          sliderEl.style.setProperty('--slider-color', color);

          const pctEl = sliderEl.closest('.progress-row')?.querySelector('.progress-pct');
          if (pctEl) pctEl.textContent = v + '%';

          const track = sliderEl.dataset.progressTrack || ROADMAP_STATE.track;
          const title = sliderEl.dataset.progressTitle || '';
          writeProgress(track, title, v);
        });
      });
    }


    function roadmapRenderTabs() {
      const tabsEl = document.getElementById('roadmap-tabs');
      const filterEl = document.getElementById('roadmap-filters');
      tabsEl.innerHTML = Object.entries(ROADMAP_TRACKS).map(([k, v]) => (
        '<button class="roadmap-tab ' + (k === ROADMAP_STATE.track ? 'active' : '') +
        '" data-track="' + k + '">' + escHtml(v.icon + ' ' + v.name) + '</button>'
      )).join('');
      filterEl.innerHTML = ['all', 'P0', 'P1', 'P2'].map((p) => (
        '<button class="roadmap-filter ' + (p === ROADMAP_STATE.priority ? 'active' : '') +
        '" data-priority="' + p + '">' + (p === 'all' ? '全部' : p) + '</button>'
      )).join('');

      tabsEl.querySelectorAll('button').forEach((btn) => {
        btn.addEventListener('click', () => {
          ROADMAP_STATE.track = btn.dataset.track;
          roadmapRender();
        });
      });
      filterEl.querySelectorAll('button').forEach((btn) => {
        btn.addEventListener('click', () => {
          ROADMAP_STATE.priority = btn.dataset.priority;
          roadmapRender();
        });
      });
    }

    function roadmapRenderPage() {
      const sections = roadmapSections();
      const pageEl = document.getElementById('roadmap-page');
      const metaEl = document.getElementById('roadmap-meta');
      metaEl.textContent = 'sections: ' + sections.length + ' · full list mode';

      if (sections.length === 0) {
        pageEl.innerHTML = '<div class="roadmap-card"><div class="roadmap-card-head"><h3 class="roadmap-title">No items</h3></div></div>';
        return;
      }

      pageEl.innerHTML = sections.map((sec) => {
        const items = (sec.items || []).map((it) => {
          const link = it.link ? ('<a href="' + escHtml(it.link) + '" target="_blank">link</a>') : '';
          const tag = it.tag ? ('<span class="roadmap-tag">' + escHtml(it.tag) + '</span>') : '';
          return '<li><span class="roadmap-dot"></span><span>' + escHtml(it.text) + link + '</span>' + tag + '</li>';
        }).join('');

        return (
          '<article class="roadmap-card">' +
          '<div class="roadmap-card-head">' +
          '<span class="roadmap-pri">' + escHtml(sec.priority || '-') + '</span>' +
          '<h3 class="roadmap-title">' + escHtml(sec.title || '') + '</h3>' +
          '<span class="roadmap-count">' + (sec.items ? sec.items.length : 0) + '</span>' +
          '</div>' +
          '<ul class="roadmap-items">' + items + '</ul>' +
          '</article>'
        );
      }).join('');

      renderProgressPanel(sections);
    }

    function roadmapRender() {
      roadmapRenderTabs();
      roadmapRenderPage();
    }

    roadmapRender();

    setInterval(updateRefreshLabel, 1000);
    setInterval(() => { if (_busy === 0) location.reload(); }, REFRESH_MS);
  </script>
</body>
</html>"""


def _row(host: str, cfg: dict) -> str:
    snap = store.latest(host)
    can_wake = "mac" in cfg
    ip = cfg.get("ip", "")

    if not snap:
        status_html = '<span class="unknown">-</span>'
        cells = ['<td class="na">-</td>'] * 7
    elif not snap.get("online", True):
        status_html = '<span class="offline">offline</span>'
        cells = ['<td class="na">-</td>'] * 7
    else:
        status_html = '<span class="online">online</span>'
        cpu_pct = snap.get("cpu_pct")
        cpu_c   = snap.get("cpu_package_c")
        mem_pct = snap.get("memory", {}).get("pct")
        gpus    = snap.get("gpus", [])
        gpu_c   = gpus[0]["temp_c"] if gpus else None
        gpu_w   = gpus[0]["power_w"] if gpus else None
        ssds    = snap.get("ssd_c", [])
        ssd_c   = f"{min(ssds):.0f}" if ssds else None
        bat_pct = snap.get("battery_pct")
        bat_state = snap.get("battery_state", "")
        bat_txt = None
        if bat_pct is not None:
            mark = "+" if bat_state in ("charging", "charged", "AC attached") else ""
            bat_txt = f"{bat_pct}{mark}"

        def cell(v): return f'<td>{v}</td>' if v is not None else '<td class="na">-</td>'
        cells = [
            cell(f"{cpu_pct:.1f}" if cpu_pct is not None else None),
            cell(f"{cpu_c:.0f}" if cpu_c else None),
            cell(f"{mem_pct:.1f}" if mem_pct else None),
            cell(f"{gpu_c}" if gpu_c is not None else None),
            cell(f"{gpu_w}" if gpu_w is not None else None),
            cell(ssd_c),
            cell(bat_txt),
        ]

    actions = ""
    if can_wake:
        actions += f'<button class="wake" onclick="wake(\'{host}\')">Wake</button>'
        actions += f'<button class="shutdown" onclick="shutdown(\'{host}\')">Shutdown</button>'

    ip_html = f'<span class="ip">{ip}</span>' if ip else ""
    return (
        f'<tr id="row-{host}">'
        f'<td class="host">{host}{ip_html}</td>'
        f'<td class="status">{status_html}</td>'
        f'{"".join(cells)}'
        f'<td class="actions">{actions}</td>'
        f'</tr>'
    )


@router.get("/ui", response_class=HTMLResponse)
def ui():
    rows = "\n".join(_row(host, cfg) for host, cfg in settings.hosts.items())
    return HTMLResponse(_PAGE.replace("{rows}", rows))
