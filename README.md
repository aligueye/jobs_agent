# jobs_agent

An **LLM-powered job search assistant** that fetches live listings from the Adzuna API, ranks them against your resume using OpenAI via LangChain, and outputs a ranked CSV of best-fit roles.

## 🚀 Features
- **Live job data**: Pulls up-to-date postings via Adzuna API.
- **LLM ranking**: Uses GPT-4 (or GPT-4o-mini) to evaluate how well each job matches your profile.
- **Vector memory**: Embeds your resume into Chroma for context-aware filtering.
- **Extensible**: Designed to evolve into a full LangChain agent with chat and automation.

## 📦 Structure
```
jobs_agent/
├── .env
├── configs/
│   └── sources.yaml        # Job queries
├── data/
│   ├── jobs.csv            # Raw normalized jobs
│   ├── jobs_ranked.csv     # LLM-ranked jobs
│   ├── profile.md          # Your resume text
│   └── chroma/             # Vector store memory
└── src/
    ├── fetchers/adzuna.py  # API wrapper
    ├── normalize.py        # Cleans Adzuna JSON
    ├── memory.py           # Vector memory
    ├── rank_llm.py         # GPT-based scoring
    └── run_fetch.py        # Fetch workflow
```

## ⚙️ Setup
```bash
git clone https://github.com/aligueye/jobs_agent
cd jobs_agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
touch .env
# Add ADZUNA_APP_ID, ADZUNA_APP_KEY, OPENAI_API_KEY
```

## 🧠 Usage
1. Put your resume text into `data/profile.md`.
2. Build vector memory:
   ```bash
   python -c "from src.memory import build_profile_index; build_profile_index()"
   ```
3. Fetch jobs:
   ```bash
   python -m src.run_fetch
   ```
4. Rank jobs:
   ```bash
   python -m src.rank_llm
   ```
5. Review `data/jobs_ranked.csv` for the best fits.

## 🧩 Next steps
- Add `agent.py` to wrap fetch + rank as LangChain tools.
- Integrate conversation memory for natural queries.
- Add Streamlit dashboard for browsing top jobs.
- Schedule daily run via GitHub Actions or cron.

## 🪪 License
MIT
