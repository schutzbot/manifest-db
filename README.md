Manifest-db
=======

Stores all the manifests and corresponding image-infos to test OSbuild.

### Update workflow

#### 1/ on GitHub: trigger the Gitlab CI


Using a GitLab `trigger token` the GitHub action starts the CI with a
different workflow than the one used to run the regression testing.

#### 2/ on CI: Manifest generation

The first job downloads the latest osbuild-composer sources from upstream,
generates all test manifests using the gen-manifest tool and stores them as an
artifact.

#### 3/ on CI: Image-info builds

Then a job for each architecture and distribution listed in
[.gitlab-ci.yml](https://github.com/osbuild/manifest-db/blob/main/.gitlab-ci.yml)
will run in parallel. Each job will:

- import the generated manifests.
- generate and include the image-info for the manifests where possible and
  expose them as artifacts.

#### 4/ on CI: PR creation

Finally the last job imports the generated manifests and image-info, updates the
DB with these information, creates a branch, a commit, pushes it on Github and
finally opens a PR using the [Schutzbot](https://github.com/schutzbot) user.

The PR message contains a check list of changed manifests and image-info. The
list is generated with the command `tool/update_tool report --github-markdown`.

#### Resuming in a diagram

```mermaid
flowchart LR
    subgraph Gitlab
        GH0[(Repo)]
        GH01[Pipeline]
        GH01 --> GH1
        GH1 -.- GH0
        GH2 -.- GH0
        GH3 -.- GH0
        GH1{3. Generate manifests}
        GH01 --> GH2{4. Build image-infos}
        GH01 --> GH3{5. Create $BRANCH\n create update commit\npush $BRANH}
    end
    subgraph Github/Manifest-db
        RS0[ 2. Action\n\nTrigger\npeline\non main ]
        RSO1[ 7. Action\n\n Propagate main's\nSHA on OSBuild]
        GH4[(Repo)]
    end
    subgraph Github/OSBuild
        OS0[(Repo)]
    end
    RS0 --> GH01    
    Maintainer -- 1. start github action--> RS0
    GH3 == open PR ==> GH4
    Maintainer --6. review to\nmerge/discard\nPR --> GH4
    Maintainer --8. review to\nmerge/discard\nPR --> OS0
    RSO1 == open PR ==> OS0
    GH4 -. upon\nupdate\non main .-> RSO1
```


### Contributing

Please refer to the [developer guide](https://www.osbuild.org/guides/developer-guide/developer-guide.html) to learn about our workflow, code style and more.

### License:

 - **Apache-2.0**
 - See LICENSE file for details.
