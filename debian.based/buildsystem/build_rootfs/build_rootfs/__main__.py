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
# Copyright 2014 LFFS project (http://www.linuxfirmwarefromscratch.org).  
# All rights reserved. Use is subject to license terms.
#
#
# Contributors list :
#
#    William Bonnet 	wllmbnnt@gmail.com
#
#
import cli
import sys


def main():
	"""
	Main entry point for the script. Create a parser, processthe command line, 
	and run it
	"""
	parser = cli.Cli()
	parser.parse(sys.argv[1:])
	return parser.run()
	

    # That's all folks. All the processing has bee done in the run
#
# Check this is code is called from the __main__
#
if __name__ == '__main__':
    sys.exit(main())	