/*
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
*/

package v1alpha1

import (
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// EDIT THIS FILE!  THIS IS SCAFFOLDING FOR YOU TO OWN!
// NOTE: json tags are required.  Any new fields you add must have json tags for the fields to be serialized.

// OrcaSpec defines the desired state of Orca
type OrcaSpec struct {
	// Image is the container image used for the managed Orca workload.
	// +kubebuilder:validation:MinLength=1
	Image string `json:"image"`

	// Replicas is the desired number of Orca workload replicas.
	// +kubebuilder:default:=1
	// +kubebuilder:validation:Minimum=1
	Replicas *int32 `json:"replicas,omitempty"`
}

// OrcaStatus defines the observed state of Orca
type OrcaStatus struct {
	// Phase is a high-level summary of the managed workload state.
	Phase string `json:"phase,omitempty"`

	// DeploymentName is the name of the deployment managed for this Orca resource.
	DeploymentName string `json:"deploymentName,omitempty"`

	// ReadyReplicas is the number of ready replicas observed on the managed deployment.
	ReadyReplicas int32 `json:"readyReplicas,omitempty"`

	// ObservedGeneration tracks the latest Orca generation processed by the controller.
	ObservedGeneration int64 `json:"observedGeneration,omitempty"`
}

//+kubebuilder:object:root=true
//+kubebuilder:subresource:status
//+kubebuilder:printcolumn:name="Image",type="string",JSONPath=".spec.image"
//+kubebuilder:printcolumn:name="Ready",type="integer",JSONPath=".status.readyReplicas"
//+kubebuilder:printcolumn:name="Phase",type="string",JSONPath=".status.phase"

// Orca is the Schema for the orcas API
type Orca struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   OrcaSpec   `json:"spec,omitempty"`
	Status OrcaStatus `json:"status,omitempty"`
}

//+kubebuilder:object:root=true

// OrcaList contains a list of Orca
type OrcaList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []Orca `json:"items"`
}

func init() {
	SchemeBuilder.Register(&Orca{}, &OrcaList{})
}

// DesiredReplicas returns the configured replica count, defaulting to 1.
func (in *Orca) DesiredReplicas() int32 {
	if in.Spec.Replicas == nil {
		return 1
	}

	return *in.Spec.Replicas
}
