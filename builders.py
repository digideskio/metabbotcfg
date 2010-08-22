import textwrap

from buildbot.process import factory
from buildbot.steps.source import Git
from buildbot.steps.shell import Compile, Test, ShellCommand
from buildbot.steps.transfer import FileDownload
from buildbot.steps.python_twisted import Trial

from metabbotcfg.slaves import slaves, get_slaves, names

builders = []

# some slaves just do "simple" builds: get the source, run the tests.  These are mostly
# windows machines where we don't have a lot of flexibility to mess around with virtualenv
def mksimplefactory(test_master=True):
	f = factory.BuildFactory()
	f.addSteps([
	Git(repourl='git://github.com/buildbot/buildbot.git', mode="copy"),
	#FileDownload(mastersrc="bbimport.py", slavedest="bbimport.py", flunkOnFailure=True),
	#ShellCommand(workdir="build/master", env={'PYTHONPATH' : '.;.'}, command=r"python ..\bbimport.py"),
	# use workdir instead of testpath because setuptools sticks its own eggs (including
	# the running version of buildbot) into sys.path *before* PYTHONPATH, but includes
	# "." in sys.path even before the eggs
	Trial(workdir="build/slave", testpath=".",
		env={ 'PYTHON_EGG_CACHE' : '../' },
		tests='buildslave.test',
		usePTY=False,
		name='test slave'),
	])
	if test_master:
		f.addStep(
		Trial(workdir="build/master", testpath=".",
			env={ 'PYTHON_EGG_CACHE' : '../' },
			tests='buildbot.test',
			usePTY=False,
			name='test master'),
		)
	return f

# much like simple buidlers, but it uses virtualenv
def mkfactory(twisted_version='twisted'):
	f = factory.BuildFactory()
	f.addSteps([
	Git(repourl='git://github.com/buildbot/buildbot.git', mode="copy"),
	FileDownload(mastersrc="virtualenv.py", slavedest="virtualenv.py", flunkOnFailure=True),
	ShellCommand(usePTY=False, command=textwrap.dedent("""
		test -z "$PYTHON" && PYTHON=python;
		$PYTHON virtualenv.py --distribute --no-site-packages ../sandbox || exit 1;
		PYTHON=../sandbox/bin/python; PATH=../sandbox/bin:$PATH; 
		export PYTHON_EGG_CACHE=$PWD/..;
		# and somehow the install_requires in setup.py doesn't always work:
		$PYTHON -c 'import json' 2>/dev/null || $PYTHON -c 'import simplejson' ||
					../sandbox/bin/easy_install simplejson || exit 1;
		$PYTHON -c 'import sqlite3, sys; assert sys.version_info >= (2,6)' 2>/dev/null || $PYTHON -c 'import pysqlite2.dbapi2' ||
					../sandbox/bin/easy_install pysqlite || exit 1;
		../sandbox/bin/easy_install %(twisted_version)s || exit 1;
		../sandbox/bin/easy_install jinja2 || exit 1;
		../sandbox/bin/easy_install mock || exit 1;
		../sandbox/bin/easy_install coverage || exit 1;
	""" % dict(twisted_version=twisted_version)),
		flunkOnFailure=True,
		haltOnFailure=True,
		name="virtualenv setup"),
	ShellCommand(usePTY=False, command=textwrap.dedent("""
		PYTHON=../sandbox/bin/python; PATH=../sandbox/bin:$PATH; 
		export PYTHON_EGG_CACHE=$PWD/..;
		$PYTHON -c 'import sys; print "Python:", sys.version; import twisted; print "Twisted:", twisted.version'
	"""),
		name="versions"),
	# see note above about workdir vs. testpath
	Trial(workdir="build/slave", testpath='.',
		env={ 'PYTHON_EGG_CACHE' : '../../' },
		tests='buildslave.test',
		trial="../../sandbox/bin/trial",
		usePTY=False,
		name='test slave'),
	Trial(workdir="build/master", testpath='.',
		env={ 'PYTHON_EGG_CACHE' : '../../' },
		tests='buildbot.test',
		trial="../../sandbox/bin/trial",
		usePTY=False,
		name='test master'),
	])
	return f


docs_factory = factory.BuildFactory()
docs_factory.addStep(Git(repourl='git://github.com/buildbot/buildbot.git', mode="update"))
docs_factory.addStep(ShellCommand(command="make docs", name="create docs"))
docs_factory.addStep(ShellCommand(command=textwrap.dedent("""\
		tar -C /home/buildbot/html/buildbot/docs -zvxf master/docs/docs.tgz latest/ &&
		chmod -R a+rx /home/buildbot/html/buildbot/docs/latest
		"""), name="docs to web", flunkOnFailure=True, haltOnFailure=True))
docs_factory.addStep(ShellCommand(command="make apidocs", name="create apidocs",
			flunkOnFailure=True, haltOnFailure=True))
docs_factory.addStep(ShellCommand(command=textwrap.dedent("""\
		tar -C /home/buildbot/html/buildbot/docs/latest -zxf apidocs/reference.tgz &&
		chmod -R a+rx /home/buildbot/html/buildbot/docs/latest/reference
		"""), name="api docs to web", flunkOnFailure=True, haltOnFailure=True))

#### docs

builders.append({
	'name' : 'docs',
	'slavenames' : names(get_slaves(buildbot_net=1)),
	'workdir' : 'docs',
	'factory' : docs_factory,
	'category' : 'docs' })

#### single-slave builders

for sl in get_slaves(run_single=True).values():
	if sl.use_simple:
		f = mksimplefactory(test_master=sl.test_master)
	else:
		f = mkfactory()
	builders.append({
		'name' : 'slave-%s' % sl.slavename,
		'slavenames' : [ sl.slavename ],
		'workdir' : 'slave-%s' % sl.slavename,
		'factory' : f,
		'category' : 'slave' })

#### config builders

twisted_versions = dict(
	tw0810='Twisted==8.1.0',
	tw0820='Twisted==8.2.0',
	tw0900='Twisted==9.0.0',
	tw1000='Twisted==10.0.0',
	tw1010='Twisted==10.1.0',
)

config_slaves = names(get_slaves(run_config=True))

for tw, twisted_version in twisted_versions.items():
	f = mkfactory(twisted_version=twisted_version)
	name = "%s-%s" % ('py26', tw)
	builders.append({
		'name' : name,
		'slavenames' : config_slaves,
		'factory' : f,
		'category' : 'config' })
