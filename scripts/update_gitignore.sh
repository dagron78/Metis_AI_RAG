#!/bin/bash
# Script to update .gitignore and remove tracked files that should be ignored

# Remove cache files from git tracking but keep them locally
git rm --cached data/cache/llm_response/cache.pickle
git rm --cached data/cache/llm_response/stats.json
git rm --cached data/cache/vector_search/cache.pickle
git rm --cached data/cache/vector_search/stats.json
git rm --cached logs/security/security_events.log

echo "Removed cache and log files from git tracking"
echo "These files will remain in your local directory but won't be tracked by git anymore"