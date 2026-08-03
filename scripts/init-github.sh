#!/usr/bin/env bash
set -euo pipefail

git init
git add .
git commit -m "chore: initialize DealerMind AI platform"
git branch -M main

echo "Repository initialized locally."
echo "Create an empty GitHub repository named dealermind-ai, then run:"
echo "git remote add origin git@github.com:YOUR_USERNAME/dealermind-ai.git"
echo "git push -u origin main"
