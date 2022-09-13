#!/bin/bash
set -euxo pipefail
sudo dnf install gh -y pip python3-gitlab

# Login to GH
echo "${SCHUTZBOT_GH_TOKEN}" | gh auth login --with-token

# import the image info from the current build
./tools/ci_import --pipeline-id "$CI_PIPELINE_ID" --token "${GITLAB_TOKEN}"

#remove ci-details-before-run
mv ci-details-before-run /tmp
rm -rf generated-image-infos

git config --local user.name "SchutzBot"
git config --local user.email "imagebuilder-bots+schutzbot@redhat.com"

git remote add upstream https://schutzbot:"$SCHUTZBOT_GH_TOKEN"@github.com/schutzbot/manifest-db.git

pip install columnify

now=$(date '+%Y-%m-%d-%H%M%S')
BRANCH_NAME="db-update-$now"

git add -A && \
    git commit -m "db: update


Automatic update:
- manifests from latest composer
- image-info from pipeline $CI_PIPELINE_ID" && \
    git push upstream "$BRANCH_NAME:$BRANCH_NAME" && \
    gh pr create \
        --title "db: automated update" \
        --body "$(tools/update_tool report --github-markdown)" \
        --repo "osbuild/manifest-db" \
        -r lavocatt

#restore ci-details-before-run
mv /tmp/ci-details-before-run .
