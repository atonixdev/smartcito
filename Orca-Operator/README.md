# orca-operator

## Description
Orca Operator is the Kubernetes operator scaffold for ORCA control-plane
resources. It manages the `Orca` custom resource and is intended to evolve into
the cluster-native deployment surface for ORCA services.

## Getting Started

### Prerequisites
- go version v1.24.0+
- docker version 17.03+.
- kubectl version v1.11.3+.
- Access to a Kubernetes v1.11.3+ cluster.
- `kind` installed if you want to run the e2e suite.

### Local Development

Generate API helpers and manifests:

```sh
make generate
make manifests
```

Compile the operator locally:

```sh
go build ./...
```

Run the controller test suite with envtest assets bootstrapped automatically:

```sh
make test
```

Notes:

- `go test ./...` will skip the controller suite if envtest assets have not been downloaded yet.
- The e2e suite requires `kind` and a working Kubernetes CLI context.

### To Deploy on the cluster
**Build and push your image to the location specified by `IMG`:**

```sh
make docker-build docker-push IMG=<some-registry>/orca-operator:tag
```

Default local image naming now uses `atonixdev/orca-operator:0.0.1`.

If you want to use the project defaults directly:

```sh
make docker-build
make docker-push
```

**NOTE:** This image ought to be published in the personal registry you specified. 
And it is required to have access to pull the image from the working environment. 
Make sure you have the proper permission to the registry if the above commands don’t work.

If Docker push keeps retrying, that is usually a registry/auth issue rather than an operator build issue. Use a registry you actually control, for example after `docker login`, or override `IMG=` with your preferred registry path.

### OLM

Do not run `operator-sdk olm install` repeatedly on a cluster that already has OLM.

Check status first:

```sh
operator-sdk olm status
```

If the `olm` and `operators` namespaces and OLM CRDs already exist, reuse that installation and continue with bundle or deployment work. Only uninstall and reinstall OLM if you intentionally want to replace the cluster's current OLM installation.

**Install the CRDs into the cluster:**

```sh
make install
```

**Deploy the Manager to the cluster with the image specified by `IMG`:**

```sh
make deploy IMG=<some-registry>/orca-operator:tag
```

> **NOTE**: If you encounter RBAC errors, you may need to grant yourself cluster-admin 
privileges or be logged in as admin.

**Create instances of your solution**
You can apply the samples (examples) from the config/sample:

```sh
kubectl apply -k config/samples/
```

>**NOTE**: Ensure that the samples has default values to test it out.

### To Uninstall
**Delete the instances (CRs) from the cluster:**

```sh
kubectl delete -k config/samples/
```

**Delete the APIs(CRDs) from the cluster:**

```sh
make uninstall
```

**UnDeploy the controller from the cluster:**

```sh
make undeploy
```

## Contributing
Use the generated API and controller scaffolding as the base for ORCA-specific
reconciliation logic. Keep CRD updates paired with regenerated manifests.

**NOTE:** Run `make help` for more information on all potential `make` targets

More information can be found via the [Kubebuilder Documentation](https://book.kubebuilder.io/introduction.html)

## License

Copyright 2026.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

