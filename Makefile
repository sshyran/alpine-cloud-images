# vim: ts=8 noet:

NVME_SCRIPTS := $(subst scripts/,build/,$(wildcard scripts/nvme/*))
CORE_PROFILES := $(wildcard profiles/*/*)
TARGET_PROFILES := $(wildcard profiles/*.conf)

PROFILE :=
BUILD :=
BUILDS := $(BUILD)
LEVEL :=

# by default, use the 'packer' in the path
PACKER := packer
export PACKER


check_defined = \
    $(strip $(foreach 1,$1, \
        $(call __check_defined,$1,$(strip $(value 2)))))
__check_defined = \
    $(if $(value $1),, \
        $(error Undefined $1$(if $2, ($2))$(if $(value @), \
                required by target `$@')))


.PHONY: amis prune release-readme clean

amis: build/packer.json build/profile/$(PROFILE) build build/setup-ami $(NVME_SCRIPTS)
	@:$(call check_defined, PROFILE, target profile name)
	build/builder make-amis $(PROFILE) $(BUILDS)

prune: build
	@:$(call check_defined, LEVEL, pruning level)
	@:$(call check_defined, PROFILE, target profile name)
	build/builder prune-amis $(LEVEL) $(PROFILE) $(BUILD)

release-readme: releases/README.md
releases/README.md: build
	@:$(call check_defined, PROFILE, target profile name)
	@:$(call require_var, PROFILE)
	build/builder gen-release-readme $(PROFILE)

build:
	python3 -m venv build
	[ -d build/profile ] || mkdir -p build/profile
	build/bin/pip install -U pip pyhocon pyyaml boto3

	echo -e "#!/bin/sh\n$$(pwd)/build/bin/python scripts/builder.py \$$@" > $@
	chmod +x $@

build/packer.json: packer.conf build
	build/builder convert-packer-config

.PHONY: build/profile/$(PROFILE)
build/profile/$(PROFILE): build $(CORE_PROFILES) $(TARGET_PROFILES)
	@:$(call check_defined, PROFILE, target profile name)
	build/builder resolve-profile $(PROFILE)

clean:
	rm -rf build
