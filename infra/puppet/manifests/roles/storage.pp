class smartcito::roles::storage {
  include smartcito::database

  file { '/etc/smartcito/storage.conf':
    ensure  => file,
    content => "role=storage\nservices=postgres,object-store\n",
    mode    => '0644',
  }
}
