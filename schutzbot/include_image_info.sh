#!/bin/bash
set -euxo pipefail
sudo dnf install gh -y
sudo pip install python-gitlab

echo "${SCHUTZBOT_GH_TOKEN}" > /tmp/secret.txt
gh auth login --with-token < /tmp/secret.txt

#./tools/ci_import --pipeline-id "$CI_PIPELINE_ID" --token  ${GITLAB_TOKEN} --verbose

git checkout $CI_COMMIT_BRANCH

git config --local user.name "SchutzBot"
git config --local user.email "schutzbot@redhat.com"

git remote add origin2 https://@github.com/schutzbot/manifest-db.git
touch toto

# only change the last commit and push to github if things were changed
git diff-index --quiet HEAD -- || git add -A && \
    git commit --amend -m "db: update

Automatic update:
- manifests from latest composer
- image-info from pipeline $CI_PIPELINE_ID" && \
    git push https://"$SCHUTZBOT_PUSH_TOKEN"@github.com/schutzbot/manifest-db.git $CI_COMMIT_BRANCH && \
    gh pr create \
        --title "db update" \
        --body "automated db update" \
        --repo "osbuild/manifest-db" \
        --base "main" \
        --head "$CI_COMMIT_BRANCH" \
        -r lavocatt
