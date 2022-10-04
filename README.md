Manifest-db
=======

This repo serves as a data base to store the test cases for OSBuild. It contains
all the tooling to automatically update the DB by scanning regularly
OSBuild-composer.

## The test code and its cases are stored on Manifest-DB

### test code

In
[`tools/osbuild-image-test`](https://github.com/osbuild/manifest-db/tree/main/tools/osbuild-image-test)
this serves as the main entry point to both:

- generate an update to the database (with `--generator-mode` flag)
- test a version of OSBuild against the database

The default mode (test mode) will compare that the resulting `image-info` JSON
extracted from the build is the same as the one in the DB.

Note that a
[filter](https://github.com/osbuild/manifest-db/blob/main/tools/osbuild-image-test#L281)
function will mask some of the fields during the comparison time.

[Learn more why here](https://github.com/osbuild/manifest-db/commit/f89978d957fd3085063ae44692d326d11223d92f)

### DB

Stored in the
[`manifest-db`](https://github.com/osbuild/manifest-db/tree/main/manifest-db)
directory.

# Update workflow

To update the data base, an automated workflow is triggered every 15 days, on
1st and 15th of each month. This process allows to sync with the latest
composer.

#### 1/ on GitHub: trigger the Gitlab CI

Using a GitLab `trigger token` the GitHub action starts the CI with a
different workflow than the one used to run the regression testing.

#### 2/ on CI: Manifest generation

The first job downloads the latest osbuild-composer sources from upstream,
[generates all the test
manifests](https://github.com/osbuild/manifest-db/blob/main/.gitlab-ci.yml#L68)
using the gen-manifest tool and stores them as an
artifact.

This step is easy to run, consume few
[resources](https://github.com/osbuild/manifest-db/blob/main/.gitlab-ci.yml#L58)

#### 3/ on CI: Image-info generation

A job for each architecture and distribution listed in
[.gitlab-ci.yml](https://github.com/osbuild/manifest-db/blob/main/.gitlab-ci.yml)
will run in parallel. Each job will:

- [Run OSBuild on
them](https://github.com/osbuild/manifest-db/blob/main/test/cases/manifest_tests#L27)
- [Generate the image
info](https://github.com/osbuild/manifest-db/blob/main/tools/osbuild-image-test#L274)

This step is the longest, it can take up to 2h to finish some jobs.

#### 4/ on CI: Image-info generation

Finally the last job imports the generated manifests and image-info,
[updates the DB with these information](https://github.com/osbuild/manifest-db/blob/main/.gitlab-ci.yml#L117),
creates a branch, a commit, pushes it on Github and finally [opens](https://github.com/osbuild/manifest-db/blob/main/schutzbot/include_image_info.sh#L33) a
[PR](https://github.com/osbuild/manifest-db/pull/55) using the
[Schutzbot](https://github.com/schutzbot) user.

The PR message contains a check list of changed manifests and image-info. The
list is generated with the command `tool/update_tool report --github-markdown`.

#### 5/ on Github: reviewing the PR.

Then a reviewer needs to look that the update PR is in good shape.
Tooling to help [`tools/update_tool`](https://github.com/osbuild/manifest-db/pull/42)

Note: you can add yourself to the [list of
reviewers](https://github.com/osbuild/manifest-db/blob/main/schutzbot/include_image_info.sh#L37)
if you want to get notified

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
        GH01 --> GH2{4. Build all image-info}
        GH01 --> GH3{5. Create $BRANCH\n create update commit\npush $BRANCH}
    end
    subgraph Github/Manifest-db
        RS0[ 2. Action\n\nTrigger pipeline\non branch main ]
        RSO1[ 7. Action\n\n Propagate main's\nSHA on OSBuild]
        GH4[(Repo)]
    end
    subgraph Github/OSBuild
        OS0[(Repo)]
        OS1[ 9. Action\n\n Propagate main's\nSHA on Manifest-db]
        OS0 ---|upon\nupdate\non main| OS1

    end
    RS0 --> GH01    
    i((Scheduler)) -- 1. start github action--> RS0
    GH3 == open PR ===> GH4
    j{{Maintainer}} -.6. review to\nmerge/discard\nPR .-> GH4
    j -..8. review to\nmerge/discard\nPR ..-> OS0

    RSO1 == open PR ==> OS0
    GH4 ---|upon\nupdate\non main| RSO1

    OS1 == open PR ==> GH4
    j -..10. review to\nmerge/discard\nPR ..-> GH4
```

# Keeping toolchain up to date

Two Github actions will propagate the up-to-date DB to OSBuild and the
up-to-date OSbuild to manifest-db.

- [GH action](https://github.com/osbuild/manifest-db/blob/main/.github/workflows/propagate_to_osbuild.yml) to update OSBuild's reference commit
- [GH action](https://github.com/osbuild/osbuild/blob/main/.github/workflows/propagate_to_manifestdb.yml) to update Manifest-DB's reference commit


# Why this repository

Before Manifest-DB the test-case generation was manual and required:

- in depth knowledge of our toolchain is required
- access to internal network for rhel distributions
- access to specialized hardware (ppc)

As a result, it was not accessible especially for external developers
(preventing them from contributing to image definitions)

## The tests and their cases were stored on Composer

As their main purpose is to test the non regression of OSBuild (using
[image_test](https://github.com/osbuild/osbuild-composer/blob/main/test/cases/image_tests.sh))
they should not belong in Composer

# Terminology

## Image definitions

Image definitions are the way we describe an image and there is one for every image
we support. Definitions can be found in
[osbuild-composer/internal/distros](https://github.com/osbuild/osbuild-composer/tree/main/internal/distro)

### Image definitions must be tested

- We need to run OSBuild against each one of them
- Check whether the build is *correct*
    - Absence of accidental change
    - Validate changes on a rare occasion

OSBuild can't run the image definition directly.
It needs an intermediate format, the
[manifest](https://github.com/osbuild/manifest-db/blob/main/manifest-db/centos_8-aarch64-ami-boot.json#L8)

## Manifests

The Manifest is a JSON representation of an image definition. It tells OSBuild
what to do to make an Image.

## Image info

The [Image
info](https://github.com/osbuild/manifest-db/blob/main/manifest-db/centos_8-aarch64-ami-boot.json#L6868)
is a JSON representation of an image.

Generated by the tool
[`image-info`](https://github.com/osbuild/manifest-db/blob/main/tools/image-info)
it contains a list of discoverable pieces of information such as:
- Package list
- Network configuration
- ...

## Test cases

Combination of manifest and image-info. They are the reference point of what is
`correct` for a given input. They must be generated and stored for later use.

![](https://mermaid.ink/svg/pako:eNo9j70OwjAMhF_F8kxfoAMTDJXoAiPpYBqnWGoclDpCCPHuhN_NJ393p7vjmDxji2FO1_FM2WC3d9odu0gTg-cgKiZJB2iaiRUiqQRerGnW0B_7rxqc9hWAtJyKzB5e3y5-Q0RDGnCFkXMk8bXs7hTAoZ05ssO2nrWIymwOnT4qWi6ejLdeLGVsA80Lr5CKpcNNR2wtF_5BG6EpU_xT_Db1n1XvcY8nBzNOUA)

## The data base

Hosted under the `manifest-db` directory, each file is an entry to a test case.


### Contributing

Please refer to the [developer guide](https://www.osbuild.org/guides/developer-guide/developer-guide.html) to learn about our workflow, code style and more.

### License:

 - **Apache-2.0**
 - See LICENSE file for details.
