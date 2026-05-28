class orca::roles::compute {
  package { ['nvidia-driver', 'docker', 'kubelet']:
    ensure => installed,
  }

  file { '/etc/orca/compute.conf':
    ensure  => file,
    content => "role=compute\nservices=camera-service,gps-service,ai-service\n",
    mode    => '0644',
  }
}
