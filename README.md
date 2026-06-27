# 🌽 Alibaba Cloud Farm

> Farm **free API keys** from Alibaba Cloud (DashScope) — each account gives **1M tokens per model**, completely free.

![Dashboard Preview](assets/dashboard-preview.png)

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔑 **Auto Farm** | Create accounts & get API keys automatically via headless browser |
| 📊 **Usage Dashboard** | Real-time token usage tracking per model via web UI |
| 🗑️ **Delete Account** | Remove accounts directly from the dashboard |
| 📋 **One-click Copy** | Copy API keys & endpoints to clipboard instantly |
| 🔄 **9Router Integration** | Auto-register farmed keys into [9Router](https://github.com/9router/9router) proxy |
| 🧩 **Quick API Test** | Test any model directly from the dashboard |
| 📈 **Quota Tracker** | See how many tokens you've used per model with visual progress bars |

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Firefox (installed by Playwright)
- Linux (tested on Ubuntu 22.04)

### 1. Install Dependencies

```bash
git clone https://github.com/YOUR_USERNAME/alibaba-cloud-farm.git
cd alibaba-cloud-farm
pip install camoufox[geoip] playwright httpx
playwright install firefox
```

### 2. Set Up Catch-All Email

You need a **catch-all email domain** so every random email forwards to your inbox. Options:

**Option A: Cloudflare Email Routing (Recommended — Free)**
1. Add a domain to Cloudflare (or use an existing one)
2. Go to **Email** → **Email Routing** → **Catch-All Address**
3. Set action to "Send to an email" (your Gmail)
4. Enable catch-all rule

**Option B: Gmail + Alias**
Create a Gmail filter to catch `{anything}@yourdomain.com`

### 3. Run the Farm

```bash
python farm.py --email your@email.com
```

This will:
1. Open Alibaba Cloud registration page
2. Fill in a random email (`{random}@yourdomain.com`)
3. Verify email via IMAP/Gmail
4. Complete registration
5. Save API key to `results.json`

### 4. Run the Dashboard

```bash
python dashboard.py --port 8888
```

Open `http://localhost:8888` in your browser.

## 📊 Dashboard Features

### Accounts Tab
- View all farmed accounts with API keys
- **Copy** — one-click copy to clipboard
- **Delete** — remove accounts you no longer need
- **Test** — quick API test per model

### Usage Tracker
- Real-time token usage from [9Router](https://github.com/9router/9router) SQLite database
- Per-model breakdown with progress bars
- Auto-refreshes every 30 seconds

### Farm Tab
- Run new farm sessions directly from the UI
- Set number of accounts to farm
- Real-time status updates

## 🔌 9Router Integration

To use farmed keys with [9Router](https://github.com/9router/9router) (AI proxy router):

1. Register a new provider in 9Router Dashboard
2. Add farmed API keys as connections
3. Set base URL: `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`
4. Use model prefix `qf/` to distinguish farmed keys

Example Hermes config:
```yaml
aliases:
  glm52: qf/glm-5.2
  qw37m: qf/qwen3.7-max
  ds4pro: qf/deepseek-v4-pro
```

## 📋 Supported Models

| Model | Description |
|-------|-------------|
| `qwen-plus` | General purpose (best balance) |
| `qwen-max` | Most capable Qwen model |
| `qwen3-max` | Qwen3 flagship |
| `qwen3.7-max` | Latest Qwen3.7 |
| `qwen3.7-plus` | Fast + capable |
| `qwen3.6-flash` | Ultra-fast |
| `glm-5.2` | Zhipu GLM (strong reasoning) |
| `deepseek-v3.2` | DeepSeek general |
| `deepseek-v4-pro` | DeepSeek latest |
| `qwen3-coder-plus` | Code-specialized |
| `qwen3-coder-flash` | Fast code model |
| `qwen3-8b` | Small + fast |
| `qwen3-30b-a3b` | Medium MoE |
| `qwen3-235b-a22b` | Large MoE |
| `qwen3.5-plus-turbo` | Thinking model |
| `qwen3-max-thinking` | Deep reasoning |

> 100+ models available. Full list: [DashScope Models](https://help.aliyun.com/zh/model-studio/getting-started/models)

## 💰 Quota Info

| Resource | Limit |
|----------|-------|
| Tokens per model | **1,000,000** (1M) |
| Accounts per email | 1 |
| Models per account | 100+ |
| Cost | **Free** |

**Math:** 3 accounts × 1M tokens = **3M tokens per model** — enough for most use cases.

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐
│   farm.py       │────▶│  Alibaba Cloud   │
│ (Camoufox +     │     │  Registration    │
│  Playwright)    │◀────│  + API Key Gen   │
└────────┬────────┘     └──────────────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│  results.json   │────▶│  dashboard.py    │
│ (API keys)      │     │  (Web UI :8888)  │
└─────────────────┘     └────────┬─────────┘
                                 │
                                 ▼
                         ┌──────────────────┐
                         │  9Router Proxy   │
                         │  (qf/ prefix)    │
                         └──────────────────┘
```

## ⚠️ Important Notes

- **Email verification** is required — each account needs a unique email
- **Camoufox** (anti-detection Firefox) is used to avoid Cloudflare bot detection
- **Residential proxy** recommended but not required (Cloudflare slider may appear without it)
- Alibaba may rate-limit registration from the same IP — add delays if needed
- **Quota is per-model** — running out on `glm-5.2` doesn't affect `qwen-plus`

## 🔧 Configuration

### Environment Variables

```bash
# Optional: Gmail app password for email verification
export GMAIL_APP_PASSWORD="your-app-password"

# Optional: Proxy for Cloudflare bypass
export HTTP_PROXY="http://user:pass@proxy:port"
```

### Dashboard Options

```bash
python dashboard.py --port 8888 --host 0.0.0.0
```

## 📁 Project Structure

```
alibaba-cloud-farm/
├── farm.py              # Main farming script
├── dashboard.py         # Web dashboard
├── results.json         # Farmed accounts (auto-generated, gitignored)
├── assets/
│   └── dashboard-preview.png
├── README.md
└── .gitignore
```

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch
3. Commit your changes
4. Open a PR

## 📄 License

MIT License — use at your own risk.

## ⚠️ Disclaimer

This project is for **educational purposes only**. Respect Alibaba Cloud's Terms of Service. The authors are not responsible for any misuse or account suspensions.

## 🔗 Related Projects

- [9Router](https://github.com/9router/9router) — AI proxy router with multi-provider support
- [Camoufox](https://camoufox.com/) — Anti-detection Firefox browser
- [DashScope API](https://dashscope-intl.aliyuncs.com/) — Alibaba Cloud AI API
