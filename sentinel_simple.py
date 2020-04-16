import sentinel
# Look at: https://pypi.org/project/sentinel/

# Creates simple sentinel objects which are the only instance of their own anonymous class.
# As a singleton, there is a guarantee that there will only ever be one instance:
# they can be safely used with pickle and cPickle alike,
# as well as being able to be used properly with copy.deepcopy().
# In addition, a self-documenting __repr__ is provided for free!

# All that’s needed to create a sentinel is its name:
Nothing = sentinel.create('Nothing')
print(Nothing)
print('-----------------------------------')

# This by itself is useful when other objects such as None, False, 0, -1, etc. are entirely valid values.
# For example, setting default values when all other values are valid with: dict.setdefault():
MissingEntry = sentinel.create('MissingEntry')

d = {'stdout': None, 'stdin': 0, 'EOF': -1}
print([d.setdefault(key, MissingEntry) for key in ('stdin', 'stdout', 'stderr')])
print('-----------------------------------')

# Alternatively, using dict.get() when fetching values:
d = {'stdout': None, 'stdin': 0, 'EOF': -1}
print(d.get('stdout', MissingEntry))
print(d.get('stdin', MissingEntry))
print(d.get('stderr', MissingEntry))
print('-----------------------------------')
