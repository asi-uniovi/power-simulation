# Copyright 2019 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

.PHONY: init test lint cleanall clean cleanlogs cleanpyc

init:
	pipenv install --dev

test:
	pipenv run pytest
	pipenv run ./main.py --config config/test.ini

lint:
	pipenv run flake8

cleanall: clean cleanlogs cleanpyc

clean:
	rm -f *.db
	rm -f *.png

cleanlogs:
	rm -f *.log

cleanpyc:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
