import sys, os
from buildbot.buildslave import BuildSlave

class MySlaveBase(object):
	# true if this box is buildbot.net, and can build docs, etc.
	buildbot_net = False
	
	# true if this box should use a 'simple' factory, meaning no virtualenv
	# (basically good for windows)
	use_simple = False

	# true if this box can test the buildmaster and buildslave, respectively
	test_master = True
	test_slave = True

	# true if this slave should have a single-slave builder of its own
	run_single = True

	# true if this slave can contribute to the virtualenv-managed pool of
	# specific-configuration builders.  Specific supported python versions
	# are given, too
	run_config = False
	py24 = False
	py25 = False
	py26 = False
	py27 = False

	def extract_attrs(self, name, **kwargs):
		self.slavename = name
		remaining = {}
		for k in kwargs:
			if hasattr(self, k):
				setattr(self, k, kwargs[k])
			else:
				remaining[k] = kwargs[k]
		return remaining

	def get_pass(self, name):
		# get the password based on the name
		path = os.path.join(os.path.dirname(__file__), "%s.pass" % name)
		pw = open(path).read().strip()
		return pw

	def get_ec2_creds(self, name):
		path = os.path.join(os.path.dirname(__file__), "%s.ec2" % name)
		return open(path).read().strip().split(" ")

class MySlave(MySlaveBase, BuildSlave):
	def __init__(self, name, **kwargs):
		password = self.get_pass(name)
		kwargs = self.extract_attrs(name, **kwargs)
		BuildSlave.__init__(self, name, password, **kwargs)

#class MyEC2LatentBuildSlave(MySlaveBase, EC2LatentBuildSlave):
#	def __init__(self, name, ec2type, **kwargs):
#		password = self.get_pass(name)
#		identifier, secret_identifier = self.get_ec2_creds(name)
#		kwargs = self.extract_attrs(name, **kwargs)
#		EC2LatentBuildSlave.__init__(self, name, password, ec2type,
#			identifier=identifier, secret_identifier=secret_identifier, **kwargs)

slaves = [
	# Local
	MySlave('buildbot.net',
		buildbot_net=True,
		run_config=False,
		run_single=False,
		),

	# Steve 'Ashcrow' Milner
	MySlave('centos_5_python2_4',
		),

	# Dustin Sallings
	MySlave('minimata',
		),

 	# Dustin Mitchell
	MySlave('knuth.r.igoro.us',
		max_builds=2,
		run_single=False,
		run_config=True,
		py24=True,
		py25=True,
		py26=True,
		py27=True,
		),

	# maruel
	MySlave('xp-cygwin-1.7',
		max_builds=1,
		use_simple=True,
		test_master=False, # master doesn't work on cygwin
		),

	MySlave('win7-py26',
		max_builds=1,
		use_simple=True,
		),

	# Mozilla
	MySlave('cm-bbot-linux-001',
		max_builds=3,
		run_single=False,
		run_config=True,
		py24=True,
		py25=True,
		py26=True,
		py27=True,
		),

	MySlave('cm-bbot-linux-002',
		max_builds=3,
		run_single=False,
		run_config=True,
		py24=True,
		py25=True,
		py26=True,
		py27=True,
		),

	MySlave('cm-bbot-linux-003',
		max_builds=3,
		run_single=False,
		run_config=True,
		py24=True,
		py25=True,
		py26=True,
		py27=True,
		),

	MySlave('cm-bbot-xp-001',
		max_builds=1,
		use_simple=True,
		),

	MySlave('cm-bbot-xp-002',
		max_builds=1,
		use_simple=True,
		),

	MySlave('cm-bbot-xp-003',
		max_builds=1,
		use_simple=True,
		),

	# (EC2 - kept here as an indication of how to set it up)
#	MyEC2LatentBuildSlave('ec2slave', 'm1.small',
#		ami='ami-5a749c33',
#		keypair_name='buildbot-setup',
#		security_name='buildslaves',
#		),
]

# these are slaves that haven't been up and from whose owners I have not heard in a while
retired_slaves = [
	# Dustin Sallings
	MySlave('ubuntu810-64'),
	MySlave('minime',
		max_builds=1),
	MySlave('freebsd_7',
		max_builds=1),

	# "Jeremy C. Reed" <reed@reedmedia.net> (emailed 2/2/10)
	MySlave('reed.tx.reedmedia.net'),

	# Tim Hatch <tim@timhatch.com> (emailed 2/3/10)
	MySlave('automan'),
]

def get_slaves(*args, **kwargs):
	rv = {}
	for arg in args:
		rv.update(arg)
	for sl in slaves:
		for k in kwargs:
			if getattr(sl, k) != kwargs[k]:
				break
		else:
			rv[sl.slavename] = sl
	return rv

def names(slavedict):
	return slavedict.keys()
