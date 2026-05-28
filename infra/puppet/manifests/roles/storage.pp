class orca::roles::storage {
  include orca::database

  file { '/etc/orca/storage.conf':
    ensure  => file,
    content => "role=storage\nservices=postgres,object-store\n",
    mode    => '0644',
  }
}
