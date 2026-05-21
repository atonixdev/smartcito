# SmartCito Puppet site manifest.

node /^controller/ {
  include smartcito::roles::controller
}

node /^compute/ {
  include smartcito::roles::compute
}

node /^storage/ {
  include smartcito::roles::storage
}

node default {
  notify { 'No role matched for this node.': }
}
