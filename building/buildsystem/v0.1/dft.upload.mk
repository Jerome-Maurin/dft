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
# Copyright 2017 DFT project (http://www.debianfirmwaretoolkit.org).
# All rights reserved. Use is subject to license terms.
#
#
# Even if this work is a complete rewrite, it is originally derivated work based
# upon mGAR build system from OpenCSW project (http://www.opencsw.org).
#
# Copyright 2001 Nick Moffitt: GAR ports system
# Copyright 2006 Cory Omand: Scripts and add-on make modules, except where otherwise noted.
# Copyright 2008 Dagobert Michelsen (OpenCSW): Enhancements to the CSW GAR system
# Copyright 2008-2013 Open Community Software Association: Packaging content
#
#
# Contributors list :
#
#    William Bonnet     wllmbnnt@gmail.com, wbonnet@theitmakers.com
#
#

# ------------------------------------------------------------------------------
#
# Execute the upload target script
#

do-upload :
	@if test -f $(COOKIE_DIR)/do-upload ; then \
		true ; \
	else \
		echo "        running upload"  ; \
	 	if [ ! "" = "$(DFT_DEB_UPLOAD_PATH)" ] && [ ! "" = "$(DFT_DEB_UPLOAD_SERVER)" ] ; then \
			scp $(abspath $(PACKAGE_DIR))/*.deb $(DFT_DEB_UPLOAD_SERVER):$(DFT_DEB_UPLOAD_PATH) ; \
	 	else \
	 	    if [ "" = "$(DFT_DEB_UPLOAD_SERVER)" ] ; then \
			    echo "        Variable DFT_DEB_UPLOAD_SERVER is not set, please define it your shell environment."  ; \
			else \
			    echo "        DFT_DEB_UPLOAD_SERVER = $(DFT_DEB_UPLOAD_SERVER)."  ; \
			fi ; \
	 	    if [ "" = "$(DFT_DEB_UPLOAD_PATH)" ] ; then \
			    echo "        Variable DFT_DEB_UPLOAD_PATH is not set, please define it your shell environment."  ; \
			else \
			    echo "        DFT_DEB_UPLOAD_PATH = $(DFT_DEB_UPLOAD_PATH)."  ; \
			fi ; \
			false ; \
		fi ; \
	fi ;
	@$(TARGET_DONE)

do-reupload :
	@if test -f $(COOKIE_DIR)/do-upload ; then \
		rm -f $(COOKIE_DIR)/do-upload ; \
		rm -fr $(abspath $(INSTALL_DIR)) ; \
	fi ;
	$(TARGET_DONE)

