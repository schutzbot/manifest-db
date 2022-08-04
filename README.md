Manifest-db
=======

Stores all the  manifests and corresponding image-infos to test OSbuild.

### Update workflow

The update workflow starts with a github action that is manually triggered. This
GH action is named `Update DB`. It will firstly clone the latests
`osbuild-composer` and copy all its manifests into the database. Secondly the
action will create a commit and push this on the corresponding gitlab ci
project
(https://gitlab.com/redhat/services/products/image-builder/ci/manifest-db).
Thirdly, after the push is completed, the action triggers a special pipeline on
the CI. This pipeline builds every manifests from the DB. Once building is done,
the pipeline starts the `schutzbot/include_image_info.sh` script. This script
will download all the produced image-infos resulting from the builds and update
the DB with them. Then it will amend the commit sent to the CI pipeline with
these freshly builds image-info, push those commit to github on a branch and
create a pull request out of them.

### Contributing

Please refer to the [developer guide](https://www.osbuild.org/guides/developer-guide/developer-guide.html) to learn about our workflow, code style and more.

### Repository:

 - **web**:   <https://github.com/osbuild/osbuild>
 - **https**: `https://github.com/osbuild/osbuild.git`
 - **ssh**:   `git@github.com:osbuild/osbuild.git`

### License:

 - **Apache-2.0**
 - See LICENSE file for details.
