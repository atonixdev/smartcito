class smartcito::database {
  package { 'postgresql':
    ensure => installed,
  }

  service { 'postgresql':
    ensure => running,
    enable => true,
    require => Package['postgresql'],
  }

  file { '/etc/smartcito/database.conf':
    ensure  => file,
    content => "database=smartcito\nrole=storage\n",
    mode    => '0644',
  }
}
