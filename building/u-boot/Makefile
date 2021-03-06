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
# Copyright 2018 DFT project (http://www.debianfirmwaretoolkit.org).
# All rights reserved. Use is subject to license terms.
#
#
# Contributors list :
#
#    William Bonnet     wllmbnnt@gmail.com, wbonnet@theitmakers.com
#
#

# Defines the software version
NEW_BOARD = $*

# Create a new board entry in the repository
new-board-%:
	@if [ -d "./$(NEW_BOARD)" ] ; then \
		echo ". Directory ./($(NEW_BOARD) already exist. Doing nothing..." ; \
	else  \
		echo ". Creating the directory storing the new board kernerls (./$(NEW_BOARD))" ; \
		mkdir -p $(NEW_BOARD) ; \
		mkdir -p $(NEW_BOARD)/files ; \
		echo ". Copying install procedure template" ; \
		cp ../buildsystem/current/templates/u-boot.install.template $(NEW_BOARD)/files/install.u-boot.$(NEW_BOARD).md ; \
		sed -i -e "s/__BOARD_NAME__/$(NEW_BOARD)/g" $(NEW_BOARD)/files/install.u-boot.$(NEW_BOARD).md ; \
		echo ". Copying the Makefile template to the new board directory" ; \
		ln -s ../../buildsystem/current/templates/board-u-boot.makefile $(NEW_BOARD)/Makefile ; \
		echo ". Copying board specific Makefile template" ; \
		cp ../buildsystem/current/templates/board-specific.u-boot.makefile $(NEW_BOARD)/$(NEW_BOARD).mk ; \
		sed -i -e "s/__BOARD_NAME__/$(NEW_BOARD)/g" $(NEW_BOARD)/$(NEW_BOARD).mk ; \
		ln -s $(NEW_BOARD).mk $(NEW_BOARD)/board.mk; \
		echo ". Adding ./$(NEW_BOARD) to git" ; \
		git add $(NEW_BOARD) ; \
	fi ;

# Catch all target. Call the same targets in each subfolder
%:
	@for i in $(filter-out $(FILTER_DIRS),$(wildcard */)) ; do \
		$(MAKE) -C $$i $* || exit 1 ; \
	done

# ------------------------------------------------------------------------------
#
# Target that prints the help
#
help :
	@echo "Available targets are :"
	@echo '   new-board-[BOARD-NAME]  Create a new board entry. ex: make new-board-orangepi-zero'
	@echo '                           This target create a new directory named after the BOARD-NAME'
	@echo '                           It will generate the Makefile and a blank config file.'
	@echo '                           After creation you have to set the architecture in board.mk'
	@echo '                           and fill config content.'
	@echo
	@echo '                           Do not forget to add bsp definition and bootscripts to DFT tree'
