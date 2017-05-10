.PHONY: cleanall clean cleanlogs cleanpyc

pylint:
	-find . -name '*.py' | xargs pylint --jobs=2 --rcfile=.pylintrc --reports=n | tee pylint.log

cleanall: clean cleanlogs cleanpyc

clean:
	rm -f *.db
	rm -f *.png

cleanlogs:
	rm -f pylint.log

cleanpyc:
	find . -name '*.pyc' -delete
