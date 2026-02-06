# GitHub Copilot Impact Dashboard

A rapidly deployable, containerized solution that allows organizations to visualize the impact of GitHub Copilot adoption by overlaying GitHub Copilot usage metrics with developer activity metrics from GitHub.

**Disclaimer**: This project is open source and provides insights that may not be natively available in GitHub Copilot. Opinions and views expressed are those of the project maintainers and do not necessarily reflect the views of GitHub or any employer. Uses only standard GitHub REST APIs to collect, aggregate, and visualize data.

## Quick Start

Get up and running in about 5 minutes.

**You'll need:**
- Docker Desktop ([grab it here](https://www.docker.com/products/docker-desktop))
- A GitHub Personal Access Token with `manage_billing:copilot` scope ([create one here](https://github.com/settings/tokens))
- Your GitHub organization name

**Setup:**

Clone the repo and configure your environment:

```bash
git clone https://github.com/satomic/gh-copilot-developer-impact-dashboard.git
cd gh-copilot-developer-impact-dashboard
cp .env.template .env
# Edit .env with your GitHub PAT and org name
```

Your `.env` file should have at minimum:
```env
GITHUB_PAT=ghp_your_token_here
ORGANIZATION_SLUGS=your-org-name
```

Start everything:
```bash
docker-compose up -d
```

Open Grafana at **http://localhost:8080** (username: `admin`, password: `copilot`) and the dashboard will be ready to go. The system automatically starts Elasticsearch, sets up Grafana with datasources, loads the dashboard, and begins fetching data from GitHub every hour.

---

## Demo Mode

Want to explore the dashboard without connecting to a real GitHub organization? Demo mode generates realistic mock data so you can see exactly what the dashboard looks like with a full dataset.

**Quick start with demo mode:**

```bash
git clone https://github.com/satomic/gh-copilot-developer-impact-dashboard.git
cd gh-copilot-developer-impact-dashboard
ENABLE_DEMO_MODE=true docker-compose up -d
```

Or add it to your `.env` file:
```env
ENABLE_DEMO_MODE=true
```

**What you get:**

Demo mode automatically generates 5 months of realistic data based on actual GitHub research into Copilot productivity gains:

- **25 developers** across 5 teams (Platform, Frontend, Backend, Data, Mobile)
- **Different seniority levels** - junior, mid-level, senior, staff, and principal engineers
- **Realistic productivity patterns** - 20-30% productivity improvements after Copilot adoption
- **Gradual ramp-up period** - 8-week adoption curve as developers learn to use Copilot effectively
- **Varied usage patterns** - power users, regular users, and occasional users
- **Research-based metrics** - 26-30% acceptance rates, typical chat/agent usage patterns
- **Before/after comparison** - Copilot adoption date set to 10 weeks ago so you can see the impact
- **Complete history** - 150 days of developer activity and Copilot metrics

The mock data includes all the same metrics you'd see with real data:
- Commits, pull requests, code reviews, issues
- Copilot suggestions, acceptances, chat interactions
- Team breakdowns and individual user activity
- Acceptance rates and productivity trends

This is perfect for:
- Testing the dashboard before deploying to production
- Demoing the solution to stakeholders
- Understanding what metrics are available
- Exploring the dashboard features without needing GitHub access

**Note:** Demo mode skips GitHub API calls entirely, so you don't need a GitHub token or organization access.

---

## What This Does

This dashboard helps you understand whether GitHub Copilot is actually making your developers more productive. Instead of just showing Copilot usage stats in isolation, it overlays those metrics with actual developer activity from GitHub like commits, pull requests, and code reviews. This way you can see correlations between Copilot adoption and productivity changes.

The goal is to answer questions like:
- Are developers who use Copilot more committing more code?
- Did PR velocity increase after Copilot rollout?
- Which teams are getting the most value from Copilot?
- Are we actually getting ROI on those Copilot licenses?

**Data sources:**

We pull from several GitHub APIs to build a complete picture:

For Copilot metrics:
- Team-level usage stats from the Copilot Metrics API
- Individual user activity from the User Metrics API (28-day rolling window)
- Seat assignments and license utilization
- Active user tracking

For developer activity:
- Commit frequency and patterns via the Search API
- Issue creation and resolution
- Pull request creation, merging, and review activity
- Code review participation

All of this gets stored in Elasticsearch (not limited to just 28 days like the GitHub UI), so you can analyze trends over months or years.

---

## Features

**Productivity impact analysis** - Compare developer metrics before and after Copilot adoption. See which teams improved the most and identify patterns in how developers use Copilot.

**Comprehensive metrics** - Track Copilot suggestions, acceptance rates, lines of code generated, plus traditional metrics like commits, PRs, code reviews, and issues. Also monitors chat usage, agent usage, and active days.

**Automated collection** - Runs hourly (configurable) to fetch fresh data. Keeps historical records indefinitely and automatically handles deduplication.

**Visual analysis** - Time series charts showing trends over time, leaderboards for top contributors and Copilot users, team breakdowns by seniority and contribution type, acceptance rate tracking, and activity heatmaps.

**Demo mode with realistic data** - Generate 5 months of research-based synthetic data representing 25 developers across 5 teams. Includes realistic Copilot adoption patterns (20-30% productivity gains over an 8-week ramp-up), varied usage by seniority level, and before/after metrics for impact analysis. Perfect for testing or demos without GitHub access.

---

## The Dashboard

The main view gives you a comprehensive look at how Copilot adoption correlates with developer productivity.

**Summary metrics** show total commits, PRs opened, Copilot interactions, and acceptance rates across your selected time range. These give you the high-level view at a glance.

**Team analysis** breaks down commits by team on a weekly basis, shows total contributions (commits + PRs + reviews) by team and by seniority level. This helps you spot which teams are benefiting most from Copilot and whether there are patterns by experience level.

**Leaderboards** highlight your top contributors by commits and your most active Copilot users. Great for identifying power users who could become Copilot champions in your organization.

**Detailed comparisons** give you user-level analysis side-by-side with Copilot usage, time series trends showing productivity changes, and cross-team benchmarking.

You can filter everything by organization (supports multiple orgs), team, seniority level (junior, mid, senior, staff, principal), and time range. The default is 90 days but you've got unlimited historical data available.

---

## Deployment

You've got a few options depending on your needs.

**Azure Container Apps** - Best for production. Fully managed, auto-scales, integrates with Azure Monitor, includes GitHub Actions CI/CD, and uses Azure Key Vault for secrets. See the [Azure deployment guide](deploy/azure-container-apps.md) for details.

**Linux with Docker** - Perfect for development or self-hosted scenarios. Single-command deployment, persistent data volumes, easy backups. Works great for small teams or when you want to run it on your own infrastructure. Check out the [Docker deployment guide](deploy/linux-with-docker.md).

**Kubernetes** - For large enterprises that need horizontal scaling, high availability, and cloud-agnostic deployment. See the [Kubernetes guide](deploy/kubernetes.md).

---

## Configuration

**Required settings:**

You must provide a GitHub Personal Access Token and at least one organization name:

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_PAT` | GitHub PAT with `manage_billing:copilot` scope | `ghp_xxxxx...` |
| `ORGANIZATION_SLUGS` | Comma-separated org names | `my-org,other-org` |

**Optional settings:**

| Variable | Default | Description |
|----------|---------|-------------|
| `ELASTICSEARCH_URL` | `http://elasticsearch:9200` | Where to store data |
| `EXECUTION_INTERVAL_HOURS` | `1` | How often to fetch from GitHub |
| `ENABLE_DEVELOPER_ACTIVITY` | `true` | Collect commit/PR/review data |
| `DEVELOPER_ACTIVITY_DAYS_BACK` | `28` | Days of history for dev activity |
| `ENABLE_DEMO_MODE` | `false` | Use mock data instead of real GitHub |

**Index names** (if you need to customize where data is stored):

| Variable | Default |
|----------|---------|
| `INDEX_USER_METRICS` | `copilot_user_metrics` |
| `INDEX_USER_ADOPTION` | `copilot_user_adoption` |
| `INDEX_DEVELOPER_ACTIVITY` | `developer_activity` |
| `INDEX_BREAKDOWN` | `copilot_usage_breakdown` |
| `INDEX_TOTAL` | `copilot_usage_total` |
| `INDEX_SEAT_ASSIGNMENTS` | `copilot_seat_assignments` |
| `INDEX_SEAT_INFO_SETTINGS` | `copilot_seat_info_settings` |

For Azure deployments, you'll need additional variables. Check the [Azure deployment guide](deploy/azure-container-apps.md).

---

## How It Works

The architecture is pretty straightforward:

```
GitHub APIs <---> Data Collector (cpuad-updater) <---> Elasticsearch
                                                            |
                                                            v
                                                        Grafana
```

The data collector runs hourly and fetches Copilot metrics plus developer activity from GitHub. Everything gets indexed to Elasticsearch which stores it indefinitely. Grafana queries Elasticsearch to render the dashboard with interactive filtering and drill-down.

Built with Python 3.11+, Elasticsearch 8.x, and Grafana 11.x, all containerized with Docker.

---

## Getting Help

Check the [docs](docs/) folder for detailed guides. Report issues or request features via [GitHub Issues](https://github.com/satomic/gh-copilot-developer-impact-dashboard/issues).

Deployment guides:
- [Azure Container Apps](deploy/azure-container-apps.md)
- [Linux with Docker](deploy/linux-with-docker.md)
- [Kubernetes](deploy/kubernetes.md)

---

## License

MIT License - see [LICENSE](LICENSE) for details.

Built with data from GitHub's official REST APIs to help organizations maximize their GitHub Copilot investment through data-driven insights.
