class smartcito::roles::controller {
  package { ['docker', 'kubeadm', 'kubectl']:
    ensure => installed,
  }

  file { '/etc/smartcito/controller.conf':
    ensure  => file,
    content => "role=controller\nservices=api-gateway,security-service\n",
    mode    => '0644',
  }
}
