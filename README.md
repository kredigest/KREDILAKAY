# KrediGest / KREDILAKAY

![Logo](static/logo.png)

## Fonctionnalités
- Portail client sécurisé
- Scoring crédit IA (300-850 pts)
- Chatbot FR/Kreyòl/EN
- Conformité RGPD/HDS
- PWA hors-ligne

## Installation
```bash
git clone https://github.com/kredigest/kredilakay.git
cd kredilakay
cp .env.example .env

# Backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
flask db upgrade

# Frontend
cd frontend
npm install
npm run build
