# Alpine Linux EC2 AMIs

**These are not official AWS or Alpine images.  They are community built and
supported.**

These AMIs should work with most EC2 features such as Elastic Network Adapters
and NVMe EBS volumes.  If you find any problems launching them on current
generation instances, please open an [issue](https://github.com/mcrute/alpine-ec2-ami/issues)
and include as much detailed information as possible.

During the *first boot* of instances created with these AMIs, the lightweight
[tiny-ec2-bootstrap](https://github.com/mcrute/tiny-ec2-bootstrap) init
script...
- sets the instance's hostname,
- installs the SSH authorized_keys for the 'alpine' user,
- disables 'root' and 'alpine' users' passwords,
- expands the root partition to use all available EBS volume space,
- and executes a "user data" script (must be a shell script that starts with `#!`)

If you launch these AMIs to build other images (via [Packer](https://packer.io),
etc.), don't forget to remove `/var/lib/cloud/.bootstrap-complete` --
otherwise, instances launched from those second-generation AMIs will not run
`tiny-ec2-bootstrap` on their first boot.

The more popular [cloud-init](https://cloudinit.readthedocs.io/en/latest/)
is currently not supported on Alpine Linux.  If `cloud-init` support is
important to you, please open an [issue](https://github.com/mcrute/alpine-ec2-ami/issues).

## AMIs

### Alpine Linux 3.10.1 (2019-07-26)
<details><summary><i>click to show/hide</i></summary><p>

| Region | alpine-ami-3.10.1-x86_64-r1 |
| ------ | --- |
| ap-northeast-1 | [ami-0adeee26a46805278](https://ap-northeast-1.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-0adeee26a46805278) ([launch](https://ap-northeast-1.console.aws.amazon.com/ec2/home#launchAmi=ami-0adeee26a46805278)) |
| ap-northeast-2 | [ami-06637cd011ec49efa](https://ap-northeast-2.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-06637cd011ec49efa) ([launch](https://ap-northeast-2.console.aws.amazon.com/ec2/home#launchAmi=ami-06637cd011ec49efa)) |
| ap-south-1 | [ami-09e1bd549945283a2](https://ap-south-1.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-09e1bd549945283a2) ([launch](https://ap-south-1.console.aws.amazon.com/ec2/home#launchAmi=ami-09e1bd549945283a2)) |
| ap-southeast-1 | [ami-081de8e0c4d9e28e5](https://ap-southeast-1.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-081de8e0c4d9e28e5) ([launch](https://ap-southeast-1.console.aws.amazon.com/ec2/home#launchAmi=ami-081de8e0c4d9e28e5)) |
| ap-southeast-2 | [ami-0e2c774fdc1d38ba1](https://ap-southeast-2.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-0e2c774fdc1d38ba1) ([launch](https://ap-southeast-2.console.aws.amazon.com/ec2/home#launchAmi=ami-0e2c774fdc1d38ba1)) |
| ca-central-1 | [ami-02fed61c453469d90](https://ca-central-1.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-02fed61c453469d90) ([launch](https://ca-central-1.console.aws.amazon.com/ec2/home#launchAmi=ami-02fed61c453469d90)) |
| eu-central-1 | [ami-0659cf3939d5818e6](https://eu-central-1.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-0659cf3939d5818e6) ([launch](https://eu-central-1.console.aws.amazon.com/ec2/home#launchAmi=ami-0659cf3939d5818e6)) |
| eu-north-1 | [ami-0859a31a742c902ed](https://eu-north-1.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-0859a31a742c902ed) ([launch](https://eu-north-1.console.aws.amazon.com/ec2/home#launchAmi=ami-0859a31a742c902ed)) |
| eu-west-1 | [ami-00fcd74ef57d7f27d](https://eu-west-1.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-00fcd74ef57d7f27d) ([launch](https://eu-west-1.console.aws.amazon.com/ec2/home#launchAmi=ami-00fcd74ef57d7f27d)) |
| eu-west-2 | [ami-06e36c52d4a7c245a](https://eu-west-2.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-06e36c52d4a7c245a) ([launch](https://eu-west-2.console.aws.amazon.com/ec2/home#launchAmi=ami-06e36c52d4a7c245a)) |
| eu-west-3 | [ami-06a5559ce996d5bac](https://eu-west-3.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-06a5559ce996d5bac) ([launch](https://eu-west-3.console.aws.amazon.com/ec2/home#launchAmi=ami-06a5559ce996d5bac)) |
| sa-east-1 | [ami-0087fd3ce3d62d34d](https://sa-east-1.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-0087fd3ce3d62d34d) ([launch](https://sa-east-1.console.aws.amazon.com/ec2/home#launchAmi=ami-0087fd3ce3d62d34d)) |
| us-east-1 | [ami-063929a9ea787ced6](https://us-east-1.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-063929a9ea787ced6) ([launch](https://us-east-1.console.aws.amazon.com/ec2/home#launchAmi=ami-063929a9ea787ced6)) |
| us-east-2 | [ami-0a5ef71ab2deee8fd](https://us-east-2.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-0a5ef71ab2deee8fd) ([launch](https://us-east-2.console.aws.amazon.com/ec2/home#launchAmi=ami-0a5ef71ab2deee8fd)) |
| us-west-1 | [ami-04165aa967c5fb241](https://us-west-1.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-04165aa967c5fb241) ([launch](https://us-west-1.console.aws.amazon.com/ec2/home#launchAmi=ami-04165aa967c5fb241)) |
| us-west-2 | [ami-08147c2b1a80b44c4](https://us-west-2.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-08147c2b1a80b44c4) ([launch](https://us-west-2.console.aws.amazon.com/ec2/home#launchAmi=ami-08147c2b1a80b44c4)) |

</p></details>

### Alpine Linux 3.9.4 (2019-07-26)
<details><summary><i>click to show/hide</i></summary><p>

| Region | alpine-ami-3.9.4-x86_64-r1 |
| ------ | --- |
| ap-northeast-1 | [ami-0d12649cf98b9c29b](https://ap-northeast-1.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-0d12649cf98b9c29b) ([launch](https://ap-northeast-1.console.aws.amazon.com/ec2/home#launchAmi=ami-0d12649cf98b9c29b)) |
| ap-northeast-2 | [ami-004372232cf1a20ac](https://ap-northeast-2.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-004372232cf1a20ac) ([launch](https://ap-northeast-2.console.aws.amazon.com/ec2/home#launchAmi=ami-004372232cf1a20ac)) |
| ap-south-1 | [ami-091de53a3582f2779](https://ap-south-1.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-091de53a3582f2779) ([launch](https://ap-south-1.console.aws.amazon.com/ec2/home#launchAmi=ami-091de53a3582f2779)) |
| ap-southeast-1 | [ami-07f6f363322b884d5](https://ap-southeast-1.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-07f6f363322b884d5) ([launch](https://ap-southeast-1.console.aws.amazon.com/ec2/home#launchAmi=ami-07f6f363322b884d5)) |
| ap-southeast-2 | [ami-0eeff0d7c1943665c](https://ap-southeast-2.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-0eeff0d7c1943665c) ([launch](https://ap-southeast-2.console.aws.amazon.com/ec2/home#launchAmi=ami-0eeff0d7c1943665c)) |
| ca-central-1 | [ami-011ad5e9b2fcfa1d5](https://ca-central-1.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-011ad5e9b2fcfa1d5) ([launch](https://ca-central-1.console.aws.amazon.com/ec2/home#launchAmi=ami-011ad5e9b2fcfa1d5)) |
| eu-central-1 | [ami-0d4f6bb2a4f857256](https://eu-central-1.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-0d4f6bb2a4f857256) ([launch](https://eu-central-1.console.aws.amazon.com/ec2/home#launchAmi=ami-0d4f6bb2a4f857256)) |
| eu-north-1 | [ami-01c04b1d21717da2d](https://eu-north-1.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-01c04b1d21717da2d) ([launch](https://eu-north-1.console.aws.amazon.com/ec2/home#launchAmi=ami-01c04b1d21717da2d)) |
| eu-west-1 | [ami-0c9ac6e4570bad5c1](https://eu-west-1.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-0c9ac6e4570bad5c1) ([launch](https://eu-west-1.console.aws.amazon.com/ec2/home#launchAmi=ami-0c9ac6e4570bad5c1)) |
| eu-west-2 | [ami-0bc07c10c240525e4](https://eu-west-2.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-0bc07c10c240525e4) ([launch](https://eu-west-2.console.aws.amazon.com/ec2/home#launchAmi=ami-0bc07c10c240525e4)) |
| eu-west-3 | [ami-0ebda60768a596a7f](https://eu-west-3.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-0ebda60768a596a7f) ([launch](https://eu-west-3.console.aws.amazon.com/ec2/home#launchAmi=ami-0ebda60768a596a7f)) |
| sa-east-1 | [ami-0a2d4fb282401447a](https://sa-east-1.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-0a2d4fb282401447a) ([launch](https://sa-east-1.console.aws.amazon.com/ec2/home#launchAmi=ami-0a2d4fb282401447a)) |
| us-east-1 | [ami-0a8b8edcf88c2e496](https://us-east-1.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-0a8b8edcf88c2e496) ([launch](https://us-east-1.console.aws.amazon.com/ec2/home#launchAmi=ami-0a8b8edcf88c2e496)) |
| us-east-2 | [ami-030ce78952c4c097c](https://us-east-2.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-030ce78952c4c097c) ([launch](https://us-east-2.console.aws.amazon.com/ec2/home#launchAmi=ami-030ce78952c4c097c)) |
| us-west-1 | [ami-0e27a7d83365f16be](https://us-west-1.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-0e27a7d83365f16be) ([launch](https://us-west-1.console.aws.amazon.com/ec2/home#launchAmi=ami-0e27a7d83365f16be)) |
| us-west-2 | [ami-07f10e32e0621a4eb](https://us-west-2.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-07f10e32e0621a4eb) ([launch](https://us-west-2.console.aws.amazon.com/ec2/home#launchAmi=ami-07f10e32e0621a4eb)) |

</p></details>

### Alpine Linux Edge (2019-07-27)
<details><summary><i>click to show/hide</i></summary><p>

| Region | alpine-ami-edge-x86_64-20190727002240 |
| ------ | --- |
| ap-northeast-1 | [ami-0c4b05d8ac25f8333](https://ap-northeast-1.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-0c4b05d8ac25f8333) ([launch](https://ap-northeast-1.console.aws.amazon.com/ec2/home#launchAmi=ami-0c4b05d8ac25f8333)) |
| ap-northeast-2 | [ami-0b7287e80730d405a](https://ap-northeast-2.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-0b7287e80730d405a) ([launch](https://ap-northeast-2.console.aws.amazon.com/ec2/home#launchAmi=ami-0b7287e80730d405a)) |
| ap-south-1 | [ami-0668e96d07b4c5cd0](https://ap-south-1.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-0668e96d07b4c5cd0) ([launch](https://ap-south-1.console.aws.amazon.com/ec2/home#launchAmi=ami-0668e96d07b4c5cd0)) |
| ap-southeast-1 | [ami-051fa7a03bd74b58d](https://ap-southeast-1.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-051fa7a03bd74b58d) ([launch](https://ap-southeast-1.console.aws.amazon.com/ec2/home#launchAmi=ami-051fa7a03bd74b58d)) |
| ap-southeast-2 | [ami-0d3bd765176e0489b](https://ap-southeast-2.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-0d3bd765176e0489b) ([launch](https://ap-southeast-2.console.aws.amazon.com/ec2/home#launchAmi=ami-0d3bd765176e0489b)) |
| ca-central-1 | [ami-001b638763735e3d7](https://ca-central-1.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-001b638763735e3d7) ([launch](https://ca-central-1.console.aws.amazon.com/ec2/home#launchAmi=ami-001b638763735e3d7)) |
| eu-central-1 | [ami-06638105f6e72062b](https://eu-central-1.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-06638105f6e72062b) ([launch](https://eu-central-1.console.aws.amazon.com/ec2/home#launchAmi=ami-06638105f6e72062b)) |
| eu-north-1 | [ami-02652b5900d1d6b2d](https://eu-north-1.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-02652b5900d1d6b2d) ([launch](https://eu-north-1.console.aws.amazon.com/ec2/home#launchAmi=ami-02652b5900d1d6b2d)) |
| eu-west-1 | [ami-064c071f028660b8e](https://eu-west-1.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-064c071f028660b8e) ([launch](https://eu-west-1.console.aws.amazon.com/ec2/home#launchAmi=ami-064c071f028660b8e)) |
| eu-west-2 | [ami-01b93011a9e8fb2f9](https://eu-west-2.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-01b93011a9e8fb2f9) ([launch](https://eu-west-2.console.aws.amazon.com/ec2/home#launchAmi=ami-01b93011a9e8fb2f9)) |
| eu-west-3 | [ami-0dc28d63cbf57a03f](https://eu-west-3.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-0dc28d63cbf57a03f) ([launch](https://eu-west-3.console.aws.amazon.com/ec2/home#launchAmi=ami-0dc28d63cbf57a03f)) |
| sa-east-1 | [ami-08e65c7559326c353](https://sa-east-1.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-08e65c7559326c353) ([launch](https://sa-east-1.console.aws.amazon.com/ec2/home#launchAmi=ami-08e65c7559326c353)) |
| us-east-1 | [ami-042fef15f7a3cecb8](https://us-east-1.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-042fef15f7a3cecb8) ([launch](https://us-east-1.console.aws.amazon.com/ec2/home#launchAmi=ami-042fef15f7a3cecb8)) |
| us-east-2 | [ami-08edf1150ecd85e18](https://us-east-2.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-08edf1150ecd85e18) ([launch](https://us-east-2.console.aws.amazon.com/ec2/home#launchAmi=ami-08edf1150ecd85e18)) |
| us-west-1 | [ami-002a540d70018332e](https://us-west-1.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-002a540d70018332e) ([launch](https://us-west-1.console.aws.amazon.com/ec2/home#launchAmi=ami-002a540d70018332e)) |
| us-west-2 | [ami-04e6cbf239d3d6723](https://us-west-2.console.aws.amazon.com/ec2/home#Images:visibility=public-images;imageId=ami-04e6cbf239d3d6723) ([launch](https://us-west-2.console.aws.amazon.com/ec2/home#launchAmi=ami-04e6cbf239d3d6723)) |

</p></details>
