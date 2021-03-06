# vim: ft=make ts=4 sw=4 noet
#
# The contents of this file are subject to the Apache 2.0 license you may not
# use this file except in compliance with the License.
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
#
# Copyright 2016 DFT project (http://www.debianfirmwaretoolkit.org).
# All rights reserved. Use is subject to license terms.
#
#
# Contributors list :
#
#    William Bonnet     wllmbnnt@gmail.com, wbonnet@theitmakers.com
#
#

# Include the board definition
include board.mk

# Defines the software version
NEW_VERSION  = $*
PACAKGE_DATE = $(shell LC_ALL=C date +"%a, %d %b %Y %T %z")
PACAKGE_DATE = $(shell date )
FILTER_DIRS  = config_files/
HOST_ARCH    = $(shell uname -m)

# ------------------------------------------------------------------------------
#
# Targets not associated with a file (aka PHONY)
#
.PHONY: help

# Create a new board entry in the repository
new-version-%:
	@if [ -d "./$(NEW_VERSION)" ] ; then \
		echo ". Directory ./($(NEW_VERSION) already exist. Doing nothing..." ; \
	else  \
		echo ". Creating the directory structure (./$(NEW_VERSION))" ; \
		mkdir -p $(NEW_VERSION) ; \
		cp -f ../../buildsystem/current/templates/kernel-version.makefile $(NEW_VERSION)/Makefile ; \
		ln -s ../../../buildsystem/current $(NEW_VERSION)/buildsystem ; \
		mkdir -p $(NEW_VERSION)/files ; \
		ln -s ../../config_files/default.$(BOARD_NAME).config $(NEW_VERSION)/files/$(BOARD_NAME).config ; \
		mkdir -p $(NEW_VERSION)/patches ; \
		touch $(NEW_VERSION)/patches/.gitkeep ; \
		echo "work-$(BOARD_NAME)/" > $(NEW_VERSION)/.gitignore ; \
		sed -i -e "s/__KERNEL_VERSION__/$(NEW_VERSION)/g" $(NEW_VERSION)/Makefile ; \
		cp -fr ../../buildsystem/current/templates/debian.kernel $(NEW_VERSION)/debian; \
		cd $(NEW_VERSION)/debian ; \
		mv linux-image.postinst  linux-image-$(BOARD_NAME).postinst ; \
		mv linux-image.postrm    linux-image-$(BOARD_NAME).postrm ; \
		mv linux-image.preinst   linux-image-$(BOARD_NAME).preinst ; \
		mv linux-image.prerm     linux-image-$(BOARD_NAME).prerm ; \
		mv linux-image.install   linux-image-$(BOARD_NAME).install ; \
		mv linux-headers.install linux-headers-$(BOARD_NAME).install ; \
		cd ../.. ; \
		find $(NEW_VERSION)/debian -type f | xargs sed -i -e "s/__KERNEL_VERSION__/$(NEW_VERSION)/g" \
	                                         -e "s/__BOARD_NAME__/$(BOARD_NAME)/g" \
	                                         -e "s/__DATE__/$(shell LC_ALL=C date +"%a, %d %b %Y %T %z")/g" ; \
        if [ "${DEBEMAIL}" = "" ] ; then \
			find $(NEW_VERSION)/debian -type f | xargs sed -i -e "s/__MAINTAINER_EMAIL__/unknown/g" ; \
		else \
			find $(NEW_VERSION)/debian -type f | xargs sed -i -e "s/__MAINTAINER_EMAIL__/${DEBEMAIL}/g" ; \
		fi ; \
		if [ "${DEBFULLNAME}" = "" ] ; then \
			find $(NEW_VERSION)/debian -type f | xargs sed -i -e "s/__MAINTAINER_NAME__/unknown/g" ; \
		else \
			find $(NEW_VERSION)/debian -type f | xargs sed -i -e "s/__MAINTAINER_NAME__/${DEBFULLNAME}/g" ; \
		fi ; \
		git add $(NEW_VERSION) ; \
	fi ;

# Catch all target. Call the same targets in each subfolder
%:
	@for i in $(filter-out $(FILTER_DIRS),$(wildcard */)) ; do \
		$(MAKE) -C $$i $* || exit 1 ; \
	done

# Catch all target. Call the same targets in each subfolder
%:
	@if [ ! "x$(HOST_ARCH)" = "x$(BOARD_ARCH)" ] ; \
	then \
	    echo "Board is $(BOARD_ARCH) and i run on $(HOST_ARCH). Skipping recursive target call..." ; \
	    true ; \
	else \
		for i in $(filter-out $(FILTER_DIRS),$(wildcard */)) ; do \
			$(MAKE) -C $$i $* || exit 1 ; \
		done \
	fi


# ------------------------------------------------------------------------------
#
# Target that prints the help
#
help :
	@echo "Available targets are :"
	@echo '   new-version-[VERSION]   Create a new version entry. ex: make new-version-4.15.3'
	@echo '                           This target will create a subdirectory name VERSION, containing'
	@echo '                           the Makefile and all the files needed to fetch and build given'
	@echo '                           version. It also instanciate Debian package template'
