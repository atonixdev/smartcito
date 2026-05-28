class orca::database {
  package { 'postgresql':
    ensure => installed,
  }

  service { 'postgresql':
    ensure => running,
    enable => true,
    require => Package['postgresql'],
  }

  file { '/etc/orca/database.conf':
    ensure  => file,
    content => "database=orca\nrole=storage\n",
    mode    => '0644',
  }
}
