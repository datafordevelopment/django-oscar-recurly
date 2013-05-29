# These targets are not files
.PHONY: install coverage travis

install:
	pip install -r requirements.txt --use-mirrors
	python setup.py develop

coverage:
	coverage run ./runtests.py --with-xunit
	coverage xml -i
    
# It is important that this target only depends on install
# (instead of upgrade) because we install Django in the .travis.yml
# and upgrade would overwrite it.  We also build the sandbox as part of this target
# to catch any errors that might come from that build process.
travis: install coverage