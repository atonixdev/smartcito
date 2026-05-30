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

package controller

import (
	"context"
	"fmt"

	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	apierrors "k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	"sigs.k8s.io/controller-runtime/pkg/log"

	cachev1alpha1 "github.com/example/Orca-operator/api/v1alpha1"
)

// OrcaReconciler reconciles a Orca object
type OrcaReconciler struct {
	client.Client
	Scheme *runtime.Scheme
}

//+kubebuilder:rbac:groups=cache.example.com,resources=orcas,verbs=get;list;watch;create;update;patch;delete
//+kubebuilder:rbac:groups=cache.example.com,resources=orcas/status,verbs=get;update;patch
//+kubebuilder:rbac:groups=cache.example.com,resources=orcas/finalizers,verbs=update
//+kubebuilder:rbac:groups=apps,resources=deployments,verbs=get;list;watch;create;update;patch;delete

// Reconcile is part of the main kubernetes reconciliation loop which aims to
// move the current state of the cluster closer to the desired state.
// TODO(user): Modify the Reconcile function to compare the state specified by
// the Orca object against the actual cluster state, and then
// perform operations to make the cluster state reflect the state specified by
// the user.
//
// For more details, check Reconcile and its Result here:
// - https://pkg.go.dev/sigs.k8s.io/controller-runtime@v0.16.3/pkg/reconcile
func (r *OrcaReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	logger := log.FromContext(ctx)

	orca := &cachev1alpha1.Orca{}
	if err := r.Get(ctx, req.NamespacedName, orca); err != nil {
		return ctrl.Result{}, client.IgnoreNotFound(err)
	}

	deployment := &appsv1.Deployment{ObjectMeta: metav1.ObjectMeta{Name: workloadName(orca.Name), Namespace: orca.Namespace}}
	_, err := controllerutil.CreateOrUpdate(ctx, r.Client, deployment, func() error {
		labels := workloadLabels(orca.Name)
		deployment.Labels = labels
		deployment.Spec.Selector = &metav1.LabelSelector{MatchLabels: labels}
		deployment.Spec.Replicas = ptrTo(orca.DesiredReplicas())
		deployment.Spec.Template.ObjectMeta.Labels = labels
		deployment.Spec.Template.Spec.Containers = []corev1.Container{
			{
				Name:            "orca-platform",
				Image:           orca.Spec.Image,
				ImagePullPolicy: corev1.PullIfNotPresent,
				Env: []corev1.EnvVar{
					{Name: "ORCA_RESOURCE_NAME", Value: orca.Name},
					{Name: "ORCA_RESOURCE_NAMESPACE", Value: orca.Namespace},
				},
			},
		}

		return controllerutil.SetControllerReference(orca, deployment, r.Scheme)
	})
	if err != nil {
		logger.Error(err, "unable to reconcile managed deployment", "deployment", deployment.Name)
		return ctrl.Result{}, err
	}

	phase := "Progressing"
	if deployment.Status.ReadyReplicas >= orca.DesiredReplicas() && deployment.Status.AvailableReplicas >= orca.DesiredReplicas() {
		phase = "Ready"
	}

	if orca.Status.DeploymentName != deployment.Name ||
		orca.Status.ReadyReplicas != deployment.Status.ReadyReplicas ||
		orca.Status.ObservedGeneration != orca.Generation ||
		orca.Status.Phase != phase {
		updated := orca.DeepCopy()
		updated.Status.DeploymentName = deployment.Name
		updated.Status.ReadyReplicas = deployment.Status.ReadyReplicas
		updated.Status.ObservedGeneration = updated.Generation
		updated.Status.Phase = phase

		if err := r.Status().Update(ctx, updated); err != nil {
			if apierrors.IsConflict(err) {
				return ctrl.Result{Requeue: true}, nil
			}

			logger.Error(err, "unable to update Orca status")
			return ctrl.Result{}, err
		}
	}

	return ctrl.Result{}, nil
}

// SetupWithManager sets up the controller with the Manager.
func (r *OrcaReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&cachev1alpha1.Orca{}).
		Owns(&appsv1.Deployment{}).
		Complete(r)
}

func workloadName(name string) string {
	return fmt.Sprintf("%s-control-plane", name)
}

func workloadLabels(name string) map[string]string {
	return map[string]string{
		"app.kubernetes.io/name":       "orca",
		"app.kubernetes.io/instance":   name,
		"app.kubernetes.io/managed-by": "orca-operator",
	}
}

func ptrTo[T any](value T) *T {
	return &value
}
