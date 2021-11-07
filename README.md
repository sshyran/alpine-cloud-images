## _**NOTE: This is a Work-in-Progress**_

_It is intended that this will eventually replace
https://gitlab.alpinelinux.org/alpine/cloud/alpine-ec2-ami
as the offical multi-cloud image builder for Alpine Linux._

----

# Alpine Linux Cloud Image Builder

This repository contains the code and and configs for the build system used to
create official Alpine Linux images for various cloud providers, in various
configurations.  This build system is flexible, enabling others to build their
own customized images.

----
## Pre-Built Offical Cloud Images

To get started with offical pre-built Alpine Linux cloud images, visit
https://alpinelinux.org/cloud.  Currently, we build official images for the
following providers:
* AWS

You should also be able to find the most recently published Alpine Linux
images via your cloud provider's web console, or programatically query their
API with a CLI tool or library.

_(TODO: examples)_

----
## Build System

The build system consists of a number of components:

* the primary `build` script and related cloud-specific helpers
* a directory of `configs/` defining the set of images to be built
* a Packer `alpine.pkr.hcl` orchestrating the images' local build, as well as
  importing them to cloud providers and publishing them to desitnation regions
* a directory of `scripts/` which set up the images' contents during
  provisioning

### Build Requirements
* [Python](https://python.org) (3.9.7 is known to work)
* [Packer](https://packer.io) (1.7.6 is known to work)
* [QEMU](https://www.qemu.org) (6.1.0 is known to work)
* cloud provider account(s)

### Cloud Credentials

This build system relies on the cloud providers' Python API libraries to find
and use the necessary credentials -- via configuration in the user's home
directory (i.e. `~/.aws/...`, `~/.oci/...`, etc.) or with special environment
variables (i.e.  `AWS_...`, `OCI_...`, etc.)

It is expected that each cloud provider's user/role will have been set up with
sufficient permission in order to accomplish the operations necessary to query,
import, and publish images; _it is highly recommended that no permissions are
granted beyond what is absolutely necessary_.

### The `build` Script

```
usage: build [-h] [--debug] [--clean] [--revise] {configs,local,import,publish}
         [--custom DIR [DIR ...]] [--skip KEY [KEY ...]] [--only KEY [KEY ...]]
         [--no-color] [--parallel N] [--vars FILE [FILE ...]]

build steps:
  configs                 resolve build configuration
  local                   build local images
  import                  import to cloud providers
  publish                 set permissions and publish to cloud regions

optional arguments:
  -h, --help              show this help message and exit
  --debug                 enable debug output (False)
  --clean                 start with a clean work environment (False)
  --revise                bump revisions if images already published (False)
  --custom DIR [DIR ...]  overlay custom directory in work environment
  --skip KEY [KEY ...]    skip variants with dimension key(s)
  --only KEY [KEY ...]    only variants with dimension key(s)
  --no-color              turn off Packer color output (False)
  --parallel N            build N images in parallel (1)
  --vars FILE [FILE ...]  supply Packer with additional -vars-file(s)
```

A `work/` directory will be created for its Python virtual environment, any
necessary Python libraries will be `pip install`ed, and `build` will execute
itself to ensure that it's running in the work environment.

This directory also contains `configs/` and `scripts/` subdirs (with custom
overlays), UEFI firmware for QEMU, Packer cache, the generated `configs.yaml`
and `actions.yaml` configs, and the `images/` tree for local image builds.

Use `--clean` if you want to re-overlay, re-download, re-generate, or rebuild
anything in the `work/` directory.  To redo the Python virtual environment,
simply remove the `work/` directory and its contents, and it will be recreated
the next time `build` is run.

### Build Steps

When executing `build` you also provide the target step you wish to reach.  For
example, if you only want to build local images, use `build local`.  Any
predecessor steps which haven't been done will also be executed -- that is,
`build local` also implies `build configs` if that step hasn't completed yet.

The **configs** step determines the latest stable Alpine Linux release, and
ensures that the `configs/` and `scripts/` overlays, UEFI firmware, and
`configs.yaml` exist.  This allows you to validate the generated build variant
configuration before attempting to build any images locally.

If `build` is moving on past **configs** to other steps, it will determine which
image variants to work on (based on `--skip` and `--only` values) and what
actions will be taken, based on existence of local/imported/published images, and
generate the `actions.yaml` file.  Providing the `--revise` flag allows you to
rebuild local images that were previously built, reimport unpublished images to
cloud providers, and bump the "revision" value of previously published images --
this is useful if published images require fixes but the Alpine release itself
isn't changing; published images are not removed (though they may be pruned once
their "end-of-life" date has passed).

At this point, `build` executes Packer, which is responsible for the remaining
**local**, **import**, and **publish** steps -- and also for parallelization, if
the `--parallel` argument is given.  Because build hardware varies, it is also
possible to tune a number of QEMU timeouts and memory requirements by providing
an HCL2 Packer Vars file and specifying `--vars <filename>` to override the
defaults in `alpine.pkr.hcl`.

### Packer and `alpine.pkr.hcl`

Packer loads and merges `actions.yaml` and `configs.yaml`, and iterates the
resulting object in order to determine what it should do with each image
variant configuration.

`alpine.pkr.hcl` defines two base `source` blocks --  `null` is used when an
image variant is already built locally and/or already imported to the
destination cloud provider; otherwise, the `qemu` source is used.

The `qemu` builder spins up a QEMU virtual machine with a blank virtual disk
attached, using the latest stable Alpine Linux Virtual ISO, brings up the VM's
network, enables the SSH daemon, and sets a random password for root.

If an image variant is to be **built locally**, the two dynamic provisioners copy
the required data for the setup scripts to the VM's `/tmp/` directory, and then
run those setup scripts.  It's these scripts that are ultimately responsible for
installing and configuring the desired image on the attached virtual disk.
When the setup scripts are complete, the virtual machine is shut down, and the
resulting local disk image can be found at
`work/images/<cloud>/<build-name>/image.qcow2`.

The dynamic post-processor uses the `cloud_helper.py` script to **import** a
local image to the cloud provider, and/or **publish** an imported image to the
cloud provider's destination regions, based on what actions are applicable for
that image variant.  When the **publish** step is reapplied to an
already-published image, the script ensures that images have been copied to all
destination regions (for example, if the cloud provider recently added a new
region), and that all launch permissions are set as expected.

### The `cloud_helper.py` Script

This script is only meant to be imported by `build` and called from Packer, and
provides a normalized cloud-agnostic way of doing common cloud operations --
getting details about a variant's latest imported image, importing new local
image to the cloud, removing a previouly imported (but unpublished) image so it
can be replaced, or publishing an imported image to destination regions.

----
## Build Configuration

The `build` script generates `work/configs.yaml` based on the contents of the
top-level config file, `work/configs/configs.conf`; normally this is a symlink to
`alpine.conf`, but can be overridden for custom builds.  All configs are
declared in [HOCON](https://github.com/lightbend/config/blob/master/HOCON.md)
format, which allows importing from other files, simple variable interpolation,
and easy merging of objects.  This flexibility helps keep configuration
[DRY](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself).

The top-level `build.conf` has three main blocks, `Default` (default/starting
values), `Dimensions` (with configs that apply in different circumstances), and
`Mandatory` (required/final values).  The configuration for these blocks are
merged in this exact order.

### Dimensions and Build Variants

Build variants _(I was watching Loki™ at the time...)_ are the sets of
dimensional "features" and related configuration details produced from a
Cartesian product across each of the dimensional keys.  Dimensional configs are
merged together in the order they appear in `build.conf`.

If two dimensional keys are incompatible (for example, **version/3.11** did not
yet support **arch/aarch64**), an `EXCLUDE` directive indicates that such a
variant is non-viable, and will be skipped.

Likewise, if one dimension's configuration depends on the value of a different
dimensional key, the `WHEN` directive will supply the conditional config
details when that other dimensional key is part of the variant.

Currently the base set of dimensions (and dimension keys) are...

**version** - current "release" value for each is autodetected, and always a
 component of an image's name
* **edge** ("release" value is the current UTC date)
* all *non-EOL* Alpine Linux versions

 **arch** - machine architecture
 * **x86_64** (aka "amd64")
 * **aarch64** (aka "arm64")

**firmware** - machine boot firmware
* **bios** (legacy BIOS)
* **uefi**

**bootstrap** - image instantiation bootstrap is provided by...
* **tiny** (tiny-cloud-boostrap)
* **cloudinit** (cloud-init)

**cloud** - cloud provider or platform
* **aws** - Amazone Web Services / EC2
* **oci** - Oracle Cloud Infrastructure _(WiP)_
* **gcp** - Google Cloud Platform _(WiP)_
* **azure** - Microsoft Azure _(WiP)_

...each dimension may (or may not) contribute to the image name or description,
if the dimensional key's config contributes to the `name` or `description`
array values.

### Customized Builds

_(TODO)_