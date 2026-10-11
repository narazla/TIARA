# TIARA — BOT Chain Care DApp

Live app: https://www.tiaracare.my.id, 
X: https://x.com/tiaracareai

<br>
<div align="left">
  <img
    src="https://drive.google.com/uc?export=view&id=1rhJCGPOvsYHlw2Tl5m5wh-WzsWgavw_K"
    alt="TIARA DApp"
    style="width:100%; max-width:1400px;"
  />
</div>
<br>

> **Medical disclaimer:** TIARA is not a medical diagnosis tool. It provides informational cognitive trend monitoring and caregiver support only, and does not replace professional clinical assessment.

## Overview

TIARA (Thinking, Interaction, And Recall Assistant) is an AI-powered cognitive care platform that supports families and caregivers.

TIARA helps families notice early cognitive changes through daily AI-guided check-ins (voice, video and language signals) and gives caregivers a PIN-protected dashboard with trends, alerts and recommendations. For this hackathon we added a Dementia Guidance chatbot grounded in Indonesian medical documents (RAG) and a smart contract on BOT Chain Mainnet where any answer can be minted as a permanent, publicly verifiable wisdom log.

## Core User Flows

```text
Older adult:
Login -> Home -> Daily check-in -> Video/audio capture -> Supportive result

Caregiver:
Login -> Caregiver PIN -> Dashboard -> Alerts -> Recommendations -> Guidance AI -> Reports

Healthcare worker:
Login -> Patient monitoring -> Session history -> Longitudinal trends
```

## Features

- **Daily video/audio check-in:** AI-guided questions with consent-based media capture.
- **AI analysis pipeline:** Transcription, voice feature extraction, language analysis, and risk scoring.
- **Caregiver dashboard:** Cognitive trend charts, patient summaries, alerts, and recommendations.
- **Dementia Guidance AI:** Answers are retrieved from validated documents (PNPK Dementia, Kemenkes caregiver guide) using RAG (multilingual-e5-large + FAISS), generated with Gemini, and returned in the language of the question.
- **Role-based access:** Separate elderly, caregiver, and healthcare worker flows.
- **Caregiver PIN protection:** An additional access step for sensitive caregiver insights.
- **On-chain Wisdom Log:** After the Dementia Guidance AI answers, the caregiver clicks the mint button in the chat. MetaMask asks them to sign a transaction that stores the question, the answer and a timestamp in the TiaraWisdomLog contract on BOT Chain Mainnet. Entries are public and verifiable on the block explorer. Only Q&A pairs that a user chooses to mint go on-chain; check-in data, reports and patient records stay in the app database.

## Deployment & Smart Contract

The smart contract source code is located in [`contracts/WisdomLog.sol`](contracts/WisdomLog.sol). TIARA's deployed contract is available on both networks:

