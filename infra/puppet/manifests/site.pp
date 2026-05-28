# Orca Puppet site manifest.

node /^controller/ {
  include orca::roles::controller
}

node /^compute/ {
  include orca::roles::compute
}

node /^storage/ {
  include orca::roles::storage
}

node default {
  notify { 'No role matched for this node.': }
}