| Network | Chain ID | Contract Name | Address / Explorer Link |
|---|---|---|---|
| **BOT Chain Testnet** | `968` | TiaraWisdomLog | `0x9E71519cD8C72379caD79c6A6Fc5bf5FF261b149` ([View on Explorer](https://scan.bohr.life/address/0x9E71519cD8C72379caD79c6A6Fc5bf5FF261b149)) |
| **BOT Chain Mainnet** | `677` | TiaraWisdomLog | `0x9E71519cD8C72379caD79c6A6Fc5bf5FF261b149` ([View on Explorer](https://scan.botchain.ai/address/0x9E71519cD8C72379caD79c6A6Fc5bf5FF261b149)) |

The address is the same on both networks (same deployer wallet and nonce).

### BOT Chain network configuration

- **Network:** BOT Chain Mainnet
- **Chain ID:** `677` (`0x2A5`)
- **RPC URL:** `https://rpc.botchain.ai`
- **Block explorer:** `https://scan.botchain.ai`
- **Native currency:** BOT

- **Network:** BOT Chain Testnet
- **Chain ID:** `968`
- **RPC URL:** `https://rpc.bohr.life`
- **Block explorer:** `https://scan.bohr.life`
- **Native currency:** BOT

## How to Use the Live Application

1. Open https://www.tiaracare.my.id
2. Log in with the caregiver demo account, then enter PIN `123456`.
3. Open the Dementia Guidance tab and ask a question or click a suggested one.
4. Click the **Save to wisdom log** button under the answer and approve in MetaMask. BOT Chain Mainnet is added or switched automatically. Minting costs about 0.01 BOT in gas.
5. Click the **view transaction** link to see the entry on scan.botchain.ai.

## Demo Accounts

The seeded development environment includes these demo accounts:

| Role | Email | Password |
|---|---|---|
| Older adult | `elderly@tiara.app` | `password123` |
| Caregiver | `caregiver@tiara.app` | `password123` |
| Healthcare worker | `doctor@tiara.app` | `password123` |

**Caregiver dashboard PIN:** `123456`

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js, TypeScript, Tailwind CSS, Framer Motion, Recharts |
| Backend | FastAPI, Python, SQLAlchemy, PostgreSQL, Alembic |
| Authentication | JWT, bcrypt, caregiver PIN protection |
| AI and media | Google GenAI SDK, faster-whisper, librosa, OpenCV |
| Wallet integration | Browser EIP-1193 provider, MetaMask-compatible wallets |
| Blockchain target | BOT Chain Mainnet |

## Repository Structure

```text
TIARA_2/
├── frontend/              # Next.js application
│   ├── app/               # App Router pages and user flows
│   ├── components/        # Shared UI components, including ConnectWallet
│   └── lib/               # API client, authentication, and types
├── backend/               # FastAPI application
│   ├── app/               # Routes, models, services, and configuration
│   └── alembic/           # Database migrations
├── contracts/             # Solidity smart contracts
│   └── WisdomLog.sol      # On-chain care checkpoint registry
├── docs/                  # Product, architecture, API, AI, and security docs
├── docker-compose.yml     # PostgreSQL, backend, and frontend services
└── README.md
```

## Local Setup

### Prerequisites

- Node.js 18 or newer
- Python 3.11 or newer
- PostgreSQL 15 or newer
- Optional: Docker and Docker Compose

### Backend

```bash
cd backend
python -m venv venv

# Windows PowerShell
venv\Scripts\Activate.ps1

# macOS/Linux
# source venv/bin/activate

pip install -r requirements.txt
alembic upgrade head
python -m app.scripts.seed
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

For Render, set the service root directory to `backend` and use this start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Set these environment variables in Render:

```text
FRONTEND_URL=https://tiaracare.my.id,https://www.tiaracare.my.id
DATABASE_URL=<your-render-postgres-connection-string>
JWT_SECRET_KEY=<a-long-random-production-secret>
```

`FRONTEND_URL` accepts comma-separated origins so local development and Vercel preview URLs can be added when needed. The API CORS policy uses this value instead of allowing every origin.

### Railway alternative

Create a Railway project with a **PostgreSQL** service and a backend service connected to this repository. Configure the backend service with:

- **Root Directory:** `/backend`
- **Builder:** `Dockerfile`
- **Build Command:** leave empty; the Dockerfile installs dependencies
- **Start Command:** leave empty; the Dockerfile runs migrations and Uvicorn

Add the same `FRONTEND_URL` and `JWT_SECRET_KEY` variables listed above. Copy Railway PostgreSQL&apos;s `DATABASE_URL` into the backend service variables. The backend automatically converts Railway&apos;s standard PostgreSQL URL to the async SQLAlchemy driver required by the application.

For the Railway Free plan, leave `ENABLE_LOCAL_RAG` unset or set it to `false`; the large local embedding model is disabled by default so caregiver guidance stays responsive. Set `GEMINI_API_KEY` to enable AI-generated answers. Set `ENABLE_LOCAL_RAG=true` only on a host with enough memory for the embedding model.

### Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend reads `NEXT_PUBLIC_BACKEND_URL` first, then `NEXT_PUBLIC_API_URL`. Configure either variable in Vercel with the backend service URL, for example `https://tiara-backend.onrender.com`.

The frontend runs at `http://localhost:3000` and the backend API runs at `http://localhost:8000`. The API documentation is available at `http://localhost:8000/docs` when the backend is running.

### Docker Compose

From the repository root:

```bash
docker compose up --build
```

Configure database credentials, JWT settings, and the backend URL through the environment variables documented in the project configuration before using Docker in production.

## AI Pipeline

After a check-in is submitted, TIARA processes the session through these stages:

1. Transcription from recorded audio.
2. Voice feature extraction, including speech rate and hesitation signals.
3. Language analysis for orientation, memory recall, coherence, and vocabulary.
4. Basic facial and video analysis when media is available.
5. Composite cognitive trend scoring.
6. Caregiver alerts and recommendations based on observed patterns.

All results are informational indicators. They are not diagnoses.

## Security and Privacy

- Authentication uses JWT access tokens.
- Caregiver dashboard access requires a separate PIN.
- Camera and microphone flows require user consent.
- The system should be deployed with strong secrets and protected database credentials.
- Do not commit `.env` files, API keys, private keys, or wallet seed phrases.

## Documentation

Additional project documentation is available in [`docs/`](docs/), including:

- [Product requirements](docs/01-product-requirements.md)
- [MVP scope](docs/02-mvp-scope.md)
- [System architecture](docs/03-system-architecture.md)
- [Database design](docs/04-database-design.md)
- [API specification](docs/05-api-specification.md)
- [AI pipeline](docs/06-ai-pipeline.md)
- [Security and privacy](docs/07-security-and-privacy.md)
- [Development roadmap](docs/08-development-roadmap.md)
- [Demo script](docs/09-demo-script.md)

## Known Limitations

- On-chain wisdom logs are public, so personal patient information must not be minted.
- Minting needs a small amount of BOT for gas.
- RAG is used only in Dementia Guidance chat, while check-in analysis uses transcription, voice and language analysis without RAG.
- Some dashboard summary cards show sample values.
- AI model quality depends on available models, media quality, and runtime configuration.
- TIARA must not be used as a substitute for professional medical evaluation.

## Team

Built by Nazla Azzahra Hermana as a hackathon project on BOT Chain. The base TIARA platform (check-ins and dashboards) was built earlier as a team project.
